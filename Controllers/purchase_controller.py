import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, WebSocket
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
    purchase_data = db.query(models.PurchaseData).filter(models.PurchaseData.user_id == user_id).all()
    return_data = []
    for data in purchase_data:
        formatted_data = data.to_json()
        return_data.append(formatted_data)
    return JSONResponse(
        content={"response": 200, "message": "Purchase data retrieved successfully", "data": return_data},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )