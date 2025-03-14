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
    prefix="/operator",
    tags=["operator"]
)

"""
가장 마지막의 id가 오픈인지 아닌지 
return true, false
"""
@router.get("/open-closs")
async def get_open_closs():
    db : Session = get_db_direct()
    open_closs = db.query(models.OpenClossData).order_by(models.OpenClossData.id.desc()).first()
    
    if open_closs is None:
        return JSONResponse(
            content={"response": 200 , "data": "CLOSE"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    if open_closs.status == "OPEN":
        return JSONResponse(
            content={"response": 200, "data": "OPEN"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    else:
        return JSONResponse(
            content={"response": 200, "data": "CLOSE"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )


"""
매장 오픈하기
마지막에 있는 Status가 OPEN이면 닫기
마지막에 있는 Status가 CLOSE이면 오픈
"""
@router.post("/open-closs-toggle")
async def post_open_closs():
    db : Session = get_db_direct()
    open_closs:models.OpenClossData = db.query(models.OpenClossData).order_by(models.OpenClossData.id.desc()).first()
    
    new_open_closs = None
    if open_closs is None:
        new_open_closs = models.OpenClossData(
            status = "OPEN",
            operator_year = datetime.now().year,
            operator_month = datetime.now().month,
            operator_day = datetime.now().day
        )
        db.add(new_open_closs)
        db.commit()
        return JSONResponse(
            content={"response": 200, "data": new_open_closs.to_json()},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    if open_closs.status == "OPEN":
        new_open_closs = models.OpenClossData(
            status = "CLOSE",
            operator_year = open_closs.operator_year,
            operator_month = open_closs.operator_month,
            operator_day = open_closs.operator_day,
            timestamp = datetime.now()  
        )
    else:
        new_open_closs = models.OpenClossData(
            status = "OPEN",
            operator_year = datetime.now().year,
            operator_month = datetime.now().month,
            operator_day = datetime.now().day,
            timestamp = datetime.now()
        )
        
    db.add(new_open_closs)
    db.commit()
    
    return JSONResponse(
        content={"response": 200, "data": new_open_closs.to_json()},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )


async def get_last_open_data():
    db : Session = get_db_direct()
    open_closs:models.OpenClossData = db.query(models.OpenClossData).order_by(models.OpenClossData.id.desc()).first()
    
    print("open_closs : ", open_closs.to_json())
    
    return open_closs
