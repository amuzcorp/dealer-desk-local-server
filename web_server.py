from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
import signal
import sys

app = FastAPI(
    title="Dealer Desk Web Server",
    description="딜러 데스크 웹 서버",
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

# 정적 파일 서빙 설정
app.mount("/assets", StaticFiles(directory="app/web/assets"), name="assets")
app.mount("/canvaskit", StaticFiles(directory="app/web/canvaskit"), name="canvaskit")

# 웹소켓 연결 관리
class ConnectionManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()
        self.shutdown_event = asyncio.Event()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print("브라우저가 연결되었습니다.")

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print("브라우저 연결이 종료되었습니다.")
        if not self.active_connections:
            print("모든 브라우저가 종료되었습니다. 서버를 종료합니다.")
            self.shutdown_event.set()
            # 프로세스 종료
            os.kill(os.getpid(), signal.SIGTERM)

manager = ConnectionManager()

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
    # await manager.connect(websocket)
    # try:
    #     while True:
    #         # 클라이언트로부터의 메시지 대기
    #         await websocket.receive_text()
    # except Exception as e:
    #     await manager.disconnect(websocket)

@app.get("/")
async def root():
    return FileResponse('app/web/index.html')

@app.get("/index.html")
async def serve_index():
    return FileResponse('app/web/index.html')

@app.get("/{full_path:path}")
async def serve_web(full_path: str):
    # 정적 파일이 실제로 존재하는 경우 해당 파일 제공
    static_file = f"app/web/{full_path}"
    if os.path.isfile(static_file):
        return FileResponse(static_file)
    
    # 그 외의 모든 경로는 index.html로 리다이렉트
    return FileResponse('app/web/index.html') 