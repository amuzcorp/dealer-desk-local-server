import pystray
from PIL import Image, ImageDraw
import subprocess
import sys
import os
import threading
import asyncio
import signal
import time
import webbrowser
import socket
import json
from pathlib import Path

# PyWin32 라이브러리 명시적 가져오기
try:
    import win32api
    import win32con
    import win32gui
except ImportError:
    pass  # macOS 등 다른 플랫폼에서는 무시

class DealerDeskTray:
    def __init__(self):
        self.icon = None
        self.process = None
        self.is_running = False
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_file = os.path.join(self.app_dir, "dealer_desk.log")
        self.config_file = os.path.join(self.app_dir, "config.json")
        self.config = self.load_config()
        
    def load_config(self):
        """설정 파일 로드"""
        default_config = {
            "api_port": 401,
            "web_port": 3000,
            "auto_start": True,
            "open_browser": True
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return default_config
        except Exception as e:
            self.log(f"설정 로드 오류: {e}")
            return default_config
            
    def save_config(self):
        """설정 파일 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.log(f"설정 저장 오류: {e}")
    
    def log(self, message):
        """로그 기록"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message)
        except Exception as e:
            print(f"로그 기록 오류: {e}")
            
    def create_icon(self, color):
        """트레이 아이콘 이미지 생성"""
        width, height = 64, 64
        image = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # 원형 아이콘 그리기
        dc.ellipse((4, 4, width-4, height-4), fill=color)
        
        # 테두리 그리기
        dc.ellipse((4, 4, width-4, height-4), outline="white", width=2)
        
        return image
        
    def is_port_in_use(self, port):
        """포트가 사용 중인지 확인"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
            
    def start_server(self):
        """서버 시작"""
        if not self.is_running:
            try:
                # 포트 확인
                api_port = self.config.get("api_port", 401)
                web_port = self.config.get("web_port", 3000)
                
                if self.is_port_in_use(api_port):
                    self.log(f"API 포트 {api_port}가 이미 사용 중입니다.")
                    return False
                    
                if self.is_port_in_use(web_port):
                    self.log(f"웹 포트 {web_port}가 이미 사용 중입니다.")
                    return False
                
                # 실행 파일 경로 설정
                if getattr(sys, 'frozen', False):
                    # PyInstaller로 패키징된 경우
                    script_path = os.path.join(sys._MEIPASS, "main.py")
                    self.log(f"패키징된 환경에서 실행 중: {script_path}")
                else:
                    # 일반 Python 스크립트로 실행되는 경우
                    script_path = os.path.join(self.app_dir, "main.py")
                    self.log(f"개발 환경에서 실행 중: {script_path}")
                
                # 환경 변수 설정
                env = os.environ.copy()
                env["PYTHONUNBUFFERED"] = "1"
                
                # 서버 프로세스 시작
                if os.name == 'nt':  # Windows
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0  # SW_HIDE
                    
                    self.process = subprocess.Popen(
                        [sys.executable, script_path],
                        cwd=self.app_dir,
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        startupinfo=startupinfo,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:  # macOS, Linux 등
                    self.process = subprocess.Popen(
                        [sys.executable, script_path],
                        cwd=self.app_dir,
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                
                self.is_running = True
                self.icon.icon = self.create_icon((0, 200, 0))  # 초록색 - 실행 중
                self.update_menu()
                
                # 로그 스레드 시작
                threading.Thread(target=self.log_output, daemon=True).start()
                
                # 브라우저 열기
                if self.config.get("open_browser", True):
                    time.sleep(2)  # 서버가 시작될 때까지 잠시 대기
                    webbrowser.open(f"http://localhost:{web_port}")
                
                self.log("서버가 성공적으로 시작되었습니다.")
                return True
                
            except Exception as e:
                self.log(f"서버 시작 중 오류 발생: {e}")
                return False
        return True
                
    def log_output(self):
        """서버 출력을 로그 파일에 기록"""
        while self.process and self.is_running:
            try:
                for line in iter(self.process.stdout.readline, b''):
                    if line:
                        self.log(line.decode('utf-8', errors='replace').strip())
                for line in iter(self.process.stderr.readline, b''):
                    if line:
                        self.log(f"ERROR: {line.decode('utf-8', errors='replace').strip()}")
            except Exception as e:
                self.log(f"로그 출력 처리 중 오류: {e}")
                break
                
    def stop_server(self):
        """서버 중지"""
        if self.is_running and self.process:
            try:
                # 서버 프로세스 종료
                self.process.terminate()
                
                # 5초 대기 후 강제 종료
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    
                self.process = None
                self.is_running = False
                self.icon.icon = self.create_icon((200, 0, 0))  # 빨간색 - 중지됨
                self.update_menu()
                self.log("서버가 중지되었습니다.")
                return True
            except Exception as e:
                self.log(f"서버 중지 중 오류 발생: {e}")
                return False
        return True
                
    def toggle_server(self, _):
        """서버 상태 토글"""
        if self.is_running:
            self.stop_server()
        else:
            self.start_server()
            
    def open_web_interface(self, _):
        """웹 인터페이스 열기"""
        web_port = self.config.get("web_port", 3000)
        webbrowser.open(f"http://localhost:{web_port}")
        
    def open_log_file(self, _):
        """로그 파일 열기"""
        if os.path.exists(self.log_file):
            if os.name == 'nt':  # Windows
                os.startfile(self.log_file)
            else:  # macOS, Linux 등
                subprocess.call(['open', self.log_file])
        else:
            self.log("로그 파일이 존재하지 않습니다.")
            
    def toggle_auto_start(self, _):
        """자동 시작 설정 토글"""
        self.config["auto_start"] = not self.config.get("auto_start", True)
        self.save_config()
        self.update_menu()
        
    def toggle_open_browser(self, _):
        """브라우저 자동 열기 설정 토글"""
        self.config["open_browser"] = not self.config.get("open_browser", True)
        self.save_config()
        self.update_menu()
            
    def exit_application(self, _):
        """애플리케이션 종료"""
        self.stop_server()
        self.icon.stop()
        
    def update_menu(self):
        """메뉴 업데이트"""
        self.icon.menu = self.create_menu()
        
    def create_menu(self):
        """트레이 아이콘 메뉴 생성"""
        auto_start = self.config.get("auto_start", True)
        open_browser = self.config.get("open_browser", True)
        
        return pystray.Menu(
            pystray.MenuItem(
                "딜러 데스크 서버" + (" (실행 중)" if self.is_running else " (중지됨)"),
                None,
                enabled=False
            ),
            pystray.MenuItem(
                "중지" if self.is_running else "시작",
                self.toggle_server
            ),
            pystray.MenuItem(
                "웹 인터페이스 열기",
                self.open_web_interface,
                enabled=self.is_running
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "설정",
                pystray.Menu(
                    pystray.MenuItem(
                        "✓ 자동 시작" if auto_start else "자동 시작",
                        self.toggle_auto_start
                    ),
                    pystray.MenuItem(
                        "✓ 브라우저 자동 열기" if open_browser else "브라우저 자동 열기",
                        self.toggle_open_browser
                    )
                )
            ),
            pystray.MenuItem("로그 보기", self.open_log_file),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("종료", self.exit_application)
        )
        
    def run(self):
        """트레이 애플리케이션 실행"""
        # 초기 아이콘 생성 (빨간색 - 중지 상태)
        self.icon = pystray.Icon(
            "dealer_desk",
            self.create_icon((200, 0, 0)),
            "딜러 데스크 서버",
            self.create_menu()
        )
        
        # 자동 시작 설정이 켜져 있으면 서버 시작
        if self.config.get("auto_start", True):
            # 아이콘이 표시된 후 서버 시작을 위해 스레드 사용
            threading.Thread(target=lambda: time.sleep(1) or self.start_server(), daemon=True).start()
        
        # 트레이 아이콘 표시
        self.icon.run()

if __name__ == "__main__":
    # Windows에서만 실행
    if os.name == 'nt':
        app = DealerDeskTray()
        app.run()
    else:
        print("이 애플리케이션은 Windows에서만 실행할 수 있습니다.")
        sys.exit(1) 