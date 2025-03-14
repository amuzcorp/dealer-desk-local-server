from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from Controllers import device_controller, device_socket_manager

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models
import schemas
from database import get_db, get_db_direct

router = APIRouter(
    prefix="/tables",
    tags=["tables"]
)

@router.get("/", response_model=List[schemas.TableData])
async def get_tables():
    """모든 테이블 정보를 조회합니다."""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        tables = db.query(models.TableData).all()
        
        if not tables:
            return JSONResponse(
                content={"response": 201, "message": "테이블을 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        json_data_tables = []
        for table in tables:
            model_table = models.TableData(
                id=table.id,  
                game_id=table.game_id,
                title=table.title,
                current_players=table.current_players,
                max_players=table.max_players,
                position=table.position,
                size=table.size
            )
            json_data_tables.append(jsonable_encoder(model_table.to_json()))
            
        return JSONResponse(
            content={"response": 200, "data": json_data_tables},
            headers={"Content-Type": "application/json; charset=utf-8"},
            media_type="application/json"
        )
    finally:
        db.close()

@router.post("/save-table")
async def save_table(tables: List[schemas.TableData]):
    """테이블 정보를 저장하거나 업데이트합니다."""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        result = []
        
        # 요청에 포함된 테이블 ID 목록 생성
        existing_table_ids = set(table.id for table in tables if table.id is not None)
        
        # 요청에 포함되지 않은 테이블 삭제 처리
        tables_to_delete = db.query(models.TableData).filter(
            ~models.TableData.id.in_(existing_table_ids) if existing_table_ids else True
        ).all()
        
        # 삭제할 테이블에 연결된 디바이스 처리
        for table_to_delete in tables_to_delete:
            # 디바이스 DB에서 해당 테이블 연결 해제
            device_data = db.query(models.AuthDeviceData).filter(
                models.AuthDeviceData.connect_table_id == table_to_delete.id
            ).all()
            
            for device in device_data:
                device.connect_table_id = None
                db.commit()
                print(f"디바이스 연결 해제: {device.device_uid}")
                await device_socket_manager.socket_manager.handle_game_connection(device.device_uid, table_to_delete.id)
                
            db.delete(table_to_delete)
        
        # 테이블 생성 또는 업데이트
        for table in tables:
            table_data = jsonable_encoder(table)
            existing_table = db.query(models.TableData).filter(models.TableData.id == table.id).first()
            
            if existing_table:
                # 기존 테이블 업데이트
                for key, value in table_data.items():
                    setattr(existing_table, key, value)
                result.append(existing_table)
            else:
                # 새 테이블 생성
                db_table = models.TableData(**table_data)
                db.add(db_table)
                result.append(db_table)
        
        try:
            # 변경사항 저장
            db.commit()
            for table in result:
                db.refresh(table)
                
            import main
            for table in result:
                table.game_id = None
            await main.socket_controller.save_tables(result)
            return JSONResponse(
                content={"response": 200, "data": "테이블 저장 성공"},
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
    finally:
        db.close()

@router.put("/disconnect-table-game/{table_id}")
async def disconnect_game(table_id: str):
    """테이블과 게임의 연결을 해제합니다."""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        print(f"테이블 연결 해제 시작: 테이블 ID {table_id}")
        
        # 테이블 조회
        table = db.query(models.TableData).filter(models.TableData.id == table_id).first()
        if not table:
            print(f"테이블을 찾을 수 없음: {table_id}")
            return JSONResponse(
                content={"response": 404, "message": "테이블을 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        game_id = table.game_id
        print(f"테이블({table_id})에 연결된 게임 ID: {game_id}")
        
        # 연결된 게임이 없는 경우
        if not game_id:
            print(f"테이블에 연결된 게임이 없습니다: {table_id}")
            return JSONResponse(
                content={"response": 400, "message": "테이블에 연결된 게임이 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        # 게임 조회
        game = db.query(models.GameData).filter(models.GameData.id == game_id).first()
        if not game:
            print(f"게임을 찾을 수 없음: {game_id}")
            table.game_id = None
            db.commit()
            return JSONResponse(
                content={"response": 404, "message": "게임을 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        # 테이블 연결 로그 업데이트
        table_connect_log = game.table_connect_log.copy() if game.table_connect_log else []
        print(f"기존 로그: {table_connect_log}")
        
        # 새 로그 항목 생성
        log_entry = {
            "table_id": table_id,
            "is_connected": False,
            "connect_time": datetime.now().isoformat()
        }
        
        # 로그에 추가
        table_connect_log.append(log_entry)
        print(f"추가 후 로그: {table_connect_log}")
        
        # 게임 객체 업데이트
        game.table_connect_log = table_connect_log
        
        # 테이블 연결 해제
        table.game_id = None
        
        # 변경사항 저장
        db.commit()
        
        # 로그 확인
        db.refresh(game)
        devices = db.query(models.AuthDeviceData).filter(models.AuthDeviceData.connect_table_id == table_id).all()
         
        print(f"커밋 후 게임 로그: {game.table_connect_log}")
        
        # 테이블에 연결된 디바이스가 있으면 이벤트 전송
        if devices:
            for device in devices:
                print(f"테이블에 연결된 디바이스 UID: {device.device_uid}")
                await device_socket_manager.socket_manager.handle_game_connection(device.device_uid, table_id)
        else:
            print(f"테이블 {table_id}에 연결된 디바이스가 없습니다.")
        
        return JSONResponse(
            content={"response": 200, "message": "테이블 게임 ID 연결 해제 성공"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        print(f"테이블 게임 연결 해제 중 오류 발생: {str(e)}")
        db.rollback()
        return JSONResponse(
            content={"response": 500, "message": f"서버 에러: {str(e)}"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.post("/connect-table-game-id")
async def connect_table_game_id(table_game_id: dict):
    """테이블과 게임을 연결합니다."""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        # 요청 데이터 확인
        table_id = table_game_id.get("table_id")
        game_id = table_game_id.get("game_id")
        
        if not table_id or not game_id:
            return JSONResponse(
                content={"response": 400, "message": "테이블 ID와 게임 ID가 필요합니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        print(f"테이블 ID: {table_id}, 게임 ID: {game_id}")
        
        # 테이블 조회
        table = db.query(models.TableData).filter(models.TableData.id == table_id).first()
        if not table:
            return JSONResponse(
                content={"response": 404, "message": "테이블을 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        print(f"찾은 테이블: {table.to_json()}")
        
        # 테이블에 게임 ID 설
        table.game_id = game_id
        
        # 게임 조회
        game = db.query(models.GameData).filter(models.GameData.id == game_id).first()
        if not game:
            return JSONResponse(
                content={"response": 404, "message": "게임을 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        # 테이블 연결 로그 업데이트
        table_connect_log = game.table_connect_log if game.table_connect_log else []
        print(f"기존 로그: {table_connect_log}")
        
        # 새 로그 항목 생성
        log_entry = {
            "table_id": table_id,
            "is_connected": True,
            "connect_time": datetime.now().isoformat()
        }
        
        # 로그에 추가
        table_connect_log.append(log_entry)
        
        # 게임 객체 업데이트
        db.query(models.GameData).filter(models.GameData.id == game_id).update({
            models.GameData.table_connect_log: table_connect_log
        })
        # 변경사항 저장
        db.commit()
        
        # 테이블에 연결된 디바이스 찾기
        devices = db.query(models.AuthDeviceData).filter(models.AuthDeviceData.connect_table_id == table_id).all()
        
        # 디바이스가 있으면 이벤트 전송
        if devices:
            for device in devices:
                print(f"테이블에 연결된 디바이스 UID: {device.device_uid}")
                await device_socket_manager.socket_manager.handle_game_connection(device.device_uid, table_id)
        else:
            print(f"테이블 {table_id}에 연결된 디바이스가 없습니다.")
        
        return JSONResponse(
            content={"response": 200, "message": "테이블 게임 ID 연결 성공"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        print(f"테이블 게임 연결 중 오류 발생: {str(e)}")
        db.rollback()
        return JSONResponse(
            content={"response": 500, "message": f"서버 에러: {str(e)}"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()