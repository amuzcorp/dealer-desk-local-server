@echo off
echo 딜러 데스크 API 서버 개발 환경을 시작합니다...
echo.

REM Python이 설치되어 있는지 확인
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python이 설치되어 있지 않습니다. Python 3.8 이상을 설치해주세요.
    echo https://www.python.org/downloads/ 에서 다운로드할 수 있습니다.
    pause
    exit /b 1
)

REM 필요한 패키지 설치
python -m pip install -r requirements.txt

echo.
echo API 서버를 시작합니다...
echo.

start python main.py

echo.
echo 서버가 시작되었습니다.
echo 브라우저를 열고 http://localhost:3000 으로 접속하세요.
echo.

timeout /t 5
start http://localhost:3000

echo 종료하려면 이 창을 닫으세요.
pause 