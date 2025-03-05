import asyncio
from datetime import datetime
import websockets
import aiohttp
import json
import logging
import os
from pathlib import Path
from database import get_db
from models import PurchaseData
import models

# 로거 설정
logger = logging.getLogger('ReverbTestController')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
db = next(get_db())

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
    is_subscribed:bool = False  # 채널 구독 상태를 추적하는 플래그 추가
    message_queue = []
    websocket = None
    user_id = ""
    user_pwd = ""
    tenant_id = ""
    is_handling_message = False
    auth_event = None  # 인증 완료를 추적하기 위한 이벤트
    store_name = ""
    _listening_task = None  # 메시지 수신 태스크를 추적하기 위한 변수
    
    def __init__(self):
        self.bearer_token = ""
        self.login_uri = "http://127.0.0.1:8000/api/login"
        self.channel_name = "private-admin_penal_" 
        self.server_url = "ws://192.168.200.115:6001/app/zyyqa9xa1labneonsu90"
        self.auth_event = asyncio.Event()  # 인증 이벤트 초기화
        self.queue_manager = MessageQueueManager()  # 메시지 큐 매니저 초기화
        # logger.debug('ReverbTestController 초기화')
        # asyncio.run(self.main())

    async def request_auth(self):
        """인증 요청을 수행하는 메서드"""
        try:
            logger.debug(f'로그인 시도 - User ID: {self.user_id}, User PWD: {self.user_pwd}')
            async with aiohttp.ClientSession() as session:
                auth_data = { 
                    "email": self.user_id,
                    "password": self.user_pwd
                }
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                logger.debug('로그인 시도')
                async with session.post(
                    "http://192.168.200.115:8000/api/login",
                    json=auth_data,
                    headers=headers
                ) as response:
                    data = await response.json()
                    print(data)
                    if 'token' in data:
                        self.bearer_token = data['token']
                        self.tenant_id = data['stores'][0]['tenant_id']
                        self.store_name = data['stores'][0]['name']
                        logger.debug(f'Bearer Token: {self.bearer_token}')
                        return data
                    else:
                        logger.error('토큰이 응답에 없습니다. 인증 실패')
                        return False
        except Exception as e:
            logger.error(f'인증 에러 발생: {e}')
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
                    'http://192.168.200.115:8000/api/pusher/user-auth',
                    headers=headers,
                    params=params
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
        try:
            # 이전 상태 초기화
            await self.reset_state()
            
            # 새로운 WebSocket 연결 시도
            self.websocket = await websockets.connect(self.server_url)
            logger.info('WebSocket 연결 성공')
            
            # 새로운 listening 태스크 시작
            self._listening_task = asyncio.create_task(self.listen_for_messages())
            
            return True
        except Exception as e:
            logger.error(f'WebSocket 연결 중 에러 발생: {e}')
            await self.reset_state()
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
                    elif data['event'] == 'App\\Events\\PurchaseEvent':
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
                        db.add(purchase_model)
                        db.commit()
                        db.refresh(purchase_model)
                        logger.info(f'구매 데이터 저장: {purchase_model.id}')
                        
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
        await self.send_message("App\\Events\\WebSocketMessageListener", channel_name=self.channel_name+self.tenant_id, data_type="PaymentSucess", message=purchase_data.uuid)

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
        logger.debug('WebSocket 연결 시도: ' + self.server_url)
        self.user_id = user_id
        self.user_pwd = user_pwd
        self.auth_event.clear()  # 인증 이벤트 초기화
        
        # 이미 연결되어 있다면 연결을 재사용
        if self.is_connected and self.websocket and self.is_subscribed:
            logger.debug('이미 WebSocket이 연결되어 있습니다. 기존 연결을 유지합니다.')
            return True
        
        # 인증 요청 먼저 수행
        auth_result = await self.request_auth()
        if not auth_result or auth_result is False:
            logger.error('인증 실패. WebSocket 연결을 진행하지 않습니다.')
            return False
            
        success = await self.handle_websocket()
        if not success:
            return False
            
        # 인증 완료될 때까지 대기
        try:
            await asyncio.wait_for(self.auth_event.wait(), timeout=30.0)  # 30초 타임아웃으로 증가
            if not self.is_connected or not self.is_subscribed:
                logger.error('인증은 완료되었으나 연결 또는 구독 상태가 아닙니다.')
                return False
            return True
        except asyncio.TimeoutError:
            logger.error('인증 타임아웃')
            self.is_connected = False
            self.is_subscribed = False
            return False

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
                
            # 모든 상태 초기화
            self.is_connected = False
            self.is_subscribed = False
            self.is_handling_message = False
            self.websocket = None
            self.bearer_token = ""
            self.user_id = ""
            self.user_pwd = ""
            self.tenant_id = ""
            self.socket_id = ""
            self.store_name = ""
            self.message_queue = []
            self.auth_event.clear()
            
            logger.info('로그아웃 처리 완료')
            return True
        except Exception as e:
            logger.error(f'로그아웃 처리 중 에러 발생: {e}')
            return False