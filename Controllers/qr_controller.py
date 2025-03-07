from datetime import datetime
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
    prefix="/tables",
    tags=["tables"]
)

@router.post("/create-qr-code")
async def create_qr_code(qr_code: schemas.QrCode):
    import main
    """QR 코드 생성"""
    
    tenant_host = main.socket_controller
    return JSONResponse(content={"message": "QR 코드 생성 완료"})
