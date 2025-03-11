from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
import asyncio
import uuid

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
    """사용자 ID로 포인트를 추가합니다."""
    db = get_db_direct()
    try:
        user = db.query(models.UserData).filter(models.UserData.id == user_id).first()
        if not user:
            return JSONResponse(
                content={"response": 404, "message": "사용자를 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
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
        
        # 소켓 이벤트 전송 부분을 비동기적으로 처리
        try:
            import main
            await main.socket_controller.add_point_history_data(point_history)
        except Exception as socket_error:
            print(f"소켓 이벤트 전송 중 오류 발생: {str(socket_error)}")
        
        return JSONResponse(
            content={"response": 200, "message": "포인트가 성공적으로 추가되었습니다"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            content={"response": 500, "message": f"포인트 추가 중 오류 발생: {str(e)}"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.get("/get-point-history-by-user-id/{user_id}")
async def get_point_history_by_user_id(user_id: int):
    """사용자 ID로 포인트 내역을 조회합니다."""
    db = get_db_direct()
    try:
        # 쿼리 최적화 - 필요한 필드만 선택
        point_history_records = db.query(models.PointHistoryData).filter(
            models.PointHistoryData.customer_id == user_id
        ).order_by(models.PointHistoryData.created_at.desc()).all()
        
        # 리스트 컴프리헨션으로 변환 성능 향상
        point_history_list = [record.to_json() for record in point_history_records]
        
        return JSONResponse(
            content={"response": 200, "message": "포인트 내역 조회 성공", "data": point_history_list},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "message": f"포인트 내역 조회 중 오류 발생: {str(e)}"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.get("/get-current-point-by-user-id/{user_id}")
async def get_current_point_by_user_id(user_id: int):
    """사용자 ID로 현재 사용 가능한 포인트를 조회합니다."""
    db = get_db_direct()
    try:
        # 쿼리 최적화 - 합계 계산을 DB에서 처리
        total_amount_records = db.query(models.PointHistoryData).filter(
            models.PointHistoryData.customer_id == user_id,
            models.PointHistoryData.is_expired == False,
            models.PointHistoryData.is_increase == True,
            models.PointHistoryData.available_amount > 0
        ).all()
        
        total_amount = sum(point.available_amount for point in total_amount_records)
        print(f"total_amount : {total_amount}")  # 로그 출력
        
        return JSONResponse(
            content={"response": 200, "message": "현재 포인트 조회 성공", "data": total_amount},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        print(f"현재 포인트 조회 중 오류 발생: {str(e)}")  # 오류 로그 출력
        return JSONResponse(
            content={"response": 500, "message": f"현재 포인트 조회 중 오류 발생: {str(e)}"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()
@router.get("/get-total-point-by-user-id/{user_id}")
async def get_total_point_by_user_id(user_id: int):
    """사용자 ID로 총 적립된 포인트를 조회합니다."""
    db = get_db_direct()
    try:
        # 쿼리 최적화 - 합계 계산을 DB에서 처리 
        total_amount_records = db.query(models.PointHistoryData).filter(
            models.PointHistoryData.customer_id == user_id,
            models.PointHistoryData.is_increase == True,
            models.PointHistoryData.available_amount > 0
        ).all()
         
        total_amount = sum(point.available_amount for point in total_amount_records)
        print(f"total_point : {total_amount}")
        return JSONResponse(
            content={"response": 200, "message": "총 포인트 조회 성공", "data": total_amount},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "message": f"총 포인트 조회 중 오류 발생: {str(e)}"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.get("/get-expire-point-by-user-id/{user_id}")
async def get_expire_point_by_user_id(user_id: int):
    """사용자 ID로 한 달 이내 만료되는 포인트를 조회합니다."""
    db = get_db_direct()
    try:
        # 쿼리 최적화 - 합계 계산을 DB에서 처리
        total_point = db.query(
            models.PointHistoryData.customer_id == user_id,
            models.PointHistoryData.is_expired == False,
            models.PointHistoryData.is_increase == True,
            models.PointHistoryData.available_amount > 0,
            models.PointHistoryData.expire_at < (datetime.now() + timedelta(days=30))
        ).all()
        
        
        total_point_amount = sum(point.available_amount for point in total_point)
        print(f"total_point : {total_point_amount}")
        return JSONResponse(
            content={"response": 200, "message": "만료 예정 포인트 조회 성공", "data": total_point_amount},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "message": f"만료 예정 포인트 조회 중 오류 발생: {str(e)}"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()