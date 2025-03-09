from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import json
class TableData(Base):
    __tablename__ = "table_data"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, nullable=True, index=True)
    title = Column(String, index=True)
    current_players = Column(Integer, default = 0)
    max_players = Column(Integer, default = 12)
    position = Column(JSON, default = {"x" : 0, "y" : 0})
    size = Column(JSON, default = {"width" : 100, "height" : 100})
    
    # 관계 설정
    auth_devices = relationship("AuthDeviceData", back_populates="table")
    
    def to_json(self):
        return {
                "id" : self.id,
                "game_id" : self.game_id,
                "title" : self.title,
                "current_players" : self.current_players,
                "max_players" : self.max_players,
                "position" : self.position,
                "size" : self.size
            }
        
    
class AuthDeviceData(Base):
    __tablename__ = "auth_device_data"

    id = Column(Integer, primary_key=True, index=True)
    device_uid = Column(String, index=True)
    device_name = Column(String, index=True)
    connect_table_id = Column(Integer, ForeignKey("table_data.id", ondelete="CASCADE"), index=True, nullable=True)
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
    device_name = Column(String, index=True)
    connect_status = Column(String, index=True, default="waiting") # 대기, 승인, 거절
    request_time = Column(DateTime, default=datetime.now())
    update_time = Column(DateTime, default=datetime.now())
    
    def to_json(self):
        return {
            "id" : self.id,
            "device_uid" : self.device_uid,
            "device_name" : self.device_name,
            "connect_status" : self.connect_status,
            "request_time" : self.request_time,
            "update_time" : self.update_time
        }


class PresetData(Base):
    __tablename__ = "preset_data"

    id = Column(Integer, primary_key=True, index=True)
    preset_name = Column(String, index=True)
    time_table_data = Column(JSON)
    buy_in_price = Column(Integer)
    re_buy_in_price = Column(Integer)
    starting_chip = Column(Integer)
    rebuyin_payment_chips = Column(JSON)
    rebuyin_number_limits = Column(JSON)
    addon_data = Column(JSON)
    prize_settings = Column(JSON)
    rebuy_cut_off = Column(JSON)

    def to_json(self):
        return {
            "id": self.id,
            "preset_name": self.preset_name,
            "time_table_data": self.time_table_data,
            "buy_in_price": self.buy_in_price,
            "re_buy_in_price": self.re_buy_in_price,
            "starting_chip": self.starting_chip,
            "rebuyin_payment_chips": self.rebuyin_payment_chips,
            "rebuyin_number_limits": self.rebuyin_number_limits,
            "addon_data": self.addon_data,
            "prize_settings": self.prize_settings,
            "rebuy_cut_off": self.rebuy_cut_off
        }


class GameData(Base):
    __tablename__ = "game_data"

    id = Column(Integer, primary_key=True, index=True)
    game_code = Column(String, index=True)
    title = Column(String, index=True)
    game_start_time = Column(DateTime, default=datetime.now())
    game_calcul_time = Column(DateTime, default=datetime.now())
    game_stop_time = Column(DateTime, nullable=True, default=datetime.now())
    game_end_time = Column(DateTime, default=None, nullable=True)
    game_status = Column(String, index=True, default="waiting")  # waiting, in_progress, end
    game_in_player = Column(JSON, default=list)
    table_connect_log = Column(JSON, default=list)
    addon_count = Column(Integer, default=0)

    # 게임 데이터는 프리셋 전체 데이터를 가짐     
    time_table_data = Column(JSON)
    buy_in_price = Column(Integer)
    re_buy_in_price = Column(Integer)
    starting_chip = Column(Integer)
    rebuyin_payment_chips = Column(JSON)
    rebuyin_number_limits = Column(JSON)
    addon_data = Column(JSON)
    prize_settings = Column(JSON)
    rebuy_cut_off = Column(JSON)
    
    # 최종 상금
    final_prize = Column(Integer, default=0)
    
    def to_json(self):
        return {
            "id" : self.id,
            "game_code" : self.game_code,
            "title" : self.title,
            "game_start_time" : self.game_start_time.isoformat(),
            "game_calcul_time" : self.game_calcul_time.isoformat(),
            "game_stop_time" : self.game_stop_time.isoformat() if self.game_stop_time else None,
            "game_end_time" : self.game_end_time.isoformat() if self.game_end_time else None,
            "game_status" : self.game_status,
            "addon_count" : self.addon_count,
            "game_in_player" : self.game_in_player,
            "table_connect_log" : self.table_connect_log,
            "time_table_data" : self.time_table_data,
            "buy_in_price" : self.buy_in_price,
            "re_buy_in_price" : self.re_buy_in_price, 
            "starting_chip" : self.starting_chip,
            "rebuyin_payment_chips" : self.rebuyin_payment_chips,
            "rebuyin_number_limits" : self.rebuyin_number_limits,
            "addon_data" : self.addon_data,
            "addon_price" : 0,
            "prize_settings" : self.prize_settings,
            "rebuy_cut_off" : self.rebuy_cut_off,
            "final_prize" : self.final_prize
        }

