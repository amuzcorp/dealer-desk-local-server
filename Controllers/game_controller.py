import asyncio
from datetime import datetime
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

# import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Controllers import device_controller, table_controller
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
    
    return JSONResponse(
        content={
            "response": 200,
            "message": "Game start dates retrieved successfully",
            "data": {
                "first_game_start_date": first_game.game_start_time.isoformat(),
                "last_game_start_date": last_game.game_start_time.isoformat()
            }
        },
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

@router.get("/get-activate-games")
async def get_activate_games(db: Session = Depends(get_db)):
    async def get_active_list(db_inFun : Session):
        games = db_inFun.query(models.GameData).filter(models.GameData.game_status.in_(["waiting", "in-progress"])).all()
        game_list = []
        for g in games:
            game_list.append(g.to_json())
        return game_list
    
    async def event_generator(db_inFun : Session):
        while True:
            try:
                game_list = await get_active_list(db_inFun)
                print(f"전송된 게임 개수 : {len(game_list)}")
                yield f"{json.dumps(game_list)}\n\n"
                await asyncio.sleep(3)
            except Exception as e:
                print(f"오류 발생: {str(e)}")
                yield f"error: {str(e)}\n\n"
                break;

    return EventSourceResponse(event_generator(db), media_type="text/event-stream")

@router.get("/get-active-game-no-sse-data")
async def get_active_game_no_sse_data(db: Session = Depends(get_db)):
    games = db.query(models.GameData).filter(models.GameData.game_status.in_(["waiting", "in-progress"])).all()
    game_list = []
    for g in games:
        game_list.append(g.to_json())
    return JSONResponse(
        content={"response": 200, "message": "Active games retrieved successfully", "data": game_list},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

@router.post("/create-game")
async def create_game(game_data: dict, db: Session = Depends(get_db)):
    preset_id = game_data.get("preset_id")
    table_id = game_data.get("table_id")
    
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
    print(preset_id)
    preset = db.query(models.PresetData).filter(models.PresetData.id == preset_id).first()
    if not preset:
        return JSONResponse(
            content={"response": 404, "message": "Preset not found"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    # 게임 데이터 생성
    game = models.GameData(
        title=preset.preset_name,
        game_code=str(random.randint(0, 99999)).zfill(5),
        game_start_time=datetime.now(),
        game_calcul_time=datetime.now(),
        game_stop_time=None,
        game_end_time=None,
        game_in_player=[],
        table_connect_log=[],
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
    
    await table_controller.connect_table_game_id(
        {
            "table_id": table_id,
            "game_id": game.id
        }, db)
    
    import main
    
    print(f'소켓 컨트롤러 상태: {main.socket_controller}')
    
    if main.socket_controller and main.socket_controller.is_connected:
        print(f'게임 데이터 소켓 전송 시작 - 게임 ID: {game.id}')
        try:
            await main.socket_controller.create_game_data(game)
            print(f'게임 데이터 소켓 전송 성공 - 게임 ID: {game.id}')
        except Exception as e:
            print(f'게임 데이터 소켓 전송 중 오류 발생: {e}')
    else:
        print(f'소켓 컨트롤러 연결 상태: {getattr(main.socket_controller, "is_connected", None)}')
        print(f'소켓 컨트롤러 구독 상태: {getattr(main.socket_controller, "is_subscribed", None)}')
        if main.socket_controller:
            print(f'소켓 ID: {main.socket_controller.socket_id}')
    
    return JSONResponse(
        content={"response": 200, "message": "Game created successfully", "game_id": game.id},
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
        
    print(len(game_list))
    
    return JSONResponse(
        content={"response": 200, "message": "Game found", "data": game_list},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    
@router.post("/control-game-state")
async def control_game_state(game_data: dict, db: Session = Depends(get_db)):
    game_id = game_data.get("game_id")
    game_status = game_data.get("game_status")
    
    game = db.query(models.GameData).filter(models.GameData.id == game_id).first()
    if not game:
        return JSONResponse(
            content={"response": 404, "message": "게임을 찾을 수 없습니다"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    if game_status == "in-progress":
        game.game_status = game_status
        if game.game_stop_time:
            # 중지 시간과 현재 시간 차이 값 구하기
            calc_time = datetime.now() - game.game_stop_time
            game.game_calcul_time = game.game_calcul_time + calc_time
            game.game_stop_time = None 
    elif game_status == "stop":
        game.game_stop_time = datetime.now()
        print(game.game_calcul_time)
    elif game_status == "end":
        game.game_end_time = datetime.now()
        game.game_status = "end"
    db.commit()
    db.refresh(game)
    
    if game_status != "end":
        tables = db.query(models.TableData).filter(models.TableData.game_id == game.id).all()
        for table in tables:
            devices = db.query(models.AuthDeviceData).filter(models.AuthDeviceData.connect_table_id == table.id).all()
            for device in devices:
                await device_controller.send_connect_game_socket_event(device.device_uid, table.id, db)
    
    
    return JSONResponse(
        content={"response": 200, "message": "게임 상태가 성공적으로 업데이트되었습니다"},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )


@router.put("/control-game-time/{game_id}")  
async def control_game_time(game_id: str, time_dict: dict, db: Session = Depends(get_db)):
    from datetime import timedelta
    
    # 초로 받아옴
    game_time_seconds = time_dict.get("game_time")
    print(f"요청된 시간 조정: {game_time_seconds}초")
    
    game = db.query(models.GameData).filter(models.GameData.id == game_id).first()
    if not game:
        return JSONResponse(
            content={"response": 404, "message": "게임을 찾을 수 없습니다"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    # 초 단위로 받은 시간을 timedelta로 변환
    time_delta = timedelta(seconds=game_time_seconds)
    
    print("원래 시간 : ", game.game_calcul_time)
    
    # game.game_calcul_time이 존재하는 경우
    if game.game_calcul_time:
        # 시간을 앞으로 당기는 경우(양수) - 게임 시작 시간을 더 과거로 설정
        if game_time_seconds > 0:
            game.game_calcul_time = game.game_calcul_time - time_delta
        # 시간을 뒤로 돌리는 경우(음수) - 게임 시작 시간을 더 최근으로 설정
        else:
            # 음수 값이므로 빼기 대신 더하기 사용
            game.game_calcul_time = game.game_calcul_time - time_delta
        
        # 게임이 정지 상태인 경우 정지 시간도 동일하게 조정
        # if game.game_stop_time:
        #     if game_time_seconds > 0:
        #         game.game_stop_time = game.game_stop_time - time_delta
        #     else:
        #         game.game_stop_time = game.game_stop_time - time_delta
    
    print(f"게임 시간 업데이트 후: {game.game_calcul_time}")
    
    db.commit()
    db.refresh(game)
    
    # 테이블에 연결된 디바이스에 업데이트된 게임 정보 전송
    tables = db.query(models.TableData).filter(models.TableData.game_id == game.id).all()
    for table in tables:
        devices = db.query(models.AuthDeviceData).filter(models.AuthDeviceData.connect_table_id == table.id).all()
        for device in devices:
            await device_controller.send_connect_game_socket_event(device.device_uid, table.id, db)
    
    return JSONResponse(
        content={"response": 200, "message": "게임 시간이 성공적으로 업데이트되었습니다"},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    
@router.get("/get-game-by-id/{game_id}")
async def get_game_by_id(game_id: int, db: Session = Depends(get_db)):
    game = db.query(models.GameData).filter(models.GameData.id == game_id).first()
    if not game:
        return JSONResponse(
            content={"response": 404, "message": "게임을 찾을 수 없습니다"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    return JSONResponse(
        content={"response": 200, "message": "게임을 찾았습니다", "data": game.to_json()},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )