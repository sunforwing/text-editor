from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import all_models as models
from pydantic import BaseModel
from typing import List, Optional
import uuid
import datetime

# --- Pydantic 数据模型（保持不变）---

class TransportTaskCreate(BaseModel):
    driver_id: int
    vehicle_id: int
    start_station_id: int
    end_station_id: int
    parcel_ids: List[str]

class TransportStatusUpdate(BaseModel):
    status: str
    current_station_id: Optional[int] = None
    operator_id: int = 0 


# --- API 路由（保持不变）---

router = APIRouter(prefix="/api/v1", tags=["Transport"])

@router.post("/transport-tasks")
def create_transport_task(task_in: TransportTaskCreate, db: Session = Depends(get_db)):
    # ... (此函数保持不变，逻辑正确)
    new_task = models.TransportTask(
        task_code=f"T-{task_in.start_station_id}-{task_in.end_station_id}-{uuid.uuid4().hex[:4]}",
        driver_id=task_in.driver_id,
        vehicle_id=task_in.vehicle_id,
        start_station_id=task_in.start_station_id,
        end_station_id=task_in.end_station_id,
        status="planned"
    )
    db.add(new_task)
    db.flush()

    for pid in task_in.parcel_ids:
        rel = models.TaskParcelRelation(task_id=new_task.id, parcel_id=pid)
        db.add(rel)
        
        p = db.query(models.Parcel).filter(models.Parcel.tracking_number == pid).first()
        if p: p.status = "dispatching" # 包裹状态变为 dispatching
        
    db.commit()
    return {"task_id": new_task.id, "task_code": new_task.task_code, "status": new_task.status}

@router.get("/driver/tasks")
def get_driver_tasks(driver_id: int, status: str = "planned", db: Session = Depends(get_db)):
    # ... (此函数保持不变)
    tasks = db.query(models.TransportTask).filter(
        models.TransportTask.driver_id == driver_id,
        models.TransportTask.status == status
    ).all()
    return tasks

@router.put("/transport-tasks/{task_id}/status")
def update_transport_status(
    task_id: int, 
    update_data: TransportStatusUpdate, 
    db: Session = Depends(get_db)
):
    task = db.query(models.TransportTask).filter(models.TransportTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Transport Task not found")

    new_status = update_data.status
    logs_to_add = []

    # 1. 状态流转：in_transit (发车)
    if new_status == "in_transit":
        if task.status != "planned":
            raise HTTPException(status_code=400, detail=f"Task status must be 'planned' to start, current is '{task.status}'")
            
        task.status = "in_transit"
        task.start_time = datetime.datetime.now()
        log_desc = f"车辆已发车，前往站点ID: {task.end_station_id}"
        
        parcel_relations = db.query(models.TaskParcelRelation).filter(models.TaskParcelRelation.task_id == task_id).all()
        parcel_tracking_numbers = [rel.parcel_id for rel in parcel_relations]

        db.query(models.Parcel).filter(
            models.Parcel.tracking_number.in_(parcel_tracking_numbers)
        ).update({"status": "in_transit"}, synchronize_session=False)

        for tn in parcel_tracking_numbers:
            logs_to_add.append(models.ParcelLog(
                parcel_id=tn,
                station_id=task.start_station_id,
                operator_id=update_data.operator_id,
                action="load",  # <--- 修正：使用数据库枚举中的 'load'
                description=log_desc
            ))

    # 2. 状态流转：completed (到达)
    elif new_status == "completed":
        if task.status != "in_transit":
            raise HTTPException(status_code=400, detail="Task status must be 'in_transit' to complete")

        if not update_data.current_station_id:
             raise HTTPException(status_code=400, detail="current_station_id is required for 'completed' status")

        task.status = "completed"
        task.end_time = datetime.datetime.now()
        log_desc = f"车辆已安全到达站点ID: {update_data.current_station_id}，正在卸货"
        
        parcel_relations = db.query(models.TaskParcelRelation).filter(models.TaskParcelRelation.task_id == task_id).all()
        parcel_tracking_numbers = [rel.parcel_id for rel in parcel_relations]

        db.query(models.Parcel).filter(
            models.Parcel.tracking_number.in_(parcel_tracking_numbers)
        ).update({
            "current_station_id": update_data.current_station_id,
            "status": "sorting" # <--- 修正：到达后转为 sorting
        }, synchronize_session=False)

        for tn in parcel_tracking_numbers:
            logs_to_add.append(models.ParcelLog(
                parcel_id=tn,
                station_id=update_data.current_station_id,
                operator_id=update_data.operator_id,
                action="unload", # <--- 修正：使用数据库枚举中的 'unload'
                description=log_desc
            ))
    else:
        raise HTTPException(status_code=400, detail="Invalid status update value. Must be 'in_transit' or 'completed'.")

    # 3. 提交事务
    db.add_all(logs_to_add)
    db.commit()
    
    return {"task_id": task_id, "status": task.status}