import asyncio
from datetime import time
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
from database import get_db, get_db_direct

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

#################################################
# WebSocket 관련 함수 및 엔드포인트
#################################################

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
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 엔드포인트 - 디바이스 연결 및 인증 처리
    """
    await websocket.accept()
    
    print("Device connected successfully")
    
    # 디바이스 데이터 수신
    device_datas_message = await websocket.receive_text()
    device_data_json = json.loads(device_datas_message)
    
    # 직접 세션 가져오기
    db = get_db_direct()
    
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
                
            await send_socket_message(websocket, 201, {"event" : "Wait Auth Device"})
            await asyncio.sleep(1)
        
        await send_socket_message(websocket, 200, {"event": "connected"})
        device_socket_data.append(DeviceSocketData(device_uid=device_data.device_uid, device_socket=websocket))
        # 2초간 대기
        await asyncio.sleep(2)
        await connect_table_device_socket_event(device_data.device_uid)
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
    finally:
        db.close()

async def connect_table_device_socket_event(device_uid: str):
    """
    디바이스를 테이블에 연결하는 이벤트 처리
    """
    try:
        # 직접 세션 가져오기
        db = get_db_direct()
        try:
            # 인증된 디바이스 찾기
            auth_device = db.query(models.AuthDeviceData).filter(
                models.AuthDeviceData.device_uid == device_uid
            ).first()
            
            if not auth_device or not auth_device.connect_table_id:
                return
                
            # 테이블 찾기
            table = db.query(models.TableData).filter(
                models.TableData.id == auth_device.connect_table_id
            ).first()
            
            if not table:
                return
                
            # 디바이스 소켓 찾기
            device_socket = next(
                (socket for socket in device_socket_data if socket.device_uid == device_uid),
                None
            )
            
            if device_socket:
                device_socket.table_title = table.table_title
                await send_socket_message(
                    device_socket.device_socket,
                    200,
                    {
                        "event": "connect_table",
                        "table_title": table.table_title
                    }
                )
        finally:
            db.close()
    except Exception as e:
        print(f"Error in connect_table_device_socket_event: {e}")

async def disconnect_table_device_socket_event(device_uid: str):
    """
    디바이스를 테이블에서 연결 해제하는 이벤트 처리
    """
    try:
        # 디바이스 소켓 찾기
        device_socket = next(
            (socket for socket in device_socket_data if socket.device_uid == device_uid),
            None
        )
        
        if device_socket:
            device_socket.table_title = None
            await send_socket_message(
                device_socket.device_socket,
                200,
                {
                    "event": "disconnect_table"
                }
            )
    except Exception as e:
        print(f"Error in disconnect_table_device_socket_event: {e}")

async def send_delete_device_socket_event(device_uid: str):
    """디바이스 삭제 시 소켓 연결 해제"""
    for device in device_socket_data:
        if device.device_uid == device_uid:
            await device.device_socket.close()
            del device_socket_data[device_socket_data.index(device)]
            break

async def send_connect_game_socket_event(device_uid: str, table_id: str):
    """
    디바이스에 게임 연결 이벤트를 전송합니다.
    """
    try:
        # 직접 세션 가져오기
        db = get_db_direct()
        try:
            # 테이블 데이터 조회
            table_data = db.query(models.TableData).filter(models.TableData.id == table_id).first()
            
            if not table_data:
                print(f"테이블을 찾을 수 없음: {table_id}")
                return
                
            game_id = table_data.game_id
            
            # 게임 데이터가 없는 경우 연결 해제 메시지 전송
            if not game_id:
                # 디바이스 소켓 찾기
                for device in device_socket_data:
                    if device.device_uid == device_uid:
                        await send_socket_message(
                            device.device_socket,
                            200,
                            {
                                "event": "game_disconnect"
                            }
                        )
                        break
                return
                
            # 게임 데이터 조회
            game_data = db.query(models.GameData).filter(models.GameData.id == game_id).first()
            
            if not game_data:
                print(f"게임을 찾을 수 없음: {game_id}")
                return
                
            # 디바이스 소켓 찾기
            for device in device_socket_data:
                if device.device_uid == device_uid:
                    try:
                        await send_socket_message(
                            device.device_socket,
                            200,
                            {
                                "event": "game_connect",
                                "game_data": game_data.to_json()
                            }
                        )
                    except Exception as e:
                        print(f"디바이스 {device_uid}에 메시지 전송 중 오류: {e}")
                    break
        finally:
            db.close()
    except Exception as e:
        print(f"게임 연결 이벤트 처리 중 오류: {e}")

#################################################
# REST API 엔드포인트
#################################################

@router.get("/get-waiting-device")
async def get_waiting_device():
    # 직접 세션 가져오기
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
        
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "error": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.get("/get-auth-device")
async def get_auth_device():
    # 직접 세션 가져오기
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
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
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
    finally:
        db.close()

@router.post("/device-name-change")
async def device_name_change(device_data: DeviceNameChangeData):
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        # 디바이스 이름 길이 검증
        if len(device_data.device_name) > MAX_DEVICE_NAME_LENGTH:
            return JSONResponse(
                content={"response": 400, "message": f"Device name too long. Maximum length is {MAX_DEVICE_NAME_LENGTH} characters."},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 인증된 디바이스 찾기
        auth_device = db.query(models.AuthDeviceData).filter(
            models.AuthDeviceData.device_uid == device_data.device_uid
        ).first()
        
        if not auth_device:
            return JSONResponse(
                content={"response": 404, "message": "Device not found"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 디바이스 이름 변경
        auth_device.device_name = device_data.device_name
        db.commit()
        
        return JSONResponse(
            content={"response": 200, "message": "Device name changed successfully"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.delete("/device-delete/{device_uid}")
async def device_delete(device_uid: str):
    """디바이스 삭제"""
    # 직접 세션 가져오기
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
        
        await send_delete_device_socket_event(device_uid)
        
        return JSONResponse(
            content={"response": 200, "message": "Device deleted successfully"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.post("/connect-table")
async def connect_table(device_data: schemas.ConnectTableData):
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        # 인증된 디바이스 찾기
        auth_device = db.query(models.AuthDeviceData).filter(
            models.AuthDeviceData.device_uid == device_data.device_uid
        ).first()
        
        if not auth_device:
            return JSONResponse(
                content={"response": 404, "message": "Device not found"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 테이블 찾기
        table = db.query(models.TableData).filter(
            models.TableData.id == device_data.table_id
        ).first()
        
        if not table:
            return JSONResponse(
                content={"response": 404, "message": "Table not found"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 디바이스를 테이블에 연결
        auth_device.connect_table_id = table.id
        db.commit()
        
        # 소켓 연결 업데이트
        await connect_table_device_socket_event(device_data.device_uid)
        
        return JSONResponse(
            content={"response": 200, "message": "Device connected to table successfully"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.post("/disconnect-table")
async def disconnect_table(device_data: schemas.DisconnectTableData):
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        # 인증된 디바이스 찾기
        auth_device = db.query(models.AuthDeviceData).filter(
            models.AuthDeviceData.device_uid == device_data.device_uid
        ).first()
        
        if not auth_device:
            return JSONResponse(
                content={"response": 404, "message": "Device not found"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 디바이스 연결 해제
        auth_device.connect_table_id = None
        db.commit()
        
        # 소켓 연결 업데이트
        await disconnect_table_device_socket_event(device_data.device_uid)
        
        return JSONResponse(
            content={"response": 200, "message": "Device disconnected from table successfully"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.delete("/delete-auth-device/{device_id}")
async def delete_auth_device(device_id: int):
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        # 인증된 디바이스 찾기
        auth_device = db.query(models.AuthDeviceData).filter(
            models.AuthDeviceData.id == device_id
        ).first()
        
        if not auth_device:
            return JSONResponse(
                content={"response": 404, "message": "Device not found"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 디바이스 삭제
        db.delete(auth_device)
        db.commit()
        
        return JSONResponse(
            content={"response": 200, "message": "Device deleted successfully"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()
