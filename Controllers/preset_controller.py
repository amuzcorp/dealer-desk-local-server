from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models
import schemas
from database import get_db, get_db_direct

router = APIRouter(
    prefix="/presets",
    tags=["presets"]
)

@router.post("/create-preset")
async def create_preset(preset_data: schemas.PresetData):
    """프리셋 생성 엔드포인트"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        preset = models.PresetData(
            preset_name=preset_data.preset_name,
            time_table_data=preset_data.time_table_data,
            buy_in_price=preset_data.buy_in_price,
            re_buy_in_price=preset_data.re_buy_in_price,
            starting_chip=preset_data.starting_chip,
            rebuyin_payment_chips=preset_data.rebuyin_payment_chips,
            rebuyin_number_limits=preset_data.rebuyin_number_limits,
            addon_data=preset_data.addon_data,
            prize_settings=preset_data.prize_settings,
            rebuy_cut_off=preset_data.rebuy_cut_off,
        )
        db.add(preset)
        db.commit()
        db.refresh(preset)
        import main
        await main.socket_controller.save_preset(presets=preset)
        return JSONResponse(
            content={"response": 200, "message": "프리셋이 저장되었습니다", "id": preset.id},
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

@router.put("/update-preset/{preset_id}")
async def update_preset(preset_id: int, preset_data: schemas.PresetData):
    """프리셋 업데이트 엔드포인트"""
    # 직접 세션 가져오기
    db :Session = get_db_direct()
    try:
        preset = db.query(models.PresetData).filter(models.PresetData.id == preset_id).first()
        if not preset:
            return JSONResponse(
                content={"response": 404, "message": "프리셋을 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        
        # 프리셋 데이터 직접 업데이트
        preset.preset_name = preset_data.preset_name
        preset.time_table_data = preset_data.time_table_data
        preset.buy_in_price = preset_data.buy_in_price
        preset.re_buy_in_price = preset_data.re_buy_in_price
        preset.starting_chip = preset_data.starting_chip
        preset.rebuyin_payment_chips = preset_data.rebuyin_payment_chips
        preset.rebuyin_number_limits = preset_data.rebuyin_number_limits
        preset.addon_data = preset_data.addon_data
        preset.prize_settings = preset_data.prize_settings
        preset.rebuy_cut_off = preset_data.rebuy_cut_off

        db.commit()
        db.refresh(preset)
        
        # 데이터 검증을 위한 로깅 추가
        print("Updated preset data:")
        print(f"preset_name: {preset.preset_name}")
        print(f"time_table_data: {preset.time_table_data}")
        print(f"buy_in_price: {preset.buy_in_price}")
        print(f"re_buy_in_price: {preset.re_buy_in_price}")
        print(f"starting_chip: {preset.starting_chip}")
        print(f"rebuyin_payment_chips: {preset.rebuyin_payment_chips}")
        print(f"rebuyin_number_limits: {preset.rebuyin_number_limits}")
        print(f"addon_data: {preset.addon_data}")
        print(f"prize_settings: {preset.prize_settings}")
        print(f"rebuy_cut_off: {preset.rebuy_cut_off}")
        
        import main
        await main.socket_controller.save_preset(presets=preset)
        
        return JSONResponse(
            content={
                "response": 200, 
                "message": "프리셋이 업데이트되었습니다",
                "data": preset.to_json() # 업데이트된 데이터 반환
            },
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        db.rollback()
        print(f"Error updating preset: {str(e)}")  # 에러 로깅 추가
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.get("/")
async def get_presets():
    """모든 프리셋 조회 엔드포인트"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        presets = db.query(models.PresetData).all()
        
        if not presets:
            return JSONResponse(
                content={"response": 200, "data": []},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        preset_list = []
        for preset in presets:
            preset_list.append(jsonable_encoder(preset.to_json()))
            
        return JSONResponse(
            content={"response": 200, "data": preset_list},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.get("/{preset_id}")
async def get_preset(preset_id: int):
    """특정 프리셋 조회 엔드포인트"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        preset = db.query(models.PresetData).filter(models.PresetData.id == preset_id).first()
        
        if not preset:
            return JSONResponse(
                content={"response": 404, "message": "프리셋을 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        return JSONResponse(
            content={"response": 200, "data": jsonable_encoder(preset.to_json())},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        return JSONResponse(
            content={"response": 500, "message": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    finally:
        db.close()

@router.delete("/{preset_id}")
async def delete_preset(preset_id: int):
    """프리셋 삭제 엔드포인트"""
    # 직접 세션 가져오기
    db = get_db_direct()
    try:
        preset = db.query(models.PresetData).filter(models.PresetData.id == preset_id).first()
        
        if not preset:
            return JSONResponse(
                content={"response": 404, "message": "프리셋을 찾을 수 없습니다"},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        db.delete(preset)
        db.commit()
        
        import main
        await main.socket_controller.delete_preset(preset_id)
        return JSONResponse(
            content={"response": 200, "message": "프리셋이 삭제되었습니다"},
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