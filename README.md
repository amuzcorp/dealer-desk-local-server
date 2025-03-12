# 딜러 데스크 로컬 서버

딜러 데스크 API 서버 및 웹 서버를 로컬에서 실행할 수 있는 애플리케이션입니다.

## 윈도우용 트레이 애플리케이션

이 프로젝트는 이제 윈도우 트레이 애플리케이션으로 빌드하여 사용할 수 있습니다. 트레이 애플리케이션은 작업 표시줄의 알림 영역(시스템 트레이)에 아이콘으로 표시되며, 이를 통해 서버를 시작/정지하고 웹 인터페이스에 접근할 수 있습니다.

### 필요 사항

- Python 3.13.2
- 필요한 패키지들 (requirements.txt 참조)

### 설치 방법

1. 필요한 패키지 설치:

```bash
pip install -r requirements.txt
```

### 빌드 방법

윈도우용 실행 파일(.exe)로 빌드하려면 다음 명령을 실행하세요:

```bash
python build_windows.py
```

빌드가 완료되면 `dist/DealerDesk` 디렉토리에 DealerDesk.exe 파일이 생성됩니다.

### 트레이 애플리케이션 실행하기

#### 방법 1: 실행 파일 직접 실행

```bash
dist/DealerDesk/DealerDesk.exe
```

#### 방법 2: 런처 스크립트 사용 (권장)

_internal 디렉토리 문제가 발생한다면 런처 스크립트를 통해 실행하는 것을 권장합니다:

```bash
python run_dealerdesk.py
```

이 스크립트는 _internal 디렉토리의 존재를 확인하고, 필요하면 자동으로 생성하여 필요한 파일을 복사합니다.

### 트레이 애플리케이션 사용 방법

1. 위 방법 중 하나로 애플리케이션을 실행합니다.
2. 시스템 트레이(작업 표시줄 우측 알림 영역)에 아이콘이 나타납니다.
3. 트레이 아이콘을 클릭하면 메뉴가 표시됩니다:
   - `서버 시작`: API 서버와 웹 서버를 시작하고 웹 브라우저에서 인터페이스를 엽니다.
   - `서버 정지`: 실행 중인 서버를 중지합니다.
   - `웹 인터페이스 열기`: 웹 브라우저에서 인터페이스를 엽니다.
   - `로그`: 로그 파일 관련 옵션이 있는 하위 메뉴를 엽니다:
     - `트레이 로그 보기 (내부)`: 트레이 앱 로그를 내장 뷰어로 엽니다.
     - `런처 로그 보기 (내부)`: 런처 로그를 내장 뷰어로 엽니다.
     - `트레이 로그 파일 열기 (외부)`: 트레이 앱 로그를 시스템 기본 텍스트 편집기로 엽니다.
     - `런처 로그 파일 열기 (외부)`: 런처 로그를 시스템 기본 텍스트 편집기로 엽니다.
   - `종료`: 애플리케이션을 종료합니다.

#### 로그 뷰어 사용법

내장 로그 뷰어를 사용하면 다음과 같은 기능을 이용할 수 있습니다:
- 자동 스크롤: 로그가 업데이트되면 자동으로 최신 내용을 보여줍니다. 체크박스로 켜고 끌 수 있습니다.
- 새로고침: 수동으로 로그 내용을 업데이트합니다.
- 로그 지우기: 뷰어에서 로그 내용을 지웁니다(실제 로그 파일은 변경되지 않습니다).

### 직접 실행하기

빌드된 실행 파일 없이 직접 트레이 애플리케이션을 실행하려면:

```bash
python tray_app.py
```

### 기존 실행 방법

기존 방식으로 서버를 직접 실행하려면:

```bash
python main.py
```

## _internal 디렉토리 문제 해결

빌드 후 "_internal 디렉토리가 누락되었습니다" 오류가 발생하는 경우 다음 방법으로 해결할 수 있습니다:

1. **런처 스크립트 사용**: `python run_dealerdesk.py` 명령으로 실행하면 자동으로 필요한 _internal 디렉토리를 생성하고 파일을 복사합니다.

2. **수동으로 디렉토리 생성**: 다음 단계로 수동 설정할 수 있습니다:
   ```
   mkdir -p dist/DealerDesk/_internal
   cp main.py web_server.py database.py schemas.py models.py auth_manager.py central_socket.py app_icon.ico dist/DealerDesk/_internal/
   cp -r app databases Controllers dist/DealerDesk/_internal/
   ```

3. **환경 변수 설정**: `INTERNAL_DIR` 환경 변수를 설정하여 _internal 디렉토리 위치를 지정할 수 있습니다:
   ```
   set INTERNAL_DIR=C:\path\to\your\_internal
   dist\DealerDesk\DealerDesk.exe
   ```

## 서버 정보

- API 서버는 401번 포트에서 실행됩니다.
- 웹 서버는 3000번 포트에서 실행됩니다.

## 개발 안내

### API 서버

API 서버는 FastAPI를 기반으로 개발되었으며, 다음과 같은 기능을 제공합니다:

- 로그인 및 인증
- 매장 선택
- 소켓 연결 관리
- 각종 컨트롤러를 통한 데이터 관리

### 웹 서버

웹 인터페이스는 3000번 포트에서 실행됩니다. 애플리케이션 시작 시 자동으로 웹 브라우저에서 열립니다.

## 문제 해결

- **서버가 시작되지 않는 경우**: `dealer_desk_tray.log` 파일을 확인하여 오류 메시지를 확인하세요.
- **포트 충돌**: 401번 또는 3000번 포트가 이미 사용 중인 경우 서버가 시작되지 않을 수 있습니다. 다른 프로그램을 종료하거나 포트 설정을 변경하세요.
- **트레이 아이콘이 보이지 않는 경우**: 작업 표시줄의 숨겨진 아이콘을 확인하거나, 애플리케이션을 재시작하세요.
- **_internal 디렉토리 문제**: 위의 "_internal 디렉토리 문제 해결" 섹션을 참조하세요.

## 로그 확인

애플리케이션 로그는 다음 위치에서 확인할 수 있습니다:
- 트레이 앱 로그: `dealer_desk_tray.log`
- 런처 로그: `dealerdesk_launcher.log`

로그는 트레이 앱 메뉴의 `로그` 하위 메뉴를 통해 내장 뷰어나 외부 편집기로 쉽게 열어볼 수 있습니다.

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