import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, WebSocket, Query
from sqlalchemy import DateTime
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

import json 
import sys
import os
from dataclasses import dataclass
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Controllers import user_controller
import models
import schemas
from database import get_db, get_db_direct

router = APIRouter(
    prefix="/purchase",
    tags=["purchase"]
)

# 구매 데이터 조회
@router.get("/get-purchase-data")
async def get_purchase_data(db: Session = Depends(get_db)):
    purchase_data = db.query(models.PurchaseData).filter(models.PurchaseData.payment_status == "SUCCESS").all()
    
    return_data = []
    for data in purchase_data:
        formatted_data = data.to_json()
        return_data.append(formatted_data)

    return JSONResponse(
        content={
            "response": 200,
            "message": "Purchase data retrieved successfully",
            "data": return_data
        },
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    
# 구매 데이터 컨트롤 - WAITING to PAYMENT_CHIP
@router.get("/waiting-to-payment-chip/{purchase_id}")
async def waiting_to_payment_chip(purchase_id: int, db: Session = Depends(get_db)):
    purchase_data = db.query(models.PurchaseData).filter(models.PurchaseData.id == purchase_id).first()
    if not purchase_data:
        raise HTTPException(status_code=404, detail="Purchase data not found")
    
    purchase_data.payment_status = "SUCCESS"
    purchase_data.status = "CHIP_WAITING"
    db.commit()
    
    import main
    await main.socket_controller.update_purchase_data_payment_success(purchase_data)
    
    await user_controller.update_user_in_game_join_count(game_id=purchase_data.game_id, user_id=purchase_data.customer_id, is_purchase=True, db=db)
    
    return JSONResponse(
        content={
            "response": 200,
            "message": "Purchase data updated successfully",
            "data": purchase_data.to_json()
        },
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

# 구매 데이터 컨트롤 - CHIP_WAITING to SUCCESS
@router.get("/chip-waiting-to-success/{purchase_id}")
async def chip_waiting_to_success(purchase_id: int, db: Session = Depends(get_db)):
    purchase_data = db.query(models.PurchaseData).filter(models.PurchaseData.id == purchase_id).first()
    if not purchase_data:
        raise HTTPException(status_code=404, detail="Purchase data not found")
    
    purchase_data.status = "SUCCESS"
    db.commit()
    
    import main
    await main.socket_controller.update_purchase_data_chip_success(purchase_data)
    
    return JSONResponse(
        content={
            "response": 200,
            "message": "Purchase data updated successfully",
            "data": purchase_data
        },
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

@router.get("/get-purchase-data-by-user-id/{user_id}")
async def get_purchase_data_by_user_id(user_id: int, db: Session = Depends(get_db)):
    purchase_data = db.query(models.PurchaseData).filter(models.PurchaseData.customer_id == user_id, models.PurchaseData.payment_status == "SUCCESS").all()
    return_data = []
    for data in purchase_data:
        formatted_data = data.to_json()
        return_data.append(formatted_data)
    return JSONResponse(
        content={"response": 200, "message": "Purchase data retrieved successfully", "data": return_data},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

@router.get("/get-purchase-data-by-game-id/{game_id}")
async def get_purchase_data_by_game_id(game_id: int, db: Session = Depends(get_db)):
    purchase_data = db.query(models.PurchaseData).filter(models.PurchaseData.game_id == game_id, models.PurchaseData.payment_status == "SUCCESS").all()
    return_data = []
    for data in purchase_data:
        formatted_data = data.to_json()
        return_data.append(formatted_data)
    return JSONResponse(
        content={"response": 200, "message": "Purchase data retrieved successfully", "data": return_data},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
 
@router.get("/get-purchase-data-by-date/{startTime}/{endTime}")
async def get_purchase_data_by_date(startTime: str, endTime: str, db: Session = Depends(get_db)):
    try:
        startTime_dateTime = datetime.fromisoformat(startTime)
        endTime_dateTime = datetime.fromisoformat(endTime)
        
        purchase_data = db.query(models.PurchaseData).filter(
            models.PurchaseData.purchased_at >= startTime_dateTime,
            models.PurchaseData.purchased_at <= endTime_dateTime,
            models.PurchaseData.payment_status == "SUCCESS"
        ).all()
        
        return_data = []
        for data in purchase_data:
            formatted_data = data.to_json()
            return_data.append(formatted_data)
            
        return JSONResponse(
            content={"response": 200, "message": "Purchase data retrieved successfully", "data": return_data},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except ValueError:
        return JSONResponse(
            content={"response": 400, "message": "Invalid date format. Please use ISO format (YYYY-MM-DDTHH:MM:SS)"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        
@router.get("/get-paginated-purchase-data")
async def get_paginated_purchase_data(page: int = 1, page_size: int = 20):
    """페이지네이션된 구매 데이터 조회"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        # 모든 구매 데이터 조회
        query = db.query(models.PurchaseData)
        
        # 총 레코드 수 계산
        total_records = query.count()
        
        # 페이지네이션 적용
        query = query.order_by(models.PurchaseData.purchased_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        # 결과 가져오기
        purchase_data = query.all()
        
        # 총 페이지 수 계산
        total_pages = (total_records + page_size - 1) // page_size
        
        # 결과 포맷팅
        result = []
        for item in purchase_data:
            purchase_json = item.to_json()
            purchase_json["purchased_at"] = purchase_json["purchased_at"].isoformat()
            result.append(purchase_json)
        
        return JSONResponse(
            content={
                "response": 200, 
                "data": {
                    "items": result,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages,
                    "total_records": total_records
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