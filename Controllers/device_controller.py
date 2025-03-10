import asyncio
from fastapi import APIRouter, WebSocket
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import JSONResponse
from dataclasses import dataclass
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models
import schemas
from database import get_db_direct
from .device_socket_manager import socket_manager

@dataclass
class DeviceNameChangeData:
    device_uid: str
    device_name: str
    
    def from_json(self, json_data: dict):
        return DeviceNameChangeData(
            device_uid=json_data["device_uid"],
            device_name=json_data["device_name"]
        )

router = APIRouter(
    prefix="/devices",
    tags=["devices"]
)

MAX_DEVICE_NAME_LENGTH = 20

#################################################
# WebSocket 엔드포인트
#################################################

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 엔드포인트 - 디바이스 연결 및 인증 처리
    """
    device_uid = None
    db = None
    connection_accepted = False
    
    try:
        # 웹소켓 연결 수락
        await websocket.accept()
        connection_accepted = True
        
        db = get_db_direct()
        
        # 디바이스 데이터 수신
        try:
            device_datas_message = await websocket.receive_text()
            device_data_json = json.loads(device_datas_message)
            
            # 디바이스 데이터 모델 생성
            device_data = models.RequestDeviceData(
                device_name=device_data_json["device_name"],
                device_uid=device_data_json["device_uid"],
            )
            device_uid = device_data.device_uid
            
        except json.JSONDecodeError:
            await websocket.send_text(
                json.dumps({
                    "response": 400,
                    "data": {"event": "Invalid device data format"}
                })
            )
            return
        except KeyError:
            await websocket.send_text(
                json.dumps({
                    "response": 400,
                    "data": {"event": "Missing required device data"}
                })
            )
            return
        
        # 소켓 매니저에 연결 등록
        await socket_manager.connect(device_uid, websocket)
        
        # 인증된 디바이스 확인
        auth_device = db.query(models.AuthDeviceData).filter(
            models.AuthDeviceData.device_uid == device_uid
        ).first()
        
        # 요청 db에 이미 있는 디바이스인지 확인
        request_device = db.query(models.RequestDeviceData).filter(
            models.RequestDeviceData.device_uid == device_uid
        ).first()
        
        # 미인증 디바이스 처리
        if not auth_device:
            if not request_device:
                db.add(device_data)
                db.commit()
                db.refresh(device_data)
        
        # 인증 대기
        auth_wait_count = 0
        while not auth_device and auth_wait_count < 60:  # 최대 60초 대기
            auth_device = db.query(models.AuthDeviceData).filter(
                models.AuthDeviceData.device_uid == device_uid
            ).first()
            
            if auth_device:
                break
                
            await socket_manager.send_message(device_uid, 201, {"event": "Wait Auth Device"})
            await asyncio.sleep(1)
            auth_wait_count += 1
            
        if not auth_device:
            await socket_manager.send_message(device_uid, 408, {"event": "Auth timeout"})
            return
        
        await socket_manager.send_message(device_uid, 200, {"event": "connected"})
        
        # 테이블 연결 처리
        if auth_device.connect_table_id:
            await socket_manager.handle_table_connection(device_uid, auth_device.connect_table_id)
            await socket_manager.handle_game_connection(device_uid, auth_device.connect_table_id)
            
        await socket_manager.update_device_status(device_uid, True, db)
        
        # 메시지 수신 대기
        while True:
            try:
                data = await websocket.receive_text()
                print(f"Received message: {data}")
            except Exception as e:
                print(f"Error receiving message: {e}")
                break
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        try:
            if device_uid and db:
                await socket_manager.update_device_status(device_uid, False, db)
                await socket_manager.disconnect(device_uid)
            if db:
                db.close()
            if connection_accepted and not websocket.client_state.DISCONNECTED:
                await websocket.close()
        except Exception as e:
            print(f"Error in cleanup: {e}")

#################################################
# REST API 엔드포인트
#################################################

@router.get("/get-waiting-device")
async def get_waiting_device():
    db = get_db_direct()
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
    finally:
        db.close()

@router.get("/get-auth-device")
async def get_auth_device():
    db = get_db_direct()
    try:
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
    finally:
        db.close()

@router.post("/auth-device")
async def auth_device(device_data: schemas.RequestDeviceData):
    db = get_db_direct()
    try:
        request_device = db.query(models.RequestDeviceData).filter(
            models.RequestDeviceData.device_uid == device_data.device_uid,
            models.RequestDeviceData.connect_status == "waiting"
        ).first()
        
        if not request_device:
            return JSONResponse(
                content={"response": 404, "message": "Device not found"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        if device_data.connect_status == "approved":
            auth_device = models.AuthDeviceData(
                device_uid=request_device.device_uid,
                device_name=request_device.device_name,
                is_connected=True
            )
            db.add(auth_device)
            db.delete(request_device)
            db.commit()
            
            return JSONResponse(
                content={"response": 200, "message": "Device authorized successfully"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
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
    finally:
        db.close()

@router.post("/device-name-change")
async def device_name_change(device_data: DeviceNameChangeData):
    db = get_db_direct()
    try:
        if len(device_data.device_name) > MAX_DEVICE_NAME_LENGTH:
            return JSONResponse(
                content={"response": 400, "message": f"Device name too long. Maximum length is {MAX_DEVICE_NAME_LENGTH} characters."},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        auth_device = db.query(models.AuthDeviceData).filter(
            models.AuthDeviceData.device_uid == device_data.device_uid
        ).first()
        
        if not auth_device:
            return JSONResponse(
                content={"response": 404, "message": "Device not found"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        auth_device.device_name = device_data.device_name
        db.commit()
        
        return JSONResponse(
            content={"response": 200, "message": "Device name changed successfully"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.post("/connect-table")
async def connect_table(device_data: schemas.ConnectTableData):
    db = get_db_direct()
    try:
        auth_device = db.query(models.AuthDeviceData).filter(
            models.AuthDeviceData.device_uid == device_data.device_uid
        ).first()
        
        if not auth_device:
            return JSONResponse(
                content={"response": 404, "message": "Device not found"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        table = db.query(models.TableData).filter(
            models.TableData.id == device_data.table_id
        ).first()
        
        if not table:
            return JSONResponse(
                content={"response": 404, "message": "Table not found"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        auth_device.connect_table_id = table.id
        db.commit()
        
        await socket_manager.handle_table_connection(device_data.device_uid, table.id)
        
        return JSONResponse(
            content={"response": 200, "message": "Device connected to table successfully"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.post("/disconnect-table")
async def disconnect_table(device_data: schemas.DisconnectTableData):
    db = get_db_direct()
    try:
        auth_device = db.query(models.AuthDeviceData).filter(
            models.AuthDeviceData.device_uid == device_data.device_uid
        ).first()
        
        if not auth_device:
            return JSONResponse(
                content={"response": 404, "message": "Device not found"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        auth_device.connect_table_id = None
        db.commit()
        
        await socket_manager.handle_table_connection(device_data.device_uid)
        
        return JSONResponse(
            content={"response": 200, "message": "Device disconnected from table successfully"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.delete("/device-delete/{device_uid}")
async def device_delete(device_uid: str):
    db = get_db_direct()
    try:
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
        
        await socket_manager.disconnect(device_uid)
        
        return JSONResponse(
            content={"response": 200, "message": "Device deleted successfully"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()
