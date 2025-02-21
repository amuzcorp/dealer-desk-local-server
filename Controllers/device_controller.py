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
from dataclasses import dataclass
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models
import schemas
from database import get_db

@dataclass
class DeviceNameChangeData:
    device_uid: str
    device_name: str
    
    def from_json(self, json_data: dict):
        return DeviceNameChangeData(
            device_uid=json_data["device_uid"],
            device_name=json_data["device_name"]
        )
    
@dataclass
class DeviceSocketData:
    device_uid: str
    device_socket: WebSocket
    table_title: str = None
    
device_socket_data : List[DeviceSocketData] = [];

router = APIRouter(
    prefix="/devices",
    tags=["devices"]
)

MAX_DEVICE_NAME_LENGTH = 20

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

async def update_auth_device_status(device_uid: str, is_connected: bool, db: Session):
    try:
        auth_device = db.query(models.AuthDeviceData).filter(
            models.AuthDeviceData.device_uid == device_uid
        ).first()
        if auth_device:
            auth_device.is_connected = is_connected
            db.commit()
    except Exception as e:
        print(f"Error updating device status: {e}")

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
        device_socket_data.append(DeviceSocketData(device_uid=device_data.device_uid, device_socket=websocket))
        # 2초간 대기
        await asyncio.sleep(2)
        await connect_table_device_socket_event(device_data.device_uid, db)
        if(auth_device):
            await update_auth_device_status(auth_device.device_uid, True, db)
        
        # 메시지 수신 대기
        while True:
            data = await websocket.receive_text()
            print(f"Received message: {data}")
            
    except Exception as e:
        print(e)
        auth_device = db.query(models.AuthDeviceData).filter(
                models.AuthDeviceData.device_uid == device_data.device_uid
            ).first()
        
        # 디바이스 소켓 찾기
        device_socket = next(
            (socket for socket in device_socket_data if socket.device_uid == device_data.device_uid),
            None
        )
        
        if device_socket:
            del device_socket_data[device_socket_data.index(device_socket)]
        

        if auth_device:
            await update_auth_device_status(auth_device.device_uid, False, db)

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

@router.get("/get-auth-device")
async def get_auth_device(db: Session = Depends(get_db)):
    auth_device = db.query(models.AuthDeviceData).all()
    auth_device_list = []
    for device in auth_device:
        device_json = device.to_json()
        device_json["created_at"] = device_json["created_at"].isoformat()
        auth_device_list.append(device_json)
        
    return JSONResponse(
        content={"response": 200, "data": auth_device_list},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

@router.post("/auth-device")
async def auth_device(device_data: schemas.RequestDeviceData, db: Session = Depends(get_db)):
    # 요청된 디바이스 찾기
    request_device = db.query(models.RequestDeviceData).filter(
        models.RequestDeviceData.device_uid == device_data.device_uid,
        models.RequestDeviceData.connect_status == "waiting"
    ).first()
    
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

@router.get("/get-waiting-device")
async def get_waiting_device(db: Session = Depends(get_db)):
    waiting_device = db.query(models.RequestDeviceData).filter(
        models.RequestDeviceData.connect_status == "waiting"
    ).all()
    
    if waiting_device:
        device_list = []
        for device in waiting_device:
            device_json = device.to_json()
            device_json["request_time"] = device_json["request_time"].isoformat()
            device_json["update_time"] = device_json["update_time"].isoformat()
            device_list.append(device_json)
            
        device_list.sort(key=lambda x: x["request_time"])
            
        return JSONResponse(
            content={"response": 200, "data": device_list},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )    
 
@router.post("/device-name-change")
async def device_name_change(device_data: DeviceNameChangeData, db: Session = Depends(get_db)):
    auth_device = db.query(models.AuthDeviceData).filter(
        models.AuthDeviceData.device_uid == device_data.device_uid
    ).first()
    
    if not auth_device: 
        return JSONResponse(
            content={"response": 404, "message": "Device not found"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    if len(device_data.device_name) > MAX_DEVICE_NAME_LENGTH:
        return JSONResponse(
            content={"response": 400, "message": "Device name is too long"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    auth_device.device_name = device_data.device_name
    db.commit()
    
    return JSONResponse(
        content={"response": 200, "message": "Device name changed successfully"},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

@router.delete("/device-delete/{device_uid}")
async def device_delete(device_uid: str, db: Session = Depends(get_db)):
    auth_device = db.query(models.AuthDeviceData).filter(
        models.AuthDeviceData.device_uid == device_uid
    ).first()
    
    if not auth_device:
        return JSONResponse(
            content={"response": 404, "message": "Device not found"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    db.delete(auth_device)
    db.commit()
    
    return JSONResponse(
        content={"response": 200, "message": "Device deleted successfully"},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

@router.post("/connect-table-device")
async def connect_table_device(device_uid: str, table_id: str = None, db: Session = Depends(get_db)):
    device_data = db.query(models.AuthDeviceData).filter(
        models.AuthDeviceData.device_uid == device_uid
    ).first()
    
    if not device_data:
        return JSONResponse(
            content={"response": 404, "message": "Device not found"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    device_data.connect_table_id = table_id
    print(f"디바이스 연결 테이블 ID: {device_data.connect_table_id}")
    db.commit()
    
    await connect_table_device_socket_event(device_uid, db)
    
    return JSONResponse(
        content={"response": 200, "message": "Device connected to table successfully"},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    
    
async def connect_table_device_socket_event(device_uid: str, db: Session = Depends(get_db)):
    device_data = db.query(models.AuthDeviceData).filter(
        models.AuthDeviceData.device_uid == device_uid
    ).first()
    device_uid = device_data.device_uid
    print(device_data.connect_table_id)
    
    if(device_data.connect_table_id == None):
        # 테이블 연결 해제
        # uid에 해당하는 소켓 찾기
        # 디바이스 소켓 찾기
        device_socket = next(
            (socket for socket in device_socket_data if socket.device_uid == device_uid),
            None
        )
        device_socket.table_title = None

        # 소켓이 존재하면 연결 해제 메시지 전송
        if device_socket:
            disconnect_message = {
                "response": 200,
                "data": "table_disconnect"
            }
            await device_socket.device_socket.send_text(json.dumps(disconnect_message))
        
        return
    
    # 테이블 찾기
    # 테이블 데이터 조회 
    table_data = db.query(models.TableData).filter(
        models.TableData.id == device_data.connect_table_id
    ).first()
    
    # 디버깅을 위한 로그 출력
    print(f"테이블 데이터: {table_data}")
    print(f"연결할 테이블 ID: {device_data.connect_table_id}")
    print(f"테이블 데이터 타입: {type(table_data)}")
    print(f"테이블 데이터 타입: {table_data.table_title}")
    
    if table_data is None:
        print("테이블 데이터가 없습니다.")
        disconnect_message = {
                "response": 200,
                "data": "table_disconnect"
            }
        await device_socket.device_socket.send_text(json.dumps(disconnect_message))
        return
    
    # 테이블 타이틀 받기
    table_title = table_data.table_title
    
    for device in device_socket_data:
        if device.device_uid == device_uid:
            await device.device_socket.send_text(json.dumps({
                "response": 200,
                "data" : "connect_table",
                "table_title" : table_title
            }))
            break
