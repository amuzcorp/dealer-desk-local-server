@echo off
echo Dealer Desk Local Server 빌드 스크립트 (Windows용)
echo ======================================================

rem 필요한 디렉토리가 없는 경우 생성
if not exist "build" mkdir build
if not exist "dist" mkdir dist

rem 파이썬 가상환경 설정
echo 가상환경 설정 중...
python -m venv build\venv
call build\venv\Scripts\activate.bat

rem 의존성 설치
echo 필요한 패키지 설치 중...
pip install -r requirement.txt
pip install pyinstaller pystray pillow

rem 앱 아이콘 생성 스크립트 실행
if not exist "app_icon.png" (
    echo 앱 아이콘 생성 중...
    python create_app_icon.py
)

rem 애플리케이션 빌드
echo PyInstaller로 애플리케이션 빌드 중...

rem tray_app.py가 없으면 생성
if not exist "tray_app.py" (
    echo import os > tray_app.py
    echo import sys >> tray_app.py
    echo import asyncio >> tray_app.py
    echo import webbrowser >> tray_app.py
    echo import subprocess >> tray_app.py
    echo import threading >> tray_app.py
    echo from PIL import Image >> tray_app.py
    echo import pystray >> tray_app.py
    echo import tkinter as tk >> tray_app.py
    echo import traceback >> tray_app.py
    echo from tkinter import messagebox >> tray_app.py
    echo. >> tray_app.py
    echo def resource_path^(relative_path^): >> tray_app.py
    echo     """ 리소스 경로 가져오기 함수 """ >> tray_app.py
    echo     if hasattr^(sys, '_MEIPASS'^): >> tray_app.py
    echo         return os.path.join^(sys._MEIPASS, relative_path^) >> tray_app.py
    echo     return os.path.join^(os.path.abspath^("."), relative_path^) >> tray_app.py
    echo. >> tray_app.py
    echo def run_server^(^): >> tray_app.py
    echo     """ 서버 실행 함수 """ >> tray_app.py
    echo     try: >> tray_app.py
    echo         import main >> tray_app.py
    echo         asyncio.run^(main.run_all^(^)^) >> tray_app.py
    echo     except Exception as e: >> tray_app.py
    echo         traceback.print_exc^(^) >> tray_app.py
    echo         root = tk.Tk^(^) >> tray_app.py
    echo         root.withdraw^(^) >> tray_app.py
    echo         messagebox.showerror^("오류", f"서버 실행 중 오류가 발생했습니다: {str^(e^)}") >> tray_app.py
    echo         root.destroy^(^) >> tray_app.py
    echo         sys.exit^(1^) >> tray_app.py
    echo. >> tray_app.py
    echo def on_clicked^(icon, item^): >> tray_app.py
    echo     """ 트레이 아이콘 클릭 이벤트 처리 """ >> tray_app.py
    echo     if str^(item^) == "웹 페이지 열기": >> tray_app.py
    echo         webbrowser.open^("http://localhost:3000") >> tray_app.py
    echo     elif str^(item^) == "종료": >> tray_app.py
    echo         icon.stop^(^) >> tray_app.py
    echo         os._exit^(0^) >> tray_app.py
    echo. >> tray_app.py
    echo def setup_tray^(^): >> tray_app.py
    echo     """ 트레이 아이콘 설정 """ >> tray_app.py
    echo     try: >> tray_app.py
    echo         icon_path = resource_path^("app_icon.png") >> tray_app.py
    echo         image = Image.open^(icon_path^) >> tray_app.py
    echo         menu = ^(pystray.MenuItem^('웹 페이지 열기', on_clicked^), >> tray_app.py
    echo                pystray.MenuItem^('종료', on_clicked^)^) >> tray_app.py
    echo         icon = pystray.Icon^("dealer_desk", image, "딜러 데스크", menu^) >> tray_app.py
    echo         return icon >> tray_app.py
    echo     except Exception as e: >> tray_app.py
    echo         traceback.print_exc^(^) >> tray_app.py
    echo         print^(f"트레이 아이콘 설정 중 오류 발생: {str^(e^)}") >> tray_app.py
    echo         return None >> tray_app.py
    echo. >> tray_app.py
    echo if __name__ == "__main__": >> tray_app.py
    echo     # 서버 스레드 시작 >> tray_app.py
    echo     server_thread = threading.Thread^(target=run_server, daemon=True^) >> tray_app.py
    echo     server_thread.start^(^) >> tray_app.py
    echo     # 트레이 아이콘 설정 및 실행 >> tray_app.py
    echo     icon = setup_tray^(^) >> tray_app.py
    echo     if icon: >> tray_app.py
    echo         # 웹 페이지 자동 열기 >> tray_app.py
    echo         threading.Timer^(2, lambda: webbrowser.open^("http://localhost:3000")^).start^(^) >> tray_app.py
    echo         # 트레이 아이콘 실행 >> tray_app.py
    echo         icon.run^(^) >> tray_app.py
    echo     else: >> tray_app.py
    echo         # 트레이 아이콘 설정 실패 시 서버만 실행 >> tray_app.py
    echo         run_server^(^) >> tray_app.py
)

rem Controllers 디렉토리에 __init__.py 파일이 없으면 생성
if not exist "Controllers\__init__.py" (
    type nul > Controllers\__init__.py
)

rem databases 디렉토리가 없으면 생성
if not exist "databases" (
    mkdir databases
)

rem 빌드 명령 실행
echo 패키징 명령 시작...
pyinstaller --clean --noconfirm --name "DealerDesk" ^
    --add-data "app_icon.png;." ^
    --add-data "app;app" ^
    --add-data "databases;databases" ^
    --add-data "Controllers;Controllers" ^
    --add-data "main.py;." ^
    --add-data "web_server.py;." ^
    --add-data "database.py;." ^
    --add-data "schemas.py;." ^
    --add-data "models.py;." ^
    --add-data "auth_manager.py;." ^
    --add-data "central_socket.py;." ^
    --add-data "sql_app.db;." ^
    --hidden-import uvicorn.logging ^
    --hidden-import uvicorn.lifespan.on ^
    --hidden-import uvicorn.lifespan.off ^
    --hidden-import pydantic ^
    --hidden-import sqlalchemy.sql.default_comparator ^
    --hidden-import email.mime.multipart ^
    --hidden-import email.mime.text ^
    --hidden-import email.mime.image ^
    --hidden-import fastapi.middleware ^
    --hidden-import fastapi.middleware.cors ^
    --hidden-import fastapi.responses ^
    --hidden-import starlette.middleware ^
    --hidden-import starlette.middleware.cors ^
    --hidden-import starlette.responses ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import tkinter.scrolledtext ^
    --hidden-import tkinter.messagebox ^
    --hidden-import tkinter.filedialog ^
    --hidden-import fastapi ^
    --hidden-import starlette ^
    --hidden-import asyncio ^
    --hidden-import aiohttp ^
    --hidden-import logging.handlers ^
    --hidden-import encodings.idna ^
    --icon app_icon.png ^
    --windowed ^
    tray_app.py

echo.
echo 빌드가 완료되었습니다.
echo dist\DealerDesk 디렉토리에 실행 파일이 생성되었습니다.

rem 가상환경 비활성화
call build\venv\Scripts\deactivate.bat

echo.
echo ======================================================
echo 빌드를 시작하려면 아무 키나 누르세요...
pause 