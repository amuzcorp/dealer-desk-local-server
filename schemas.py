from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Optional, Any, List

"""
테이블 데이터
"""
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
        
        
"""
디바이스 데이터
"""
class DeviceDataBase(BaseModel):
    id: Optional[int] = None
    name: str
    device_uid: str
    
class RequestDeviceDataCreate(DeviceDataBase):
    pass

class RequestDeviceDataUpdate(DeviceDataBase):
    pass

class AuthDeviceDataCreate(DeviceDataBase):
    pass

class AuthDeviceDataUpdate(DeviceDataBase):
    pass

class AuthDeviceData(DeviceDataBase):
    is_connected: bool
    connect_table_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True 

class RequestDeviceData(DeviceDataBase):
    connect_status: str
    request_time: datetime
    update_time: datetime
    
    class Config:
        from_attributes = True 
        
        
class PresetDataBase(BaseModel):
    title: str
    payment_chip: int
    buyin_price: int
    rebuyin_price: int
    rebuyin_block: Dict[str, int]
    addon: Dict[str, int]
    prize_setting: Dict[str, int]
    blind_setting: Dict[str, int]
    
class PresetDataCreate(PresetDataBase):
    pass

class PresetDataUpdate(PresetDataBase):
    id: Optional[int] = None
    
    class Config:
        from_attributes = True 

class PresetData(BaseModel):
    id: Optional[int] = Field(default=-1)
    preset_name: str
    time_table_data: List[Dict[str, Any]]
    buy_in_price: int
    re_buy_in_price: int
    starting_chip: int
    rebuyin_payment_chips: List[Dict[str, Any]]
    rebuyin_number_limits: Dict[str, Any]
    addon_data: Dict[str, Any]
    prize_settings: Dict[str, Any]
    rebuy_cut_off: Dict[str, Any]

    class Config:
        from_attributes = True 
