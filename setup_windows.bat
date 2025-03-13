@echo off
echo ==============================
echo 딜러 데스크 서버 설치 스크립트
echo ==============================
echo.

REM Python 설치 확인
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python이 설치되어 있지 않습니다.
    echo https://www.python.org/downloads/ 에서 Python 3.8 이상을 설치하세요.
    pause
    exit /b
)

echo Python이 설치되어 있습니다.
echo.

REM pip 업그레이드
echo pip를 최신 버전으로 업그레이드합니다...
python -m pip install --upgrade pip

REM 필요한 라이브러리 설치
echo 필요한 패키지를 설치합니다...
python -m pip install fastapi uvicorn sqlalchemy pyinstaller python-multipart websockets requests aiohttp

REM requirements.txt가 있다면 설치
if exist requirements.txt (
    echo requirements.txt에서 패키지를 설치합니다...
    python -m pip install -r requirements.txt
)

REM 필요한 디렉토리 생성
if not exist templates mkdir templates
if not exist static mkdir static
if not exist dist mkdir dist

echo.
echo 설치가 완료되었습니다!
echo.
echo 다음 중 하나를 선택하세요:
echo 1. 실행 파일 빌드 (python build_windows.py)
echo 2. 직접 실행 (run_server.bat)
echo.

set /p choice="선택 (1 또는 2): "

if "%choice%"=="1" (
    echo.
    echo 실행 파일을 빌드합니다...
    python build_windows.py
) else if "%choice%"=="2" (
    echo.
    echo 서버를 직접 실행합니다...
    call run_server.bat
) else (
    echo.
    echo 잘못된 선택입니다. setup_windows.bat를 다시 실행하여 선택하세요.
)

pause 