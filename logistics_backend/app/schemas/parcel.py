from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# 基础模型
class ParcelBase(BaseModel):
    weight: float
    volume: str
    # 严格遵循 MD 文档 Request Body 的键名 (sender, receiver)
    sender: Dict[str, Any]
    receiver: Dict[str, Any]
    start_station_id: Optional[int]
    final_station_id: Optional[int]

# 创建请求 (对应 MD 文档中的 Request Body)
class ParcelCreate(ParcelBase):
    start_station_id: int
    final_station_id: int

# 日志响应子模型
class ParcelLogResponse(BaseModel):
    # 严格遵循 MD 文档 Response 的键名
    # MD 文档中使用了 time, station, action, desc。这里使用DB模型的字段，但描述时会转换为所需格式。
    station_id: Optional[int]
    action: str
    description: str
    created_at: datetime
    class Config:
        from_attributes = True

# 响应模型 (主要用于 trace 接口)
class ParcelResponse(ParcelBase):
    tracking_number: str
    status: str
    current_station_id: Optional[int]
    next_station_id: Optional[int]
    # logs 字段用于 trace 接口返回
    logs: List[ParcelLogResponse] = [] 
    class Config:
        from_attributes = True

# 扫描请求 (严格根据 MD 文档：Request Body 只有 tracking_number 和 action)
class ScanRequest(BaseModel):
    tracking_number: str
    action: str
    
# 异常上报请求 (新增)
class ExceptionRequest(BaseModel):
    tracking_number: str
    description: str