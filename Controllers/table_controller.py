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
from database import get_db

router = APIRouter(
    prefix="/tables",
    tags=["tables"]
)

@router.get("/", response_model=List[schemas.TableData])
async def get_tables(db: Session = Depends(get_db)):
    tables = db.query(models.TableData).all()
    if not tables:
        return JSONResponse(
            content={"response": 201, "message": "Table not found"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    
    json_data_tables = []
    for table in tables:
        modelTable = models.TableData(
            id = table.id,  
            table_title = table.table_title,
            current_player_count = table.current_player_count,
            max_player_count = table.max_player_count,
            position = table.position,
            size = table.size
        )
        json_data_tables.append(jsonable_encoder(modelTable.to_json()))
    return JSONResponse(
        content={"response": 200, "data": json_data_tables},
        headers={"Content-Type": "application/json; charset=utf-8"},
        media_type="application/json"
    )

@router.post("/save-table")
async def save_table(tables: List[schemas.TableData], db: Session = Depends(get_db)):
    result = []
    
    existing_table_ids = set(table.id for table in tables if table.id is not None)
    
    tables_to_delete = db.query(models.TableData).filter(
        ~models.TableData.id.in_(existing_table_ids) if existing_table_ids else True
    ).all()
    
    for table_to_delete in tables_to_delete:
        db.delete(table_to_delete)
    
    for table in tables:
        table_data = jsonable_encoder(table)
        existing_table = db.query(models.TableData).filter(models.TableData.id == table.id).first()
        
        if existing_table:
            for key, value in table_data.items():
                setattr(existing_table, key, value)
            result.append(existing_table)
        else:
            db_table = models.TableData(**table_data)
            db.add(db_table)
            result.append(db_table)
    
    try:
        db.commit()
        for table in result:
            db.refresh(table)
        
        return JSONResponse(
            content={"response": 200, "data": "Success Saved Tables"},
            headers={"Content-Type": "application/json; charset=utf-8"},
            media_type="application/json"
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            content={"response": 500, "error": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"},
            media_type="application/json"
        )
 