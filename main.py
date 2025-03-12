import asyncio
import webbrowser
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from central_socket import ReverbTestController
import models, schemas, database
import dataclasses
import socket
from Controllers import game_controller, purchase_controller, qr_controller, table_controller, device_controller, preset_controller, user_controller, awarding_controller, point_controller
import sys
import signal

app = FastAPI(
    title="Dealer Desk API Server",
    description="딜러 데스크 API 서버",
    version="1.0.0"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 매장 ID 미들웨어 추가
app.add_middleware(database.StoreIDMiddleware)

# 라우터 등록
app.include_router(table_controller.router)
app.include_router(device_controller.router)
app.include_router(preset_controller.router)
app.include_router(game_controller.router)
app.include_router(purchase_controller.router)
app.include_router(user_controller.router)
app.include_router(awarding_controller.router)
app.include_router(point_controller.router)
app.include_router(qr_controller.router)
socket_controller: ReverbTestController = ReverbTestController()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 서버의 ip 전달
@app.get("/get-ip-address")
async def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return {"ip_address": s.getsockname()[0]}

@dataclasses.dataclass
class LoginData:
    user_id: str
    user_pwd: str

@dataclasses.dataclass
class StoreSelectData:
    store_id: int

@app.post("/login")
async def login(login_data: LoginData):
    global socket_controller
    try:
        success = await socket_controller.main(user_id=login_data.user_id, user_pwd=login_data.user_pwd)
        if success:
            print("로그인 성공")
            
            # 로그인 성공 시 각 매장별 데이터베이스 초기화
            store_ids = []
            for store in socket_controller.stores:
                store_id = store['id']
                store_ids.append(store_id)
                db_init_success = database.initialize_store_database(store_id)
                if db_init_success:
                    print(f"매장 {store['name']}의 데이터베이스가 초기화되었습니다")
                else:
                    print(f"매장 {store['name']}의 데이터베이스 초기화 실패")
                    return {"status": "error", "message": f"매장 {store['name']}의 데이터베이스 초기화 실패"}
            
            # 오프라인 모드 여부와 매장 정보 반환
            return {
                "status": "success",
                "is_offline_mode": socket_controller.is_offline_mode,
                "stores": socket_controller.stores,
                "store_ids": store_ids
            }
        else:
            print("로그인 실패")
            return {"status": "failed", "message": "로그인 실패"}
    except Exception as e:
        error_message = str(e)
        print(f"로그인 중 오류 발생: {error_message}")
        if "인증 실패" in error_message:
            return {"status": "failed", "message": error_message, "code": "AUTH_ERROR"}
        socket_controller = None
        return {"status": "error", "message": error_message}

@app.post("/select-store")
async def select_store(store_data: StoreSelectData):
    """매장 선택 및 소켓 연결 엔드포인트"""
    global socket_controller
    try:
        if socket_controller is None:
            return {"status": "error", "message": "로그인이 필요합니다"}
            
        # 현재 매장 ID 설정
        database.set_current_store_id(store_data.store_id)
        
        success = await socket_controller.select_store(store_data.store_id)
        if success:
            selected_store = socket_controller.selected_store
            return {
                "status": "success",
                "store_name": selected_store['name'],
                "tenant_id": selected_store['tenant_id'],
                "is_offline_mode": socket_controller.is_offline_mode,
                "is_connected": socket_controller.is_connected and socket_controller.is_subscribed
            }
        else:
            return {"status": "failed", "message": "매장 선택 실패"}
    except Exception as e:
        error_message = str(e)
        print(f"매장 선택 중 오류 발생: {error_message}")
        return {"status": "error", "message": error_message}

@app.post("/re-connect-central-socket")
async def re_connect_central_socket():
    global socket_controller
    socket_controller.handle_message()
    return {"status": "success", "message": "소켓 연결 재시도"}

@app.post("/logout")
async def logout():
    """로그아웃 처리를 수행하는 엔드포인트"""
    global socket_controller
    try:
        if socket_controller is None:
            return {"status": "success", "message": "이미 로그아웃된 상태입니다"}
            
        success = await socket_controller.logout()
        if success:
            print("소켓 컨트롤러가 성공적으로 종료되었습니다")
            return {"status": "success", "message": "로그아웃 성공"}
        else:
            print("소켓 컨트롤러 종료 실패")
            return {"status": "failed", "message": "로그아웃 처리 중 오류가 발생했습니다"}
    except Exception as e:
        error_message = str(e)
        print(f"로그아웃 처리 중 오류 발생: {error_message}")
        return {"status": "error", "message": error_message}

class UvicornServer:
    def __init__(self, app, host="0.0.0.0", port=401):
        self.app = app
        self.host = host
        self.port = port
        self.config = uvicorn.Config(app, host=host, port=port, reload=True)
        self.server = uvicorn.Server(config=self.config)
    
    async def run(self):
        await self.server.serve()

async def run_api_server():
    api_server = UvicornServer(app="/Users/gimjuyeong/Projects/dealer-desk-local-server/main:app", host="0.0.0.0", port=401)
    await api_server.run()

async def run_web_server():
    web_server = UvicornServer(app="web_server:app", host="0.0.0.0", port=3000)
    await web_server.run()

async def run_all():
    # 시그널 핸들러 설정
    def signal_handler(signum, frame):
        print("\n서버를 종료합니다...")
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    
    print("웹 서버가 3000번 포트에서 실행됩니다.")
    print("API 서버가 401번 포트에서 실행됩니다.")
    
    # 웹페이지 띄워주기
    webbrowser.open("http://localhost:3000")
    
    await asyncio.gather(
        run_api_server(),
        run_web_server()
    )

if __name__ == "__main__":
    asyncio.run(run_all())
