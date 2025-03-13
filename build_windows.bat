@echo off
echo Dealer Desk Local Server Build Script (Windows)
echo ======================================================

rem Create necessary directories if they don't exist
if not exist "build" mkdir build
if not exist "dist" mkdir dist

rem Setup Python virtual environment
echo Setting up virtual environment...
python -m venv build\venv
call build\venv\Scripts\activate.bat

rem Install dependencies
echo Installing required packages...
pip install -r requirement.txt
pip install pyinstaller pystray pillow

rem Run app icon creation script
if not exist "app_icon.png" (
    echo Creating app icon...
    python create_app_icon.py
)

rem Build application
echo Building with PyInstaller...

rem Create tray_app.py if it doesn't exist
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
    echo     """ Get resource path function """ >> tray_app.py
    echo     if hasattr^(sys, '_MEIPASS'^): >> tray_app.py
    echo         return os.path.join^(sys._MEIPASS, relative_path^) >> tray_app.py
    echo     return os.path.join^(os.path.abspath^("."), relative_path^) >> tray_app.py
    echo. >> tray_app.py
    echo def run_server^(^): >> tray_app.py
    echo     """ Server execution function """ >> tray_app.py
    echo     try: >> tray_app.py
    echo         import main >> tray_app.py
    echo         asyncio.run^(main.run_all^(^)^) >> tray_app.py
    echo     except Exception as e: >> tray_app.py
    echo         traceback.print_exc^(^) >> tray_app.py
    echo         root = tk.Tk^(^) >> tray_app.py
    echo         root.withdraw^(^) >> tray_app.py
    echo         messagebox.showerror^("Error", f"Error occurred while running the server: {str^(e^)}") >> tray_app.py
    echo         root.destroy^(^) >> tray_app.py
    echo         sys.exit^(1^) >> tray_app.py
    echo. >> tray_app.py
    echo def on_clicked^(icon, item^): >> tray_app.py
    echo     """ Tray icon click event handler """ >> tray_app.py
    echo     if str^(item^) == "Open Web Page": >> tray_app.py
    echo         webbrowser.open^("http://localhost:3000") >> tray_app.py
    echo     elif str^(item^) == "Exit": >> tray_app.py
    echo         icon.stop^(^) >> tray_app.py
    echo         os._exit^(0^) >> tray_app.py
    echo. >> tray_app.py
    echo def setup_tray^(^): >> tray_app.py
    echo     """ Setup tray icon """ >> tray_app.py
    echo     try: >> tray_app.py
    echo         icon_path = resource_path^("app_icon.png") >> tray_app.py
    echo         image = Image.open^(icon_path^) >> tray_app.py
    echo         menu = ^(pystray.MenuItem^('Open Web Page', on_clicked^), >> tray_app.py
    echo                pystray.MenuItem^('Exit', on_clicked^)^) >> tray_app.py
    echo         icon = pystray.Icon^("dealer_desk", image, "Dealer Desk", menu^) >> tray_app.py
    echo         return icon >> tray_app.py
    echo     except Exception as e: >> tray_app.py
    echo         traceback.print_exc^(^) >> tray_app.py
    echo         print^(f"Error setting up tray icon: {str^(e^)}") >> tray_app.py
    echo         return None >> tray_app.py
    echo. >> tray_app.py
    echo if __name__ == "__main__": >> tray_app.py
    echo     # Start server thread >> tray_app.py
    echo     server_thread = threading.Thread^(target=run_server, daemon=True^) >> tray_app.py
    echo     server_thread.start^(^) >> tray_app.py
    echo     # Setup and run tray icon >> tray_app.py
    echo     icon = setup_tray^(^) >> tray_app.py
    echo     if icon: >> tray_app.py
    echo         # Auto-open web page >> tray_app.py
    echo         threading.Timer^(2, lambda: webbrowser.open^("http://localhost:3000")^).start^(^) >> tray_app.py
    echo         # Run tray icon >> tray_app.py
    echo         icon.run^(^) >> tray_app.py
    echo     else: >> tray_app.py
    echo         # Run server only if tray icon setup fails >> tray_app.py
    echo         run_server^(^) >> tray_app.py
)

rem Create __init__.py in Controllers directory if it doesn't exist
if not exist "Controllers\__init__.py" (
    type nul > Controllers\__init__.py
)

rem Create databases directory if it doesn't exist
if not exist "databases" (
    mkdir databases
)

rem Execute build command
echo Starting packaging command...
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
echo Build completed.
echo Executable has been created in the dist\DealerDesk directory.

rem Deactivate virtual environment
call build\venv\Scripts\deactivate.bat

echo.
echo ======================================================
echo Press any key to start building...
pause 