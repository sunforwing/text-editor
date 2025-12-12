from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# 基础模型
class ParcelBase(BaseModel):
    weight: float
    volume: str
    sender_info: Dict[str, Any]
    receiver_info: Dict[str, Any]
    start_station_id: Optional[int]
    final_station_id: Optional[int]

# 创建请求
class ParcelCreate(ParcelBase):
    start_station_id: int

# 响应模型
class ParcelLogResponse(BaseModel):
    station_id: Optional[int]
    action: str
    description: str
    created_at: datetime
    class Config:
        from_attributes = True

class ParcelResponse(ParcelBase):
    tracking_number: str
    status: str
    current_station_id: Optional[int]
    next_station_id: Optional[int]
    logs: List[ParcelLogResponse] = []
    class Config:
        from_attributes = True

# 扫描请求
class ScanRequest(BaseModel):
    station_id: int
    action: str  # arrive, sort, exception
    description: str
    operator_id: Optional[int] = None