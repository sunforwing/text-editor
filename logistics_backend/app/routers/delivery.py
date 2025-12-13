from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import all_models as models
from pydantic import BaseModel
from typing import List
import datetime

router = APIRouter(prefix="/api/v1/delivery", tags=["Delivery"])

# --- Pydantic Data Models (Strictly following MD Request Bodies) ---

class DeliveryStartReq(BaseModel):
    courier_id: int
    parcel_ids: List[str]

class DeliveryStatusUpdateReq(BaseModel):
    parcel_id: str  # MD specifies "parcel_id": 1, but Parcel PK is usually string/varchar
    status: str     # start or finish   

# --- API Routes ---

@router.post("/start")
def create_delivery_task(req: DeliveryStartReq, db: Session = Depends(get_db)):
    """
    Interface 6: Create Last Mile Delivery Task (POST /api/v1/delivery/start)
    """
    # Verify Courier exists
    courier = db.query(models.User).filter(models.User.id == req.courier_id).first()
    if not courier:
        raise HTTPException(status_code=404, detail=f"没有这个编号为{req.courier_id}的快递员")

    tasks_created = []

    for tracking_number in req.parcel_ids:
        # 1. Fetch Parcel
        parcel = db.query(models.Parcel).filter(models.Parcel.tracking_number == tracking_number).first()
        if not parcel:
            raise HTTPException(status_code=404, detail=f"Parcel {tracking_number} not found")

        # 2. Validation: Status must be 'sorting'
        if parcel.status != "sorting":
            raise HTTPException(
                status_code=400, 
                detail=f"Parcel {tracking_number} status is '{parcel.status}', expected 'sorting'"
            )

        # 3. Validation: Current station must match Final station
        if parcel.current_station_id != parcel.final_station_id:
            raise HTTPException(
                status_code=400, 
                detail=f"Parcel {tracking_number} is at station {parcel.current_station_id}, but destination is {parcel.final_station_id}. Not at final station."
            )

        # 4. Update Parcel Status
        # "如果是的，将其parcel的状态改为dispatching"
        # parcel.status = "dispatching"

        # 5. Write Logs (2 entries)
        # "写入log里面两条条目，一个action为sorted_completed，还有一个为dispathed_started"
        # Note: Using standard English 'dispatch_started' for 'dispathed_started'
        

        # 6. Create DeliveryTask
        # "然后为分别每个parcel写入delivery的status为assigned状态, 写入时间"
        new_task = models.DeliveryTask(
            courier_id=req.courier_id,
            parcel_id=tracking_number,
            status="assigned",
            # created_at handled by DB default or implied
        )
        db.add(new_task)
        tasks_created.append(new_task)

    # db.add_all(logs_to_add)
    db.commit()

    return {"message": "Delivery tasks started", "count": len(tasks_created)}


@router.put("/status")
def update_delivery_status(req: DeliveryStatusUpdateReq, db: Session = Depends(get_db)):
    """
    Interface 7: Update Delivery Status (PUT /api/v1/delivery/status)
    """
    # Find the ACTIVE delivery task for this parcel
    # Since the request only gives parcel_id, we look for a task that is not yet finalized (not success/fail)
    # or simply the latest one.
    task = db.query(models.DeliveryTask).filter(
        models.DeliveryTask.parcel_id == req.parcel_id,
        models.DeliveryTask.status.in_(["assigned", "delivering"])  # Assuming these are the active statuses
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail=f"No active delivery task found for parcel {req.parcel_id}")

    parcel = db.query(models.Parcel).filter(models.Parcel.tracking_number == req.parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    logs_to_add = []

    if req.status == "start":
        # "代表这个包裹成功被快递小哥接受了，就需要修改一下delivery_tasks表的条目的状态就行了"
        task.status = "delivering"
        parcel.status = "dispatching"
        # Optional: Log this action if needed, though MD doesn't explicitly ask for a log here, 
        # only implies task update.
                # Log 1: sorting_completed
        logs_to_add.append(models.ParcelLog(
            parcel_id=req.parcel_id,
            station_id=parcel.current_station_id,
            operator_id=task.courier_id, 
            action="sorting_completed",
            description="包裹分拣完成，准备派送"
        ))

        # Log 2: dispatch_started
        logs_to_add.append(models.ParcelLog(
            parcel_id=req.parcel_id,
            station_id=parcel.current_station_id,
            operator_id=task.courier_id,
            action="dispatch_started",
            description=f"开始由派送员No.{task.courier_id} ，从站点送到家里中"
        ))

    elif req.status == "finish":
        # "修改一下delivery_tasks表的条目的状态和完成的时间"
        task.status = "success"
        task.completed_at = datetime.datetime.now() # Assuming field exists based on context

        # "再修改parcel的状态delivered"
        parcel.status = "delivered"

        # "最后在pacel_log新增加一个action为dispatch_completed的条目"
        logs_to_add.append(models.ParcelLog(
            parcel_id=req.parcel_id,
            station_id=parcel.current_station_id, 
            operator_id=task.courier_id,
            action="dispatch_completed",
            description="包裹成功派送到达目的地"
        ))

    else:
        raise HTTPException(status_code=400, detail="Invalid status. Must be 'start' or 'finish'")

    if logs_to_add:
        db.add_all(logs_to_add)
    db.commit()

    return {"parcel_id": req.parcel_id, "status": req.status}