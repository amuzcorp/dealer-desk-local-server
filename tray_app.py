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
import traceback
import time

# uvicorn 서버를 직접 실행하기 위한 임포트 추가
try:
    import uvicorn
    import uvicorn.config
    import uvicorn.lifespan
    logger = logging.getLogger("DealerDeskTray")
    logger.info("uvicorn 모듈 로드 성공")
except ImportError as e:
    print(f"uvicorn 모듈 임포트 실패: {str(e)}")
    logger = logging.getLogger("DealerDeskTray")
    logger.error(f"uvicorn 모듈 임포트 실패: {str(e)}")

# 기본 디렉토리 설정
base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))

# 로그 파일 경로 설정
tray_log_file = os.path.join(base_dir, "dealer_desk_tray.log")
launcher_log_file = os.path.join(base_dir, "dealerdesk_launcher.log")

# 간단한 로깅 설정
try:
    # 기존 핸들러 제거
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # 기본 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        handlers=[
            logging.FileHandler(tray_log_file, encoding='utf-8', mode='a'),
            logging.StreamHandler()
        ]
    )
except Exception as e:
    # 로깅 설정 실패 시 최소한의 출력
    print(f"로깅 설정 실패: {str(e)}")
    
# 로거 생성
logger = logging.getLogger("DealerDeskTray")

# 글로벌 변수 설정
application_path = None
internal_path = None

# 경로 설정
try:
    if getattr(sys, 'frozen', False):
        # PyInstaller로 빌드된 실행 파일인 경우
        application_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
        logger.info(f"PyInstaller 환경에서 실행 중: {application_path}")
        
        # _internal 디렉토리 경로 설정
        internal_path = find_internal_directory()
    else:
        # 일반 Python 스크립트로 실행되는 경우
        application_path = os.path.dirname(os.path.abspath(__file__))
        internal_path = os.path.join(application_path, "_internal")
        if not os.path.exists(internal_path):
            os.makedirs(internal_path, exist_ok=True)
        
        logger.info(f"일반 Python 스크립트로 실행 중: {application_path}")
except Exception as e:
    logger.error(f"경로 설정 중 오류 발생: {str(e)}")
    traceback.print_exc()

def find_internal_directory():
    """_internal 디렉토리를 찾거나 생성"""
    try:
        # 후보 경로들
        candidates = [
            os.environ.get("INTERNAL_DIR", ""),
            os.path.join(application_path, "_internal") if application_path else "",
            os.path.join(os.path.dirname(sys.executable), "_internal"),
            os.path.join(os.getcwd(), "_internal")
        ]
        
        # 존재하는 디렉토리 찾기
        for path in candidates:
            if path and os.path.exists(path):
                logger.info(f"_internal 디렉토리 발견: {path}")
                return path
        
        # 존재하지 않으면 생성
        for path in candidates:
            if path:
                try:
                    os.makedirs(path, exist_ok=True)
                    logger.info(f"_internal 디렉토리 생성: {path}")
                    return path
                except:
                    continue
        
        # 마지막 수단으로 현재 디렉토리에 생성
        fallback_path = os.path.join(os.getcwd(), "_internal")
        os.makedirs(fallback_path, exist_ok=True)
        logger.info(f"_internal 디렉토리 생성 (최후 수단): {fallback_path}")
        return fallback_path
    except Exception as e:
        logger.error(f"_internal 디렉토리 찾기 실패: {str(e)}")
        fallback_path = os.path.join(os.getcwd(), "_internal")
        os.makedirs(fallback_path, exist_ok=True)
        return fallback_path

# 모듈 검색 경로 설정
try:
    for path in [application_path, internal_path, os.getcwd()]:
        if path and path not in sys.path:
            sys.path.insert(0, path)
            
    logger.info("모듈 검색 경로:")
    for path in sys.path:
        logger.info(f"  - {path}")
except Exception as e:
    logger.error(f"모듈 검색 경로 설정 실패: {str(e)}")

# main 모듈 로드 시도
main = None
try:
    import main
    logger.info("main 모듈 직접 임포트 성공")
except ImportError as ie:
    logger.warning(f"main 모듈 직접 임포트 실패: {str(ie)}")
    
    try:
        # 가능한 경로들에서 찾기
        possible_paths = [
            os.path.join(p, "main.py") for p in sys.path if os.path.exists(os.path.join(p, "main.py"))
        ]
        
        for path in possible_paths:
            try:
                logger.info(f"main.py 로드 시도: {path}")
                spec = importlib.util.spec_from_file_location("main", path)
                main = importlib.util.module_from_spec(spec)
                sys.modules["main"] = main
                spec.loader.exec_module(main)
                logger.info(f"main 모듈 로드 성공: {path}")
                break
            except Exception as e:
                logger.error(f"{path}에서 main 모듈 로드 실패: {str(e)}")
    except Exception as e:
        logger.error(f"main 모듈 동적 로드 실패: {str(e)}")

