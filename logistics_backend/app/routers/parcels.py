from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import all_models as models
from app.schemas import parcel as schemas
from app.services.route_planner import calculate_next_station
import uuid
import datetime

router = APIRouter(prefix="/api/v1/parcels", tags=["Parcels"])

@router.post("/", response_model=schemas.ParcelResponse)
def create_parcel(parcel_in: schemas.ParcelCreate, db: Session = Depends(get_db)):
    # 1. 生成运单号
    tracking_no = f"SF{uuid.uuid4().hex[:8].upper()}"
    
    # 2. 计算下一站 (路径规划)
    next_station = calculate_next_station(parcel_in.start_station_id, parcel_in.receiver_info.get("address"))
    
    # 3. 创建包裹记录
    new_parcel = models.Parcel(
        tracking_number=tracking_no,
        sender_info=parcel_in.sender_info,
        receiver_info=parcel_in.receiver_info,
        weight=parcel_in.weight,
        volume=parcel_in.volume,
        current_station_id=parcel_in.start_station_id,
        next_station_id=next_station,
        start_station_id=parcel_in.start_station_id,
        final_station_id=parcel_in.final_station_id,
        status="created"
    )
    db.add(new_parcel)
    
    # 4. 记录初始日志
    initial_log = models.ParcelLog(
        parcel_id=tracking_no,
        station_id=parcel_in.start_station_id,
        action="pickup",
        description="网点已揽收"
    )
    db.add(initial_log)
    
    db.commit()
    db.refresh(new_parcel)
    return new_parcel

@router.get("/{tracking_number}/trace", response_model=schemas.ParcelResponse)
def trace_parcel(tracking_number: str, db: Session = Depends(get_db)):
    # 1. 查询 Parcel 主记录
    parcel = db.query(models.Parcel).filter(models.Parcel.tracking_number == tracking_number).first()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    # 2. 查询该包裹的所有日志
    logs = db.query(models.ParcelLog).filter(
        models.ParcelLog.parcel_id == tracking_number
    ).order_by(models.ParcelLog.created_at).all()
    
    # 3. 将 logs 列表动态添加到 parcel 对象上
    #    这样 Pydantic 转换时就能找到 logs 字段
    #    注意：这依赖于 Pydantic 的 from_attributes = True 配置
    parcel.logs = logs 
    
    return parcel

@router.post("/{tracking_number}/scan")
def scan_parcel(tracking_number: str, scan_data: schemas.ScanRequest, db: Session = Depends(get_db)):
    parcel = db.query(models.Parcel).filter(models.Parcel.tracking_number == tracking_number).first()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    # 更新包裹位置和状态
    parcel.current_station_id = scan_data.station_id
    
    if scan_data.action == "exception":
        parcel.status = "exception"
    elif scan_data.action == "arrive":
        parcel.status = "sorting" # 到达后进入分拣状态
    
    # 如果是分拣动作，重新计算下一站（防止路线变更）
    if scan_data.action == "sort":
        next_hop = calculate_next_station(scan_data.station_id, str(parcel.receiver_info))
        parcel.next_station_id = next_hop
        parcel.status = "dispatching" # 分拣完等待发车

    # 插入日志
    new_log = models.ParcelLog(
        parcel_id=tracking_number,
        station_id=scan_data.station_id,
        operator_id=scan_data.operator_id,
        action=scan_data.action,
        description=scan_data.description
    )
    db.add(new_log)
    db.commit()
    
    return {"message": "Scan processed", "next_station_id": parcel.next_station_id}