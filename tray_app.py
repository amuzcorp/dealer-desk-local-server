import pystray
from PIL import Image, ImageDraw
import asyncio
import sys
import os
import subprocess
from threading import Thread

class DealerDeskTray:
    def __init__(self):
        self.icon = None
        self.process = None
        self.is_running = False
        
    def create_icon(self, color):
        # 아이콘 이미지 생성 (16x16 픽셀)
        image = Image.new('RGB', (16, 16), color='white')
        dc = ImageDraw.Draw(image)
        dc.rectangle([0, 0, 15, 15], fill=color)
        return image
        
    def start_server(self):
        if not self.is_running:
            try:
                # main.py 실행
                script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py')
                self.process = subprocess.Popen([sys.executable, script_path],
                                             creationflags=subprocess.CREATE_NO_WINDOW)
                self.is_running = True
                self.icon.icon = self.create_icon('green')  # 실행 중 상태 표시
                self.update_menu()
            except Exception as e:
                print(f"서버 시작 중 오류 발생: {e}")
                
    def stop_server(self):
        if self.is_running and self.process:
            try:
                self.process.terminate()
                self.process.wait()
                self.process = None
                self.is_running = False
                self.icon.icon = self.create_icon('red')  # 중지 상태 표시
                self.update_menu()
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
    app = DealerDeskTray()
    app.run() 