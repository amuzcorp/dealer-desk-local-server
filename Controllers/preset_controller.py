from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/presets",
    tags=["presets"]
)

@router.post("/save-preset")
async def save_preset(preset: schemas.PresetData, db: Session = Depends(get_db)):
    try:
        if preset.id == -1:
            # 새로운 프리셋 생성
            db_preset = models.PresetData(
                preset_name=preset.preset_name,
                time_table_data=preset.time_table_data,
                buy_in_price=preset.buy_in_price,
                re_buy_in_price=preset.re_buy_in_price,
                starting_chip=preset.starting_chip,
                rebuyin_payment_chips=preset.rebuyin_payment_chips,
                rebuyin_number_limits=preset.rebuyin_number_limits,
                addon_data=preset.addon_data,
                prize_settings=preset.prize_settings,
                rebuy_cut_off=preset.rebuy_cut_off
            )
            db.add(db_preset)
        else:
            # 기존 프리셋 업데이트
            existing_preset = db.query(models.PresetData).filter(models.PresetData.id == preset.id).first()
            if not existing_preset:
                return JSONResponse(
                    content={"response": 404, "message": "Preset not found"},
                    headers={"Content-Type": "application/json; charset=utf-8"}
                )
            
            preset_data = jsonable_encoder(preset)
            for key, value in preset_data.items():
                if key != "id":  # id는 업데이트하지 않음
                    setattr(existing_preset, key, value)

        db.commit()
        
        return JSONResponse(
            content={"response": 200, "message": "Preset saved successfully"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            content={"response": 500, "error": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )

@router.get("/", response_model=List[schemas.PresetData])
async def get_presets(db: Session = Depends(get_db)):
    presets = db.query(models.PresetData).all()
    if not presets:
        return JSONResponse(
            content={"response": 201, "message": "No presets found"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    preset_list = []
    for preset in presets:
        preset_list.append(jsonable_encoder(preset.to_json()))
    
    return JSONResponse(
        content={"response": 200, "data": preset_list},
        headers={"Content-Type": "application/json; charset=utf-8"}
    ) 
    
@router.delete("/delete-preset/{preset_id}")
async def delete_preset(preset_id: int, db: Session = Depends(get_db)):
    preset = db.query(models.PresetData).filter(models.PresetData.id == preset_id).first()
    if not preset:
        return JSONResponse(
            content={"response": 404, "message": "Preset not found"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    db.delete(preset)
    db.commit()
    
@router.put("/update-preset/{preset_id}")
async def update_preset(preset_id: int, preset: schemas.PresetData, db: Session = Depends(get_db)):
    existing_preset = db.query(models.PresetData).filter(models.PresetData.id == preset_id).first()
    if not existing_preset:
        return JSONResponse(
            content={"response": 404, "message": "Preset not found"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        
    print(existing_preset.prize_settings)
    
    preset_data = jsonable_encoder(preset)
    for key, value in preset_data.items():
        if key != "id":
            setattr(existing_preset, key, value)
    
    db.commit()
    
    return JSONResponse(
        content={"response": 200, "message": "Preset updated successfully"},
        headers={"Content-Type": "application/json; charset=utf-8"} 
    )