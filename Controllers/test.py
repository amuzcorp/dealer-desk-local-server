import asyncio
import websockets
import aiohttp
import json
import logging

# 로거 설정
logger = logging.getLogger('ReverbTestController')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class ReverbTestController:
    def __init__(self):
        self.bearer_token = ""
        self.login_uri = "http://127.0.0.1:8000/api/login"
        self.channel_name = "private-admin_penal" 
        self.server_url = "ws://192.168.200.115:6001/app/zyyqa9xa1labneonsu90"
        logger.debug('ReverbTestController 초기화')
        asyncio.run(self.main())

    async def request_auth(self):
        """인증 요청을 수행하는 메서드"""
        try:
            async with aiohttp.ClientSession() as session:
                auth_data = { 
                    "email": "test@amuz.co.kr",
                    "password": "amuz1234"
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
                    self.bearer_token = data['token']
                    logger.debug(f'Bearer Token: {self.bearer_token}')
                    return data
        except Exception as e:
            logger.error(f'인증 에러 발생: {e}')
            return None

    async def broadcast_authentication(self, socket_id):
        """WebSocket 채널 인증을 수행하는 메서드"""
        try:
            logger.debug(f'채널 인증 시도 - Channel: {self.channel_name}, SocketId: {socket_id}')
            
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
            async with websockets.connect(self.server_url) as websocket:
                logger.info('WebSocket 연결 성공')
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    logger.debug(f'수신된 메시지: {data}')
                    
                    if data["event"] == "pusher:ping":
                        # ping 이벤트에 대한 올바른 pong 응답
                        pong_response = {
                            "event": "pusher:pong",
                            "data": {}
                        }
                        await websocket.send(json.dumps(pong_response))
                    
                    elif data['event'] == 'pusher:connection_established':
                        connection_data = json.loads(data['data'])
                        socket_id = connection_data['socket_id']
                        logger.debug(f'Socket ID: {socket_id}')
                        
                        auth_response = await self.request_auth()
                        if auth_response:
                            auth_data = await self.broadcast_authentication(socket_id)
                            if auth_data:
                                await self.subscribe_to_private_channel(
                                    self.channel_name,
                                    auth_data,
                                    websocket
                                )
                    
                    elif data['event'] == 'pusher_internal:subscription_succeeded':
                        logger.info('채널 구독 성공')
                    
                    elif data['event'] == 'pusher:error':
                        error_data = json.loads(data['data'])
                        logger.error(f'Pusher 에러: {error_data["code"]} - {error_data["message"]}')
                        
        except Exception as e:
            logger.error(f'WebSocket 처리 중 에러 발생: {e}')

    async def main(self):
        """메인 실행 메서드"""
        logger.debug('WebSocket 연결 시도: ' + self.server_url)
        await self.handle_websocket()

if __name__ == "__main__":
    ReverbTestController()
