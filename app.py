import asyncio
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from central_socket import ReverbTestController
import models, schemas, database
from Controllers import game_controller, purchase_controller, table_controller, device_controller, preset_controller, user_controller

# 데이터베이스 테이블 생성
models.Base.metadata.create_all(bind=database.engine)

# 테스트 구매 데이터 생성
# database.create_test_purchase_data()

app = FastAPI(
    title="FastAPI Project",
    description="FastAPI 프로젝트 기본 설정",
    version="1.0.0"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 구체적인 도메인을 지정해야 합니다
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(table_controller.router)
app.include_router(device_controller.router)
app.include_router(preset_controller.router)
app.include_router(game_controller.router)
app.include_router(purchase_controller.router)
app.include_router(user_controller.router)

socket_controller = None;

@app.get("/")
async def root():
    return {"message": "FastAPI 서버가 실행중입니다!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    import threading
    
    # 웹소켓 서버를 백그라운드 스레드에서 비동기로 실행
    def run_socket_server():
        global socket_controller
        socket_controller = ReverbTestController()
    
    # 백그라운드 스레드 시작
    socket_thread = threading.Thread(target=run_socket_server, daemon=True)
    socket_thread.start()
    
    # database.create_test_user_data()
    # FastAPI 서버 실행
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
