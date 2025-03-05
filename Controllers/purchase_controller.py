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

import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/purchase",
    tags=["purchase"]
)

# 구매 데이터 조회
@router.get("/get-purchase-data")
async def get_purchase_data(db: Session = Depends(get_db)):
    purchase_data = db.query(models.PurchaseData).all()
    
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
    
    purchase_data.status = "PAYMENT_CHIP"
    db.commit()
    return JSONResponse(
        content={
            "response": 200,
            "message": "Purchase data updated successfully",
            "data": purchase_data
        },
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

# 구매 데이터 컨트롤 - PAYMENT_CHIP to SUCCESS
@router.get("/payment-chip-to-success/{purchase_id}")
async def payment_chip_to_success(purchase_id: int, db: Session = Depends(get_db)):
    purchase_data = db.query(models.PurchaseData).filter(models.PurchaseData.id == purchase_id).first()
    if not purchase_data:
        raise HTTPException(status_code=404, detail="Purchase data not found")
    
    purchase_data.status = "SUCCESS"
    db.commit()
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
    purchase_data = db.query(models.PurchaseData).filter(models.PurchaseData.customer_id == user_id).all()
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
    purchase_data = db.query(models.PurchaseData).filter(models.PurchaseData.game_id == game_id).all()
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
            models.PurchaseData.purchased_at <= endTime_dateTime
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
async def get_paginated_purchase_data(
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    page_size: int = Query(default=10, ge=1, le=100, description="페이지당 항목 수"),
    status: Optional[str] = Query(default=None, description="구매 상태 필터"),
    db: Session = Depends(get_db)
):
    # 기본 쿼리 생성
    query = db.query(models.PurchaseData)
    
    # 상태 필터 적용
    if status:
        query = query.filter(models.PurchaseData.status == status)
    
    # ID 기준 내림차순 정렬 (최신 데이터가 먼저 오도록)
    query = query.order_by(models.PurchaseData.id.desc())
    
    # 전체 아이템 수 계산
    total_items = query.count()
    
    # 페이지네이션 적용
    skip = (page - 1) * page_size
    query = query.offset(skip).limit(page_size)
    
    # 결과 가져오기
    purchase_data = query.all()
    
    # 응답 데이터 포맷팅
    return_data = []
    for data in purchase_data:
        formatted_data = data.to_json()
        return_data.append(formatted_data)
    
    # 메타데이터 계산
    total_pages = (total_items + page_size - 1) // page_size
    
    return JSONResponse(
        content={
            "response": 200,
            "message": "구매 데이터를 성공적으로 조회했습니다",
            "data": {
                "items": return_data,
                "metadata": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1
                }
            }
        },
        headers={"Content-Type": "application/json; charset=utf-8"}
    )