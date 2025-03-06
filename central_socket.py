import asyncio
from datetime import datetime
import certifi
import websockets
import aiohttp
import json
import logging
import os
from pathlib import Path
from database import get_db_direct
from models import PurchaseData
import models
import ssl
from auth_manager import AuthManager

# 로거 설정
logger = logging.getLogger('ReverbTestController')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# SSL 인증서 검증을 비활성화하는 컨텍스트 생성
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

class MessageQueueManager:
    """메시지 큐를 관리하는 클래스"""
    def __init__(self, store_path: str = None):
        self.store_path = store_path or os.path.join(os.path.expanduser('~'), '.dealer_desk', 'message_queue')
        self.ensure_store_directory()
        
    def ensure_store_directory(self):
        """저장소 디렉토리가 존재하는지 확인하고 없으면 생성"""
        Path(self.store_path).mkdir(parents=True, exist_ok=True)
        
    def get_queue_file_path(self, tenant_id: str) -> str:
        """테넌트별 큐 파일 경로 반환"""
        return os.path.join(self.store_path, f'queue_{tenant_id}.json')
        
    def save_message(self, tenant_id: str, message: dict):
        """메시지를 큐에 저장"""
        file_path = self.get_queue_file_path(tenant_id)
        try:
            # 기존 메시지 로드
            messages = []
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    messages = json.load(f)
            
            # 새 메시지 추가
            messages.append({
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
            
            # 파일에 저장
            with open(file_path, 'w') as f:
                json.dump(messages, f, indent=2)
                
            logger.info(f'메시지가 성공적으로 저장되었습니다: {file_path}')
            return True
        except Exception as e:
            logger.error(f'메시지 저장 중 에러 발생: {e}')
            return False
            
    def get_messages(self, tenant_id: str) -> list:
        """저장된 메시지 조회"""
        file_path = self.get_queue_file_path(tenant_id)
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f'메시지 로드 중 에러 발생: {e}')
            return []
            
    def clear_messages(self, tenant_id: str) -> bool:
        """저장된 메시지 삭제"""
        file_path = self.get_queue_file_path(tenant_id)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f'메시지 삭제 중 에러 발생: {e}')
            return False

