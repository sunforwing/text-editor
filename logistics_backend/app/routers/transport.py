from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import all_models as models
from pydantic import BaseModel
from typing import List, Optional
import uuid
import datetime

# 假设 calculate_next_station 辅助函数存在且只接收当前站点 ID
from app.services.route_planner import calculate_next_station 


# --- Pydantic 数据模型（TaskCreate 保持不变，TaskStatusUpdate 调整以匹配 transport task status 描述）---

class TransportTaskCreate(BaseModel):
    driver_id: int
    vehicle_id: int
    # start_station_id: int
    # end_station_id: int
    parcel_ids: List[str]

# 严格遵循 MD 文档的 Request Body 结构
class TransportStatusUpdate(BaseModel):
    task_code: str
    status: str # in_transit 或 completed
    # operator_id 用于记录 ParcelLog，未在 MD 中定义，但业务需要，此处假设从请求者获取

# --- API 路由 ---

router = APIRouter(prefix="/api/v1", tags=["Transport"])

@router.post("/transport/start")
def create_transport_task(task_in: TransportTaskCreate, db: Session = Depends(get_db)):
    """
    接口 4: 创建运输任务 (POST /api/v1/transport/start)
    这里的会在新增一个 transport_tasks 的条目，且 status 为 planned
    """
    task_code = f"T-{uuid.uuid4().hex[:8].upper()}"
    if not task_in.parcel_ids:
        raise HTTPException(status_code=400, detail="Parcel list cannot be empty")
    
    first_parcel_id = task_in.parcel_ids[0]
    first_parcel = db.query(models.Parcel).filter(models.Parcel.tracking_number == first_parcel_id).first()
    start_station_id = first_parcel.current_station_id
    end_station_id = first_parcel.next_station_id

    # 1. 新增 TransportTask 条目
    new_task = models.TransportTask(
        task_code=task_code,
        driver_id=task_in.driver_id,
        vehicle_id=task_in.vehicle_id,
        start_station_id=start_station_id,
        end_station_id=end_station_id,
        status="planned" # status 为 planned
    )
    db.add(new_task)
    db.flush() # 确保 new_task.id 已生成

    # 2. 写入 TaskParcelRelation
    for pid in task_in.parcel_ids:
        rel = models.TaskParcelRelation(task_id=new_task.id, parcel_id=pid)
        db.add(rel)
        
        # 可选：这里通常会将包裹状态更新为 "ready_to_load" 或类似的中间状态
        # MD 文档未明确要求，此处不做修改，等待 /transport/status 接口处理
        
    db.commit()
    # 严格遵循 MD 文档的 Response 格式 (未给出，返回关键信息)
    return {"task_id": new_task.id, "task_code": task_code, "status": new_task.status}


@router.put("/transport/status")
def update_transport_status(
    update_data: TransportStatusUpdate, 
    db: Session = Depends(get_db)
):
    """
    接口 5: 更新运输状态 (PUT /api/v1/transport/status)
    严格遵循 MD 文档中运输任务状态更新对包裹状态和日志的联动逻辑。
    """
    operator_id = 0 # 假设操作员ID为0 (应从请求者获取)
    
    task = db.query(models.TransportTask).filter(models.TransportTask.task_code == update_data.task_code).first()
    if not task:
        raise HTTPException(status_code=404, detail="Transport Task not found")

    new_status = update_data.status
    logs_to_add = []

    # 查询任务中所有包裹
    parcel_relations = db.query(models.TaskParcelRelation).filter(models.TaskParcelRelation.task_id == task.id).all()
    parcel_tracking_numbers = [rel.parcel_id for rel in parcel_relations]

    # 1. 状态流转：in_transit (发车)
    if new_status == "in_transit":
        if task.status != "planned":
            raise HTTPException(status_code=400, detail=f"任务状态必须是 'planned' 才能发车，当前是 '{task.status}'")
            
        task.status = "in_transit"
        task.start_time = datetime.datetime.now()
        
        # 严格遵循 MD 文档逻辑：
        # Parcel 状态转移：sorting -> transporting 
        # 写入 log 里面两条条目：sorting_completed 和 transport_started
        
        for tn in parcel_tracking_numbers:
            p = db.query(models.Parcel).filter(models.Parcel.tracking_number == tn).first()
            if not p: continue 

            # log 1: sorting_completed (在始发站完成分拣)
            logs_to_add.append(models.ParcelLog(
                parcel_id=tn, station_id=p.current_station_id, operator_id=operator_id,
                action="sorting_completed", description="包裹分拣完成，装车发运"
            ))

            # 更新站点信息
            # current_station_id = 原 next_station_id
            # old_next_station_id = p.next_station_id
            # p.current_station_id = old_next_station_id
            # next_station_id = calculate_next_station(current_station_id)
            # p.next_station_id = calculate_next_station(p.current_station_id)

            # 更新包裹状态
            p.status = "transporting"
            
            # log 2: transport_started (在更新后的 current_station_id 触发)
            logs_to_add.append(models.ParcelLog(
                parcel_id=tn, station_id=p.current_station_id, operator_id=operator_id,
                action="transport_started", description=f"包裹已开始运输，发往下一站ID: {p.next_station_id}"
            ))
            
    # 2. 状态流转：completed (到达)
    elif new_status == "completed":
        if task.status != "in_transit":
            raise HTTPException(status_code=400, detail="任务状态必须是 'in_transit' 才能完成")

        task.status = "completed"
        task.end_time = datetime.datetime.now()
        
        # 严格遵循 MD 文档逻辑：
        # Parcel 状态从 transporting -> sorting
        # 写入 log 里面两个条目：dispatch_completed 和 sort_started
        
        for tn in parcel_tracking_numbers:
            p = db.query(models.Parcel).filter(models.Parcel.tracking_number == tn).first()
            if not p: continue 

            # 1. 更新包裹状态和站点信息
            # current_station_id = task.end_station_id (到达终点站)
            p.current_station_id = task.end_station_id
            p.next_station_id = calculate_next_station(p.current_station_id)
            
            if(p.current_station_id == p.final_station_id):
                p.next_station_id = None
  
             # 包裹状态更新
            p.status = "sorting" # 状态转为 sorting
            # next_station_id 不变 (即保持 transport 时的下一站，或者需要重新计算)
            # 严格遵循 MD 文档：current_station_id 和 next_station_id 不变 (这里假设 next_station_id 在到达后会重新计算)
            
            # log 1: dispatch_completed (严格遵循 MD 文档的 action 名称)
            logs_to_add.append(models.ParcelLog(
                parcel_id=tn, station_id=p.current_station_id, operator_id=operator_id,
                action="transport_completed", description="包裹运输完成，已到达"
            ))
            
            # log 2: sort_started
            logs_to_add.append(models.ParcelLog(
                parcel_id=tn, station_id=p.current_station_id, operator_id=operator_id,
                action="sorting_started", description="包裹开始分拣"
            ))

    else:
        raise HTTPException(status_code=400, detail="无效的 status 值。必须是 'in_transit' 或 'completed'。")

    # 3. 提交事务
    db.add_all(logs_to_add)
    db.commit()
    
    # 返回更新后的任务状态
    return {"task_code": task.task_code, "status": task.status, "message": "Transport status updated"}