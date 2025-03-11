import asyncio
import os
import sys
import threading
import webbrowser
import subprocess
import logging
import signal
import importlib.util
from PIL import Image
import pystray
from pystray import MenuItem as item

# PyInstaller 관련 설정
if getattr(sys, 'frozen', False):
    # PyInstaller로 빌드된 실행 파일인 경우
    application_path = sys._MEIPASS
    
    # 필요한 모듈 경로 추가
    if application_path not in sys.path:
        sys.path.insert(0, application_path)
    
    # importlib을 사용하여 동적으로 모듈 로드
    def load_module(module_name, module_path):
        try:
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                sys.modules[module_name] = module
                return module
            else:
                print(f"모듈 {module_name}의 spec을 찾을 수 없습니다. 경로: {module_path}")
                return None
        except Exception as e:
            print(f"모듈 {module_name} 로드 중 오류 발생: {str(e)}")
            return None
    
    # 필요한 모듈들을 동적으로 로드
    main_module_path = os.path.join(application_path, "main.py")
    main = load_module("main", main_module_path)
else:
    # 일반 Python 스크립트로 실행되는 경우
    application_path = os.path.dirname(os.path.abspath(__file__))
    import main

# 로깅 설정
log_file = os.path.join(application_path, "dealer_desk_tray.log") if getattr(sys, 'frozen', False) else "dealer_desk_tray.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DealerDeskTray")

class DealerDeskTrayApp:
    def __init__(self):
        self.api_server_thread = None
        self.web_server_thread = None
        self.is_running = False
        self.icon = None
        self.setup_icon()
        
    def setup_icon(self):
        # 아이콘 파일 경로 설정 (PyInstaller로 빌드 시 임시 경로 고려)
        icon_path = os.path.join(application_path, "app_icon.ico")
        
        try:
            # 아이콘 파일이 존재하는 경우 사용
            if os.path.exists(icon_path):
                icon_image = Image.open(icon_path)
            else:
                # 존재하지 않으면 간단한 이미지 생성
                icon_image = Image.new('RGB', (64, 64), color=(66, 133, 244))
                
            # 트레이 아이콘 및 메뉴 설정
            self.icon = pystray.Icon(
                "dealer_desk",
                icon_image,
                "딜러 데스크 서버",
                menu=self.create_menu()
            )
        except Exception as e:
            logger.error(f"아이콘 설정 중 오류 발생: {str(e)}")
            # 오류 발생 시 기본 이미지 사용
            icon_image = Image.new('RGB', (64, 64), color=(66, 133, 244))
            self.icon = pystray.Icon(
                "dealer_desk",
                icon_image,
                "딜러 데스크 서버",
                menu=self.create_menu()
            )
        
    def create_menu(self):
        return (
            item('상태: 정지됨', self.status_action, enabled=False),
            item('웹 인터페이스 열기', self.open_web_interface),
            item('서버 시작', self.start_server),
            item('서버 정지', self.stop_server, enabled=False),
            item('종료', self.exit_app)
        )
        
    def update_menu(self):
        status_text = '상태: 실행 중' if self.is_running else '상태: 정지됨'
        self.icon.menu = (
            item(status_text, self.status_action, enabled=False),
            item('웹 인터페이스 열기', self.open_web_interface, enabled=self.is_running),
            item('서버 시작', self.start_server, enabled=not self.is_running),
            item('서버 정지', self.stop_server, enabled=self.is_running),
            item('종료', self.exit_app)
        )
        
    def status_action(self, icon, item):
        # 상태 표시용 더미 함수
        pass
    
    def open_web_interface(self, icon, item):
        if self.is_running:
            webbrowser.open("http://localhost:3000")
            logger.info("웹 인터페이스가 브라우저에서 열렸습니다.")
        else:
            logger.warning("서버가 실행 중이지 않아 웹 인터페이스를 열 수 없습니다.")
    
    def run_api_server(self):
        try:
            logger.info("API 서버 시작 중...")
            asyncio.run(main.run_api_server())
        except Exception as e:
            logger.error(f"API 서버 실행 중 오류 발생: {str(e)}")
    
    def run_web_server(self):
        try:
            logger.info("웹 서버 시작 중...")
            asyncio.run(main.run_web_server())
        except Exception as e:
            logger.error(f"웹 서버 실행 중 오류 발생: {str(e)}")
    
    def start_server(self, icon, item):
        if not self.is_running:
            logger.info("서버 시작 중...")
            self.is_running = True
            
            # API 서버 쓰레드 시작
            self.api_server_thread = threading.Thread(target=self.run_api_server)
            self.api_server_thread.daemon = True
            self.api_server_thread.start()
            
            # 웹 서버 쓰레드 시작
            self.web_server_thread = threading.Thread(target=self.run_web_server)
            self.web_server_thread.daemon = True
            self.web_server_thread.start()
            
            # 웹 페이지 자동 열기
            webbrowser.open("http://localhost:3000")
            
            self.update_menu()
            logger.info("서버가 성공적으로 시작되었습니다.")
    
    def stop_server(self, icon, item):
        if self.is_running:
            logger.info("서버 정지 중...")
            self.is_running = False
            
            # Windows에서 uvicorn 서버 강제 종료
            try:
                # API 서버 종료
                subprocess.run(["taskkill", "/f", "/im", "python.exe", "/fi", "WindowTitle eq uvicorn*"], 
                              shell=True, check=False)
                subprocess.run(["taskkill", "/f", "/im", "DealerDesk.exe", "/fi", "WindowTitle eq uvicorn*"], 
                              shell=True, check=False)
                logger.info("서버가 정지되었습니다.")
            except Exception as e:
                logger.error(f"서버 정지 중 오류 발생: {str(e)}")
            
            self.update_menu()
    
    def exit_app(self, icon, item):
        logger.info("애플리케이션 종료 중...")
        if self.is_running:
            self.stop_server(icon, item)
        icon.stop()
        sys.exit(0)
    
    def run(self):
        logger.info("딜러 데스크 트레이 애플리케이션 시작")
        logger.info(f"작업 디렉토리: {os.getcwd()}")
        logger.info(f"애플리케이션 경로: {application_path}")
        self.icon.run()

if __name__ == "__main__":
    # 시그널 핸들러 설정
    def signal_handler(signum, frame):
        logger.info("종료 신호 수신. 애플리케이션을 종료합니다.")
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    app = DealerDeskTrayApp()
    app.run() 