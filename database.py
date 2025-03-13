from datetime import datetime
import ssl
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
from fastapi import Depends, Request, HTTPException
import requests 
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import contextmanager
import aiohttp
import json

# 로거 설정
logger = logging.getLogger('DatabaseManager')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Base 클래스 생성
Base = declarative_base()

# 전역 변수로 현재 선택된 매장 ID 저장
current_store_id = None

def set_current_store_id(store_id):
    """현재 선택된 매장 ID 설정"""
    global current_store_id
    current_store_id = store_id
    logger.info(f"현재 매장 ID 설정: {store_id}")
    return store_id

def get_current_store_id():
    """현재 선택된 매장 ID 반환"""
    global current_store_id
    if current_store_id is None:
        logger.warning("현재 선택된 매장이 없습니다. 기본 매장 ID를 사용합니다.")
        return 0  # 기본 매장 ID
    return current_store_id

class DatabaseManager:
    def __init__(self):
        self.engines = {}
        self.session_makers = {}
        self.db_directory = os.path.join(os.path.expanduser("~/.dealer_desk"), ".databases")  # 윈도우 호환성을 위해 경로 수정
        
        # 데이터베이스 디렉토리가 없으면 생성
        if not os.path.exists(self.db_directory):
            os.makedirs(self.db_directory)
            logger.info(f"데이터베이스 디렉토리 생성: {self.db_directory}")
    
    def get_db_path(self, store_id):
        """매장별 데이터베이스 파일 경로 반환"""
        return os.path.join(self.db_directory, f"store_{store_id}.db")
    
    def create_engine_for_store(self, store_id):
        """매장별 데이터베이스 엔진 생성"""
        db_path = self.get_db_path(store_id)
        logger.info(f"데이터베이스 엔진 생성 시도: {db_path}")
        
        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False}
        )
        
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA encoding='UTF-8'")
            cursor.close()
            
        return engine
    
    def initialize_store_db(self, store_id):
        """매장별 데이터베이스 초기화"""
        try:
            logger.info(f"매장 {store_id}의 데이터베이스 초기화 시작")
            
            # 이미 엔진이 있는지 확인
            if store_id in self.engines:
                logger.info(f"매장 {store_id}의 데이터베이스 엔진이 이미 존재합니다")
                return
            
            # 새 엔진 생성
            engine = self.create_engine_for_store(store_id)
            self.engines[store_id] = engine
            self.session_makers[store_id] = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine
            )
            
            # models 모듈 임포트
            import models
            import main
            
            # 데이터베이스 파일이 없거나 테이블이 없으면 생성
            db_path = self.get_db_path(store_id)
            if not os.path.exists(db_path):
                logger.info(f"매장 {store_id}의 새 데이터베이스 파일 생성")
                Base.metadata.create_all(bind=engine)
                db = self.session_makers[store_id]()
                # 서버에 데이터 가져오기
                try:
                    # 오프라인 모드가 아닐 때만 서버에서 데이터 동기화 시도
                    if not main.socket_controller.is_offline_mode:
                        host_name = next((store['host'] for store in main.socket_controller.stores if store['id'] == store_id), None)
                        request_url = f"http://{main.socket_controller.base_url}/api/sync/all/{host_name}"
                        headers = {
                            'Content-Type': 'application/json',
                            'Accept': 'application/json',
                            "Authorization": f"Bearer {main.socket_controller.bearer_token}"
                        }
                        logger.info(request_url)
                        logger.info(f"Bearer 토큰: {main.socket_controller.bearer_token}")
                        
                        # 데이터베이스 디렉토리 확인 및 생성
                        db_dir = os.path.dirname(db_path)
                        if not os.path.exists(db_dir):
                            os.makedirs(db_dir)
                            logger.info(f"데이터베이스 디렉토리 생성: {db_dir}")
                        
                        # SSL 인증서 검증을 비활성화하는 컨텍스트 생성
                        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
                        ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
                        ssl_context.check_hostname = False
                        ssl_context.verify_mode = ssl.CERT_NONE
                        
                        session = requests.Session()
                        response = session.get(request_url, headers=headers,)
                        
                        if response.status_code == 200:
                            data = response.json()
                            logger.info(f"매장 {store_id}의 데이터 동기화 성공")
                            logger.info(f"매장 {store_id}의 데이터: {data}")
                            
                            # 데이터 저장 전에 트랜잭션 관리 개선
                            try:
                                # 테이블 데이터 저장
                                if 'tables' in data and data['tables']:
                                    for table in data['tables']:
                                        # 테이블 데이터에서 필요한 필드만 추출하여 모델 생성
                                        table_obj = {}
                                        for key, value in table.items():
                                            if hasattr(models.TableData, key):
                                                # title이 {"ko": name} 형식으로 들어오는 경우 name만 추출
                                                if key == "title" and isinstance(value, dict) and "ko" in value:
                                                    table_obj[key] = value["ko"]
                                                else:
                                                    table_obj[key] = value
                                        table_data = models.TableData(**table_obj)
                                        db.add(table_data)
                                    db.commit()
                                
                                # 프리셋 데이터 저장
                                if 'presets' in data and data['presets']:
                                    for preset in data['presets']:
                                        preset_obj = {}
                                        for key, value in preset.items():
                                            if hasattr(models.PresetData, key):
                                                preset_obj[key] = value
                                        preset_data = models.PresetData(**preset_obj)
                                        db.add(preset_data)
                                    db.commit()
                                
                                # 게임 데이터 저장
                                if 'games' in data and data['games']:
                                    for game in data['games']:
                                        game_obj = {}
                                        for key, value in game.items():
                                            if key == 'starting_chip':
                                                print(f"starting_chip: {value}")
                                                game_obj['starting_chip'] = value
                                            elif key == 'starting_chips':
                                                print(f"starting_chips -> starting_chip으로 변환: {value}")
                                                game_obj['starting_chip'] = value
                                            if hasattr(models.GameData, key):
                                                # datetime 필드 처리
                                                if key in ['game_start_time', 'game_calcul_time', 'game_stop_time', 'game_end_time'] and isinstance(value, str):
                                                    try:
                                                        if 'T' in value:  # ISO 형식
                                                            game_obj[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                                        else:  # 일반 형식
                                                            game_obj[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                                                    except ValueError:
                                                        logger.warning(f"게임 날짜 형식 변환 실패: {key}={value}, None으로 설정")
                                                        game_obj[key] = None
                                                # title 필드 처리 (dict 형식인 경우)
                                                elif key == 'title' and isinstance(value, dict) and 'ko' in value:
                                                    game_obj[key] = value['ko']
                                                # starting_chip 필드를 starting_chip으로 변환
                                                    # JSON 필드는 그대로 저장 (문자열로 변환하지 않음)
                                                elif key in ['game_in_player', 'table_connect_log', 'time_table_data', 'rebuyin_payment_chips', 
                                                           'rebuyin_number_limits', 'addon_data', 'prize_settings', 'rebuy_cut_off']:
                                                    # 문자열로 들어온 경우 JSON으로 파싱
                                                    if isinstance(value, str):
                                                        try:
                                                            game_obj[key] = json.loads(value)
                                                        except json.JSONDecodeError:
                                                            logger.warning(f"JSON 파싱 실패: {key}={value}, 빈 배열로 설정")
                                                            game_obj[key] = []
                                                    else:
                                                        game_obj[key] = value
                                                else:
                                                    game_obj[key] = value
                                        game_data = models.GameData(**game_obj)
                                        db.add(game_data)
                                    db.commit()
                                # 포인트 데이터 저장
                                if 'points' in data and data['points']:
                                    for point in data['points']:
                                        point_obj = {}
                                        for key, value in point.items():
                                            if hasattr(models.PointHistoryData, key):
                                                # datetime 필드 처리
                                                if key in ['expire_at', 'created_at'] and isinstance(value, str):
                                                    try:
                                                        if 'T' in value:  # ISO 형식
                                                            point_obj[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                                        else:  # 일반 형식
                                                            point_obj[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                                                    except ValueError:
                                                        logger.warning(f"날짜 형식 변환 실패: {key}={value}, None으로 설정")
                                                        point_obj[key] = None
                                                else:
                                                    point_obj[key] = value
                                        point_data = models.PointHistoryData(**point_obj)
                                        db.add(point_data)
                                    db.commit()
                                
                                # 고객 데이터 저장
                                if 'customers' in data and data['customers']:
                                    for customer in data['customers']:
                                        customer_obj = {}
                                        for key, value in customer.items():
                                            if hasattr(models.UserData, key):
                                                # datetime 문자열을 datetime 객체로 변환
                                                if key in ['register_at', 'last_visit_at'] and isinstance(value, str):
                                                    try:
                                                        customer_obj[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                                                    except ValueError:
                                                        try:
                                                            # ISO 형식 시도
                                                            customer_obj[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                                        except ValueError:
                                                            logger.warning(f"날짜 형식 변환 실패: {key}={value}, 현재 시간으로 설정")
                                                            customer_obj[key] = datetime.now()
                                                else:
                                                    customer_obj[key] = value
                                        customer_data = models.UserData(**customer_obj)
                                        db.add(customer_data)
                                    db.commit()
                                
                                # 구매 데이터 저장
                                if 'purchases' in data and data['purchases']:
                                    for purchase in data['purchases']:
                                        purchase_obj = {}
                                        for key, value in purchase.items():
                                            if hasattr(models.PurchaseData, key):
                                                # datetime 필드 처리
                                                if key.endswith('_at') and isinstance(value, str):
                                                    try:
                                                        if 'T' in value:  # ISO 형식
                                                            purchase_obj[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                                        else:  # 일반 형식
                                                            purchase_obj[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                                                    except ValueError:
                                                        logger.warning(f"날짜 형식 변환 실패: {key}={value}, 현재 시간으로 설정")
                                                        purchase_obj[key] = datetime.now()
                                                else:
                                                    purchase_obj[key] = value
                                        purchase_data = models.PurchaseData(**purchase_obj)
                                        db.add(purchase_data)
                                    db.commit()
                                # 상금 내역 데이터 저장
                                if 'awardings' in data and data['awardings']:
                                    for awarding in data['awardings']:
                                        awarding_obj = {}
                                        for key, value in awarding.items():
                                            if hasattr(models.AwardingHistoryData, key):
                                                if key.endswith('_at') and isinstance(value, str):
                                                    try:
                                                        awarding_obj[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                                    except ValueError:
                                                        logger.warning(f"날짜 형식 변환 실패: {key}={value}, 현재 시간으로 설정")
                                                        awarding_obj[key] = datetime.now()
                                                else:
                                                    awarding_obj[key] = value
                                                    
                                        awarding_data = models.AwardingHistoryData(**awarding_obj)
                                        db.add(awarding_data)
                                    db.commit()
                                
                            except Exception as tx_error:
                                db.rollback()
                                logger.error(f"데이터 저장 중 오류 발생: {tx_error}")
                                raise
                        else:
                            logger.warning(f"매장 {store_id}의 데이터 동기화 실패: 상태 코드 {response.status_code}")
                    else:
                        logger.info(f"오프라인 모드로 실행 중이므로 매장 {store_id}의 데이터 동기화를 건너뜁니다")
                except Exception as sync_error:
                    logger.error(f"매장 {store_id}의 데이터 동기화 중 오류 발생: {sync_error}")
                    # 동기화 실패해도 기본 테이블은 생성
                finally:
                    db.close()
            else:
                # 기존 데이터베이스에 누락된 테이블이 있는지 확인하고 생성
                logger.info(f"매장 {store_id}의 기존 데이터베이스 테이블 검사")
                Base.metadata.create_all(bind=engine)
            
            logger.info(f"매장 {store_id}의 데이터베이스 초기화 완료")
            
        except Exception as e:
            logger.error(f"매장 {store_id}의 데이터베이스 초기화 중 오류 발생: {e}")
            raise
    
    def get_db(self, store_id=None):
        """매장별 데이터베이스 세션 생성 (FastAPI 의존성 주입용)"""
        if store_id is None:
            store_id = get_current_store_id()
            
        if store_id not in self.session_makers:
            self.initialize_store_db(store_id)
            
        db = self.session_makers[store_id]()
        try:
            yield db
        finally:
            db.close()
    
    @contextmanager
    def get_db_session(self, store_id=None):
        """매장별 데이터베이스 세션 생성 (컨텍스트 매니저)"""
        if store_id is None:
            store_id = get_current_store_id()
            
        if store_id not in self.session_makers:
            self.initialize_store_db(store_id)
            
        db = self.session_makers[store_id]()
        try:
            yield db
        finally:
            db.close()
    
    def get_db_direct(self, store_id=None):
        """매장별 데이터베이스 세션 직접 반환 (컨트롤러용)"""
        if store_id is None:
            store_id = get_current_store_id()
            
        if store_id not in self.session_makers:
            self.initialize_store_db(store_id)
            
        return self.session_makers[store_id]()

# 전역 데이터베이스 매니저 인스턴스 생성
db_manager = DatabaseManager()

# DB 세션 의존성 (FastAPI 의존성 주입용)
def get_db():
    """현재 선택된 매장의 데이터베이스 세션 반환 (FastAPI 의존성 주입용)"""
    store_id = get_current_store_id()
    return db_manager.get_db(store_id)

# DB 세션 직접 반환 (컨트롤러용)
def get_db_direct():
    """현재 선택된 매장의 데이터베이스 세션 직접 반환 (컨트롤러용)"""
    store_id = get_current_store_id()
    return db_manager.get_db_direct(store_id)

# 매장 데이터베이스 초기화
def initialize_store_database(store_id):
    """매장 데이터베이스 초기화 함수"""
    try:
        logger.info(f"매장 {store_id} 데이터베이스 초기화 요청")
        db_manager.initialize_store_db(store_id)
        return True
    except Exception as e:
        logger.error(f"매장 {store_id} 데이터베이스 초기화 실패: {e}")
        return False

# 임의 플레이어 데이터 추가
def add_player_data():
    import models
    player_data = models.UserData(
        name="홍길동",
        phone_number="01012345678",
        regist_mail="hong@example.com",
        game_join_count=0,
        visit_count=0,
    )
    db = SessionLocal()
    db.add(player_data)
    db.commit()
    db.refresh(player_data)

# 매장 ID 미들웨어
class StoreIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 요청 헤더에서 매장 ID 확인
        store_id = request.headers.get("X-Store-ID")
        if store_id:
            try:
                store_id = int(store_id)
                set_current_store_id(store_id)
            except ValueError:
                logger.error(f"잘못된 매장 ID 형식: {store_id}")
        
        # 다음 미들웨어 또는 엔드포인트 호출
        response = await call_next(request)
        return response