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
from database import get_db, get_db_direct
from dataclasses import dataclass
@dataclass
class InGameUser:
    customer_id: str
    join_count: int
    is_sit : bool
    is_addon : bool
    
    def to_json(self):
        return {
            "customer_id": self.customer_id,
            "join_count": self.join_count,
            "is_sit": self.is_sit,
            "is_addon": self.is_addon
        }

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/get-user-list")
async def get_user_list():
    """전화번호가 있는 모든 사용자 조회"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        user_list = db.query(models.UserData).filter(models.UserData.phone_number != None).all()
        
        if not user_list:
            return JSONResponse(
                content={"response": 201, "message": "사용자를 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        json_data_users = []
        for user in user_list:
            user_json = user.to_json()
            
            # 시간 포맷 변환
            user_json["register_at"] = user_json["register_at"].isoformat()
            user_json["last_visit_at"] = user_json["last_visit_at"].isoformat()
            
            json_data_users.append(user_json)
            
        return JSONResponse(
            content={"response": 200, "data": json_data_users},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.get("/get-all-user-list")
async def get_all_user_list():
    """모든 사용자 조회 (전화번호 필터 없음)"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        user_list = db.query(models.UserData).all()
        
        if not user_list:
            return JSONResponse(
                content={"response": 201, "message": "사용자를 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        json_data_users = []
        for user in user_list:
            user_json = user.to_json()
            
            # 시간 포맷 변환
            user_json["register_at"] = user_json["register_at"].isoformat()
            user_json["last_visit_at"] = user_json["last_visit_at"].isoformat()
            
            json_data_users.append(user_json)
            
        return JSONResponse(
            content={"response": 200, "data": json_data_users},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.get("/get-user/{user_id}")
async def get_user(user_id: int):
    """특정 사용자 조회"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        user = db.query(models.UserData).filter(models.UserData.id == user_id).first()
        
        if not user:
            return JSONResponse(
                content={"response": 404, "message": "사용자를 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        user_json = user.to_json()
        
        # 시간 포맷 변환
        user_json["register_at"] = user_json["register_at"].isoformat()
        user_json["last_visit_at"] = user_json["last_visit_at"].isoformat()
        
        return JSONResponse(
            content={"response": 200, "data": user_json},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.post("/create-user")
async def create_user(user_data: schemas.UserDataCreate):
    """사용자 생성"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        user = models.UserData(
            name=user_data.name,
            phone_number=user_data.phone_number,
            regist_mail=user_data.regist_mail,
            game_join_count=user_data.game_join_count,
            visit_count=user_data.visit_count,
            register_at=user_data.register_at,
            last_visit_at=user_data.last_visit_at,
            point=user_data.point,
            total_point=user_data.total_point,
            remark=user_data.remark,
            awarding_history=user_data.awarding_history,
            point_history=user_data.point_history
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        user_json = user.to_json()
        
        # 시간 포맷 변환
        user_json["register_at"] = user_json["register_at"].isoformat()
        user_json["last_visit_at"] = user_json["last_visit_at"].isoformat()
        
        return JSONResponse(
            content={"response": 200, "message": "사용자가 생성되었습니다", "data": user_json},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.put("/update-user/{user_id}")
async def update_user(user_id: int, user_data: schemas.UserDataUpdate):
    """사용자 정보 업데이트"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        user = db.query(models.UserData).filter(models.UserData.id == user_id).first()
        
        if not user:
            return JSONResponse(
                content={"response": 404, "message": "사용자를 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        # 사용자 정보 업데이트
        user.name = user_data.name
        user.phone_number = user_data.phone_number
        user.regist_mail = user_data.regist_mail
        user.game_join_count = user_data.game_join_count
        user.visit_count = user_data.visit_count
        user.register_at = user_data.register_at
        user.last_visit_at = user_data.last_visit_at
        user.point = user_data.point
        user.total_point = user_data.total_point
        user.remark = user_data.remark
        user.awarding_history = user_data.awarding_history
        user.point_history = user_data.point_history
        
        db.commit()
        db.refresh(user)
        
        user_json = user.to_json()
        
        # 시간 포맷 변환
        user_json["register_at"] = user_json["register_at"].isoformat()
        user_json["last_visit_at"] = user_json["last_visit_at"].isoformat()
        
        return JSONResponse(
            content={"response": 200, "message": "사용자 정보가 업데이트되었습니다", "data": user_json},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.delete("/delete-user/{user_id}")
async def delete_user(user_id: int):
    """사용자 삭제"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        user = db.query(models.UserData).filter(models.UserData.id == user_id).first()
        
        if not user:
            return JSONResponse(
                content={"response": 404, "message": "사용자를 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        db.delete(user)
        db.commit()
        
        return JSONResponse(
            content={"response": 200, "message": "사용자가 삭제되었습니다"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

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
    new_player = InGameUser(customer_id=user_data.id, join_count=1, is_sit=True, is_addon=False).to_json()
    game_in_player.append(new_player)
    
    # 게임 플레이어 목록 직접 업데이트
    db.query(models.GameData).filter(models.GameData.id == game_id).update(
        {"game_in_player": game_in_player}
    )
    
    db.commit()
    
    #결제 내역에 남기기
    purchase_data = models.PurchaseData(
        customer_id =user_data.id,
        purchase_type="LOCAL_PAY",
        game_id=game_id,
        item="BUYIN",
        payment_status="COMPLETED",
        status="SUCCESS",
        price=game.buy_in_price,
        used_points=0
    )
    db.add(purchase_data)
    db.commit()
    
    import main
    
    await main.socket_controller.update_game_data(game)
    
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
        user_id = player.get("customer_id")
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
        if player.get("customer_id") == user_id:
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
    
    import main
    
    await main.socket_controller.update_game_data(game)
    
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
async def update_user_in_game_join_count(game_id: int, user_id: int, is_purchase: bool = False, db: Session = Depends(get_db)):
    game = db.query(models.GameData).filter(models.GameData.id == game_id).first()
    if not game:
        return JSONResponse(
            content={"response": 404, "message": "게임을 찾을 수 없습니다"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    game_in_player = game.game_in_player.copy() if game.game_in_player else []
    is_found = False;
    for player in game_in_player:
        if player.get("customer_id") == user_id:
            player["join_count"] += 1
            is_found = True
            
    if not is_found:
        add_in_game_user = InGameUser(customer_id=user_id, join_count=1, is_sit=True, is_addon=False).to_json()
        game_in_player.append(add_in_game_user)
            
    db.query(models.GameData).filter(models.GameData.id == game_id).update(
        {"game_in_player": game_in_player}
    )
    
    db.commit()
    db.refresh(game)
    
    if not is_purchase:
        #결제 내역에 남기기
        purchase_data = models.PurchaseData(
            customer_id=user_id,
            purchase_type="LOCAL_PAY",
            game_id=game_id,
            item="BUYIN",
            payment_status="SUCCESS",
            status="SUCCESS",
            price=game.buy_in_price,
            used_points=0
        )
        db.add(purchase_data)
        db.commit()
    
    import main
    
    await main.socket_controller.update_game_data(game)
    
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
        if player.get("customer_id") == user_id:
            player["join_count"] += 1
            
    db.query(models.GameData).filter(models.GameData.id == game_id).update(
        {"game_in_player": game_in_player}
    )
    
    #결제 내역에 남기기
    purchase_data = models.PurchaseData(
        customer_id=user_id,
        purchase_type="LOCAL_PAY",
        game_id=game_id,
        item="REBUYIN",
        payment_status="SUCCESS",
        status="SUCCESS",
        price=game.re_buy_in_price,
        used_points=0
    )
    db.add(purchase_data)
    
    db.commit()
    db.refresh(game)
    
    import main
    
    await main.socket_controller.update_game_data(game)

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

@router.put("/update-user-in-game-addon")
async def update_user_in_game_addon(game_id: int, user_id: int, is_addon: bool, db: Session = Depends(get_db)):
    game = db.query(models.GameData).filter(models.GameData.id == game_id).first()
    if not game:
        return JSONResponse(
            content={"response": 404, "message": "게임을 찾을 수 없습니다"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    game_in_player = game.game_in_player.copy() if game.game_in_player else []
    for player in game_in_player:
        if player.get("customer_id") == user_id:
            player["is_addon"] = is_addon
            
    # 명시적으로 DB 업데이트 쿼리 실행
    db.query(models.GameData).filter(models.GameData.id == game_id).update(
        {"game_in_player": game_in_player}
    )
    
    #결제 내역에 남기기
    purchase_data = models.PurchaseData(
        customer_id=user_id,
        purchase_type="LOCAL_PAY",
        game_id=game_id,
        item="ADDON",
        payment_status="COMPLETED",
        status="SUCCESS",
        price=game.addon_price,
        used_points=0
    )
    db.add(purchase_data)
    
    db.commit()
    db.refresh(game)
    
    import main
    
    await main.socket_controller.update_game_data(game)
    
    # 테이블에 연결된 디바이스에 업데이트된 게임 정보 전송
    tables = db.query(models.TableData).filter(models.TableData.game_id == game_id).all()
    for table in tables:
        devices = db.query(models.AuthDeviceData).filter(models.AuthDeviceData.connect_table_id == table.id).all()
        for device in devices:
            await device_controller.send_connect_game_socket_event(device.device_uid, table.id, db)   

    return JSONResponse(
        content={"response": 200, "message": "게임 플레이어 애드온 상태가 업데이트되었습니다"},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )