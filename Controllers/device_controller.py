import asyncio
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/devices",
    tags=["devices"]
)

async def send_socket_message(websocket: WebSocket, response_code: int, data: any):
    """
    WebSocket 메시지 전송을 위한 헬퍼 함수
    """
    await websocket.send_text(
        json.dumps({
            "response": response_code,
            "data": data
        })
    )

@router.websocket("/ws") 
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket 엔드포인트 - 디바이스 연결 및 인증 처리
    """
    await websocket.accept()
    
    print("Device connected successfully")
    
    # 디바이스 데이터 수신
    device_datas_message = await websocket.receive_text()
    device_data_json = json.loads(device_datas_message)
    
    try:
        # 디바이스 데이터 모델 생성
        device_data = models.RequestDeviceData(
            device_name=device_data_json["device_name"],
            device_uid=device_data_json["device_uid"],
        )
        
        # 인증된 디바이스 확인
        auth_device = db.query(models.AuthDeviceData).filter(
            models.AuthDeviceData.device_uid == device_data.device_uid
        ).first()
        
        # 요청 db에 이미 있는 디바이스인지 확인
        request_device = db.query(models.RequestDeviceData).filter(
            models.RequestDeviceData.device_uid == device_data.device_uid
        ).first()
        
        # 미인증 디바이스 처리
        if not auth_device:
            # 요청 db에 이미 있는 디바이스인지 확인 db에 없으면 추가
            if not request_device:
                db.add(device_data)
                db.commit()
                db.refresh(device_data)

        # 인증 대기
        while not auth_device:
            auth_device = db.query(models.AuthDeviceData).filter(
                models.AuthDeviceData.device_uid == device_data.device_uid
            ).first()
            
            if auth_device:
                break
                
            await send_socket_message(websocket, 201, "Wait Auth Device")
            await asyncio.sleep(1)
        
        await send_socket_message(websocket, 200, "connected")
        
        # 메시지 수신 대기
        while True:
            data = await websocket.receive_text()
            print(f"Received message: {data}")
    except Exception as e:
        print(e)

@router.get("/get-waiting-device")
async def get_waiting_device(db: Session = Depends(get_db)):
    try:
        waiting_device = db.query(models.RequestDeviceData).filter(
            models.RequestDeviceData.connect_status == "waiting"
        ).all()
        
        if not waiting_device:
            return JSONResponse(
                content={"response": 201, "message": "대기중인 디바이스가 없습니다."},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        device_list = []
        for device in waiting_device:
            device_json = device.to_json()
            device_json["request_time"] = device_json["request_time"].isoformat()
            device_json["update_time"] = device_json["update_time"].isoformat()
            device_list.append(device_json)
            
        return JSONResponse(
            content={"response": 200, "data": device_list},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "error": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
@router.post("/auth-device")
async def auth_device(device_data: schemas.RequestDeviceData, db: Session = Depends(get_db)):
    # 요청된 디바이스 찾기
    request_device = await get_waiting_device(device_data.device_uid, db);
    
    if not request_device:
        return JSONResponse(
            content={"response": 404, "message": "Device not found"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    # 승인 요청인 경우
    if device_data.connect_status == "approved":
        # 인증된 디바이스로 등록
        auth_device = models.AuthDeviceData(
            device_uid=request_device.device_uid,
            device_name=request_device.device_name,
            is_connected=True
        )
        db.add(auth_device)
        
        # 요청 디바이스 삭제
        db.delete(request_device)
        db.commit()
        
        return JSONResponse(
            content={"response": 200, "message": "Device authorized successfully"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        
    # 거절 요청인 경우 
    elif device_data.connect_status == "rejected":
        request_device.connect_status = "rejected"
        db.commit()
        
        return JSONResponse(
            content={"response": 200, "message": "Device rejected"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        
    return JSONResponse(
        content={"response": 400, "message": "Invalid status"},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

async def auth_device(device_data: models.RequestDeviceData, db: Session = Depends(get_db)):
    """
    디바이스 인증 처리 함수
    """
    auth_device = db.query(models.AuthDeviceData).filter(
        models.AuthDeviceData.device_uid == device_data.device_uid
    ).first()
    
    if not auth_device:
        db.add(device_data)
        db.commit()
        db.refresh(device_data)


async def get_waiting_device(device_uid: str, db: Session = Depends(get_db)):
    waiting_device = db.query(models.RequestDeviceData).filter(
        models.RequestDeviceData.device_uid == device_uid
    ).first()
    return waiting_device
