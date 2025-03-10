import asyncio
from fastapi import WebSocket
from typing import Dict, Optional
from dataclasses import dataclass
import json
from sqlalchemy.orm import Session
import models
from database import get_db_direct

@dataclass
class DeviceSocketConnection:
    device_uid: str
    websocket: WebSocket
    table_title: Optional[str] = None
    
class DeviceSocketManager:
    def __init__(self):
        self._connections: Dict[str, DeviceSocketConnection] = {}
        self._lock = asyncio.Lock()
        
    async def connect(self, device_uid: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[device_uid] = DeviceSocketConnection(
                device_uid=device_uid,
                websocket=websocket
            )
    
    async def disconnect(self, device_uid: str) -> None:
        async with self._lock:
            if device_uid in self._connections:
                connection = self._connections[device_uid]
                try:
                    await connection.websocket.close()
                except:
                    pass
                del self._connections[device_uid]
                
    async def send_message(self, device_uid: str, response_code: int, data: any) -> None:
        if device_uid in self._connections:
            connection = self._connections[device_uid]
            try:
                await connection.websocket.send_text(
                    json.dumps({
                        "response": response_code,
                        "data": data
                    })
                )
            except Exception as e:
                print(f"Error sending message to device {device_uid}: {e}")
                await self.disconnect(device_uid)
                
    def get_connection(self, device_uid: str) -> Optional[DeviceSocketConnection]:
        return self._connections.get(device_uid)
        
    def set_table_title(self, device_uid: str, table_title: str) -> None:
        if device_uid in self._connections:
            self._connections[device_uid].table_title = table_title
            
    def remove_table_title(self, device_uid: str) -> None:
        if device_uid in self._connections:
            self._connections[device_uid].table_title = None
            
    async def broadcast_to_devices(self, response_code: int, data: any) -> None:
        async with self._lock:
            for device_uid in list(self._connections.keys()):
                await self.send_message(device_uid, response_code, data)
                
    async def update_device_status(self, device_uid: str, is_connected: bool, db: Session) -> None:
        try:
            auth_device = db.query(models.AuthDeviceData).filter(
                models.AuthDeviceData.device_uid == device_uid
            ).first()
            if auth_device:
                auth_device.is_connected = is_connected
                db.commit()
        except Exception as e:
            print(f"Error updating device status: {e}")
            
    async def handle_table_connection(self, device_uid: str, table_id: Optional[str] = None) -> None:
        db = get_db_direct()
        try:
            auth_device = db.query(models.AuthDeviceData).filter(
                models.AuthDeviceData.device_uid == device_uid
            ).first()
            
            if not auth_device:
                return
                
            if table_id:
                table = db.query(models.TableData).filter(
                    models.TableData.id == table_id
                ).first()
                
                if table:
                    self.set_table_title(device_uid, table.title)
                    await self.send_message(
                        device_uid,
                        200,
                        {
                            "event": "connect_table",
                            "table_title": table.title
                        }
                    )
            else:
                self.remove_table_title(device_uid)
                await self.send_message(
                    device_uid,
                    200,
                    {
                        "event": "disconnect_table"
                    }
                )
        finally:
            db.close()
            
    async def handle_game_connection(self, device_uid: str, table_id: str = None) -> None:
        """
        디바이스에 게임 연결/해제 이벤트를 전송합니다.
        table_id가 None이면 게임 연결 해제, 아니면 해당 테이블의 게임 연결
        """
        if not device_uid in self._connections:
            print(f"Device {device_uid} not found in connections")
            return
            
        db = get_db_direct()
        try:
            if not table_id:
                await self.send_message(
                    device_uid,
                    200,
                    {
                        "event": "game_disconnect"
                    }
                )
                return
                
            table_data = db.query(models.TableData).filter(
                models.TableData.id == table_id
            ).first()
            
            if not table_data:
                print(f"Table {table_id} not found")
                return
                
            game_id = table_data.game_id
            
            if not game_id:
                await self.send_message(
                    device_uid,
                    200,
                    {
                        "event": "game_disconnect"
                    }
                )
                return
                
            game_data = db.query(models.GameData).filter(
                models.GameData.id == game_id
            ).first()
            
            if game_data:
                print(f"Sending game connection event to device {device_uid} for game {game_id}")
                await self.send_message(
                    device_uid,
                    200,
                    {
                        "event": "game_connect",
                        "game_data": game_data.to_json()
                    }
                )
            else:
                print(f"Game {game_id} not found")
                await self.send_message(
                    device_uid,
                    200,
                    {
                        "event": "game_disconnect"
                    }
                )
        except Exception as e:
            print(f"Error in handle_game_connection: {e}")
            await self.send_message(
                device_uid,
                500,
                {
                    "event": "game_connection_error",
                    "error": str(e)
                }
            )
        finally:
            db.close()
            
    async def notify_table_game_change(self, table_id: str) -> None:
        """
        테이블에 연결된 모든 디바이스에 게임 상태 변경을 알립니다.
        """
        db = get_db_direct()
        try:
            # 테이블에 연결된 모든 디바이스 찾기
            devices = db.query(models.AuthDeviceData).filter(
                models.AuthDeviceData.connect_table_id == table_id
            ).all()
            
            for device in devices:
                if device.device_uid in self._connections:
                    await self.handle_game_connection(device.device_uid, table_id)
        except Exception as e:
            print(f"Error in notify_table_game_change: {e}")
        finally:
            db.close()

# 전역 소켓 매니저 인스턴스
socket_manager = DeviceSocketManager() 