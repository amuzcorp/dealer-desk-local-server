from datetime import datetime
import random
import uuid
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
            
            json_data_users.append(user_json)
            
        return JSONResponse(
            content={"response": 200, "data": json_data_users},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        print(f"get-user-list 오류: {e}")
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
        print(f"user_list length: {len(user_list)}")
        
        if not user_list:
            return JSONResponse(
                content={"response": 201, "message": "사용자를 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        json_data_users = []
        for user in user_list:
            user_json = user.to_json()
            
            # 시간 포맷 변환
            # user_json["register_at"] = user_json["register_at"].isoformat()
            # user_json["last_visit_at"] = user_json["last_visit_at"].isoformat()
            
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
            email=user_data.email,
            game_join_count=user_data.game_join_count,
            visit_count=user_data.visit_count,
            register_at=user_data.register_at,
            last_visit_at=user_data.last_visit_at,
            remark=user_data.remark,
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
        user.email = user_data.email
        user.game_join_count = user_data.game_join_count
        user.visit_count = user_data.visit_count
        user.register_at = user_data.register_at
        user.last_visit_at = user_data.last_visit_at
        user.point = user_data.point
        user.total_point = user_data.total_point
        user.remark = user_data.remark
        
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
async def create_guest_user(game_id: str):
    """게임에 게스트 사용자를 생성합니다."""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        # 게임 조회
        game = db.query(models.GameData).filter(models.GameData.id == game_id).first()
        if not game:
            return JSONResponse(
                content={"response": 404, "message": "게임을 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 게스트 사용자 생성
        guest_name = "guest" + str(random.randint(10000, 99999))
        # ID를 1001부터 생성하도록 설정
        guest_user = models.UserData(
            id=1000 + (db.query(models.UserData).count()),  # 현재 사용자 수에 1001을 더하여 ID 설정
            name=guest_name,
            uuid=str(uuid.uuid4()),  # UUID 생성
            game_join_count=1,  # 게임 참가 횟수 1로 설정
            visit_count=1,
            register_at=datetime.now(),
            last_visit_at=datetime.now(),
            remark="",
        )
        
        print(f"guest_user: {guest_user.id}")
        
        db.add(guest_user)
        db.commit()
        db.refresh(guest_user)
        # 게임 참가자에 게스트 추가
        game_in_player = game.game_in_player.copy() if game.game_in_player else []
        
        # 플레이어 데이터 구조 확인
        player_data = {
            "customer_id": guest_user.id,
            "join_count": 1,  # 참가 횟수 1로 설정
            "is_sit": True,
            "is_addon": False
        }
        
        game_in_player.append(player_data)
        print(f"게스트 사용자 추가: {guest_name}, ID: {guest_user.id}")
        print(f"game_in_player: {json.dumps(game_in_player, ensure_ascii=False)}")
        
        # 게임 데이터 업데이트
        game.game_in_player = game_in_player
        db.query(models.GameData).filter(models.GameData.id == game_id).update(
            {"game_in_player": game_in_player}
        )
        db.commit()
        db.refresh(game)  # 게임 데이터 새로고침
        
        # 응답 데이터 준비
        user_json = guest_user.to_json()
        
        import main
        await main.socket_controller.register_customer_data(guest_user)
        # 시간 포맷 변환
        # user_json["register_at"] = user_json["register_at"].isoformat() if user_json["register_at"] else None
        # user_json["last_visit_at"] = user_json["last_visit_at"].isoformat() if user_json["last_visit_at"] else None
        
        return JSONResponse(
            content={
                "response": 200, 
                "message": "게스트 사용자가 생성되었습니다", 
                "user_id": guest_user.id, 
                "data": user_json,
                "game_in_player": game.game_in_player
            },
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        db.rollback()
        print(f"게스트 사용자 생성 오류: {str(e)}")
        return JSONResponse(
            content={"response": 500, "message": f"게스트 사용자 생성 중 오류 발생: {str(e)}"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()
@router.post("/add-point-for-user")
async def add_point_for_user(body: dict):
    """사용자에게 포인트를 추가합니다."""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        user_id = body.get("user_id")
        point = int(body.get("point", 0))
        
        if not user_id:
            return JSONResponse(
                content={"response": 400, "message": "사용자 ID가 필요합니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 사용자 조회
        user = db.query(models.UserData).filter(models.UserData.id == user_id).first()
        if not user:
            return JSONResponse(
                content={"response": 404, "message": "사용자를 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 포인트 업데이트
        user.point += point
        user.total_point += point
        
        # 포인트 기록 추가
        point_history = user.point_history if user.point_history else []
        point_history.append({
            "point": point,
            "date": datetime.now().isoformat(),
            "reason": body.get("reason", "포인트 추가")
        })
        user.point_history = point_history
        
        db.commit()
        db.refresh(user)
        
        return JSONResponse(
            content={"response": 200, "message": "포인트가 추가되었습니다", "data": user.to_json()},
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

@router.get("/in-game-user-list/{game_id}")
async def in_game_user_list(game_id: str):
    """게임에 참가 중인 사용자 목록을 조회합니다."""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        # 게임 조회
        game = db.query(models.GameData).filter(models.GameData.id == game_id).first()
        if not game:
            return JSONResponse(
                content={"response": 404, "message": "게임을 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 게임 참가자 목록
        game_in_player = game.game_in_player if game.game_in_player else []
        
        # 각 참가자의 상세 정보 조회
        result = []
        for player in game_in_player:
            user_id = player.get("customer_id")
            user = db.query(models.UserData).filter(models.UserData.id == user_id).first()
            if user:
                user_info = user.to_json()
                user_info.update(player)
                result.append(user_info)
                
        return JSONResponse(
            content={"response": 200, "data": result},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.put("/update-user-in-game-sit-status")
async def update_user_in_game_sit_status(game_id: int, user_id: int, is_sit: bool):
    """게임 참가자의 착석 상태를 업데이트합니다."""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        # 게임 조회
        game = db.query(models.GameData).filter(models.GameData.id == game_id).first()
        if not game:
            return JSONResponse(
                content={"response": 404, "message": "게임을 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 사용자 조회
        user = db.query(models.UserData).filter(models.UserData.id == user_id).first()
        if not user:
            return JSONResponse(
                content={"response": 404, "message": "사용자를 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 게임 참가자 목록
        game_in_player = game.game_in_player.copy() if game.game_in_player else []
        
        # 참가자 목록에서 해당 사용자 찾기
        user_found = False
        for player in game_in_player:
            if player.get("customer_id") == user_id:
                player["is_sit"] = is_sit
                user_found = True
                break
                
        # 참가자 목록에 사용자가 없으면 추가
        if not user_found:
            game_in_player.append({
                "customer_id": user_id,
                "join_count": 0,
                "is_sit": is_sit,
                "is_addon": False
            })
            
        # 게임 참가자 목록 업데이트
        game.game_in_player = game_in_player
        
        db.query(models.GameData).filter(models.GameData.id == game_id).update(
            {"game_in_player": game_in_player}
        )
        
        db.commit()
        
        import main
        await main.socket_controller.update_game_data(game)
        
        return JSONResponse(
            content={"response": 200, "message": "착석 상태가 업데이트되었습니다"},
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

@router.put("/update-user-in-game-join-count")
async def update_user_in_game_join_count(game_id: int, user_id: int, is_purchase: bool = False):
    """
    사용자의 게임 참여 횟수를 업데이트합니다.
    """
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        # 게임 조회
        game = db.query(models.GameData).filter(models.GameData.id == game_id).first()
        if not game:
            return JSONResponse(
                content={"response": 404, "message": "게임을 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        # 게임 참여자 목록 업데이트
        game_in_player = game.game_in_player.copy() if game.game_in_player else []
        is_found = False
        
        for player in game_in_player:
            if player.get("customer_id") == user_id:
                player["join_count"] += 1
                is_found = True
                
        if not is_found:
            add_in_game_user = InGameUser(customer_id=user_id, join_count=1, is_sit=True, is_addon=False).to_json()
            game_in_player.append(add_in_game_user)
                
        # 변경사항 저장
        db.query(models.GameData).filter(models.GameData.id == game_id).update(
            {"game_in_player": game_in_player}
        )
        
        db.commit()
        db.refresh(game)
        
        import main
        await main.socket_controller.update_game_data(game)
        
        return JSONResponse(
            content={"response": 200, "message": "게임 참여 횟수가 업데이트되었습니다"},
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
            await device_controller.send_connect_game_socket_event(device.device_uid, table.id)   

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
            await device_controller.send_connect_game_socket_event(device.device_uid, table.id)

    return JSONResponse(
        content={"response": 200, "message": "게임 플레이어 애드온 상태가 업데이트되었습니다"},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )