import os
import sys
import webbrowser
import subprocess
import threading
import asyncio
import pystray
import uvicorn
from PIL import Image, ImageDraw
import logging
import platform
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dealer_desk_tray.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dealer-desk-tray")

# 서버 상태
server_process = None
server_running = False

def create_icon():
    """시스템 트레이 아이콘 생성"""
    width = 64
    height = 64
    
    # 간단한 아이콘 이미지 생성
    image = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    
    # 딜러 데스크 아이콘 - 단순한 카드 테이블 형태로 그림
    dc.rectangle((10, 10, width-10, height-10), fill='green', outline='white', width=2)
    dc.ellipse((15, 15, width-15, height-15), outline='white', width=2)
    
    return image

def start_server():
    """서버 시작"""
    global server_process, server_running
    
    if server_running:
        logger.info("서버가 이미 실행 중입니다.")
        return
    
    try:
        logger.info("서버를 시작합니다...")
        
        # 실행 파일 디렉토리 확인
        if getattr(sys, 'frozen', False):
            # 실행 파일로 실행된 경우
            app_dir = os.path.dirname(sys.executable)
        else:
            # 스크립트로 실행된 경우
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        os.chdir(app_dir)
        
        # 기본 Popen 인자
        popen_args = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
        }
        
        # 윈도우 전용 인자 추가
        if platform.system() == 'Windows':
            popen_args['creationflags'] = subprocess.CREATE_NO_WINDOW  # 윈도우에서 콘솔 창 숨기기
        
        # FastAPI 서버 시작
        server_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
            **popen_args
        )
        
        server_running = True
        logger.info("서버가 성공적으로 시작되었습니다.")
        
        # 서버 로그 모니터링
        threading.Thread(target=monitor_server_output, daemon=True).start()
        
    except Exception as e:
        logger.error(f"서버 시작 중 오류 발생: {e}")

def monitor_server_output():
    """서버 출력 모니터링"""
    global server_process
    
    while server_process and server_process.poll() is None:
        try:
            line = server_process.stdout.readline()
            if line:
                logger.info(f"서버: {line.decode('utf-8').strip()}")
        except Exception as e:
            logger.error(f"서버 출력 모니터링 중 오류: {e}")
            break

def stop_server():
    """서버 중지"""
    global server_process, server_running
    
    if not server_running:
        logger.info("서버가 실행 중이 아닙니다.")
        return
    
    try:
        logger.info("서버를 중지합니다...")
        
        if server_process:
            server_process.terminate()
            server_process.wait(timeout=5)
            server_process = None
            
        server_running = False
        logger.info("서버가 성공적으로 중지되었습니다.")
        
    except Exception as e:
        logger.error(f"서버 중지 중 오류 발생: {e}")
        
        # 강제 종료 시도
        if server_process:
            server_process.kill()
            server_process = None
            
        server_running = False

def open_browser():
    """브라우저에서 애플리케이션 열기"""
    try:
        webbrowser.open("http://localhost:8000")
        logger.info("웹 브라우저가 열렸습니다.")
    except Exception as e:
        logger.error(f"브라우저 열기 중 오류 발생: {e}")

def exit_app(icon):
    """애플리케이션 종료"""
    stop_server()
    icon.stop()
    logger.info("애플리케이션이 종료되었습니다.")

def get_server_status():
    """서버 상태 확인"""
    return "실행 중" if server_running else "중지됨"

def setup_tray():
    """시스템 트레이 설정"""
    icon = pystray.Icon("dealer-desk")
    icon.icon = create_icon()
    
    def update_menu():
        """메뉴 업데이트"""
        return pystray.Menu(
            pystray.MenuItem(f"상태: {get_server_status()}", None, enabled=False),
            pystray.MenuItem("서버 시작", start_server, enabled=not server_running),
            pystray.MenuItem("서버 중지", stop_server, enabled=server_running),
            pystray.MenuItem("웹 인터페이스 열기", open_browser, enabled=server_running),
            pystray.MenuItem("종료", exit_app)
        )
    
    icon.menu = update_menu
    
    # 메뉴 주기적 업데이트
    def refresh_menu():
        if icon and hasattr(icon, "_menu_handle"):
            icon.update_menu()
        threading.Timer(1.0, refresh_menu).start()
    
    threading.Timer(1.0, refresh_menu).start()
    
    # 트레이 아이콘 표시
    logger.info("시스템 트레이 아이콘을 시작합니다.")
    icon.run()

def main():
    """메인 함수"""
    logger.info("딜러 데스크 로컬 서버 트레이 애플리케이션을 시작합니다.")
    logger.info(f"운영체제: {platform.system()} {platform.release()}")
    logger.info(f"Python 버전: {platform.python_version()}")
    
    # 자동으로 서버 시작
    start_server()
    
    # 시스템 트레이 설정 및 실행
    setup_tray()

if __name__ == "__main__":
    main() 