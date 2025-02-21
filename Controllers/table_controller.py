from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from Controllers import device_controller

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/tables",
    tags=["tables"]
)

@router.get("/", response_model=List[schemas.TableData])
async def get_tables(db: Session = Depends(get_db)):
    tables = db.query(models.TableData).all()
    if not tables:
        return JSONResponse(
            content={"response": 201, "message": "Table not found"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    json_data_tables = []
    for table in tables:
        modelTable = models.TableData(
            id = table.id,  
            game_id = table.game_id,
            table_title = table.table_title,
            current_player_count = table.current_player_count,
            max_player_count = table.max_player_count,
            position = table.position,
            size = table.size
        )
        json_data_tables.append(jsonable_encoder(modelTable.to_json()))
    return JSONResponse(
        content={"response": 200, "data": json_data_tables},
        headers={"Content-Type": "application/json; charset=utf-8"},
        media_type="application/json"
    )

@router.post("/save-table")
async def save_table(tables: List[schemas.TableData], db: Session = Depends(get_db)):
    result = []
    
    existing_table_ids = set(table.id for table in tables if table.id is not None)
    
    tables_to_delete = db.query(models.TableData).filter(
        ~models.TableData.id.in_(existing_table_ids) if existing_table_ids else True
    ).all()
    
    for table_to_delete in tables_to_delete:
        # 디바이스 db에 해당 테이블 연결 해제
        device_data = db.query(models.AuthDeviceData).filter(
            models.AuthDeviceData.connect_table_id == table_to_delete.id
        ).all()
        for device in device_data:
            device.connect_table_id = None
            db.commit()
            print(f"디바이스 연결 해제: {device.device_uid}")
            await device_controller.connect_table_device_socket_event(device.device_uid, db)
            
        db.delete(table_to_delete)
    
    for table in tables:
        table_data = jsonable_encoder(table)
        existing_table = db.query(models.TableData).filter(models.TableData.id == table.id).first()
        
        if existing_table:
            for key, value in table_data.items():
                setattr(existing_table, key, value)
            result.append(existing_table)
        else:
            db_table = models.TableData(**table_data)
            db.add(db_table)
            result.append(db_table)
    
    try:
        db.commit()
        for table in result:
            db.refresh(table)
        
        return JSONResponse(
            content={"response": 200, "data": "Success Saved Tables"},
            headers={"Content-Type": "application/json; charset=utf-8"},
            media_type="application/json"
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            content={"response": 500, "error": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"},
            media_type="application/json"
        )
 
 
@router.put("/disconnect-table-game/{table_id}")
async def disconnect_game(table_id: str, db: Session = Depends(get_db)):
    try:
        table = db.query(models.TableData).filter(models.TableData.id == table_id).first()
        if not table:
            return JSONResponse(
                content={"response": 404, "message": "테이블을 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        table.game_id = None
        db.commit()
        
        return JSONResponse(
            content={"response": 200, "message": "테이블 게임 ID 연결 해제 성공"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            content={"response": 500, "message": f"서버 에러: {str(e)}"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
 
@router.post("/connect-table-game-id")
async def connect_table_game_id(table_game_id: dict, db: Session = Depends(get_db)):
    try:
        table_id = table_game_id.get("table_id")
        game_id = table_game_id.get("game_id")
        
        if not table_id or not game_id:
            return JSONResponse(
                content={"response": 400, "message": "테이블 ID와 게임 ID가 필요합니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        print(f"테이블 ID: {table_id}, 게임 ID: {game_id}")
        
        table = db.query(models.TableData).filter(models.TableData.id == table_id).first()
        if not table:
            return JSONResponse(
                content={"response": 404, "message": "테이블을 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        print(f"찾은 테이블: {table.to_json()}")
        
        table.game_id = game_id
        
        game = db.query(models.GameData).filter(models.GameData.id == game_id).first()
        if not game:
            return JSONResponse(
                content={"response": 404, "message": "게임을 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        game.table_connect_log.append({
            "table_id": table_id,
            "is_connected": True,
            "connect_time": datetime.now().isoformat()
        })
        
        db.commit()
        
        # 커밋 후에 다시 조회하여 변경사항 확인
        updated_table = db.query(models.TableData).filter(models.TableData.id == table_id).first()
        print(f"업데이트된 테이블 확인: {updated_table.to_json()}")
        
        if updated_table.game_id != game_id:
            return JSONResponse(
                content={"response": 500, "message": "테이블 게임 ID 업데이트 실패"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        return JSONResponse(
            content={"response": 200, "message": "테이블 게임 ID 업데이트 성공", "data": updated_table.to_json()},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        
    except Exception as e:
        db.rollback()
        print(f"에러 발생: {str(e)}")
        return JSONResponse(
            content={"response": 500, "message": f"서버 에러: {str(e)}"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )