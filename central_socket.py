import asyncio
from datetime import datetime
import websockets
import aiohttp
import json
import logging
from database import get_db
from models import PurchaseData

# 로거 설정
logger = logging.getLogger('ReverbTestController')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
db = next(get_db())

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
    
    def __init__(self):
        self.bearer_token = ""
        self.login_uri = "http://127.0.0.1:8000/api/login"
        self.channel_name = "private-admin_penal" 
        self.server_url = "ws://192.168.200.115:6001/app/zyyqa9xa1labneonsu90"
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
            logger.debug(f'채널 인증 시도 - Channel: {self.channel_name}, SocketId: {socket_id}')
            self.socket_id = socket_id
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.bearer_token}',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                }
                params = {
                    'socket_id': socket_id,
                    'channel_name': self.channel_name
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
                        return {
                            'auth': auth_data['auth'],
                            'channel_data': auth_data.get('channel_data', '')
                        }
                    else:
                        logger.error(f'채널 인증 실패: {response.status} - {response_text}')
                        raise Exception(f'Authentication failed: {response.status} - {response_text}')
                        
        except Exception as e:
            logger.error(f'인증 처리 중 에러 발생: {e}')
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

    async def handle_websocket(self):
        """WebSocket 연결 및 메시지 처리를 담당하는 메서드"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            logger.info('WebSocket 연결 성공')
            
            # 연결 후 대기 중인 메시지가 있으면 전송
            if self.message_queue:
                for queued_message in self.message_queue:
                    await self.websocket.send(json.dumps(queued_message))
                logger.info(f'{len(self.message_queue)}개의 대기 메시지 전송 완료')
                self.message_queue = []  # 큐 비우기
            
            # 별도의 태스크로 메시지 수신 처리
            if not self.is_handling_message:
                self.is_handling_message = True
                asyncio.create_task(self.listen_for_messages())
            
            return True
        except Exception as e:
            logger.error(f'WebSocket 연결 중 에러 발생: {e}')
            self.is_connected = False
            return False

    async def listen_for_messages(self):
        """WebSocket 메시지 수신을 담당하는 메서드"""
        try:
            while True:
                if self.websocket == None:
                    logger.warning("WebSocket이 연결되지 않았습니다. 재연결 시도...")
                    await self.handle_websocket()
                    await asyncio.sleep(5)  # 재연결 대기
                    continue
                
                try:
                    message = await self.websocket.recv()
                    data = json.loads(message)
                    logger.debug(f'수신된 메시지: {data}')
                    
                    if data["event"] == "pusher:ping":
                        # ping 이벤트에 대한 올바른 pong 응답
                        pong_response = {
                            "event": "pusher:pong",
                            "data": {}
                        }
                        await self.websocket.send(json.dumps(pong_response))
                    
                    elif data['event'] == 'pusher:connection_established':
                        connection_data = json.loads(data['data'])
                        socket_id = connection_data['socket_id']
                        logger.debug(f'Socket ID: {socket_id}')
                        
                        logger.debug(f'로그인 시도 - User ID: {self.user_id}, User PWD: {self.user_pwd}')
                        auth_response = await self.request_auth()
                        if auth_response and auth_response is not False:
                            auth_data = await self.broadcast_authentication(socket_id)
                            if auth_data:
                                await self.subscribe_to_private_channel(
                                    self.channel_name,
                                    auth_data,
                                    self.websocket
                                )
                        else:
                            logger.error('인증 실패로 채널 구독을 진행할 수 없습니다.')
                            self.is_connected = False
                    
                    elif data['event'] == 'pusher_internal:subscription_succeeded':
                        logger.info('채널 구독 성공')
                        self.is_connected = True
                        self.is_subscribed = True  # 구독 성공 시 플래그 설정
                        
                        # 구독 성공 시 대기 중인 메시지 전송
                        if self.message_queue:
                            logger.info(f'구독 성공 후 {len(self.message_queue)}개의 대기 메시지 전송 시작')
                            for queued_message in self.message_queue:
                                await self.websocket.send(json.dumps(queued_message))
                            logger.info('대기 메시지 전송 완료')
                            self.message_queue = []  # 큐 비우기
                    elif data['event'] == 'pusher:error':
                        error_data = json.loads(data['data'])
                        logger.error(f'Pusher 에러: {error_data["code"]} - {error_data["message"]}')
                    elif data['event'] == r'App\Events\PurchaseEvent':
                        purchase_data_json = json.loads(data['data'])
                        purchase_data = purchase_data_json["purchaseLog"]
                        logger.info(f'구매 이벤트 수신: {purchase_data["user_id"]}')
                        
                        # datetime 객체로 변환하여 SQLite 오류 해결
                        purchased_at_str = purchase_data['purchased_at']
                        purchased_at_datetime = datetime.strptime(purchased_at_str, '%Y-%m-%d %H:%M:%S')
                        
                        # 기존 레코드 확인
                        existing_purchase = db.query(PurchaseData).filter(PurchaseData.id == purchase_data['id']).first()
                        
                        if existing_purchase:
                            # 기존 레코드가 있으면 업데이트
                            existing_purchase.purchase_type = purchase_data['purchase_type']
                            existing_purchase.payment_type = purchase_data['payment_type']
                            existing_purchase.table_id = purchase_data['table_id']
                            existing_purchase.game_id = purchase_data['game_id']
                            existing_purchase.user_id = purchase_data['user_id']
                            existing_purchase.purchased_at = purchased_at_datetime
                            existing_purchase.item = purchase_data['item']
                            existing_purchase.payment_status = purchase_data['payment_status']
                            existing_purchase.status = purchase_data['status']
                            existing_purchase.price = purchase_data['price']
                            existing_purchase.used_points = purchase_data['used_points']
                        else:
                            # 새 레코드 추가
                            db.add(PurchaseData(
                                id = purchase_data['id'],
                                purchase_type = purchase_data['purchase_type'],
                                payment_type = purchase_data['payment_type'],
                                table_id = purchase_data['table_id'],
                                game_id = purchase_data['game_id'],
                                user_id = purchase_data['user_id'],
                                purchased_at = purchased_at_datetime,  # 문자열 대신 datetime 객체 사용
                                item = purchase_data['item'],
                                payment_status = purchase_data['payment_status'],
                                status = purchase_data['status'],
                                price = purchase_data['price'],
                                used_points = purchase_data['used_points'],
                            ))
                        db.commit()
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket 연결이 닫혔습니다. 재연결 시도...")
                    self.is_connected = False
                    self.websocket = None
                    self.is_handling_message = False
                    await asyncio.sleep(5)  # 재연결 대기
        
        except Exception as e:
            logger.error(f'메시지 수신 중 에러 발생: {e}')
            self.is_connected = False
            self.websocket = None
            self.is_handling_message = False
    async def create_game_data(self, game_data):
        """게임 데이터 생성 메시지를 보내는 메서드"""
        logger.info(f'게임 데이터 생성 메시지 전송 시도: 게임 ID {game_data.id}')
        game_data_json = game_data.to_json()
        await self.send_message("App\\Events\\WebSocketMessageListener", "private-admin_penal", "GameData", game_data_json)

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
            logger.warning(f'WebSocket 연결 또는 채널 구독이 없습니다. 메시지를 큐에 저장합니다.')
            self.message_queue.append(subscription_message)
            logger.info(f'현재 대기 메시지 수: {len(self.message_queue)}개')
            
            if not self.is_connected or not self.websocket:
                # 연결이 끊어진 경우 재연결 시도
                await self.handle_websocket()
            return
        
        try:
            await self.websocket.send(json.dumps(subscription_message))
            logger.info(f'메시지 전송 성공: {event_name}')
        except Exception as e:
            logger.warning(f'메시지 전송 실패, 큐에 저장: {e}')
            self.message_queue.append(subscription_message)
            logger.info(f'현재 대기 메시지 수: {len(self.message_queue)}개')
            self.is_connected = False
            self.is_subscribed = False  # 예외 발생 시 구독 상태도 초기화
            self.websocket = None
            # 연결 재시도
            await self.handle_websocket()

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
        
        # 이미 연결되어 있다면 연결을 재사용
        if self.is_connected and self.websocket:
            logger.debug('이미 WebSocket이 연결되어 있습니다. 기존 연결을 유지합니다.')
            return True
        
        # 인증 요청 먼저 수행
        auth_result = await self.request_auth()
        if not auth_result or auth_result is False:
            logger.error('인증 실패. WebSocket 연결을 진행하지 않습니다.')
            return False
            
        success = await self.handle_websocket()
        return success