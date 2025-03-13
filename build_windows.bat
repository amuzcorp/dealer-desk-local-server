@echo off
echo DealerDesk Windows 빌드를 시작합니다...

REM 가상환경 생성 및 활성화
python -m venv venv
call venv\Scripts\activate

REM 필요한 패키지 설치
pip install -r requirements.txt
pip install pyinstaller

REM PyInstaller로 빌드
pyinstaller --clean dealer_desk.spec

echo 빌드가 완료되었습니다.
echo 실행 파일은 dist 폴더에 있습니다.

pause 