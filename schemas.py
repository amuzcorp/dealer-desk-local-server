from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
import uuid

"""
테이블 데이터
"""
class TableDataBase(BaseModel):
    title: str
    position: Dict[str, float] = {"x": 0, "y": 0}
    size: Dict[str, float] = {"width": 100, "height": 100}

class TableDataCreate(TableDataBase):
    pass

class TableDataUpdate(BaseModel):
    title: Optional[str] = None
    position: Optional[Dict[str, float]] = None
    size: Optional[Dict[str, float]] = None

class TableData(TableDataBase):
    id: Optional[int] = None
    current_players: int
    max_players: int
    
    class Config:
        from_attributes = True 
        
        
"""
디바이스 데이터
"""
class DeviceDataBase(BaseModel):
    id: Optional[int] = None
    device_name: str
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

class RequestDeviceData(BaseModel):
    device_uid: str
    device_name: str
    connect_status: str

class ConnectTableData(BaseModel):
    device_uid: str
    table_id: int

class DisconnectTableData(BaseModel):
    device_uid: str

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

"""
사용자 데이터
"""
class UserDataBase(BaseModel):
    id: Optional[int] = None
    name: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    game_join_count: int
    visit_count: int
    register_at: datetime
    last_visit_at: datetime
    point: int
    total_point: int
    remark: str
    
class UserDataCreate(UserDataBase):
    pass

class UserDataUpdate(UserDataBase):
    id: int
    
    class Config:
        from_attributes = True 
    
class UserData(UserDataBase):
    id: Optional[int] = None

"""
 시상 내역 데이터
"""

class AwardingHistoryBase(BaseModel):
    id: Optional[int] = None
    game_id: Optional[int] = None
    game_rank: Optional[int] = None
    customer_id: Optional[int] = None
    awarding_at: Optional[datetime] = datetime.now()
    awarding_amount: Optional[int] = 0

class AwardingHistoryCreate(AwardingHistoryBase):
    pass
    
class AwardingHistoryUpdate(AwardingHistoryBase):
    id: int
    
class AwardingHistory(AwardingHistoryBase):
    id: Optional[int] = None
    
    class Config:
        from_attributes = True 
    

"""
포인트 내역 데이터
"""
class PointHistoryDataBase(BaseModel):
    id: Optional[int] = None
    uuid: Optional[str] = str(uuid.uuid4())
    customer_id: int
    reason: str
    amount: int
    available_amount: int
    is_expired: bool
    expire_at: Optional[datetime] = datetime.now() + timedelta(days=365 * 99)
    is_increase: bool
    created_at: datetime
    
class PointHistoryDataCreate(PointHistoryDataBase):
    pass

class PointHistoryDataUpdate(PointHistoryDataBase):
    id: int
    
class PointHistoryData(PointHistoryDataBase):
    id: Optional[int] = None
    
    class Config:
        from_attributes = True 
