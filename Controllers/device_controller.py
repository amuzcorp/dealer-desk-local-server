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

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket 엔드포인트 - 디바이스 연결 및 인증 처리
    """
    await websocket.accept()
    
    # 디바이스 데이터 수신
    device_datas_message = await websocket.receive_text()
    device_data_json = json.loads(device_datas_message)
    
    # 디바이스 데이터 모델 생성
    device_data = models.RequestDeviceData(
        name=device_data_json["name"],
        device_uid=device_data_json["device_uid"],
        connect_status=device_data_json["connect_status"]
    )
    
    # 인증된 디바이스 확인
    auth_device = db.query(models.AuthDeviceData).filter(
        models.AuthDeviceData.device_uid == device_data.device_uid
    ).first()
    
    # 미인증 디바이스 처리
    if not auth_device:
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
            
        await websocket.send_text(
            JSONResponse(
                content={"response": 201, "data": "Wait Auth Device"},
                headers={"Content-Type": "application/json; charset=utf-8"},
                media_type="application/json"
            )
        )
        await asyncio.sleep(1)
    
    # 메시지 수신 대기
    while True:
        data = await websocket.receive_text()
        print(f"Received message: {data}")

@router.get("/get-waiting-device")
async def get_waiting_device(db: Session = Depends(get_db)):
    waiting_device = db.query(models.RequestDeviceData).filter(
        models.RequestDeviceData.connect_status == "waiting"
    ).all()
    return JSONResponse(
        content={"response": 200, "data": waiting_device},
        headers={"Content-Type": "application/json; charset=utf-8"},
        media_type="application/json"
    )
    
    
@router.post("/auth-device")
async def auth_device(device_data: schemas.RequestDeviceData, db: Session = Depends(get_db)):
    # 요청된 디바이스 찾기
    request_device = get_waiting_device(db);
    
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
            device_name=request_device.name,
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


async def get_waiting_device(db: Session = Depends(get_db)):
    waiting_device = db.query(models.RequestDeviceData).filter(
        models.RequestDeviceData.connect_status == "waiting"
    ).all()
    return waiting_device

