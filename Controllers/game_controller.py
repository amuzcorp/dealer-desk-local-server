import asyncio
from datetime import datetime, timedelta
import random
from fastapi import APIRouter, Depends, HTTPException, WebSocket, logger
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

import json 
import sys
import os
from dataclasses import dataclass
import models

# import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Controllers import device_controller, table_controller
import models
import schemas
from database import get_db, get_db_direct

router = APIRouter(
    prefix="/games",
    tags=["games"]
)

@router.get("/get-first-last-game-start-date")
async def get_first_last_game_start_date():
    """첫 번째와 마지막 게임의 시작 날짜를 조회합니다."""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        first_game = db.query(models.GameData).order_by(models.GameData.game_start_time).first()
        last_game = db.query(models.GameData).order_by(models.GameData.game_start_time.desc()).first()
        
        if not first_game or not last_game:
            return JSONResponse(
                content={"response": 201, "message": "게임 데이터가 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        return JSONResponse(
            content={
                "response": 200, 
                "data": {
                    "first_date": first_game.game_start_time.isoformat(),
                    "last_date": last_game.game_start_time.isoformat()
                }
            },
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.get("/get-activate-games")
async def get_activate_games():
    """
    활성화된 게임 목록을 조회합니다.
    """
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        games = db.query(models.GameData).filter(
            models.GameData.game_status.in_(["waiting", "in-progress"])
        ).all()
        
        if not games:
            return JSONResponse(
                content={"response": 201, "message": "활성화된 게임이 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        json_data_games = []
        for game in games:
            json_data_games.append(jsonable_encoder(game.to_json()))
            
        return JSONResponse(
            content={"response": 200, "data": json_data_games},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.get("/get-active-game-no-sse-data")
async def get_active_game_no_sse_data():
    """활성화된 게임 목록을 조회합니다 (SSE 없이)."""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        games = db.query(models.GameData).filter(
            models.GameData.game_status.in_(["waiting", "in_progress"])
        ).all()
        
        if not games:
            return JSONResponse(
                content={"response": 201, "message": "활성화된 게임이 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        game_list = []
        for game in games:
            game_list.append(game.to_json())
            
        return JSONResponse(
            content={"response": 200, "data": game_list},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.post("/create-game")
async def create_game(preset_id: dict):
    """게임을 생성합니다."""
    # 직접 세션 가져오기
    db = get_db_direct()
    preset_id = preset_id.get("preset_id");
    try:
        # 게임 코드 생성 (5자리 숫자)
        while True:
            game_code = str(random.randint(10000, 99999))
            existing_game = db.query(models.GameData).filter(models.GameData.game_code == game_code).first()
            if not existing_game:
                break
        
        preset :models.PresetData = db.query(models.PresetData).filter(models.PresetData.id == preset_id).first()
        
        if not preset:
            return JSONResponse(
                content={"response": 404, "message": "게임 프리셋을 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        
        # 새 게임 생성
        new_game = models.GameData(
            game_code=game_code,
            title=preset.preset_name,
            game_start_time=datetime.now(),
            game_calcul_time=datetime.now(),
            game_stop_time=datetime.now(),
            game_status="waiting",
            game_in_player=[],
            table_connect_log=[],
            addon_count=0,
            
            time_table_data=preset.time_table_data,
            buy_in_price=preset.buy_in_price,
            re_buy_in_price=preset.re_buy_in_price,
            starting_chip=preset.starting_chip,
            rebuyin_payment_chips=preset.rebuyin_payment_chips,
            rebuyin_number_limits=preset.rebuyin_number_limits,
            addon_data=preset.addon_data,
            prize_settings=preset.prize_settings,
            rebuy_cut_off=preset.rebuy_cut_off,
            final_prize=0
        )
        
        db.add(new_game)
        db.commit()
        db.refresh(new_game)
        
        import main
        await main.socket_controller.create_game_data(new_game)
        
        return JSONResponse(
            content={"response": 200, "message": "게임이 생성되었습니다", "data": new_game.to_json(), "game_id": new_game.id},
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
    
@router.get("/get-period-lookup")
async def get_period_lookup(firstdate: str = None, lastdate: str = None):
    """특정 기간 내의 게임 데이터를 조회합니다."""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        if not firstdate or not lastdate:
            # 기본값으로 최근 한 달의 게임 데이터를 조회
            now = datetime.now()
            firstdate_parsed = now - timedelta(days=30)
            lastdate_parsed = now
        else:
            # 문자열을 날짜로 변환
            firstdate_parsed = datetime.fromisoformat(firstdate.replace('Z', '+00:00'))
            lastdate_parsed = datetime.fromisoformat(lastdate.replace('Z', '+00:00'))
            
        # 날짜 범위 내의 게임 데이터 조회
        games = db.query(models.GameData).filter(
            models.GameData.game_start_time >= firstdate_parsed
        ).filter(
            models.GameData.game_start_time <= lastdate_parsed
        ).all()
        
        if not games:
            return JSONResponse(
                content={"response": 201, "message": "해당 기간에 게임 데이터가 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 결과 포맷팅
        result = []
        for game in games:
            game_json = game.to_json()
            result.append(game_json)
            
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

@router.post("/control-game-state")
async def control_game_state(game_data: dict):
    """게임 상태를 제어합니다."""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        game_id = game_data.get("game_id")
        game_status = game_data.get("game_status")
        
        if not game_id or not game_status:
            return JSONResponse(
                content={"response": 400, "message": "게임 ID와 상태가 필요합니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 게임 조회
        game : models.GameData = db.query(models.GameData).filter(models.GameData.id == game_id).first()
        if not game:
            return JSONResponse(
                content={"response": 404, "message": "게임을 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 게임 상태 업데이트
        if game_status == "in-progress":
            game.game_status = "in-progress"
            if(game.game_stop_time):
                game.game_calcul_time = game.game_calcul_time + (datetime.now() - game.game_stop_time)
                game.game_stop_time = None
        elif game_status == "end":
            game.game_status = "end"
            game.game_end_time = datetime.now()
        elif game_status == "stop":
            game.game_stop_time = datetime.now()
        else:
            game.game_status = game_status
            
        db.commit()
        db.refresh(game)
        
        # 관련 디바이스에게 변경 알림
        table_datas = db.query(models.TableData).filter(models.TableData.game_id == game.id).all()
        for table_data in table_datas:
            table_connect_device = db.query(models.AuthDeviceData).filter(models.AuthDeviceData.connect_table_id == table_data.id).all()
            devices_sockets = device_controller.device_socket_data;
            for device_socket in devices_sockets:
                if device_socket.device_uid in table_connect_device:
                    print(f"device_socket.device_uid : {device_socket.device_uid}")
                    await device_controller.send_connect_game_socket_event(device_socket.device_uid, game.id)
        
        # 중앙 서버에 보내기
        import main
        await main.socket_controller.update_game_data(game)
        
        return JSONResponse(
            content={"response": 200, "message": "게임 상태가 업데이트되었습니다", "data": game.to_json()},
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

@router.put("/control-game-time/{game_id}")
async def control_game_time(game_id: str, time_dict: dict):
    """게임 시간을 제어합니다."""
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
            
        # 게임 시간 업데이트
        if "game_start_time" in time_dict:
            game.game_start_time = datetime.fromisoformat(time_dict["game_start_time"].replace('Z', '+00:00'))
            
        if "game_stop_time" in time_dict:
            game.game_stop_time = datetime.fromisoformat(time_dict["game_stop_time"].replace('Z', '+00:00'))
            
        if "game_end_time" in time_dict:
            game.game_end_time = datetime.fromisoformat(time_dict["game_end_time"].replace('Z', '+00:00'))
            
        if "game_calcul_time" in time_dict:
            game.game_calcul_time = datetime.fromisoformat(time_dict["game_calcul_time"].replace('Z', '+00:00'))
            
        db.commit()
        db.refresh(game)
        
        import main
        await main.socket_controller.update_game_data(game)
        
        return JSONResponse(
            content={"response": 200, "message": "게임 시간이 업데이트되었습니다", "data": game.to_json()},
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

@router.get("/get-game-by-id/{game_id}")
async def get_game_by_id(game_id: int):
    """특정 게임을 ID로 조회합니다."""
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
            
        return JSONResponse(
            content={"response": 200, "data": game.to_json()},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.put("/update-game-final-prize-by-id/{game_id}")
async def update_game_final_prize_by_id(game_id: int, game_data: dict):
    """게임의 최종 상금을 업데이트합니다."""
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
            
        # 최종 상금 업데이트
        final_prize = game_data.get("final_prize", 0)
        game.final_prize = final_prize
        
        db.commit()
        db.refresh(game)
        
        import main
        await main.socket_controller.update_game_data(game)
        
        return JSONResponse(
            content={"response": 200, "message": "게임 최종 상금이 업데이트되었습니다", "data": game.to_json()},
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
    