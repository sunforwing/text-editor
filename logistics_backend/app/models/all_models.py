from sqlalchemy import Column, Integer, String, Float, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

# 假设您在 app/core/database.py 中定义了 Base
# from app.core.database import Base
Base = declarative_base()

# --- 1. 基础与用户模块 ---

class User(Base):
    """
    系统用户表
    对应角色: staff_station, dispatcher, driver, courier, admin
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(255))
    role = Column(String(20)) 
    station_id = Column(Integer, nullable=True)  # 逻辑关联 Station.id
    phone = Column(String(20))


class Station(Base):
    """
    网点/中转站
    """
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    type = Column(String(20)) # outlet, hub
    address = Column(String(255))
    geo_location = Column(JSON) # 存储 {lat: ..., lng: ...}


class Vehicle(Base):
    """
    车辆信息
    """
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String(20))
    capacity = Column(Float) # 载重
    status = Column(String(20)) # idle, busy, maintenance


# --- 2. 包裹核心模块 ---

class Parcel(Base):
    """
    包裹主表
    """
    __tablename__ = "parcels"

    tracking_number = Column(String(50), primary_key=True, index=True) # 运单号作为主键
    sender_info = Column(JSON)    # {name, phone, address}
    receiver_info = Column(JSON)  # {name, phone, address}
    weight = Column(Float)
    volume = Column(String(50))
    status = Column(String(20), default="created") 
    
    # 逻辑关联 Station.id，无强约束
    current_station_id = Column(Integer, nullable=True) 
    next_station_id = Column(Integer, nullable=True)
    start_station_id = Column(Integer, nullable=True) 
    final_station_id = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.now)


class ParcelRoute(Base):
    """
    包裹规划路径 (补全部分)
    """
    __tablename__ = "parcel_routes"
    
    id = Column(Integer, primary_key=True, index=True)
    # 逻辑关联 Parcel.tracking_number
    parcel_id = Column(String(50), unique=True, index=True) 
    # 存储路径序列 [StationID_1, StationID_2, ...]
    route_sequence = Column(JSON) 


class ParcelLog(Base):
    """
    包裹全生命周期轨迹日志
    """
    __tablename__ = "parcel_logs"

    id = Column(Integer, primary_key=True, index=True)
    parcel_id = Column(String(50), index=True) # 逻辑关联 Parcel.tracking_number
    station_id = Column(Integer)  # 逻辑关联 Station.id
    operator_id = Column(Integer) # 逻辑关联 User.id
    action = Column(String(20))   # pickup, load, sort, etc.
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.now)


# --- 3. 运输与调度模块 ---

class TransportTask(Base):
    """
    干线/支线运输任务
    """
    __tablename__ = "transport_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_code = Column(String(50), index=True)
    
    # 逻辑外键
    driver_id = Column(Integer)  # User.id
    vehicle_id = Column(Integer) # Vehicle.id
    start_station_id = Column(Integer) # Station.id
    end_station_id = Column(Integer)   # Station.id
    
    status = Column(String(20)) # planned, in_transit, completed, cancelled
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)


class TaskParcelRelation(Base):
    """
    任务-包裹关联表 (多对多中间表)
    """
    __tablename__ = "task_parcel_relations"
    
    # 联合主键建议在数据库层面处理，这里作为 ORM 映射只需定义字段
    # SQLAlchemy 通常需要至少一个 PrimaryKey
    task_id = Column(Integer, primary_key=True)       # 逻辑关联 TransportTask.id
    parcel_id = Column(String(50), primary_key=True)  # 逻辑关联 Parcel.tracking_number


# --- 4. 末端派送模块 ---

class DeliveryTask(Base):
    """
    最后一公里派送任务 (补全部分)
    """
    __tablename__ = "delivery_tasks"

    id = Column(Integer, primary_key=True, index=True)
    courier_id = Column(Integer, index=True) # 逻辑关联 User.id
    parcel_id = Column(String(50), index=True) # 逻辑关联 Parcel.tracking_number
    
    status = Column(String(20)) # assigned, delivering, success, fail
    fail_reason = Column(String(255), nullable=True)
    assigned_at = Column(DateTime, default=datetime.datetime.now)