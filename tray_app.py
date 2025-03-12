import asyncio
import os
import sys
import threading
import webbrowser
import subprocess
import logging
import signal
import importlib.util
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
from PIL import Image
import pystray
from pystray import MenuItem as item

# uvicorn 서버를 직접 실행하기 위한 임포트 추가
import uvicorn
import uvicorn.config
import uvicorn.lifespan

# 로그 파일 경로 설정 (먼저 정의해야 함)
log_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
tray_log_file = os.path.join(log_dir, "dealer_desk_tray.log")
launcher_log_file = os.path.join(log_dir, "dealerdesk_launcher.log")

# 로깅 설정 - uvicorn과의 충돌을 방지하기 위해 기본 설정만 사용
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(tray_log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
# 로거 생성 (Uvicorn 로거와 충돌 방지)
logger = logging.getLogger("DealerDeskTray")
logger.propagate = False  # 로그 전파 방지

# 실행 환경 설정
if getattr(sys, 'frozen', False):
    # PyInstaller로 빌드된 실행 파일인 경우
    application_path = sys._MEIPASS
    
    logger.info(f"PyInstaller 환경에서 실행 중: {application_path}")
    
    # _internal 디렉토리 경로 계산 (여러 방법으로 시도)
    internal_path = None
    
    # 1. 환경 변수에서 확인
    if "INTERNAL_DIR" in os.environ and os.path.exists(os.environ["INTERNAL_DIR"]):
        internal_path = os.environ["INTERNAL_DIR"]
        logger.info(f"환경 변수에서 _internal 경로 발견: {internal_path}")
    
    # 2. application_path 내에서 확인
    elif os.path.exists(os.path.join(application_path, "_internal")):
        internal_path = os.path.join(application_path, "_internal")
        logger.info(f"application_path 내에서 _internal 경로 발견: {internal_path}")
    
    # 3. 실행 파일 위치에서 확인
    else:
        exe_dir = os.path.dirname(sys.executable)
        potential_internal = os.path.join(exe_dir, "_internal")
        
        if os.path.exists(potential_internal):
            internal_path = potential_internal
            logger.info(f"실행 파일 위치에서 _internal 경로 발견: {internal_path}")
        else:
            # 4. 없으면 실행 파일 위치에 생성
            try:
                os.makedirs(potential_internal, exist_ok=True)
                internal_path = potential_internal
                logger.info(f"_internal 디렉토리를 생성했습니다: {internal_path}")
            except Exception as e:
                logger.error(f"_internal 디렉토리 생성 실패: {str(e)}")
                # 5. 최후의 수단으로 현재 작업 디렉토리에 생성
                current_dir_internal = os.path.join(os.getcwd(), "_internal")
                os.makedirs(current_dir_internal, exist_ok=True)
                internal_path = current_dir_internal
                logger.info(f"현재 작업 디렉토리에 _internal 생성: {internal_path}")
    
    # 필요한 모듈 경로 추가
    for path in [application_path, internal_path]:
        if path and path not in sys.path:
            sys.path.insert(0, path)
    
    # 모듈 검색 경로 출력 (디버깅용)
    logger.info("Python 모듈 검색 경로:")
    for path in sys.path:
        logger.info(f"  - {path}")
    
    # importlib을 사용하여 동적으로 모듈 로드
    def load_module(module_name, module_path):
        try:
            logger.info(f"모듈 로드 시도: {module_name} (경로: {module_path})")
            
            if not os.path.exists(module_path):
                logger.info(f"모듈 파일이 존재하지 않습니다: {module_path}")
                
                # 다른 경로에서 찾아보기
                for search_path in sys.path:
                    alt_path = os.path.join(search_path, f"{module_name}.py")
                    if os.path.exists(alt_path):
                        logger.info(f"대체 경로에서 모듈 발견: {alt_path}")
                        module_path = alt_path
                        break
            
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                logger.info(f"모듈 {module_name} 로드 성공")
                return module
            else:
                logger.error(f"모듈 {module_name}의 spec을 찾을 수 없습니다. 경로: {module_path}")
                
                # 직접 import 시도
                try:
                    logger.info(f"{module_name} 모듈을 importlib.import_module로 시도")
                    import importlib
                    return importlib.import_module(module_name)
                except Exception as e:
                    logger.error(f"직접 import 실패: {str(e)}")
                
                return None
        except Exception as e:
            logger.error(f"모듈 {module_name} 로드 중 오류 발생: {str(e)}")
            return None
    
    # main 모듈 로드 시도 (여러 경로에서)
    main = None
    possible_paths = [
        os.path.join(application_path, "main.py"),
        os.path.join(internal_path, "main.py"),
        os.path.join(os.path.dirname(sys.executable), "main.py"),
        os.path.join(os.getcwd(), "main.py")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"main.py 발견: {path}")
            main = load_module("main", path)
            if main:
                break
    
    if not main:
        logger.warning("main 모듈을 로드할 수 없습니다. 직접 웹 서버 실행 모드로 전환합니다.")
else:
    # 일반 Python 스크립트로 실행되는 경우
    application_path = os.path.dirname(os.path.abspath(__file__))
    internal_path = os.path.join(application_path, "_internal")
    if os.path.exists(internal_path):
        if internal_path not in sys.path:
            sys.path.insert(0, internal_path)
    try:
        import main
        logger.info("main 모듈 로드 성공 (일반 실행 모드)")
    except ImportError:
        logger.error("main 모듈을 가져올 수 없습니다. 직접 웹 서버 실행 모드로 전환합니다.")
        main = None

# 직접 구현한 Uvicorn 서버 클래스
class UvicornServer:
    def __init__(self, app_import_string, host="0.0.0.0", port=401):
        self.app_import_string = app_import_string
        self.host = host
        self.port = port
        
        # Uvicorn 로그 관련 문제 해결을 위한 설정
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {
                    "format": "%(levelname)s: %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "simple",
                }
            },
            "loggers": {
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "uvicorn.access": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False,
                },
            }
        }
        
        # 직접 로그 설정을 제공하여 'default' 포맷터 문제 회피
        self.config = uvicorn.Config(
            app=self.app_import_string, 
            host=self.host, 
            port=self.port, 
            log_level="info",
            log_config=log_config
        )
        self.server = uvicorn.Server(config=self.config)
    
    async def run(self):
        try:
            logger.info(f"Uvicorn 서버 시작: {self.app_import_string} (호스트: {self.host}, 포트: {self.port})")
            await self.server.serve()
        except Exception as e:
            logger.error(f"Uvicorn 서버 실행 중 오류: {str(e)}")

