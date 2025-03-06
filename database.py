from datetime import datetime
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
from fastapi import Depends, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import contextmanager

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
        return 1  # 기본 매장 ID
    return current_store_id

class DatabaseManager:
    def __init__(self):
        self.engines = {}
        self.session_makers = {}
        self.db_directory = "./databases"
        
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
            
            # 데이터베이스 파일이 없거나 테이블이 없으면 생성
            db_path = self.get_db_path(store_id)
            if not os.path.exists(db_path):
                logger.info(f"매장 {store_id}의 새 데이터베이스 파일 생성")
                Base.metadata.create_all(bind=engine)
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