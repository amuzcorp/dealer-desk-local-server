import pystray
from PIL import Image, ImageDraw
import asyncio
import sys
import os
import subprocess
from threading import Thread
import webbrowser
import signal
import time
import traceback
import logging
import tempfile

# 로깅 설정
log_dir = os.path.join(tempfile.gettempdir(), "dealer_desk_logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "dealer_desk.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("DealerDesk")

# 윈도우 환경 확인
is_windows = sys.platform.startswith('win')

# 서버 모듈 임포트
try:
    import uvicorn
    from main import app as main_app
    from web_server import app as web_app
    logger.info("서버 모듈 임포트 성공")
except ImportError as e:
    logger.error(f"서버 모듈 임포트 실패: {e}")
    traceback.print_exc()

class DealerDeskTray:
    def __init__(self):
        self.icon = None
        self.api_server = None
        self.web_server = None
        self.is_running = False
        self.api_server_thread = None
        self.web_server_thread = None
        self.api_port = 8000
        self.web_port = 3000
        logger.info("DealerDeskTray 초기화 완료")
        
    def create_icon(self, color):
        # 아이콘 이미지 생성 (16x16 픽셀)
        try:
            image = Image.new('RGB', (16, 16), color='white')
            dc = ImageDraw.Draw(image)
            dc.rectangle([0, 0, 15, 15], fill=color)
            return image
        except Exception as e:
            logger.error(f"아이콘 생성 중 오류: {e}")
            # 기본 이미지 반환
            return Image.new('RGB', (16, 16), color='white')
    
    def run_api_server(self):
        try:
            logger.info("API 서버 시작 중...")
            config = uvicorn.Config(main_app, host="0.0.0.0", port=self.api_port, reload=False)
            self.api_server = uvicorn.Server(config=config)
            self.api_server.run()
            logger.info("API 서버 종료됨")
        except Exception as e:
            logger.error(f"API 서버 실행 중 오류: {e}")
            traceback.print_exc()
        
    def run_web_server(self):
        try:
            logger.info("웹 서버 시작 중...")
            config = uvicorn.Config(web_app, host="0.0.0.0", port=self.web_port, reload=False)
            self.web_server = uvicorn.Server(config=config)
            self.web_server.run()
            logger.info("웹 서버 종료됨")
        except Exception as e:
            logger.error(f"웹 서버 실행 중 오류: {e}")
            traceback.print_exc()
        
    def start_server(self):
        if not self.is_running:
            try:
                logger.info("서버 시작 중...")
                
                # API 서버 스레드 시작
                self.api_server_thread = Thread(target=self.run_api_server)
                self.api_server_thread.daemon = True
                self.api_server_thread.start()
                logger.info("API 서버 스레드 시작됨")
                
                # 웹 서버 스레드 시작
                self.web_server_thread = Thread(target=self.run_web_server)
                self.web_server_thread.daemon = True
                self.web_server_thread.start()
                logger.info("웹 서버 스레드 시작됨")
                
                # 서버가 시작될 때까지 잠시 대기
                time.sleep(2)
                
                self.is_running = True
                if self.icon:
                    self.icon.icon = self.create_icon('green')  # 실행 중 상태 표시
                    self.update_menu()
                    logger.info("아이콘 상태 업데이트: 실행 중")
                
                # 브라우저 열기
                try:
                    webbrowser.open(f"http://localhost:{self.web_port}")
                    logger.info("웹 브라우저 열기 성공")
                except Exception as e:
                    logger.error(f"웹 브라우저 열기 실패: {e}")
                
            except Exception as e:
                logger.error(f"서버 시작 중 오류 발생: {e}")
                traceback.print_exc()
                
    def stop_server(self):
        if self.is_running:
            try:
                logger.info("서버 중지 중...")
                
                if self.api_server:
                    self.api_server.should_exit = True
                    logger.info("API 서버 종료 신호 전송")
                    
                if self.web_server:
                    self.web_server.should_exit = True
                    logger.info("웹 서버 종료 신호 전송")
                    
                self.is_running = False
                if self.icon:
                    self.icon.icon = self.create_icon('red')  # 중지 상태 표시
                    self.update_menu()
                    logger.info("아이콘 상태 업데이트: 중지됨")
                
                # 스레드 종료 대기
                if self.api_server_thread and self.api_server_thread.is_alive():
                    logger.info("API 서버 스레드 종료 대기 중...")
                    self.api_server_thread.join(timeout=5)
                    
                if self.web_server_thread and self.web_server_thread.is_alive():
                    logger.info("웹 서버 스레드 종료 대기 중...")
                    self.web_server_thread.join(timeout=5)
                
                logger.info("서버 중지 완료")
                    
            except Exception as e:
                logger.error(f"서버 중지 중 오류 발생: {e}")
                traceback.print_exc()
                
    def toggle_server(self):
        if self.is_running:
            logger.info("서버 중지 요청")
            self.stop_server()
        else:
            logger.info("서버 시작 요청")
            self.start_server()
            
    def exit_application(self):
        logger.info("애플리케이션 종료 요청")
        self.stop_server()
        if self.icon:
            logger.info("트레이 아이콘 제거")
            self.icon.stop()
        logger.info("애플리케이션 종료")
        
    def update_menu(self):
        if self.icon:
            try:
                self.icon.menu = self.create_menu()
                logger.info("메뉴 업데이트 완료")
            except Exception as e:
                logger.error(f"메뉴 업데이트 중 오류: {e}")
        
    def create_menu(self):
        try:
            return pystray.Menu(
                pystray.MenuItem(
                    "실행 중" if self.is_running else "중지됨",
                    lambda: None,
                    enabled=False
                ),
                pystray.MenuItem(
                    "중지" if self.is_running else "시작",
                    self.toggle_server
                ),
                pystray.MenuItem(
                    "웹 페이지 열기",
                    lambda: webbrowser.open(f"http://localhost:{self.web_port}") if self.is_running else None,
                    enabled=self.is_running
                ),
                pystray.MenuItem("종료", self.exit_application)
            )
        except Exception as e:
            logger.error(f"메뉴 생성 중 오류: {e}")
            # 기본 메뉴 반환
            return pystray.Menu(
                pystray.MenuItem("종료", self.exit_application)
            )
        
    def run(self):
        try:
            # 초기 아이콘 생성 (빨간색 - 중지 상태)
            logger.info("트레이 아이콘 초기화 중...")
            self.icon = pystray.Icon(
                "dealer_desk",
                self.create_icon('red'),
                "Dealer Desk Server",
                self.create_menu()
            )
            logger.info("트레이 아이콘 초기화 완료")
            
            # 서버 자동 시작
            logger.info("서버 자동 시작 중...")
            self.start_server()
            
            # 트레이 아이콘 표시
            logger.info("트레이 아이콘 표시 중...")
            self.icon.run()
            logger.info("트레이 아이콘 종료됨")
        except Exception as e:
            logger.error(f"애플리케이션 실행 중 오류: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    try:
        logger.info("애플리케이션 시작")
        
        # SIGINT 핸들러 설정
        def signal_handler(signum, frame):
            logger.info(f"시그널 수신: {signum}")
            if 'app' in globals() and app:
                app.exit_application()
            sys.exit(0)
            
        # Windows에서는 SIGINT만 처리
        signal.signal(signal.SIGINT, signal_handler)
        if is_windows:
            # Windows에서는 SIGBREAK 신호도 처리
            try:
                signal.signal(signal.SIGBREAK, signal_handler)
                logger.info("Windows SIGBREAK 핸들러 설정됨")
            except AttributeError:
                logger.warning("SIGBREAK 신호를 설정할 수 없습니다")
        else:
            # Unix 계열에서는 SIGTERM 신호도 처리
            signal.signal(signal.SIGTERM, signal_handler)
            logger.info("SIGTERM 핸들러 설정됨")
        
        app = DealerDeskTray()
        app.run()
    except Exception as e:
        logger.error(f"메인 스레드에서 처리되지 않은 예외: {e}")
        traceback.print_exc()
        sys.exit(1) 