class PurchaseData(Base):
    __tablename__ = "purchase_data"

    id = Column(Integer, primary_key=True, index=True)
    payment_type = Column(String, index=True)  # LOCAL_PAY, CASUAL_PAY
    purchase_type = Column(String, index=True)  # Game 등
    game_id = Column(Integer, ForeignKey("game_data.id"), nullable=True)
    customer_id = Column(Integer, index=True)
    uuid = Column(String, index=True)
    purchased_at = Column(DateTime, default=datetime.now())
    item = Column(String, index=True)  # BUYIN, REBUYIN 등
    payment_status = Column(String, default="WAITING")  # WAITING, COMPLETED, FAILED
    status = Column(String, default="WAITING")  # WAITING, COMPLETED, CANCELLED
    price = Column(Integer, default=0)
    used_points = Column(Integer, default=0)
    
    def to_json(self):
        return {
            "id": self.id,
            "payment_type": self.payment_type,
            "purchase_type": self.purchase_type,
            "game_id": self.game_id,
            "customer_id": self.customer_id,
            "uuid": self.uuid,
            "purchased_at": self.purchased_at.isoformat() if self.purchased_at else None,
            "item": self.item,
            "payment_status": self.payment_status,
            "status": self.status,
            "price": self.price,
            "used_points": self.used_points
        }

class UserData(Base):
    __tablename__ = "user_data"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    uuid = Column(String, index=True)
    phone_number = Column(String, index=True, nullable=True)
    email = Column(String, nullable=True)
    game_join_count = Column(Integer, default=0)
    visit_count = Column(Integer, default=0)
    register_at = Column(DateTime, default=datetime.now())
    last_visit_at = Column(DateTime, default=datetime.now())
    remark = Column(String, default="")
    
    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "uuid": self.uuid,
            "phone_number": self.phone_number,
            "email": self.email,
            "game_join_count": self.game_join_count,
            "visit_count": self.visit_count,
            "register_at": self.register_at.isoformat() if self.register_at else None,
            "last_visit_at": self.last_visit_at.isoformat() if self.last_visit_at else None,
            "remark": self.remark,
        }

class AwardingHistoryData(Base):
    __tablename__ = "awarding_history_data"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("game_data.id"), nullable=True)
    game_rank = Column(Integer, nullable=True)
    customer_id = Column(Integer, ForeignKey("user_data.id"), nullable=True)
    awarding_at = Column(DateTime, default=datetime.now())
    awarding_amount = Column(Integer, default=0)
    
    def to_json(self):
        return {
            "id": self.id,
            "game_id": self.game_id,
            "game_rank": self.game_rank,
            "customer_id": self.customer_id,
            "awarding_at": self.awarding_at.isoformat() if self.awarding_at else None,
            "awarding_amount": self.awarding_amount,
        }

class PointHistoryData(Base):
    __tablename__ = "point_history_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    uuid = Column(String, unique=True, index=True)  # UUID 형식으로 고유해야 함
    customer_id = Column(Integer, ForeignKey("user_data.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True)
    reason = Column(String, nullable=True, index=True)
    amount = Column(Integer, default=0)  # 총 적립 포인트
    available_amount = Column(Integer, default=0)  # 사용가능한 포인트
    is_expired = Column(Boolean, default=False, index=True)  # 만료 여부
    expire_at = Column(DateTime, nullable=True, index=True)  # 만료 날짜
    is_increase = Column(Boolean, default=True, index=True)  # 증가인지 감소인지
    created_at = Column(DateTime, default=datetime.now())
    
    def to_json(self):
        return {
            "id": self.id,
            "uuid": self.uuid,
            "customer_id": self.customer_id,
            "reason": self.reason,
            "amount": self.amount,
            "available_amount": self.available_amount,
            "is_expired": self.is_expired,
            "expire_at": self.expire_at.isoformat() if self.expire_at else None,
            "is_increase": self.is_increase,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
