from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db # 假设这个存在
from app.models import all_models as models
from app.schemas import parcel as schemas
# 假设 calculate_next_station 辅助函数存在且只接收当前站点 ID
from app.services.route_planner import calculate_next_station 
import uuid
import datetime

router = APIRouter(prefix="/api/v1/parcels", tags=["Parcels"])

@router.post("/")
def create_parcel(parcel_in: schemas.ParcelCreate, db: Session = Depends(get_db)):
    """
    接口 1: 创建运单 (POST /api/v1/parcels)
    严格遵循 MD 文档逻辑。
    """
    tracking_no = f"SF{uuid.uuid4().hex[:8].upper()}"
    operator_id = 0 # 假设操作员ID为0 (应从登录用户获取)
    
    # 1. 计算下一站 (路径规划)
    next_station = calculate_next_station(parcel_in.start_station_id) 
    
    # 2. 严格遵循 MD 文档逻辑：判断 next_station_id 是否和 final_station_id 相等，如果相等，报一个错
    if next_station is None or parcel_in.start_station_id == parcel_in.final_station_id:
         raise HTTPException(status_code=400, detail="路径规划失败：无法找到下一站，或起始站点与最终站点相同")
    
    # 3. 在 parcel_routes 表里面新增条目
    route = models.ParcelRoute(
        parcel_id=tracking_no, 
        route_sequence=[parcel_in.start_station_id, next_station, parcel_in.final_station_id] 
    )
    db.add(route)
    
    # 4. 创建包裹记录
    new_parcel = models.Parcel(
        tracking_number=tracking_no,
        # 字段名转换以匹配 DB 模型
        sender_info=parcel_in.sender, 
        receiver_info=parcel_in.receiver,
        weight=parcel_in.weight,
        volume=parcel_in.volume,
        current_station_id=parcel_in.start_station_id, # 这里的 current_station_id 为 start_station_id
        next_station_id=next_station, # Next_station_di为calculate_next_station(current_station_id)
        start_station_id=parcel_in.start_station_id,
        final_station_id=parcel_in.final_station_id,
        status="created" # parcel表状态改为 created
    )
    db.add(new_parcel)
    
    # 5. 记录初始日志
    initial_log = models.ParcelLog(
        parcel_id=tracking_no,
        station_id=parcel_in.start_station_id,
        operator_id=operator_id,
        action="created", # 写入到 parcel_load表 中的 action 为 created
        description="运单已创建，等待揽收"
    )
    db.add(initial_log)
    
    db.commit()
    
    # 6. 严格遵循 MD 文档的 Response 格式
    return {
        "tracking_number": tracking_no,
        "status": "created",
    }

@router.get("/trace", response_model=schemas.ParcelResponse)
def trace_parcel(tracking_number: str, db: Session = Depends(get_db)):
    """
    接口 2: 查询包裹轨迹 (GET /api/v1/parcels/trace?tracking_number=)
    """
    # 1. 查询 Parcel 主记录
    parcel = db.query(models.Parcel).filter(models.Parcel.tracking_number == tracking_number).first()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    # 2. 查询该包裹的所有日志
    logs = db.query(models.ParcelLog).filter(
        models.ParcelLog.parcel_id == tracking_number
    ).order_by(models.ParcelLog.created_at).all()
    
    # 3. 准备响应数据
    
    # MD 文档要求 response body 包含 sender/receiver，DB 模型使用 sender_info/receiver_info。
    # 这里将 DB 字段映射到 response 字段，并假设 log 中的 station ID 可以被前端转换成 name。
    response_data = schemas.ParcelResponse(
        tracking_number=parcel.tracking_number,
        sender=parcel.sender_info,
        receiver=parcel.receiver_info,
        weight=parcel.weight,
        volume=parcel.volume,
        start_station_id=parcel.start_station_id,
        final_station_id=parcel.final_station_id,
        current_station_id=parcel.current_station_id,
        next_station_id=parcel.next_station_id,
        status=parcel.status,
        logs=[
            schemas.ParcelLogResponse(
                station_id=log.station_id,
                action=log.action,
                description=log.description,
                created_at=log.created_at
            )
            for log in logs
        ]
    )
    
    return response_data

