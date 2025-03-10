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
from database import get_db, get_db_direct

router = APIRouter(
    prefix="/awarding",
    tags=["awarding"]
)


@router.post("/create-awarding-history")
async def create_awarding_history(awarding_history: schemas.AwardingHistoryCreate):
    db = get_db_direct()
    db_awarding_history = models.AwardingHistoryData(
        game_id=awarding_history.game_id,
        customer_id=awarding_history.customer_id,
        game_rank=awarding_history.game_rank,
        awarding_at= datetime.now(),
        awarding_amount=awarding_history.awarding_amount
    )
    db.add(db_awarding_history)
    db.commit()
    db.refresh(db_awarding_history)
    
    import main
    
    await main.socket_controller.add_awarding_history_data(db_awarding_history)
    
    return JSONResponse(
        content={"response": 200, "message": "Awarding history created successfully", "data": db_awarding_history.to_json()},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    
@router.get("/get-awarding-history-by-user-id/{user_id}")
async def get_awarding_history_by_user_id(user_id: int):
    db = get_db_direct()
    db_awarding_history = db.query(models.AwardingHistoryData).filter(models.AwardingHistoryData.customer_id == user_id).all()
    response_data = []
    for awarding_history in db_awarding_history:
        response_data.append(awarding_history.to_json())
    return JSONResponse(
        content={"response": 200, "message": "Awarding history created successfully", "data": response_data},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

@router.get("/get-awarding-history-by-game-id/{game_id}")
async def get_awarding_history_by_game_id(game_id: int):
    db = get_db_direct()
    db_awarding_history = db.query(models.AwardingHistoryData).filter(models.AwardingHistoryData.game_id == game_id).all()
    response_data = []
    for awarding_history in db_awarding_history:
        response_data.append(awarding_history.to_json())

    return JSONResponse(
        content={"response": 200, "message": "Awarding history created successfully", "data": response_data},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

