import asyncio
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from central_socket import ReverbTestController
import models, schemas, database
import dataclasses
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

socket_controller: ReverbTestController = ReverbTestController()

@app.get("/")
async def root():
    return {"message": "FastAPI 서버가 실행중입니다!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@dataclasses.dataclass
class LoginData:
    user_id: str
    user_pwd: str

@app.post("/login")
async def login(login_data: LoginData):
    global socket_controller
    try:
        success = await socket_controller.main(user_id=login_data.user_id, user_pwd=login_data.user_pwd)
        if success:
            print("소켓 컨트롤러가 성공적으로 초기화되었습니다")
            return {"status": "success", "store_name": socket_controller.store_name}
        else:
            print("소켓 컨트롤러 초기화 실패")
            return {"status": "failed", "message": "소켓 연결 또는 인증 실패"}
    except Exception as e:
        error_message = str(e)
        print(f"소켓 컨트롤러 초기화 중 오류 발생: {error_message}")
        if "인증 실패" in error_message:
            return {"status": "failed", "message": error_message, "code": "AUTH_ERROR"}
        socket_controller = None
        return {"status": "error", "message": error_message}

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

if __name__ == "__main__":
    import uvicorn
    
    # # FastAPI 이벤트에서 소켓 초기화가 처리되므로 여기서는 필요 없음
    # # 하지만 FastAPI 이벤트 전에 실행하고 싶다면 아래와 같이 실행할 수 있음
    # asyncio.run(startup_event())
    
    print("소켓 컨트롤러가 null인가? : ", socket_controller is None)
    # FastAPI 서버 실행
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