class ReverbTestController:
    socket_id = ""
    is_connected:bool = False
    is_subscribed:bool = False
    message_queue = []
    websocket = None
    user_id = ""
    user_pwd = ""
    tenant_id = ""
    is_handling_message = False
    auth_event = None
    store_name = ""
    stores = []
    selected_store = None  # 선택된 매장 정보
    _listening_task = None
    _reconnect_attempts = 0
    MAX_RECONNECT_ATTEMPTS = 5
    
    def __init__(self):
        self.bearer_token = ""
        self.channel_name = "private-admin_penal_"
        self.is_ssl = True
        self.base_url = "dealer-desk.dev.amuz.kr"
        self.server_url = f"{'wss' if self.is_ssl else 'ws'}://{self.base_url}/app/hyx4ylczjr3sndkwqx8u"
        self.auth_event = asyncio.Event()
        self.queue_manager = MessageQueueManager()
        self.auth_manager = AuthManager()
        self.is_offline_mode = False

    async def request_auth(self):
        """인증 요청을 수행하는 메서드"""
        try:
            logger.debug(f'로그인 시도 - User ID: {self.user_id}, User PWD: {self.user_pwd}')
            
            # 저장된 인증 데이터 확인
            saved_auth = self.auth_manager.load_auth_data()
            if saved_auth:
                if saved_auth['user_id'] == self.user_id and saved_auth['user_pwd'] == self.user_pwd:
                    logger.info('저장된 인증 정보로 오프라인 로그인 시도')
                    self.stores = saved_auth['stores']
                    self.is_offline_mode = True
                    return {"token": "offline_mode", "stores": self.stores}
            
            # 온라인 인증 시도
            try:
                async with aiohttp.ClientSession() as session:
                    auth_data = { 
                        "email": self.user_id,
                        "password": self.user_pwd
                    }
                    headers = {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                    logger.debug('온라인 로그인 시도')
                    async with session.post(
                        f"{'https' if self.is_ssl else 'http'}://{self.base_url + (':' + str(8000) if not self.is_ssl else '')}/api/login",
                        json=auth_data,
                        headers=headers,
                        ssl=ssl_context if self.is_ssl else None
                    ) as response:
                        data = await response.json()
                        print(data)
                        if data:
                            # 성공적인 온라인 인증 시 데이터 저장
                            self.bearer_token = data['token']
                            logger.info(f'bearer_token: {self.bearer_token}')
                            if self.bearer_token == None:
                                raise Exception("토큰이 없습니다.")
                            self.stores = data['stores']
                            self.is_offline_mode = False
                            
                            # 인증 데이터 저장 (기존 데이터와 다른 경우에만)
                            if not saved_auth or saved_auth['user_id'] != self.user_id or saved_auth['user_pwd'] != self.user_pwd:
                                logger.info('새로운 인증 정보 저장')
                                self.auth_manager.save_auth_data(self.user_id, self.user_pwd, self.stores)
                            
                            return data
                        else:
                            raise Exception('토큰이 응답에 없습니다.')
            except Exception as e:
                logger.error(f'온라인 인증 실패: {e}')
                # 온라인 인증 실패 시 저장된 인증 정보로 재시도
                if saved_auth and saved_auth['user_id'] == self.user_id and saved_auth['user_pwd'] == self.user_pwd:
                    logger.info('온라인 인증 실패로 인한 오프라인 모드 전환')
                    self.stores = saved_auth['stores']
                    self.is_offline_mode = True
                    return {"token": "offline_mode", "stores": self.stores}
                raise
                
        except Exception as e:
            logger.error(f'인증 처리 중 오류 발생: {e}')
            return False

    async def select_store(self, store_id: int):
        """매장 선택 및 소켓 연결 메서드"""
        try:
            # 선택된 매장 찾기
            selected_store = next((store for store in self.stores if store['id'] == store_id), None)
            if not selected_store:
                raise Exception(f'매장 ID {store_id}를 찾을 수 없습니다.')
            
            # 매장 정보 설정
            self.selected_store = selected_store
            self.tenant_id = selected_store['tenant_id']
            self.store_name = selected_store['name']
            logger.info(f'매장 선택: {self.store_name}')
            logger.info(f"오프라인 모드? {self.is_offline_mode}")
            # 오프라인 모드가 아닌 경우에만 소켓 연결 시도
            if not self.is_offline_mode:
                # 기존 연결 초기화
                await self.reset_state()
                
                # 새로운 소켓 연결 시도
                success = await self.handle_websocket()
                if not success:
                    logger.warning('소켓 연결 실패, 오프라인 모드로 전환')
                    self.is_offline_mode = True
                    return True
                
                try:
                    await asyncio.wait_for(self.auth_event.wait(), timeout=30.0)
                    if not self.is_connected or not self.is_subscribed:
                        logger.error('인증은 완료되었으나 연결 또는 구독 상태가 아닙니다')
                        self.is_offline_mode = True
                        return True
                except asyncio.TimeoutError:
                    logger.error('인증 타임아웃')
                    self.is_offline_mode = True
                    return True
            
            return True
            
        except Exception as e:
            logger.error(f'매장 선택 중 오류 발생: {e}')
            return False

    async def broadcast_authentication(self, socket_id):
        """WebSocket 채널 인증을 수행하는 메서드"""
        try:
            logger.debug(f'채널 인증 시도 - Channel: {self.channel_name+self.tenant_id}, SocketId: {socket_id}')
            self.socket_id = socket_id
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.bearer_token}',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                }
                params = {
                    'socket_id': socket_id,
                    'channel_name': self.channel_name+self.tenant_id
                }
                
                async with session.post(
                    f"{'https' if self.is_ssl else 'http'}://{self.base_url + (':' + str(8000) if not self.is_ssl else '')}/api/pusher/user-auth",
                    headers=headers,
                    params=params,
                    ssl=ssl_context if self.is_ssl else None
                ) as response:
                    logger.debug(f'인증 응답 상태 코드: {response.status}')
                    response_text = await response.text()
                    logger.debug(f'인증 응답 본문: {response_text}')

                    if response.status == 200:
                        auth_data = json.loads(response_text)
                        logger.info('채널 인증 성공')
                        self.is_connected = True  # 인증 성공 시 연결 상태 설정
                        return {
                            'auth': auth_data['auth'],
                            'channel_data': auth_data.get('channel_data', '')
                        }
                    else:
                        logger.error(f'채널 인증 실패: {response.status} - {response_text}')
                        self.is_connected = False
                        self.auth_event.set()  # 인증 실패 시 이벤트 설정
                        raise Exception(f'Authentication failed: {response.status} - {response_text}')
                        
        except Exception as e:
            logger.error(f'인증 처리 중 에러 발생: {e}')
            self.is_connected = False
            self.auth_event.set()  # 인증 실패 시 이벤트 설정
            raise

    async def subscribe_to_private_channel(self, channel_name, auth_data, websocket):
        """프라이빗 채널 구독을 요청하는 메서드"""
        logger.debug(f'프라이빗 채널 구독 시도 - Channel: {channel_name}')
        subscription_message = {
            "event": "pusher:subscribe",
            "data": {
                "channel": channel_name,
                "auth": auth_data['auth'],
            }
        }
        logger.debug(f'구독 메시지 전송: {json.dumps(subscription_message)}')
        await websocket.send(json.dumps(subscription_message))

    async def reset_state(self):
        """모든 상태를 초기화하는 메서드"""
        logger.info('상태 초기화 시작')
        try:
            # 리스닝 태스크 취소
            if self._listening_task and not self._listening_task.done():
                self._listening_task.cancel()
                try:
                    await self._listening_task
                except asyncio.CancelledError:
                    pass
                self._listening_task = None
            
            if self.websocket:
                await self.websocket.close()
                
            # 연결 관련 상태 초기화
            self.is_connected = False
            self.is_subscribed = False
            self.is_handling_message = False
            self.websocket = None
            self.socket_id = ""
            
            logger.info('상태 초기화 완료')
            return True
        except Exception as e:
            logger.error(f'상태 초기화 중 에러 발생: {e}')
            return False

    async def handle_websocket(self):
        """WebSocket 연결 및 메시지 처리를 담당하는 메서드"""
        while self._reconnect_attempts < self.MAX_RECONNECT_ATTEMPTS:
            try:
                # 이전 상태 초기화
                await self.reset_state()
                
                
                # 새로운 WebSocket 연결 시도
                self.websocket = await websockets.connect(
                    self.server_url,
                    ssl=ssl_context if self.is_ssl else None
                )
                logger.info('WebSocket 연결 성공')
                
                # 연결 성공 시 재시도 카운터 초기화
                self._reconnect_attempts = 0
                
                # 새로운 listening 태스크 시작
                self._listening_task = asyncio.create_task(self.listen_for_messages())
                
                return True
                
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                self._reconnect_attempts += 1
                wait_time = min(2 ** self._reconnect_attempts, 60)  # 지수 백오프, 최대 60초
                logger.error(f'WebSocket 연결 실패 ({self._reconnect_attempts}/{self.MAX_RECONNECT_ATTEMPTS}): {e}')
                logger.info(f'{wait_time}초 후 재시도...')
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f'예기치 않은 에러 발생: {e}')
                await self.reset_state()
                return False
                
        logger.error(f'최대 재시도 횟수({self.MAX_RECONNECT_ATTEMPTS})를 초과했습니다.')
        return False

    async def listen_for_messages(self):
        """WebSocket 메시지 수신을 담당하는 메서드"""
        try:
            while True:
                if not self.user_id or not self.bearer_token:  # 로그아웃 상태 체크
                    logger.info("로그아웃 상태입니다. 메시지 수신을 중단합니다.")
                    await self.reset_state()
                    break
                    
                if not self.websocket:
                    logger.warning("WebSocket이 연결되지 않았습니다.")
                    await self.reset_state()
                    break  # 연결이 끊긴 상태에서는 재연결을 시도하지 않고 종료
                
                try:
                    message = await self.websocket.recv()
                    data = json.loads(message)
                    logger.debug(f'수신된 메시지: {data}')
                    
                    if data["event"] == "pusher:ping":
                        pong_response = {
                            "event": "pusher:pong",
                            "data": {}
                        }
                        await self.websocket.send(json.dumps(pong_response))
                    
                    elif data['event'] == 'pusher:connection_established':
                        connection_data = json.loads(data['data'])
                        socket_id = connection_data['socket_id']
                        logger.debug(f'Socket ID: {socket_id}')
                        
                        auth_data = await self.broadcast_authentication(socket_id)
                        if auth_data:
                            await self.subscribe_to_private_channel(
                                self.channel_name+self.tenant_id,
                                auth_data,
                                self.websocket
                            )
                    
                    elif data['event'] == 'pusher_internal:subscription_succeeded':
                        logger.info('채널 구독 성공')
                        self.is_connected = True
                        self.is_subscribed = True
                        self.auth_event.set()
                        
                        # 구독 성공 시 저장된 메시지 처리
                        await self.process_queued_messages()
                    
                    elif data['event'] == 'pusher:error':
                        error_data = json.loads(data['data'])
                        logger.error(f'Pusher 에러: {error_data["code"]} - {error_data["message"]}')
                        if error_data["code"] == 4009:
                            await self.reset_state()
                            self.auth_event.set()
                            raise Exception(f'인증 실패: {error_data["message"]}')
                    elif data['event'] == 'App\\Events\\ToAdminPanel\\PurchaseEvent':
                        logger.info('메시지 수신')
                        purchase_data = json.loads(data['data'])['purchaseLog']
                        purchase_model = PurchaseData(
                            purchase_type=purchase_data['purchase_type'],
                            game_id=purchase_data['game_id'],
                            customer_id=purchase_data['customer_id'], 
                            uuid=purchase_data['uuid'],
                            purchased_at=datetime.strptime(purchase_data['purchased_at'], '%Y-%m-%d %H:%M:%S'),
                            item=purchase_data['item'],
                            payment_status=purchase_data['payment_status'],
                            status=purchase_data['status'],
                            price=purchase_data['price'],
                            used_points=purchase_data['used_points']
                        )
                        
                        # 데이터베이스 세션 가져오기
                        db = get_db_direct()
                        try:
                            db.add(purchase_model)
                            db.commit()
                            db.refresh(purchase_model)
                            logger.info(f'구매 데이터 저장: {purchase_model.id}')
                        finally:
                            db.close()
                        
                    elif data['event'] == 'App\\Events\\ToAdminPanel\\RegisterEvent':
                        logger.info('가입 메시지 수신')
                        customer_data = json.loads(data['data'])['customer']
                        logger.info(f'가입 데이터: {customer_data}')
                        
                        # 데이터베이스 세션 가져오기
                        db = get_db_direct()
                        try:
                            # 가입 데이터를 데이터베이스에 저장
                            customer_model = models.UserData(
                                name=customer_data['name'],
                                phone_number=customer_data['phone_number'],
                                regist_mail=customer_data['regist_mail'],
                                uuid=customer_data['uuid'],
                                game_join_count=customer_data['game_join_count'],
                                visit_count=customer_data['visit_count'],
                                register_at=datetime.strptime(customer_data['register_at'], '%Y-%m-%d %H:%M:%S'),
                                last_visit_at=datetime.strptime(customer_data['last_visit_at'], '%Y-%m-%d %H:%M:%S'),
                                point=customer_data['point'],
                                total_point=customer_data['total_point'],
                                remark=customer_data['remark'],
                                awarding_history=customer_data['awarding_history'],
                                point_history=customer_data['point_history']
                            )
                            db.add(customer_model)
                            db.commit()
                            db.refresh(customer_model)
                        finally:
                            db.close()
                        
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket 연결이 닫혔습니다.")
                    await self.reset_state()
                    break  # 연결이 끊긴 상태에서는 재연결을 시도하지 않고 종료
                    
                except Exception as e:
                    logger.error(f'메시지 처리 중 에러 발생: {e}')
                    await self.reset_state()
                    break  # 에러 발생 시 재연결을 시도하지 않고 종료
        
        except asyncio.CancelledError:
            logger.info("메시지 수신 태스크가 취소되었습니다.")
            await self.reset_state()
            raise
        except Exception as e:
            logger.error(f'메시지 수신 중 치명적인 에러 발생: {e}')
            await self.reset_state()
        finally:
            logger.info("메시지 수신 태스크 종료")

    async def create_game_data(self, game_data):
        """게임 데이터 생성 메시지를 보내는 메서드"""
        logger.info(f'게임 데이터 생성 메시지 전송 시도: 게임 ID {game_data.id}')
        game_data_json = game_data.to_json()
        await self.send_message("App\\Events\\WebSocketMessageListener", channel_name=self.channel_name+self.tenant_id, data_type="GameData", message=game_data_json)

    async def update_game_data(self, game_data):
        """게임 데이터 업데이트 메시지를 보내는 메서드"""
        logger.info(f'게임 데이터 업데이트 메시지 전송 시도: 게임 ID {game_data.id}')
        game_data_json = game_data.to_json()
        await self.send_message("App\\Events\\WebSocketMessageListener", channel_name=self.channel_name+self.tenant_id, data_type="GameData", message=game_data_json)
        
    async def update_purchase_data_payment_success(self, purchase_data:models.PurchaseData):
        """구매 데이터 업데이트 메시지를 보내는 메서드"""
        logger.info(f'구매 데이터 업데이트 메시지 전송 시도: 구매 ID {purchase_data.id}')
        await self.send_message("App\\Events\\WebSocketMessageListener", channel_name=self.channel_name+self.tenant_id, data_type="PaymentSuccess", message=purchase_data.uuid)

    async def update_purchase_data_chip_success(self, purchase_data:models.PurchaseData):
        """구매 데이터 업데이트 메시지를 보내는 메서드"""
        logger.info(f'구매 데이터 업데이트 메시지 전송 시도: 구매 ID {purchase_data.id}')
        await self.send_message("App\\Events\\WebSocketMessageListener", channel_name=self.channel_name+self.tenant_id, data_type="ChipSuccess", message=purchase_data.uuid)

    async def send_message(self, event_name, channel_name, data_type, message):
        """메시지를 WebSocket을 통해 전송하는 메서드"""
        subscription_message = {
            "event": event_name,
            "channel": channel_name,
            "data": {
                "tenant_id": self.tenant_id,
                "dataType": data_type,
                "data": message,
                "timestamp": datetime.now().isoformat()
            },
        }
        
        if not self.is_connected or not self.websocket or not self.is_subscribed:
            logger.warning('WebSocket이 연결되어 있지 않거나 구독되지 않았습니다.')
            # 메시지를 JSON 파일에 저장
            self.queue_manager.save_message(self.tenant_id, subscription_message)
            return False
            
        try:
            await self.websocket.send(json.dumps(subscription_message))
            logger.info(f'메시지 전송 성공: {event_name}')
            return True
        except Exception as e:
            logger.error(f'메시지 전송 실패: {e}')
            # 실패한 메시지를 JSON 파일에 저장
            self.queue_manager.save_message(self.tenant_id, subscription_message)
            await self.reset_state()
            return False

    async def process_queued_messages(self):
        """저장된 메시지 처리"""
        if not self.is_connected or not self.websocket or not self.is_subscribed:
            return False
            
        try:
            messages = self.queue_manager.get_messages(self.tenant_id)
            if not messages:
                return True
                
            logger.info(f'저장된 메시지 처리 시작: {len(messages)}개')
            success = True
            
            for message_data in messages:
                try:
                    await self.websocket.send(json.dumps(message_data['message']))
                    logger.info(f'저장된 메시지 전송 성공: {message_data["message"]["event"]}')
                except Exception as e:
                    logger.error(f'저장된 메시지 전송 실패: {e}')
                    success = False
                    break
            
            if success:
                self.queue_manager.clear_messages(self.tenant_id)
                logger.info('모든 저장된 메시지 처리 완료')
            
            return success
        except Exception as e:
            logger.error(f'저장된 메시지 처리 중 에러 발생: {e}')
            return False

    async def subscribe_send_message(self, event_name, channel_name, data_type, message):
        """이전 버전의 메시지 전송 메서드 (하위 호환성을 위해 유지)"""
        await self.send_message(event_name, channel_name, data_type, message)

    async def login_with_token(self, token):
        """토큰을 사용한 로그인 메서드"""
        logger.debug('토큰으로 로그인 시도')
        self.bearer_token = token
        
        # 이미 연결되어 있다면 연결을 재사용
        if self.is_connected and self.websocket:
            logger.debug('이미 WebSocket이 연결되어 있습니다. 기존 연결을 유지합니다.')
            return True
            
        # 새로운 WebSocket 연결 시도
        success = await self.handle_websocket()
        return success

    async def main(self, user_id, user_pwd):
        """메인 실행 메서드"""
        logger.debug('로그인 시도')
        self.user_id = user_id
        self.user_pwd = user_pwd
        self.auth_event.clear()
        
        # 인증 요청 수행
        auth_result = await self.request_auth()
        if not auth_result:
            logger.error('인증 실패')
            return False
            
        return True

    async def logout(self):
        """로그아웃 처리를 수행하는 메서드"""
        logger.info('로그아웃 처리 시작')
        try:
            # 리스닝 태스크 취소
            if self._listening_task and not self._listening_task.done():
                self._listening_task.cancel()
                try:
                    await self._listening_task
                except asyncio.CancelledError:
                    pass
                self._listening_task = None
            
            if self.websocket:
                await self.websocket.close()
                
            # 연결 관련 상태만 초기화
            self.is_connected = False
            self.is_subscribed = False
            self.is_handling_message = False
            self.websocket = None
            self.bearer_token = ""
            self.socket_id = ""
            self.message_queue = []
            self.auth_event.clear()
            self.is_offline_mode = False
            
            # 인증 데이터는 유지 (user_id, user_pwd, stores, tenant_id, store_name)
            
            logger.info('로그아웃 처리 완료 (인증 데이터 유지)')
            return True
        except Exception as e:
            logger.error(f'로그아웃 처리 중 오류 발생: {e}')
            return False