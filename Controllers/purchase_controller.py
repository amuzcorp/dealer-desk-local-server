import asyncio
from datetime import datetime, timedelta
import uuid
from fastapi import APIRouter, Depends, HTTPException, WebSocket, Query
from sqlalchemy import DateTime
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse

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
async def get_purchase_data():
    """모든 구매 데이터 조회"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        purchase_data = db.query(models.PurchaseData).all()
        
        if not purchase_data:
            return JSONResponse(
                content={"response": 201, "message": "구매 데이터가 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 결과 포맷팅
        result = []
        for purchase in purchase_data:
            purchase_json = purchase.to_json()
            result.append(purchase_json)
            
        return JSONResponse(
            content={"response": 200, "data": result},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()
    
# 구매 데이터 컨트롤 - WAITING to SUCCESS
# 결제 완료 처리(매장 결제)
@router.get("/waiting-to-payment-chip/{purchase_id}")
async def waiting_to_payment_chip(purchase_id: int):
    """구매 상태를 '결제 대기'에서 '칩 대기'로 변경"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        # 구매 데이터 조회
        purchase : models.PurchaseData = db.query(models.PurchaseData).filter(models.PurchaseData.id == purchase_id).first()
        if not purchase:
            return JSONResponse(
                content={"response": 404, "message": "구매 데이터를 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 상태 업데이트
        purchase.payment_status = "SUCCESS"
        purchase.status = "SUCCESS"
        db.commit()
        db.refresh(purchase)
        
        import main
        await main.socket_controller.update_purchase_data_payment_success(purchase)
        
        return JSONResponse(
            content={"response": 200, "message": "결제 상태가 업데이트되었습니다", "data": purchase.to_json()},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

# 구매 데이터 컨트롤 - CHIP_WAITING to SUCCESS
@router.get("/chip-waiting-to-success/{purchase_id}")
async def chip_waiting_to_success(purchase_id: int):
    """구매 상태를 '칩 대기'에서 '성공'으로 변경"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        # 구매 데이터 조회
        purchase = db.query(models.PurchaseData).filter(models.PurchaseData.id == purchase_id).first()
        if not purchase:
            return JSONResponse(
                content={"response": 404, "message": "구매 데이터를 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 상태 업데이트
        purchase.status = "SUCCESS"
        db.commit()
        db.refresh(purchase)
        
        return JSONResponse(
            content={"response": 200, "message": "구매 상태가 업데이트되었습니다", "data": purchase.to_json()},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.get("/get-purchase-data-by-user-id/{user_id}")
async def get_purchase_data_by_user_id(user_id: int):
    """사용자별 구매 데이터 조회"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        # 사용자별 구매 데이터 조회
        purchase_data = db.query(models.PurchaseData).filter(models.PurchaseData.customer_id == user_id).all()
        
        if not purchase_data:
            return JSONResponse(
                content={"response": 201, "message": "해당 사용자의 구매 데이터가 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 결과 포맷팅
        result = []
        for purchase in purchase_data:
            purchase_json = purchase.to_json()
            result.append(purchase_json)
            
        return JSONResponse(
            content={"response": 200, "data": result},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.get("/get-purchase-data-by-game-id/{game_id}")
async def get_purchase_data_by_game_id(game_id: int):
    """게임별 구매 데이터 조회"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        # 게임별 구매 데이터 조회
        purchase_data = db.query(models.PurchaseData).filter(models.PurchaseData.game_id == game_id).all()
        
        if not purchase_data:
            return JSONResponse(
                content={"response": 201, "message": "해당 게임의 구매 데이터가 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 결과 포맷팅
        result = []
        for purchase in purchase_data:
            purchase_json = purchase.to_json()
            result.append(purchase_json)
        print("resulr length : ", len(result))
        return JSONResponse(
            content={"response": 200, "data": result},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()
 
@router.get("/get-purchase-data-by-date/{startTime}/{endTime}")
async def get_purchase_data_by_date(startTime: str, endTime: str, page: int = 1, page_size: int = 10):
    """날짜 범위로 구매 데이터 조회 (페이지네이션 적용)"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        # 날짜 문자열을 datetime 객체로 변환
        start_date = datetime.fromisoformat(startTime.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(endTime.replace('Z', '+00:00'))
        
        # 전체 데이터 개수 조회
        total_count = db.query(models.PurchaseData).filter(
            models.PurchaseData.purchased_at >= start_date,
            models.PurchaseData.purchased_at <= end_date
        ).count()
        
        # 총 페이지 수 계산
        total_pages = (total_count + page_size - 1) // page_size
        
        # 날짜 범위로 구매 데이터 조회 (페이지네이션 적용)
        purchase_data = db.query(models.PurchaseData).filter(
            models.PurchaseData.purchased_at >= start_date
        ).filter(
            models.PurchaseData.purchased_at <= end_date
        ).filter(
            models.PurchaseData.status == "SUCCESS"
        ).order_by(
            models.PurchaseData.purchased_at.desc()
        ).all()
        
        # 페이지네이션 적용
        purchase_data = purchase_data[(page - 1) * page_size:page * page_size]
        
        if not purchase_data:
            return JSONResponse(
                content={
                    "response": 201, 
                    "message": "해당 기간에 구매 데이터가 없습니다",
                    "pagination": {
                        "total_count": 0,
                        "total_pages": 0,
                        "current_page": page,
                        "page_size": page_size,
                        "total_prize" : 0
                    }
                },
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 결과 포맷팅
        result = []
        for purchase in purchase_data:
            purchase_json = purchase.to_json()
            result.append(purchase_json)
        
        total_prize = 0
        for purchase in purchase_data:
            total_prize += purchase.price
        
        print("total_prize : ", total_prize) 
        return JSONResponse(
            content={
                "response": 200, 
                "data": result,
                "pagination": {
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "current_page": page,
                    "page_size": page_size,
                    "total_prize" : total_prize
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
@router.put("/create-buyin-purchase-data-by-user-id/")
async def create_buyin_purchase_data_by_user_id(user_id: int, game_id: int):
    """사용자별 구매 데이터 생성"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        # 사용자 데이터 조회
        user = db.query(models.UserData).filter(models.UserData.id == user_id).first()
        if not user:
            return JSONResponse(
                content={"response": 404, "message": "사용자 데이터를 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        # 게임 데이터 조회
        game : models.GameData = db.query(models.GameData).filter(models.GameData.id == game_id).first()
        if not game:
            return JSONResponse(
                content={"response": 404, "message": "게임 데이터를 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        # 구매 데이터 생성
        purchase = models.PurchaseData(
            payment_type="LOCAL_PAY",
            purchase_type="BUYIN",
            customer_id=user_id,
            game_id=game_id,
            uuid=str(uuid.uuid4()),
            purchased_at=datetime.now(),
            item="BUYIN",
            payment_status="SUCCESS",
            status="SUCCESS",
            price=game.buy_in_price,
            used_points=0
        )
        
        db.add(purchase)
        db.commit()
        db.refresh(purchase)
        
        import main
        await main.socket_controller.local_purchase_data(purchase)
        
        return JSONResponse(
            content={"response": 200, "message": "구매 데이터가 생성되었습니다", "data": purchase.to_json()},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.put("/create-rebuyin-purchase-data-by-user-id/")
async def create_rebuyin_purchase_data_by_user_id(user_id: int, game_id: int):
    """사용자별 구매 데이터 생성"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        # 사용자 데이터 조회
        user = db.query(models.UserData).filter(models.UserData.id == user_id).first()
        if not user:
            return JSONResponse(
                content={"response": 404, "message": "사용자 데이터를 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        # 게임 데이터 조회
        game : models.GameData = db.query(models.GameData).filter(models.GameData.id == game_id).first()
        if not game:
            return JSONResponse(
                content={"response": 404, "message": "게임 데이터를 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        # 구매 데이터 생성
        purchase = models.PurchaseData(
            payment_type="LOCAL_PAY",
            purchase_type="REBUYIN",
            customer_id=user_id,
            game_id=game_id,
            uuid=str(uuid.uuid4()),
            purchased_at=datetime.now(),
            item="BUYIN",
            payment_status="SUCCESS",
            status="SUCCESS",
            price=game.re_buy_in_price,
            used_points=0
        )

        db.add(purchase)
        db.commit()
        db.refresh(purchase)
        
        import main
        await main.socket_controller.local_purchase_data(purchase)
        
        return JSONResponse(
            content={"response": 200, "message": "구매 데이터가 생성되었습니다", "data": purchase.to_json()},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()


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