@echo off
echo ==============================
echo 딜러 데스크 API 서버 시작
echo ==============================
echo.
echo 서버를 시작합니다. 잠시 기다려주세요...
echo.
echo 포트:
echo - API 서버: 401
echo - 웹 서버: 3000
echo.
echo 서버를 종료하려면 이 창을 닫으세요.
echo.

REM EXE 파일이 있는 경우
if exist "dist\DealerDeskServer.exe" (
    start /b dist\DealerDeskServer.exe
    echo 서버가 시작되었습니다. 브라우저에서 http://localhost:3000 으로 접속하세요.
) else (
    REM EXE 파일이 없는 경우 Python으로 직접 실행
    echo 빌드된 실행 파일을 찾을 수 없습니다. Python으로 직접 실행합니다.
    
    REM Python이 설치되어 있는지 확인
    python --version > nul 2>&1
    if %errorlevel% neq 0 (
        echo ERROR: Python이 설치되어 있지 않습니다.
        echo Python을 설치하거나 build_windows.py를 실행하여 EXE 파일을 생성하세요.
        pause
        exit /b
    )
    
    REM 필요한 패키지 확인 및 설치
    echo 필요한 패키지를 확인합니다...
    pip install fastapi uvicorn sqlalchemy > nul 2>&1
    
    REM main.py 실행
    echo Python으로 서버를 시작합니다...
    start /b python main.py
    echo 서버가 시작되었습니다. 브라우저에서 http://localhost:3000 으로 접속하세요.
)

echo.
echo 서버가 백그라운드에서 실행 중입니다.
pause 