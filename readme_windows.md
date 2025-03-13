# Windows 환경에서 Dealer Desk 앱 빌드 및 실행 가이드

## 개요
이 문서는 Dealer Desk 로컬 서버를 Windows 환경에서 빌드하고 실행하는 방법을 안내합니다.

## 요구 사항
- Windows 10 이상
- Python 3.8 이상
- 인터넷 연결 (의존성 패키지 설치용)

## 개발 환경 설정

### 1. Python 설치
1. [Python 공식 사이트](https://www.python.org/downloads/)에서 Python 3.8 이상 버전을 다운로드하고 설치합니다.
2. 설치 시 "Add Python to PATH" 옵션을 선택합니다.
3. 설치 완료 후 명령 프롬프트를 열고 다음 명령어로 Python이 제대로 설치되었는지 확인합니다:
   ```
   python --version
   ```

### 2. 저장소 클론
1. Git이 설치되어 있다면 아래 명령으로 저장소를 클론합니다:
   ```
   git clone [저장소 URL]
   cd dealer-desk-local-server
   ```
2. Git이 없는 경우 저장소를 ZIP 파일로 다운로드하여 적절한 위치에 압축을 풀어도 됩니다.

### 3. 가상 환경 설정 (선택 사항)
1. 프로젝트 디렉토리에서 다음 명령어로 가상 환경을 생성합니다:
   ```
   python -m venv .venv
   ```
2. 가상 환경을 활성화합니다:
   ```
   .venv\Scripts\activate
   ```
3. 필요한 패키지를 설치합니다:
   ```
   pip install -r requirement.txt
   ```

## 빌드 방법

### 자동 빌드 스크립트 사용
1. 프로젝트 루트 디렉토리에서 `build_windows.bat` 파일을 더블 클릭하거나 명령 프롬프트에서 다음 명령어를 실행합니다:
   ```
   build_windows.bat
   ```
2. 빌드 스크립트가 자동으로 다음 작업을 수행합니다:
   - 필요한 의존성 패키지 설치
   - 앱 아이콘 생성 (없는 경우)
   - tray_app.py 파일 생성 (없는 경우)
   - PyInstaller를 사용하여 실행 파일 패키징
3. 빌드가 완료되면 `dist\DealerDesk` 디렉토리에 실행 파일이 생성됩니다.

### 수동 빌드 (스크립트 없이)
다음 단계로 직접 빌드할 수도 있습니다:

1. 필요한 패키지 설치:
   ```
   pip install -r requirement.txt
   pip install pyinstaller pystray pillow
   ```

2. PyInstaller를 사용하여 패키징:
   ```
   pyinstaller --clean --name "DealerDesk" ^
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
       --icon app_icon.png ^
       --windowed ^
       tray_app.py
   ```

## 애플리케이션 실행

### 배포 버전 실행
1. 빌드가 완료된 후 `dist\DealerDesk` 디렉토리로 이동합니다.
2. `DealerDesk.exe` 파일을 더블 클릭하여 애플리케이션을 실행합니다.
3. 애플리케이션이 트레이에 아이콘으로 표시되며, 웹 브라우저가 자동으로 열립니다.
4. 트레이 아이콘에서 다음 작업을 수행할 수 있습니다:
   - 웹 페이지 열기: 브라우저에서 Dealer Desk 웹 인터페이스 열기
   - 종료: 애플리케이션 종료

### 개발 모드로 실행
개발 목적으로 빌드하지 않고 직접 실행하려면:

1. 가상 환경이 활성화되어 있는지 확인합니다:
   ```
   .venv\Scripts\activate
   ```
2. 다음 명령으로 API 서버를 실행합니다:
   ```
   python main.py
   ```

## 문제 해결

### 애플리케이션이 실행되지 않는 경우
1. 명령 프롬프트를 열고 다음 명령으로 애플리케이션을 실행합니다:
   ```
   cd path\to\dist\DealerDesk
   DealerDesk.exe
   ```
2. 오류 메시지를 확인하고 필요한 조치를 취합니다.

### 포트 충돌 문제
서버가 포트 401이나 3000에서 시작되지 않는 경우 다른 프로그램이 해당 포트를 사용 중인지 확인합니다:
1. 관리자 권한으로 명령 프롬프트를 열고 다음 명령어를 실행합니다:
   ```
   netstat -ano | findstr "401"
   netstat -ano | findstr "3000"
   ```
2. PID를 확인하고 작업 관리자에서 해당 프로세스를 종료합니다.

## 도움말 및 지원
추가 도움이 필요하시면 프로젝트 관리자에게 문의하세요. 