# 딜러 데스크 로컬 서버

딜러 데스크 로컬 서버는 데이터베이스 관리와 웹소켓 통신을 통해 포커 게임 관리를 지원하는 백엔드 서버입니다.

## 특징

- 시스템 트레이에서 실행되는 백그라운드 서버
- 웹소켓을 통한 실시간 데이터 통신
- 게임, 사용자, 테이블 데이터 관리
- 웹 인터페이스를 통한 접근 가능
- 윈도우에서 독립 실행형 애플리케이션으로 실행 가능

## 요구 사항

- Python 3.13.2 이상
- 필요한 패키지: fastapi, uvicorn, sqlalchemy, pystray, pillow

## 설치 및 실행

### 개발 환경에서 실행

1. 필요한 패키지 설치:
```
pip install fastapi uvicorn sqlalchemy pystray pillow
```

2. 트레이 애플리케이션 실행:
```
python run_tray_app.py
```

### 윈도우용 실행 파일 빌드

1. PyInstaller 설치:
```
pip install pyinstaller
```

2. 빌드 스크립트 실행:
```
python build_windows.py
```

3. `dist` 폴더에 생성된 `DealerDeskServer.exe` 파일을 실행합니다.

## 사용법

1. 애플리케이션을 실행하면 시스템 트레이에 아이콘이 표시됩니다.
2. 트레이 아이콘을 클릭하여 메뉴를 열 수 있습니다:
   - 서버 시작: 서버를 시작합니다 (자동으로 시작됨)
   - 서버 중지: 실행 중인 서버를 중지합니다
   - 웹 인터페이스 열기: 기본 브라우저에서 웹 인터페이스를 엽니다
   - 종료: 서버를 종료하고 애플리케이션을 닫습니다

3. 웹 인터페이스는 `http://localhost:8000`에서 접근할 수 있습니다.

## 로그 확인

애플리케이션 로그는 `dealer_desk_tray.log` 파일에 저장됩니다.

## 개발 정보

- FastAPI를 사용한 RESTful API 서버
- SQLAlchemy를 사용한 데이터베이스 관리
- WebSocket을 통한 실시간 통신
- pystray를 사용한 시스템 트레이 인터페이스

## 개요
딜러 데스크 로컬 서버는 매장별 데이터를 관리하고 중앙 서버와 통신하는 로컬 서버입니다.

## 설치 및 실행

### 필수 조건

- Python 3.8 이상

### 설치

1. 저장소를 클론합니다:
```bash
git clone <repository-url>
cd dealer-desk-local-server
```

2. 가상 환경을 생성하고 활성화합니다:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows
```

3. 의존성을 설치합니다:
```bash
pip install -r requirements.txt
```

### 실행

```bash
python -m app.main
```

서버는 기본적으로 http://localhost:401 에서 실행됩니다.

## API 문서

서버 실행 후 브라우저에서 다음 URL에 접속하여 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:401/docs
- ReDoc: http://localhost:401/redoc

## 웹소켓 서버

웹소켓 서버를 실행하려면:

```bash
python central_socket.py
```

## 주요 APIs

- `/tables` - 테이블 관리
- `/devices` - 디바이스 관리 
- `/presets` - 프리셋 관리
- `/games` - 게임 관리
- `/purchases` - 구매 관리 

## API 사용 방법

### 1. 로그인
```
POST /login
```
요청 본문:
```json
{
  "user_id": "이메일",
  "user_pwd": "비밀번호"
}
```
응답:
```json
{
  "status": "success",
  "is_offline_mode": false,
  "stores": [
    {
      "id": 1,
      "name": "매장1",
      "tenant_id": "xxx",
      ...
    }
  ],
  "store_ids": [1]
}
```

### 2. 매장 선택
```
POST /select-store
```
요청 본문:
```json
{
  "store_id": 1
}
```
응답:
```json
{
  "status": "success",
  "store_name": "매장1",
  "tenant_id": "xxx",
  "is_offline_mode": false,
  "is_connected": true
}
```

### 3. API 요청 시 매장 ID 헤더 포함
매장 선택 후 모든 API 요청에는 `X-Store-ID` 헤더를 포함해야 합니다.

예시:
```
GET /devices/get-auth-device
X-Store-ID: 1
```

## 오프라인 모드
중앙 서버와 연결이 끊어진 경우에도 로컬 서버는 오프라인 모드로 동작합니다. 이전에 로그인한 계정 정보가 저장되어 있으면 오프라인 모드로 로그인이 가능합니다.

## 데이터베이스
각 매장별로 독립적인 데이터베이스가 `./databases` 디렉토리에 생성됩니다. 데이터베이스 파일명은 `store_{store_id}.db` 형식입니다. 