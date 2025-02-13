from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Optional

class TableDataBase(BaseModel):
    table_title: str
    position: Dict[str, float] = {"x": 0, "y": 0}
    size: Dict[str, float] = {"width": 100, "height": 100}

class TableDataCreate(TableDataBase):
    pass

class TableDataUpdate(BaseModel):
    table_title: Optional[str] = None
    position: Optional[Dict[str, float]] = None
    size: Optional[Dict[str, float]] = None

class TableData(TableDataBase):
    id: Optional[int] = None
    current_player_count: int
    max_player_count: int
    
    class Config:
        from_attributes = True 