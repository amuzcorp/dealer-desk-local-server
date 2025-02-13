from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import json
class TableData(Base):
    __tablename__ = "table_data"

    id = Column(Integer, primary_key=True, index=True)
    table_title = Column(String, index=True)
    current_player_count = Column(Integer, default = 0)
    max_player_count = Column(Integer, default = 12)
    position = Column(JSON, default = {"x" : 0, "y" : 0})
    size = Column(JSON, default = {"width" : 100, "height" : 100})
    
    # 관계 설정
    auth_devices = relationship("AuthDeviceData", back_populates="table")
    
    def to_json(self):
        return {
                "id" : self.id,
                "table_title" : self.table_title,
                "current_player_count" : self.current_player_count,
                "max_player_count" : self.max_player_count,
                "position" : self.position,
                "size" : self.size
            }
        
    
class AuthDeviceData(Base):
    __tablename__ = "auth_device_data"

    id = Column(Integer, primary_key=True, index=True)
    device_uid = Column(String, index=True)
    device_name = Column(String, index=True)
    connect_table_id = Column(Integer, ForeignKey("table_data.id", ondelete="CASCADE"), index=True)
    created_at = Column(DateTime, default=datetime.now())
    is_connected = Column(Boolean, default=False)
    
    # 관계 설정
    table = relationship("TableData", back_populates="auth_devices")
    
    def to_json(self):
        return {
            "id" : self.id,
            "device_uid" : self.device_uid,
            "device_name" : self.device_name,
            "connect_table_id" : self.connect_table_id,
            "created_at" : self.created_at,
            "is_connected" : self.is_connected
        }
        
        
class RequestDeviceData(Base):
    __tablename__ = "request_device_data"

    id = Column(Integer, primary_key=True, index=True)
    device_uid = Column(String, index=True)
    name = Column(String, index=True)
    connect_status = Column(String, index=True, default="waiting") # 대기, 승인, 거절
    request_time = Column(DateTime, default=datetime.now())
    update_time = Column(DateTime, default=datetime.now())
    
    def to_json(self):
        return {
            "id" : self.id,
            "device_uid" : self.device_uid,
            "name" : self.name,
            "connect_status" : self.connect_status,
            "request_time" : self.request_time,
            "update_time" : self.update_time
        }


class PresetData(Base):
    __tablename__ = "preset_data"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    payment_chip = Column(Integer)
    buyin_price = Column(Integer)
    rebuyin_price = Column(Integer)
    rebuyin_block = Column(JSON)
    addon = Column(JSON)
    prize_setting = Column(JSON)
    blind_setting = Column(JSON)
    
    def to_json(self):
        return {
            "id" : self.id,
            "title" : self.title,
            "payment_chip" : self.payment_chip,
            "buyin_price" : self.buyin_price,
            "rebuyin_price" : self.rebuyin_price,
            "rebuyin_block" : self.rebuyin_block,
            "addon" : self.addon,
            "prize_setting" : self.prize_setting,
            "blind_setting" : self.blind_setting
        }
