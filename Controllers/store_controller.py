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
    prefix="/store",
    tags=["store"]
)

@router.post("/store-open")
async def store_open(store_id: int, db: Session = Depends(get_db)):
    store_data = db.query(models.StoreData).filter(models.StoreData.id == store_id).first()
    if not store_data:
        raise HTTPException(status_code=404, detail="Store data not found")
    
    store_data.status = "OPEN"
    db.commit()