@router.post("/scan")
def scan_parcel(scan_data: schemas.ScanRequest, db: Session = Depends(get_db)):
    """
    接口 3: 状态更新 (POST /api/v1/parcels/scan)
    严格遵循 MD 文档中 "3. 状态更新" 的逻辑。
    """
    tracking_number = scan_data.tracking_number
    action = scan_data.action.lower()
    operator_id = 0 # 假设操作员ID为0 (应从登录用户获取)
        
    parcel = db.query(models.Parcel).filter(models.Parcel.tracking_number == tracking_number).first()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
        
    old_status = parcel.status
    logs_to_add = []

    # --- 状态流转逻辑 ---

    # 1. Action: sort (分拣)
    if action == "sort":
        if old_status not in ["created", "dispatching"]:
            raise HTTPException(status_code=400, detail=f"校验失败：之前的 status 必须为 created 或 dispatching，当前是 {old_status}")

        if old_status == "dispatching":
            # dispathing -> sorting, 写入 dispatch_completed 和 sort_started 两个条目
            # current_station_id 和 next_station_id 不变
            logs_to_add.append(models.ParcelLog(
                parcel_id=tracking_number, station_id=parcel.current_station_id, operator_id=operator_id,
                action="dispatch_completed", description="前一站派送完成，包裹已入库"
            ))
            
        # created/dispatching -> sorting 
        parcel.status = "sorting"
        logs_to_add.append(models.ParcelLog(
            parcel_id=tracking_number, station_id=parcel.current_station_id, operator_id=operator_id,
            action="sorting_started", description="包裹开始分拣处理"
        ))
        
    # 2. Action: transport (运输)
    elif action == "transport":
        if old_status != "sorting":
            raise HTTPException(status_code=400, detail=f"校验失败：之前的 status 必须为 sorting，当前是 {old_status}")

        # sorting -> transporting, 写入 sorted_completed 和 transport_started 两个条目
        logs_to_add.append(models.ParcelLog(
            parcel_id=tracking_number, station_id=parcel.current_station_id, operator_id=operator_id,
            action="sorting_completed", description="包裹分拣完成，准备装车运输"
        ))
        
        # 更新站点信息
        # current_station_id = 原 next_station_id
        # next_station_id = calculate_next_station(current_station_id)
        
        old_next_station_id = parcel.next_station_id
        parcel.current_station_id = old_next_station_id
        parcel.next_station_id = calculate_next_station(parcel.current_station_id)
        
        # 检查下一站是否为 None
        if parcel.next_station_id is None:
             raise HTTPException(status_code=400, detail=f"路径规划失败：无法找到下一站")

        parcel.status = "transporting"
        logs_to_add.append(models.ParcelLog(
            parcel_id=tracking_number, station_id=parcel.current_station_id, operator_id=operator_id,
            action="transport_started", description=f"包裹已装车，发往下一站ID: {parcel.next_station_id}"
        ))

    # 3. Action: dispatch (派送)
    elif action == "dispatch":
        # 只有到达最终目的地的 sorting 包裹才能执行 dispatch
        if old_status != "sorting":
            raise HTTPException(status_code=400, detail=f"校验失败：之前的 status 必须为 sorting，当前是 {old_status}")

        # 严格校验：确保当前站点就是最终目的地派送站
        if parcel.current_station_id != parcel.final_station_id:
             raise HTTPException(status_code=400, detail="校验失败：包裹尚未到达最终目的地派送站")
            
        # sorting -> dispatching, 写入 sorted_completed 和 dispathed_started 两个条目
        logs_to_add.append(models.ParcelLog(
            parcel_id=tracking_number, station_id=parcel.current_station_id, operator_id=operator_id,
            action="sorting_completed", description="包裹分拣完成，准备派送"
        ))
        
        # 更新站点信息
        # current_station_id = next_station_id（已到达目的地派送站）
        # next_station_id = None
        # 注意：这里假设到达后 current_station_id 已更新为 final_station_id，next_station_id=None
        parcel.next_station_id = None 

        parcel.status = "dispatching"
        logs_to_add.append(models.ParcelLog(
            parcel_id=tracking_number, station_id=parcel.current_station_id, operator_id=operator_id,
            action="dispatch_started", description="包裹已分配给快递员，开始末端派送"
        ))
    
    # 4. Action: finish (完成)
    elif action == "finish":
        if old_status != "dispatching":
            raise HTTPException(status_code=400, detail=f"校验失败：之前的 status 必须为 dispatching，当前是 {old_status}")
            
        # dispatching -> delivered, 写入 dispatch_completed 一个条目
        # current_station_id 和 next_station_id 不变
        parcel.status = "delivered"
        
        logs_to_add.append(models.ParcelLog(
            parcel_id=tracking_number, station_id=parcel.current_station_id, operator_id=operator_id,
            action="dispatch_completed", description="派送成功，客户已签收"
        ))
        
    else:
        raise HTTPException(status_code=400, detail=f"无效的 action 类型：{action}")

    # 提交事务
    db.add_all(logs_to_add)
    db.commit()
    db.refresh(parcel)
    
    # 返回更新后的关键状态信息
    return {"tracking_number": tracking_number, "new_status": parcel.status, "message": "Scan processed successfully"}