# 로그 뷰어 클래스
class LogViewerWindow:
    def __init__(self, log_file, title):
        self.log_file = log_file
        self.title = title
        self.root = None
        self.text_area = None
        self.auto_scroll = True
        self.update_interval = 1000  # 1초마다 업데이트
        
    def show(self):
        if self.root is not None and self.root.winfo_exists():
            self.root.lift()  # 이미 존재하면 창을 앞으로 가져옴
            return
            
        # 새 창 생성
        self.root = tk.Tk()
        self.root.title(self.title)
        self.root.geometry("800x600")
        
        # 프레임 설정
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 툴바 프레임
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 자동 스크롤 체크박스
        self.auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_check = ttk.Checkbutton(
            toolbar_frame, 
            text="자동 스크롤", 
            variable=self.auto_scroll_var,
            command=self.toggle_auto_scroll
        )
        auto_scroll_check.pack(side=tk.LEFT, padx=5)
        
        # 새로고침 버튼
        refresh_button = ttk.Button(toolbar_frame, text="새로고침", command=self.refresh_log)
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        # 로그 지우기 버튼
        clear_button = ttk.Button(toolbar_frame, text="로그 지우기", command=self.clear_log_area)
        clear_button.pack(side=tk.LEFT, padx=5)
        
        # 텍스트 영역
        self.text_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD)
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        # 로그 로드
        self.refresh_log()
        
        # 주기적으로 업데이트
        self.schedule_update()
        
        # 창 닫을 때 처리
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # 창 실행
        self.root.mainloop()
    
    def toggle_auto_scroll(self):
        self.auto_scroll = self.auto_scroll_var.get()
    
    def refresh_log(self):
        try:
            with open(self.log_file, 'r', encoding='utf-8') as file:
                content = file.read()
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, content)
                if self.auto_scroll:
                    self.text_area.see(tk.END)  # 스크롤을 끝으로
        except Exception as e:
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, f"로그 파일을 읽을 수 없습니다: {str(e)}")
    
    def clear_log_area(self):
        self.text_area.delete(1.0, tk.END)
    
    def schedule_update(self):
        if self.root and self.root.winfo_exists():
            self.refresh_log()
            self.root.after(self.update_interval, self.schedule_update)
    
    def on_close(self):
        self.root.destroy()
        self.root = None

