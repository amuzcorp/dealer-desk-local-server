@echo off
echo 딜러 데스크 API 서버 설치 스크립트를 시작합니다...
echo.

REM Python이 설치되어 있는지 확인
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python이 설치되어 있지 않습니다. Python 3.8 이상을 설치해주세요.
    echo https://www.python.org/downloads/ 에서 다운로드할 수 있습니다.
    pause
    exit /b 1
)

echo Python이 설치되어 있습니다. 필요한 패키지를 설치합니다...
echo.

REM 필요한 패키지 설치
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo 패키지 설치가 완료되었습니다. 서버를 빌드합니다...
echo.

REM 빌드 스크립트 실행
python build_win.py

echo.
echo 모든 과정이 완료되었습니다.
echo dist/DealerDeskServer 폴더에서 start_server.bat 파일을 실행하여 서버를 시작하세요.
echo.

pause 