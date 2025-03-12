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
    """QR 코드 생성"""
    
    import main
    import ssl
    from fastapi import HTTPException

    qr_request_uri = f"http://dealerdesk.app/api/game/qr/{game_id}/{main.socket_controller.store_host_name}"
    
    # SSL 인증서 검증을 비활성화하는 컨텍스트 생성
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    session = requests.Session()
    try:
        response = session.get(qr_request_uri, headers={"Accept-Encoding": "gzip", "Authorization": f"Bearer {main.socket_controller.bearer_token}"})
        response.raise_for_status()  # HTTPError가 발생하면 예외를 발생시킴
        return JSONResponse(content={"message": "QR 코드 생성 완료", "data": response.json()["data"]})
    except requests.exceptions.HTTPError as http_err:
        print(response.json())
        return JSONResponse(content={"message": "QR 코드 생성 실패"}, status_code=response.status_code)
    except Exception as err:
        return JSONResponse(content={"message": "QR 코드 생성 중 오류 발생", "error": str(err)}, status_code=500)