# 외부 텍스트 에디터로 로그 파일 열기
def open_log_with_external_editor(log_file):
    try:
        if sys.platform.startswith('win'):
            os.startfile(log_file)
        elif sys.platform.startswith('darwin'):  # macOS
            subprocess.call(['open', log_file])
        else:  # Linux
            subprocess.call(['xdg-open', log_file])
        logger.info(f"외부 에디터로 로그 파일 열기: {log_file}")
    except Exception as e:
        logger.error(f"로그 파일 열기 실패: {str(e)}")

class DealerDeskTrayApp:
    def __init__(self):
        self.api_server_thread = None
        self.web_server_thread = None
        self.is_running = False
        self.icon = None
        self.log_viewers = {}
        self.setup_icon()
        
    def setup_icon(self):
        # 아이콘 파일 경로 설정 (PyInstaller로 빌드 시 임시 경로 고려)
        icon_paths = [
            os.path.join(application_path, "app_icon.ico"),
            os.path.join(os.path.dirname(sys.executable), "app_icon.ico")
        ]
        
        if internal_path:
            icon_paths.append(os.path.join(internal_path, "app_icon.ico"))
            
        if getattr(sys, 'frozen', False) and hasattr(sys, "_MEIPASS"):
            icon_paths.append(os.path.join(sys._MEIPASS, "app_icon.ico"))
            if os.path.exists(os.path.join(sys._MEIPASS, "_internal")):
                icon_paths.append(os.path.join(sys._MEIPASS, "_internal", "app_icon.ico"))
        
        # 모든 가능한 경로에서 아이콘 찾기
        icon_image = None
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                logger.info(f"아이콘 파일 발견: {icon_path}")
                try:
                    icon_image = Image.open(icon_path)
                    break
                except Exception as e:
                    logger.error(f"아이콘 파일 열기 실패: {str(e)}")
        
        # 아이콘을 찾지 못한 경우 간단한 이미지 생성
        if icon_image is None:
            logger.warning("아이콘 파일을 찾을 수 없어 기본 이미지를 생성합니다.")
            icon_image = Image.new('RGB', (64, 64), color=(66, 133, 244))
        
        try:
            # 트레이 아이콘 및 메뉴 설정
            self.icon = pystray.Icon(
                "dealer_desk",
                icon_image,
                "딜러 데스크 서버",
                menu=self.create_menu()
            )
        except Exception as e:
            logger.error(f"트레이 아이콘 생성 중 오류 발생: {str(e)}")
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
            item('로그', self.create_log_submenu()),
            item('종료', self.exit_app)
        )
    
    def create_log_submenu(self):
        return pystray.Menu(
            item('트레이 로그 보기 (내부)', self.open_tray_log_viewer),
            item('런처 로그 보기 (내부)', self.open_launcher_log_viewer),
            item('트레이 로그 파일 열기 (외부)', self.open_tray_log_external),
            item('런처 로그 파일 열기 (외부)', self.open_launcher_log_external)
        )
        
    def update_menu(self):
        status_text = '상태: 실행 중' if self.is_running else '상태: 정지됨'
        self.icon.menu = (
            item(status_text, self.status_action, enabled=False),
            item('웹 인터페이스 열기', self.open_web_interface, enabled=self.is_running),
            item('서버 시작', self.start_server, enabled=not self.is_running),
            item('서버 정지', self.stop_server, enabled=self.is_running),
            item('로그', self.create_log_submenu()),
            item('종료', self.exit_app)
        )
    
    def open_tray_log_viewer(self, icon, item):
        self.open_log_viewer(tray_log_file, "딜러 데스크 트레이 로그")
    
    def open_launcher_log_viewer(self, icon, item):
        self.open_log_viewer(launcher_log_file, "딜러 데스크 런처 로그")
    
    def open_tray_log_external(self, icon, item):
        open_log_with_external_editor(tray_log_file)
    
    def open_launcher_log_external(self, icon, item):
        open_log_with_external_editor(launcher_log_file)
    
    def open_log_viewer(self, log_file, title):
        if not os.path.exists(log_file):
            logger.warning(f"로그 파일이 존재하지 않습니다: {log_file}")
            return
            
        viewer_key = log_file
        
        # 이미 뷰어가 있는지 확인
        if viewer_key in self.log_viewers and hasattr(self.log_viewers[viewer_key], 'root') and self.log_viewers[viewer_key].root and self.log_viewers[viewer_key].root.winfo_exists():
            # 이미 창이 열려있으면 앞으로 가져옴
            self.log_viewers[viewer_key].root.lift()
            return
        
        # 새 뷰어 생성
        viewer = LogViewerWindow(log_file, title)
        self.log_viewers[viewer_key] = viewer
        
        # 별도 스레드에서 뷰어 실행
        threading.Thread(target=viewer.show, daemon=True).start()
        logger.info(f"로그 뷰어를 열었습니다: {title}")
        
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
            # main 모듈 사용 여부 확인
            if main and hasattr(main, 'run_api_server'):
                logger.info("main 모듈의 run_api_server 함수 사용")
                asyncio.run(main.run_api_server())
            else:
                # 직접 API 서버 실행
                logger.info("API 서버 직접 실행 (main 모듈의 run_api_server 함수 없음)")
                # 모듈 검색 경로에 현재 작업 디렉토리 추가
                if os.getcwd() not in sys.path:
                    sys.path.insert(0, os.getcwd())
                
                # 절대 경로 형식의 모듈 임포트 시도
                try:
                    api_server = UvicornServer("main:app", host="0.0.0.0", port=401)
                    asyncio.run(api_server.run())
                except (ModuleNotFoundError, ImportError) as e:
                    logger.error(f"main 모듈을 찾을 수 없습니다: {str(e)}")
                    
                    # 모듈 직접 생성 시도
                    logger.info("API 서버 직접 생성 시도...")
                    
                    # 기본 FastAPI 앱 생성
                    try:
                        from fastapi import FastAPI
                        app = FastAPI(title="딜러 데스크 API 서버")
                        
                        @app.get("/")
                        async def read_root():
                            return {"message": "딜러 데스크 API 서버가 실행 중입니다."}
                        
                        # 서버 실행
                        config = uvicorn.Config(app=app, host="0.0.0.0", port=401)
                        server = uvicorn.Server(config=config)
                        asyncio.run(server.serve())
                    except Exception as e:
                        logger.error(f"API 서버 직접 생성 실패: {str(e)}")
                
        except Exception as e:
            logger.error(f"API 서버 실행 중 오류 발생: {str(e)}")
    
    def run_web_server(self):
        try:
            logger.info("웹 서버 시작 중...")
            # main 모듈 사용 여부 확인
            if main and hasattr(main, 'run_web_server'):
                logger.info("main 모듈의 run_web_server 함수 사용")
                asyncio.run(main.run_web_server())
            else:
                # 직접 웹 서버 실행
                logger.info("웹 서버 직접 실행 (main 모듈의 run_web_server 함수 없음)")
                
                # 모듈 검색 경로에 현재 작업 디렉토리 추가
                if os.getcwd() not in sys.path:
                    sys.path.insert(0, os.getcwd())
                
                # web_server 모듈 확인
                web_server_paths = [
                    os.path.join(application_path, "web_server.py"),
                    os.path.join(internal_path, "web_server.py") if internal_path else None,
                    os.path.join(os.getcwd(), "web_server.py")
                ]
                
                web_server_exists = False
                for path in web_server_paths:
                    if path and os.path.exists(path):
                        logger.info(f"web_server.py 발견: {path}")
                        web_server_exists = True
                        break
                
                if web_server_exists:
                    try:
                        web_server = UvicornServer("web_server:app", host="0.0.0.0", port=3000)
                        asyncio.run(web_server.run())
                    except (ModuleNotFoundError, ImportError) as e:
                        logger.error(f"web_server 모듈을 찾을 수 없습니다: {str(e)}")
                        self.create_simple_web_server()
                else:
                    logger.warning("web_server.py를 찾을 수 없습니다. 간단한 웹 서버를 생성합니다.")
                    self.create_simple_web_server()
        except Exception as e:
            logger.error(f"웹 서버 실행 중 오류 발생: {str(e)}")
    
    def create_simple_web_server(self):
        """간단한 웹 서버 직접 생성"""
        try:
            logger.info("간단한 웹 서버 생성 중...")
            
            from fastapi import FastAPI
            from fastapi.responses import HTMLResponse
            
            app = FastAPI(title="딜러 데스크 웹 서버")
            
            @app.get("/", response_class=HTMLResponse)
            async def read_root():
                return """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>딜러 데스크 웹 인터페이스</title>
                    <style>
                        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                        h1 { color: #4285f4; }
                        .info { background-color: #f5f5f5; padding: 15px; border-radius: 5px; }
                        .error { color: #d32f2f; }
                    </style>
                </head>
                <body>
                    <h1>딜러 데스크 웹 인터페이스</h1>
                    <div class="info">
                        <p>웹 서버가 실행 중입니다만, web_server.py 모듈을 찾을 수 없어 간단한 페이지를 표시합니다.</p>
                        <p>API 서버는 <a href="http://localhost:401/docs">http://localhost:401/docs</a>에서 접근할 수 있습니다.</p>
                    </div>
                    <div class="error">
                        <p>전체 기능을 사용하려면 web_server.py 파일이 필요합니다.</p>
                    </div>
                </body>
                </html>
                """
            
            # 서버 실행
            config = uvicorn.Config(app=app, host="0.0.0.0", port=3000)
            server = uvicorn.Server(config=config)
            asyncio.run(server.serve())
        except Exception as e:
            logger.error(f"간단한 웹 서버 생성 실패: {str(e)}")
    
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
        
        # 열려 있는 로그 뷰어 창 닫기
        for viewer_key, viewer in list(self.log_viewers.items()):
            if hasattr(viewer, 'root') and viewer.root:
                try:
                    viewer.root.destroy()
                except:
                    pass
        
        icon.stop()
        sys.exit(0)
    
    def run(self):
        logger.info("딜러 데스크 트레이 애플리케이션 시작")
        logger.info(f"작업 디렉토리: {os.getcwd()}")
        logger.info(f"애플리케이션 경로: {application_path}")
        
        if getattr(sys, 'frozen', False):
            # 실행 환경 정보 로깅
            logger.info(f"PyInstaller로 빌드된 실행 파일 모드")
            if hasattr(sys, "_MEIPASS"):
                logger.info(f"sys._MEIPASS: {sys._MEIPASS}")
            
            # _internal 디렉토리 정보 로깅
            if internal_path and os.path.exists(internal_path):
                logger.info(f"_internal 디렉토리 발견: {internal_path}")
                logger.info("_internal 디렉토리 내용:")
                try:
                    for item in os.listdir(internal_path):
                        logger.info(f"  - {item}")
                except Exception as e:
                    logger.error(f"_internal 디렉토리 내용 확인 중 오류: {str(e)}")
            else:
                logger.warning(f"_internal 디렉토리를 찾을 수 없거나 비어 있습니다: {internal_path}")
        
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