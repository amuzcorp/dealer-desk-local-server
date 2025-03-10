from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
import requests
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
    prefix="/qr",
    tags=["qr"]
)

@router.get("/create-qr-code")
async def create_qr_code(game_id: int):
    import main
    """QR 코드 생성"""
    
    import main
    qr_request_uri = f"http://{main.socket_controller.store_host_name}.dealer-desk.dev.amuz.kr/api/game/qr"
    body = {
        "game_id": game_id
    }
    
    # SSL 인증서 검증을 비활성화하는 컨텍스트 생성
    import ssl
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    session = requests.Session()
    response = session.get(qr_request_uri, json=body)
    if response.status_code == 200:
        print(response.json())
        return JSONResponse(content={"message": "QR 코드 생성 완료", "data": response.json()})
    else:
        return JSONResponse(content={"message": "QR 코드 생성 실패", "data": response.json()})
