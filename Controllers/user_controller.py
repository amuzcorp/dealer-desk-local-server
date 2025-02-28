from datetime import datetime
import random
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
from dataclasses import dataclass
@dataclass
class InGameUser:
    user_id: str
    join_count: int
    is_sit : bool
    is_addon : bool
    
    def to_json(self):
        return {
            "user_id": self.user_id,
            "join_count": self.join_count,
            "is_sit": self.is_sit,
            "is_addon": self.is_addon
        }

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/get-user-list")
async def get_user_list(db: Session = Depends(get_db)):
    user_list = db.query(models.UserData).filter(models.UserData.phone_number != None).all()
    user_list_json = []
    for user in user_list:
        user_list_json.append(user.to_json())
    return JSONResponse(
        content={"response": 200, "message": "User list", "data": user_list_json},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    
@router.put("/create-guest-user/{game_id}")
async def create_guest_user(game_id: str, db: Session = Depends(get_db)):
    user_data = models.UserData(
        name=f"guest{random.randint(10000, 99999)}",
        phone_number=None,
    )
    db.add(user_data)
    db.commit()
    db.refresh(user_data)
    
    game = db.query(models.GameData).filter(models.GameData.id == game_id).first()
    if not game:
        return JSONResponse(
            content={"response": 404, "message": "게임을 찾을 수 없습니다"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    # 기존 게임 플레이어 목록 가져오기
    game_in_player = game.game_in_player.copy() if game.game_in_player else []
    
    # 새 플레이어 정보 생성 및 추가
    new_player = InGameUser(user_id=user_data.id, join_count=1, is_sit=True, is_addon=False).to_json()
    game_in_player.append(new_player)
    
    # 게임 플레이어 목록 직접 업데이트
    db.query(models.GameData).filter(models.GameData.id == game_id).update(
        {"game_in_player": game_in_player}
    )
    
    db.commit()
    
    # 업데이트 확인을 위해 다시 조회
    updated_game = db.query(models.GameData).filter(models.GameData.id == game_id).first()
    print(f"게임 {game_id}에 사용자 {user_data.id} 추가 완료: {updated_game.game_in_player}")
    
    # 테이블에 연결된 디바이스에 업데이트된 게임 정보 전송
    tables = db.query(models.TableData).filter(models.TableData.game_id == game_id).all()
    for table in tables:
        devices = db.query(models.AuthDeviceData).filter(models.AuthDeviceData.connect_table_id == table.id).all()
        for device in devices:
            await device_controller.send_connect_game_socket_event(device.device_uid, table.id, db)
    
    return JSONResponse(
        content={"response": 200, "message": "User created", "data": user_data.to_json()},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

@router.post("/create-user-data")
async def create_user_data(user_data: schemas.UserDataCreate, db: Session = Depends(get_db)):
    try:
        # 네, id 값은 데이터베이스에서 자동으로 생성됩니다.
        # UserData 모델에서 id는 자동 증가(auto-increment) 필드로 설정되어 있습니다.
        db_user_data = models.UserData(**user_data.model_dump())
        db.add(db_user_data)
        db.commit()
        db.refresh(db_user_data)  # 이 단계에서 자동 생성된 id 값이 db_user_data에 반영됩니다
        return JSONResponse(
            content={"response": 200, "message": "User created", "data": db_user_data.to_json()}, 
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "message": "User creation failed", "data": str(e)}, 
            headers={"Content-Type": "application/json; charset=utf-8"}
        )

@router.post("/update-user-data")
async def update_user_data(user_data: schemas.UserDataUpdate, db: Session = Depends(get_db)):
    db_user_data = db.query(models.UserData).filter(models.UserData.id == user_data.id).first()
    if not db_user_data:
        return JSONResponse(
            content={"response": 404, "message": "User not found"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    db.query(models.UserData).filter(models.UserData.id == user_data.id).update(user_data.model_dump())
    db.commit()
    db.refresh(db_user_data)
    return JSONResponse(
        content={"response": 200, "message": "User updated", "data": db_user_data.to_json()},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    
@router.post("/add-point-for-user")
async def add_point_for_user(body: dict, db: Session = Depends(get_db)):
    user_id = body.get("user_id")
    point_history = body.get("point_history")
    db_user_data = db.query(models.UserData).filter(models.UserData.id == user_id).first()
    if not db_user_data:
        return JSONResponse(
            content={"response": 404, "message": "사용자를 찾을 수 없습니다"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    # 쿼리 결과가 아닌 실제 사용자 객체를 사용
    point_to_add = point_history.get("point", 0)
    db_user_data.point += point_to_add
    db_user_data.total_point += point_to_add
    
    # 포인트 히스토리가 None인 경우 빈 리스트로 초기화
    if db_user_data.point_history is None:
        db_user_data.point_history = []
    
    # 기존 히스토리를 복사하고 새 항목 추가
    current_history = db_user_data.point_history.copy() if db_user_data.point_history else []
    current_history.append(point_history)
    
    # 명시적으로 point_history 업데이트
    db_user_data.point_history = current_history
    
    # 변경사항 저장 전 로그 출력
    # print(f"포인트 히스토리 업데이트: {db_user_data.point_history}")
    
    db.commit()
    db.refresh(db_user_data)
    
    # 저장 후 확인
    # print(f"저장 후 포인트 히스토리: {db_user_data.point_history}")
    
    return JSONResponse(
        content={"response": 200, "message": "사용자 포인트가 업데이트되었습니다", "data": db_user_data.to_json()},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    
@router.get("/in-game-user-list/{game_id}")
async def in_game_user_list(game_id: str, db: Session = Depends(get_db)):
    game = db.query(models.GameData).filter(models.GameData.id == game_id).first()
        
    if not game:
        return JSONResponse(
            content={"response": 404, "message": "게임을 찾을 수 없습니다"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    user_list = []
    in_game_user_id_list = []
    for player in game.game_in_player:
        user_id = player.get("user_id")
        print(user_id)
        in_game_user_id_list.append(user_id)
    
    user_list = db.query(models.UserData).filter(models.UserData.id.in_(in_game_user_id_list)).all()
    user_list_json = []
    for user in user_list:
        user_list_json.append(user.to_json())
    return JSONResponse(
        content={"response": 200, "message": "게임 플레이어 목록", "data": user_list_json},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

@router.put("/update-user-in-game-sit-status")
async def update_user_in_game_sit_statue(game_id: int, user_id: int, is_sit: bool, db: Session = Depends(get_db)):
    game = db.query(models.GameData).filter(models.GameData.id == game_id).first()
    if not game:
        return JSONResponse(
            content={"response": 404, "message": "게임을 찾을 수 없습니다"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    game_in_player = game.game_in_player.copy() if game.game_in_player else []
    for player in game_in_player:
        if player.get("user_id") == user_id:
            player["is_sit"] = is_sit
    
    # 명시적으로 DB 업데이트 쿼리 실행
    db.query(models.GameData).filter(models.GameData.id == game_id).update(
        {"game_in_player": game_in_player}
    )
    
    db.commit()
    db.refresh(game)
    
    # 업데이트 확인을 위해 로그 출력
    print(f"게임 {game_id}의 사용자 {user_id} 자리 상태 업데이트: {is_sit}")
    print(f"업데이트된 게임 플레이어 목록: {game.game_in_player}")
    
    # 테이블에 연결된 디바이스에 업데이트된 게임 정보 전송
    tables = db.query(models.TableData).filter(models.TableData.game_id == game_id).all()
    for table in tables:
        devices = db.query(models.AuthDeviceData).filter(models.AuthDeviceData.connect_table_id == table.id).all()
        for device in devices:
            await device_controller.send_connect_game_socket_event(device.device_uid, table.id, db)    
    
    return JSONResponse(
        content={"response": 200, "message": "게임 플레이어 자리 상태가 업데이트되었습니다"},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

@router.put("/update-user-in-game-join-count")
async def update_user_in_game_join_count(game_id: int, user_id: int, db: Session = Depends(get_db)):
    game = db.query(models.GameData).filter(models.GameData.id == game_id).first()
    if not game:
        return JSONResponse(
            content={"response": 404, "message": "게임을 찾을 수 없습니다"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    game_in_player = game.game_in_player.copy() if game.game_in_player else []
    add_in_game_user = InGameUser(user_id=user_id, join_count=1, is_sit=True, is_addon=False).to_json()
    game_in_player.append(add_in_game_user)
            
    db.query(models.GameData).filter(models.GameData.id == game_id).update(
        {"game_in_player": game_in_player}
    )
    
    db.commit()
    db.refresh(game)
    
    #결제 내역에 남기기
    purchase_data = models.PurchaseData(
        user_id=user_id,
        purchase_type="LOCAL_PAY",
        game_id=game_id,
        item="BUYIN",
        payment_status="COMPLETED",
        status="SUCCESS",
        price=0,
        used_points=0
    )
    db.add(purchase_data)
    db.commit()
    
    # 테이블에 연결된 디바이스에 업데이트된 게임 정보 전송
    tables = db.query(models.TableData).filter(models.TableData.game_id == game_id).all()
    for table in tables:
        devices = db.query(models.AuthDeviceData).filter(models.AuthDeviceData.connect_table_id == table.id).all()
        for device in devices:
            await device_controller.send_connect_game_socket_event(device.device_uid, table.id, db)    
    
    return JSONResponse(
        content={"response": 200, "message": "게임 플레이어 참여 횟수가 업데이트되었습니다"},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

@router.put("/update-user-rebuy-in")
async def update_user_rebuy_in(game_id: int, user_id: int, db: Session = Depends(get_db)):
    game = db.query(models.GameData).filter(models.GameData.id == game_id).first()
    if not game:
        return JSONResponse(
            content={"response": 404, "message": "게임을 찾을 수 없습니다"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    game_in_player = game.game_in_player.copy() if game.game_in_player else []
    for player in game_in_player:
        if player.get("user_id") == user_id:
            player["join_count"] += 1
            
    db.query(models.GameData).filter(models.GameData.id == game_id).update(
        {"game_in_player": game_in_player}
    )
    
    db.commit()
    db.refresh(game)

    # 테이블에 연결된 디바이스에 업데이트된 게임 정보 전송
    tables = db.query(models.TableData).filter(models.TableData.game_id == game_id).all()
    for table in tables:
        devices = db.query(models.AuthDeviceData).filter(models.AuthDeviceData.connect_table_id == table.id).all()
        for device in devices:
            await device_controller.send_connect_game_socket_event(device.device_uid, table.id, db)   

    return JSONResponse(
        content={"response": 200, "message": "게임 플레이어 리버이 인 상태가 업데이트되었습니다"},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
