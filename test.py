import websocket
import threading
import time
import logging
import json

# 로거 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger('WebSocketTester')

class WebSocketClient:
    def __init__(self, url):
        self.ws_url = url
        self.ws = None
        self.retry_interval = 3  # 재연결 간격 (초)
        self.is_connected = False
        self.should_reconnect = True
        self.thread = None

    def connect(self):
        """WebSocket 연결 시작"""
        self.should_reconnect = True
        if self.thread and self.thread.is_alive():
            return

        # 웹소켓 연결 스레드 시작
        self.thread = threading.Thread(target=self._run_websocket)
        self.thread.daemon = True
        self.thread.start()

    def _run_websocket(self):
        """WebSocket 클라이언트 실행 루프"""
        while self.should_reconnect:
            try:
                logger.info(f"Connecting to {self.ws_url}...")
                self.ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )
                self.ws.run_forever()
            except Exception as e:
                logger.error(f"Connection failed: {e}")
            finally:
                if self.should_reconnect:
                    logger.info(f"Reconnecting in {self.retry_interval} seconds...")
                    time.sleep(self.retry_interval)

    def _on_open(self, ws):
        """연결 성공 핸들러"""
        logger.info("Connection opened")
        self.is_connected = True
        self._send_test_message()

    def _on_message(self, ws, message):
        """메시지 수신 핸들러"""
        try:
            data = json.loads(message)
            logger.info(f"Received message: {data}")
        except json.JSONDecodeError:
            logger.info(f"Received raw message: {message}")

    def _on_error(self, ws, error):
        """에러 핸들러"""
        logger.error(f"WebSocket error: {error}")
        self.is_connected = False

    def _on_close(self, ws, close_status_code, close_msg):
        """연결 종료 핸들러"""
        logger.info(f"Connection closed [{close_status_code}] {close_msg or ''}")
        self.is_connected = False

    def _send_test_message(self):
        """테스트 메시지 전송"""
        if self.is_connected:
            msg = {"event": "ping", "data": "test"}
            self.send_json(msg)

    def send_json(self, data):
        """JSON 데이터 전송"""
        if self.is_connected and self.ws:
            try:
                self.ws.send(json.dumps(data))
                logger.info(f"Sent message: {data}")
            except Exception as e:
                logger.error(f"Message send failed: {e}")

    def close(self):
        """연결 종료"""
        self.should_reconnect = False
        if self.ws:
            self.ws.close()
        logger.info("WebSocket client stopped")

# 테스트 실행
if __name__ == "__main__":
    # 테스트 서버 주소 (websocket.org 예제)
    ws_url = "ws://192.168.200.115:6001/"
    
    client = WebSocketClient(ws_url)
    client.connect()
    
    try:
        # 테스트용 메시지 주기적 전송
        while True:
            if client.is_connected:
                client.send_json({
                    "event": "test",
                    "data": {"timestamp": int(time.time())}
                })
            time.sleep(5)
    except KeyboardInterrupt:
        client.close()
        logger.info("테스트 종료")
