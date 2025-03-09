from datetime import datetime, timedelta
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

router = APIRouter(
    prefix="/point",
    tags=["point"]
)

@router.post("/add-point-by-user-id/{user_id}")
async def add_point_by_user_id(user_id: int, pointHistory: schemas.PointHistoryDataCreate):
    db = get_db_direct()
    try:
        user = db.query(models.UserData).filter(models.UserData.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        import uuid
        point_history = models.PointHistoryData(
            uuid=str(uuid.uuid4()),
            customer_id=user_id,
            reason=pointHistory.reason,
            amount=pointHistory.amount,
            available_amount=pointHistory.available_amount,
            is_expired=False,
            expire_at=pointHistory.expire_at,
            is_increase=True,
            created_at=datetime.now()
        )
        db.add(point_history)
        db.commit()
        db.refresh(point_history)
        
        import main
        await main.socket_controller.add_point_history_data(point_history)
        
        return JSONResponse(content={"message": "Point added successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding point: {str(e)}")

@router.get("/get-point-history-by-user-id/{user_id}")
async def get_point_history_by_user_id(user_id: int):
    db = get_db_direct()
    try:
        point_history = db.query(models.PointHistoryData).filter(models.PointHistoryData.customer_id == user_id).all()
        point_history_list = []
        for point_history in point_history:
            point_history_list.append(point_history.to_json())
        return JSONResponse(content={"message": "Point history retrieved successfully", "data": point_history_list})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving point history: {str(e)}")
    

@router.get("/get-current-point-by-user-id/{user_id}")
async def get_current_point_by_user_id(user_id: int):
    db = get_db_direct()
    try:
        point_history = db.query(models.PointHistoryData).filter(
            models.PointHistoryData.customer_id == user_id,
            models.PointHistoryData.is_expired == False,
            models.PointHistoryData.is_increase == True,
            models.PointHistoryData.available_amount > 0
        ).all()
        
        total_amount = sum(ph.available_amount for ph in point_history)
        
        return JSONResponse(content={"message": "Current point retrieved successfully", "data": total_amount})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving current point: {str(e)}")

@router.get("/get-total-point-by-user-id/{user_id}")
async def get_total_point_by_user_id(user_id: int):
    db = get_db_direct()
    try:
        point_history = db.query(models.PointHistoryData).filter(
            models.PointHistoryData.customer_id == user_id,
            models.PointHistoryData.is_increase == True
        ).all()
        
        total_point = sum(ph.amount for ph in point_history)
        
        return JSONResponse(content={"message": "Total point retrieved successfully", "data": total_point})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving total point: {str(e)}")

#한달 이내 만료 포인트 조회
@router.get("/get-expire-point-by-user-id/{user_id}")
async def get_expire_point_by_user_id(user_id: int):
    db = get_db_direct()
    try:
        point_history = db.query(models.PointHistoryData).filter(
            models.PointHistoryData.customer_id == user_id,
            models.PointHistoryData.is_expired == False,
            models.PointHistoryData.is_increase == True,
            models.PointHistoryData.available_amount > 0,
            models.PointHistoryData.expire_at < (datetime.now() + timedelta(days=30))
        ).all()
        
        total_point = sum(ph.available_amount for ph in point_history)
        
        return JSONResponse(content={"message": "Expiring point retrieved successfully", "data": total_point})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving expiring point: {str(e)}")