if main is None:
    logger.critical("main 모듈을 로드할 수 없습니다. 애플리케이션이 제대로 작동하지 않을 수 있습니다.")
else:
    # main 모듈 기능 확인
    if hasattr(main, 'run_api_server'):
        logger.info("main.run_api_server 함수 확인 완료")
    else:
        logger.error("main.run_api_server 함수가 존재하지 않습니다.")
        
    if hasattr(main, 'run_web_server'):
        logger.info("main.run_web_server 함수 확인 완료")
    else:
        logger.error("main.run_web_server 함수가 존재하지 않습니다.")

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
        try:
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
        except Exception as e:
            logger.error(f"로그 뷰어 생성 실패: {str(e)}")
    
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
        
        try:
            self.setup_icon()
        except Exception as e:
            logger.error(f"트레이 아이콘 설정 실패: {str(e)}")
            traceback.print_exc()
            raise
        
    def setup_icon(self):
        # 아이콘 파일 경로 설정 (PyInstaller로 빌드 시 임시 경로 고려)
        icon_paths = [
            os.path.join(p, "app_icon.ico") for p in [
                application_path,
                internal_path,
                os.path.dirname(sys.executable),
                os.getcwd()
            ] if p
        ]
        
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
        try:
            status_text = '상태: 실행 중' if self.is_running else '상태: 정지됨'
            self.icon.menu = (
                item(status_text, self.status_action, enabled=False),
                item('웹 인터페이스 열기', self.open_web_interface, enabled=self.is_running),
                item('서버 시작', self.start_server, enabled=not self.is_running),
                item('서버 정지', self.stop_server, enabled=self.is_running),
                item('로그', self.create_log_submenu()),
                item('종료', self.exit_app)
            )
        except Exception as e:
            logger.error(f"메뉴 업데이트 실패: {str(e)}")
    
    def open_tray_log_viewer(self, icon, item):
        self.open_log_viewer(tray_log_file, "딜러 데스크 트레이 로그")
    
    def open_launcher_log_viewer(self, icon, item):
        self.open_log_viewer(launcher_log_file, "딜러 데스크 런처 로그")
    
    def open_tray_log_external(self, icon, item):
        open_log_with_external_editor(tray_log_file)
    
    def open_launcher_log_external(self, icon, item):
        open_log_with_external_editor(launcher_log_file)
    
    def open_log_viewer(self, log_file, title):
        try:
            if not os.path.exists(log_file):
                logger.warning(f"로그 파일이 존재하지 않습니다: {log_file}")
                # 로그 파일이 없으면 빈 파일 생성
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(f"로그 파일 생성 시간: {logging.Formatter().formatTime(record=None)}\n")
                
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
        except Exception as e:
            logger.error(f"로그 뷰어 열기 실패: {str(e)}")
        
    def status_action(self, icon, item):
        # 상태 표시용 더미 함수
        pass
    
    def open_web_interface(self, icon, item):
        try:
            if self.is_running:
                webbrowser.open("http://localhost:3000")
                logger.info("웹 인터페이스가 브라우저에서 열렸습니다.")
            else:
                logger.warning("서버가 실행 중이지 않아 웹 인터페이스를 열 수 없습니다.")
        except Exception as e:
            logger.error(f"웹 인터페이스 열기 실패: {str(e)}")
    
    def run_api_server(self):
        try:
            logger.info("API 서버 쓰레드 시작")
            if main and hasattr(main, 'run_api_server'):
                # main.py 의 함수 사용
                logger.info("main.py의 run_api_server 함수 사용")
                asyncio.run(main.run_api_server())
            else:
                logger.warning("main.run_api_server 함수를 찾을 수 없습니다. 직접 서버를 실행합니다.")
                # 대체 서버 실행
                try:
                    # 먼저 main에서 app 가져오기 시도
                    if main and hasattr(main, 'app'):
                        app = main.app
                        logger.info("main.app 객체를 사용하여 API 서버 실행")
                    else:
                        # FastAPI 직접 생성
                        from fastapi import FastAPI
                        app = FastAPI(title="딜러 데스크 API 서버")
                        
                        @app.get("/health")
                        async def health_check():
                            return {"status": "healthy"}
                        
                        logger.info("FastAPI 앱 객체 직접 생성")
                    
                    # uvicorn 설정 및 서버 실행
                    config = uvicorn.Config(
                        app=app, 
                        host="0.0.0.0", 
                        port=401,
                        log_level="info",
                        log_config=None,  # 로깅 문제 방지
                        access_log=False
                    )
                    server = uvicorn.Server(config=config)
                    asyncio.run(server.serve())
                except Exception as inner_e:
                    logger.error(f"API 서버 직접 실행 실패: {str(inner_e)}")
                    logger.info("문자열 경로로 app 참조 시도")
                    
                    # 마지막 방법: 문자열 참조로 실행
                    config = uvicorn.Config(
                        app="main:app", 
                        host="0.0.0.0", 
                        port=401,
                        log_level="info",
                        log_config=None,  # 로깅 문제 방지
                        access_log=False
                    )
                    server = uvicorn.Server(config=config)
                    asyncio.run(server.serve())
        except Exception as e:
            logger.error(f"API 서버 실행 중 오류 발생: {str(e)}")
            traceback.print_exc()
    
    def run_web_server(self):
        try:
            logger.info("웹 서버 쓰레드 시작")
            if main and hasattr(main, 'run_web_server'):
                # main.py 의 함수 사용
                logger.info("main.py의 run_web_server 함수 사용")
                asyncio.run(main.run_web_server())
            else:
                logger.warning("main.run_web_server 함수를 찾을 수 없습니다. 직접 서버를 실행합니다.")
                # web_server.py 파일 직접 찾아서 실행 시도
                try:
                    # 먼저 web_server 모듈 임포트 시도
                    web_server_module = None
                    try:
                        import web_server
                        web_server_module = web_server
                        logger.info("web_server 모듈 임포트 성공")
                    except ImportError:
                        # web_server.py 파일 찾기
                        for path in sys.path:
                            web_server_path = os.path.join(path, "web_server.py")
                            if os.path.exists(web_server_path):
                                logger.info(f"web_server.py 파일 발견: {web_server_path}")
                                try:
                                    spec = importlib.util.spec_from_file_location("web_server", web_server_path)
                                    web_server_module = importlib.util.module_from_spec(spec)
                                    sys.modules["web_server"] = web_server_module
                                    spec.loader.exec_module(web_server_module)
                                    logger.info("web_server.py 모듈 로드 성공")
                                    break
                                except Exception as e:
                                    logger.error(f"web_server.py 모듈 로드 실패: {str(e)}")
                
                    # web_server 모듈에서 app 객체 사용
                    if web_server_module and hasattr(web_server_module, 'app'):
                        logger.info("web_server.app 객체를 사용하여 웹 서버 실행")
                        config = uvicorn.Config(
                            app=web_server_module.app, 
                            host="0.0.0.0", 
                            port=3000,
                            log_level="info",
                            log_config=None,  # 로깅 문제 방지
                            access_log=False
                        )
                        server = uvicorn.Server(config=config)
                        asyncio.run(server.serve())
                    else:
                        # 문자열 참조로 실행
                        logger.info("문자열 참조로 web_server:app 사용")
                        config = uvicorn.Config(
                            app="web_server:app", 
                            host="0.0.0.0", 
                            port=3000,
                            log_level="info",
                            log_config=None,  # 로깅 문제 방지
                            access_log=False
                        )
                        server = uvicorn.Server(config=config)
                        asyncio.run(server.serve())
                except Exception as e:
                    logger.error(f"web_server 모듈 로드 및 실행 실패: {str(e)}")
                    
                    # 최후의 방법: 간단한 웹 페이지 생성
                    logger.info("간단한 웹 서버 직접 생성")
                    from fastapi import FastAPI
                    from fastapi.responses import HTMLResponse
                    
                    app = FastAPI(title="딜러 데스크 웹 서버")
                    
                    @app.get("/", response_class=HTMLResponse)
                    async def read_root():
                        return """
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <title>딜러 데스크</title>
                            <style>
                                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                                h1 { color: #4285f4; }
                                .info { background-color: #f5f5f5; padding: 15px; border-radius: 5px; }
                                .api-link { margin-top: 20px; }
                            </style>
                        </head>
                        <body>
                            <h1>딜러 데스크 웹 인터페이스</h1>
                            <div class="info">
                                <p>웹 서버가 실행 중입니다.</p>
                                <p>web_server.py 모듈을 찾을 수 없어 기본 페이지를 표시합니다.</p>
                            </div>
                            <div class="api-link">
                                <p>API 서버: <a href="http://localhost:401/docs">http://localhost:401/docs</a></p>
                            </div>
                        </body>
                        </html>
                        """
                    
                    # uvicorn 서버 실행
                    config = uvicorn.Config(
                        app=app, 
                        host="0.0.0.0", 
                        port=3000,
                        log_level="info",
                        log_config=None,  # 로깅 문제 방지
                        access_log=False
                    )
                    server = uvicorn.Server(config=config)
                    asyncio.run(server.serve())
        except Exception as e:
            logger.error(f"웹 서버 실행 중 오류 발생: {str(e)}")
            traceback.print_exc()
    
    def start_server(self, icon, item):
        try:
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
                try:
                    # 서버 시작을 위한 짧은 대기
                    time.sleep(2)
                    webbrowser.open("http://localhost:3000")
                except Exception as e:
                    logger.error(f"웹 브라우저 열기 실패: {str(e)}")
                
                self.update_menu()
                logger.info("서버가 성공적으로 시작되었습니다.")
        except Exception as e:
            logger.error(f"서버 시작 실패: {str(e)}")
            traceback.print_exc()
            self.is_running = False
            self.update_menu()
    
    def stop_server(self, icon, item):
        try:
            if self.is_running:
                logger.info("서버 정지 중...")
                self.is_running = False
                
                # 서버 종료 처리
                try:
                    # 플랫폼에 따른 처리
                    if sys.platform.startswith('win'):
                        # Windows 환경
                        subprocess.run(["taskkill", "/f", "/im", "python.exe", "/fi", "WindowTitle eq uvicorn*"], 
                                    shell=True, check=False)
                        subprocess.run(["taskkill", "/f", "/im", "DealerDesk.exe", "/fi", "WindowTitle eq uvicorn*"], 
                                    shell=True, check=False)
                    else:
                        # macOS 또는 Linux 환경
                        subprocess.run(["pkill", "-f", "uvicorn"], check=False)
                        subprocess.run(["pkill", "-f", "DealerDesk"], check=False)
                        
                        # 스레드 종료 시도
                        if self.api_server_thread and self.api_server_thread.is_alive():
                            logger.info("API 서버 스레드 종료 시도")
                            # 여기서는 스레드를 직접 종료할 수 없으므로 로그만 남김
                        
                        if self.web_server_thread and self.web_server_thread.is_alive():
                            logger.info("웹 서버 스레드 종료 시도")
                            # 여기서는 스레드를 직접 종료할 수 없으므로 로그만 남김
                    
                    logger.info("서버가 정지되었습니다.")
                except Exception as e:
                    logger.error(f"서버 정지 중 오류 발생: {str(e)}")
                
                self.update_menu()
        except Exception as e:
            logger.error(f"서버 정지 실패: {str(e)}")
    
    def exit_app(self, icon, item):
        try:
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
        except Exception as e:
            logger.error(f"애플리케이션 종료 실패: {str(e)}")
            sys.exit(1)
    
    def run(self):
        try:
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
        except Exception as e:
            logger.critical(f"트레이 애플리케이션 실행 실패: {str(e)}")
            traceback.print_exc()
            # 심각한 오류 시 30초 대기 후 종료
            print(f"심각한 오류가 발생했습니다: {str(e)}")
            print("로그 파일을 확인하세요: " + tray_log_file)
            print("30초 후 종료됩니다...")
            time.sleep(30)
            sys.exit(1)

if __name__ == "__main__":
    # 예외 처리
    try:
        # 시그널 핸들러 설정
        def signal_handler(signum, frame):
            logger.info("종료 신호 수신. 애플리케이션을 종료합니다.")
            sys.exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # 애플리케이션 실행
        app = DealerDeskTrayApp()
        app.run()
    except Exception as e:
        logger.critical(f"애플리케이션 초기화 중 치명적 오류: {str(e)}")
        traceback.print_exc()
        
        # 심각한 오류 시 파일에 기록하고 콘솔에 표시
        error_message = f"치명적 오류: {str(e)}\n{traceback.format_exc()}"
        
        try:
            with open(os.path.join(os.getcwd(), "dealerdesk_critical_error.log"), "a", encoding="utf-8") as f:
                f.write(f"\n{'-'*50}\n{time.strftime('%Y-%m-%d %H:%M:%S')}\n{error_message}\n")
        except:
            pass
            
        print("\n" + "!" * 80)
        print(error_message)
        print("!" * 80 + "\n")
        
        print("30초 후 종료됩니다...")
        time.sleep(30)
        sys.exit(1) 