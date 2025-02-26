# 딜러 데스크 로컬 서버

딜러 데스크 시스템의 로컬 백엔드 서버 애플리케이션입니다.

## 프로젝트 구조

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