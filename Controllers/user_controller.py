from datetime import datetime
import random
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
from database import get_db

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/get-user-list")
async def get_user_list(db: Session = Depends(get_db)):
    user_list = db.query(models.UserData).filter(models.UserData.phone_number != None).all()
    user_list_json = []
    for user in user_list:
        user_list_json.append(user.to_json())
    return JSONResponse(
        content={"response": 200, "message": "User list", "data": user_list_json},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    
@router.post("/create-guest-user")
async def create_guest_user(db: Session = Depends(get_db)):
    user_data = models.UserData(
        name=f"guest{random.randint(10000, 99999)}",
        phone_number=None,
    )
    db.add(user_data)
    db.commit()
    db.refresh(user_data)
    return JSONResponse(
        content={"response": 200, "message": "User created", "data": user_data.to_json()},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

@router.post("/create-user-data")
async def create_user_data(user_data: schemas.UserDataCreate, db: Session = Depends(get_db)):
    try:
        # 네, id 값은 데이터베이스에서 자동으로 생성됩니다.
        # UserData 모델에서 id는 자동 증가(auto-increment) 필드로 설정되어 있습니다.
        db_user_data = models.UserData(**user_data.model_dump())
        db.add(db_user_data)
        db.commit()
        db.refresh(db_user_data)  # 이 단계에서 자동 생성된 id 값이 db_user_data에 반영됩니다
        return JSONResponse(
            content={"response": 200, "message": "User created", "data": db_user_data.to_json()}, 
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "message": "User creation failed", "data": str(e)}, 
            headers={"Content-Type": "application/json; charset=utf-8"}
        )

@router.post("/update-user-data")
async def update_user_data(user_data: schemas.UserDataUpdate, db: Session = Depends(get_db)):
    db_user_data = db.query(models.UserData).filter(models.UserData.id == user_data.id).first()
    if not db_user_data:
        return JSONResponse(
            content={"response": 404, "message": "User not found"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    db.query(models.UserData).filter(models.UserData.id == user_data.id).update(user_data.model_dump())
    db.commit()
    db.refresh(db_user_data)
    return JSONResponse(
        content={"response": 200, "message": "User updated", "data": db_user_data.to_json()},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    
@router.post("/add-point-for-user")
async def add_point_for_user(body: dict, db: Session = Depends(get_db)):
    user_id = body.get("user_id")
    point_history = body.get("point_history")
    db_user_data = db.query(models.UserData).filter(models.UserData.id == user_id).first()
    if not db_user_data:
        return JSONResponse(
            content={"response": 404, "message": "사용자를 찾을 수 없습니다"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    # 쿼리 결과가 아닌 실제 사용자 객체를 사용
    point_to_add = point_history.get("point", 0)
    db_user_data.point += point_to_add
    db_user_data.total_point += point_to_add
    
    # 포인트 히스토리가 None인 경우 빈 리스트로 초기화
    if db_user_data.point_history is None:
        db_user_data.point_history = []
    
    # 기존 히스토리를 복사하고 새 항목 추가
    current_history = db_user_data.point_history.copy() if db_user_data.point_history else []
    current_history.append(point_history)
    
    # 명시적으로 point_history 업데이트
    db_user_data.point_history = current_history
    
    # 변경사항 저장 전 로그 출력
    # print(f"포인트 히스토리 업데이트: {db_user_data.point_history}")
    
    db.commit()
    db.refresh(db_user_data)
    
    # 저장 후 확인
    # print(f"저장 후 포인트 히스토리: {db_user_data.point_history}")
    
    return JSONResponse(
        content={"response": 200, "message": "사용자 포인트가 업데이트되었습니다", "data": db_user_data.to_json()},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )