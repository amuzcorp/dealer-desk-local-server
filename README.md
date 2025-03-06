# Dealer Desk Local Server

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

서버는 기본적으로 http://localhost:8000 에서 실행됩니다.

## API 문서

서버 실행 후 브라우저에서 다음 URL에 접속하여 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

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