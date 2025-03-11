import pystray
from PIL import Image, ImageDraw
import asyncio
import sys
import os
import subprocess
from threading import Thread
import webbrowser
import signal
import uvicorn
import main
from main import app as main_app
from web_server import app as web_app

class DealerDeskTray:
    def __init__(self):
        self.icon = None
        self.api_server = None
        self.web_server = None
        self.is_running = False
        self.api_server_thread = None
        self.web_server_thread = None
        
    def create_icon(self, color):
        # 아이콘 이미지 생성 (16x16 픽셀)
        image = Image.new('RGB', (16, 16), color='white')
        dc = ImageDraw.Draw(image)
        dc.rectangle([0, 0, 15, 15], fill=color)
        return image
    
    def run_api_server(self):
        config = uvicorn.Config(main_app, host="0.0.0.0", port=8000, reload=False)
        self.api_server = uvicorn.Server(config=config)
        self.api_server.run()
        
    def run_web_server(self):
        config = uvicorn.Config(web_app, host="0.0.0.0", port=3000, reload=False)
        self.web_server = uvicorn.Server(config=config)
        self.web_server.run()
        
    def start_server(self):
        if not self.is_running:
            try:
                # API 서버 스레드 시작
                self.api_server_thread = Thread(target=self.run_api_server)
                self.api_server_thread.daemon = True
                self.api_server_thread.start()
                
                # 웹 서버 스레드 시작
                self.web_server_thread = Thread(target=self.run_web_server)
                self.web_server_thread.daemon = True
                self.web_server_thread.start()
                
                self.is_running = True
                self.icon.icon = self.create_icon('green')  # 실행 중 상태 표시
                self.update_menu()
                
                # 브라우저 열기
                webbrowser.open("http://localhost:3000")
                
            except Exception as e:
                print(f"서버 시작 중 오류 발생: {e}")
                
    def stop_server(self):
        if self.is_running:
            try:
                if self.api_server:
                    self.api_server.should_exit = True
                if self.web_server:
                    self.web_server.should_exit = True
                    
                self.is_running = False
                self.icon.icon = self.create_icon('red')  # 중지 상태 표시
                self.update_menu()
                
                # 스레드 종료 대기
                if self.api_server_thread:
                    self.api_server_thread.join(timeout=5)
                if self.web_server_thread:
                    self.web_server_thread.join(timeout=5)
                    
            except Exception as e:
                print(f"서버 중지 중 오류 발생: {e}")
                
    def toggle_server(self):
        if self.is_running:
            self.stop_server()
        else:
            self.start_server()
            
    def exit_application(self):
        self.stop_server()
        self.icon.stop()
        
    def update_menu(self):
        self.icon.menu = self.create_menu()
        
    def create_menu(self):
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
                lambda: webbrowser.open("http://localhost:3000") if self.is_running else None,
                enabled=self.is_running
            ),
            pystray.MenuItem("종료", self.exit_application)
        )
        
    def run(self):
        # 초기 아이콘 생성 (빨간색 - 중지 상태)
        self.icon = pystray.Icon(
            "dealer_desk",
            self.create_icon('red'),
            "Dealer Desk Server",
            self.create_menu()
        )
        
        # 서버 자동 시작
        self.start_server()
        
        # 트레이 아이콘 표시
        self.icon.run()

if __name__ == "__main__":
    # SIGINT 핸들러 설정
    def signal_handler(signum, frame):
        if app:
            app.exit_application()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    app = DealerDeskTray()
    app.run() 