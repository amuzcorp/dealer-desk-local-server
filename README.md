# 딜러 데스크 API 서버

윈도우 환경에서 실행 가능한 딜러 데스크 API 서버입니다.

## 시스템 요구사항

- Windows 10 이상
- Python 3.8 이상

## 빠른 시작 가이드

### 개발자를 위한 설치 및 실행 방법

1. 이 저장소를 복제하세요:
```
git clone <저장소 URL>
cd dealer-desk-local-server
```

2. `run_dev.bat` 파일을 실행하세요:
   - 자동으로 필요한 패키지를 설치하고 서버를 시작합니다.
   - 브라우저가 자동으로 열리고 http://localhost:3000으로 접속합니다.

### 배포용 버전 빌드 방법

1. `install_win.bat` 파일을 실행하세요:
   - 필요한 패키지를 설치하고 서버를 빌드합니다.
   - 빌드 결과물은 `dist/DealerDeskServer` 폴더에 생성됩니다.

2. 빌드 완료 후 `dist/DealerDeskServer` 폴더에서 `start_server.bat` 파일을 실행하세요:
   - 서버가 시작되고 브라우저가 자동으로 열립니다.

## 서버 정보

- API 서버는 401번 포트에서 실행됩니다.
- 웹 서버는 3000번 포트에서 실행됩니다.
- 서버 상태 확인: http://localhost:401/health
- API 문서: http://localhost:401/docs

## 로그인 정보

- 로그인 API: http://localhost:401/login
- 매장 선택 API: http://localhost:401/select-store

## 문제 해결

1. 서버가 실행되지 않는 경우:
   - Python이 올바르게 설치되어 있는지 확인하세요.
   - `pip install -r requirements.txt`로 필요한 패키지가 설치되어 있는지 확인하세요.

2. 포트 충돌 문제:
   - 다른 애플리케이션이 401번 또는 3000번 포트를 사용 중인지 확인하세요.
   - 필요한 경우 `main.py` 파일에서 포트 번호를 변경할 수 있습니다.

## 라이센스

이 프로젝트는 비공개 라이센스로 배포됩니다.

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