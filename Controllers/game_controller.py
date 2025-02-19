import asyncio
from datetime import datetime
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

router = APIRouter(
    prefix="/games",
    tags=["games"]
)

@router.get("/get-first-last-game-start-date")
async def get_first_last_game_start_date(db: Session = Depends(get_db)):
    # db에 있는 첫번째 게임과 두번째 게임의 시작 날짜 가져와서 리턴
    first_game = db.query(models.GameData).order_by(models.GameData.game_start_time).first()
    last_game = db.query(models.GameData).order_by(models.GameData.game_start_time.desc()).first()
    # 만약 둘다 없으면 404 리턴
    if not first_game or not last_game:
        return JSONResponse(
            content={"response": 404, "message": "No games found"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    return {
        "first_game_start_date": first_game.game_start_time,
        "last_game_start_date": last_game.game_start_time
    }
    
@router.post("/create-game/{preset_id}/{table_id}")
async def create_game(preset_id: int, table_id: int, db: Session = Depends(get_db)):
    if not preset_id or not table_id:
        return JSONResponse(
            content={"response": 400, "message": "Preset ID and Table ID are required"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    table = db.query(models.TableData).filter(models.TableData.id == table_id).first()
    if not table:
        return JSONResponse(
            content={"response": 404, "message": "Table not found"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    # 프리셋 데이터 가져오기
    preset = db.query(models.PresetData).filter(models.PresetData.id == preset_id).first()
    if not preset:
        return JSONResponse(
            content={"response": 404, "message": "Preset not found"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    # 게임 데이터 생성
    game = models.GameData(
        title=preset.preset_name,
        game_start_time=datetime.now(),
        game_calcul_time=datetime.now(),
        game_stop_time=None,
        game_end_time=None,
        game_status="waiting",
        game_in_player=[],
        table_connect_log=[
            {
                "table_id": table_id,
                "is_connected": True,
                "connect_time": datetime.now().isoformat()
            }
        ],
        time_table_data=preset.time_table_data,
        buy_in_price=preset.buy_in_price,
        re_buy_in_price=preset.re_buy_in_price,
        starting_chip=preset.starting_chip,
        rebuyin_payment_chips=preset.rebuyin_payment_chips,
        rebuyin_number_limits=preset.rebuyin_number_limits,
        addon_data=preset.addon_data,
        prize_settings=preset.prize_settings,
        rebuy_cut_off=preset.rebuy_cut_off
    )
    db.add(game)
    db.commit()
    
    return JSONResponse(
        content={"response": 200, "message": "Game created successfully"},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

from datetime import datetime

@router.get("/get-period-lookup")
async def get_period_lookup(firstdate: str = None, lastdate: str = None, db: Session = Depends(get_db)):
    if not firstdate:
        return JSONResponse(
            content={"response": 400, "message": "First date is required"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    if not lastdate:
        return JSONResponse(
            content={"response": 400, "message": "Last date is required"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    try:
        firstdate_parsed = datetime.fromisoformat(firstdate)
        lastdate_parsed = datetime.fromisoformat(lastdate)
    except ValueError:
        return JSONResponse(
            content={"response": 400, "message": "Invalid date format"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )

    game = db.query(models.GameData).filter(models.GameData.game_start_time >= firstdate_parsed).filter(models.GameData.game_start_time <= lastdate_parsed).all()
    if not game:
        return JSONResponse(
            content={"response": 404, "message": "Game not found"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        
    game_list = []
    for g in game:
        game_list.append(g.to_json())
    
    return JSONResponse(
        content={"response": 200, "message": "Game found", "data": game_list},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )