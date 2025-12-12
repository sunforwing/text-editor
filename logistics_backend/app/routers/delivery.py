from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import all_models as models
from pydantic import BaseModel
import datetime

router = APIRouter(prefix="/api/v1/delivery-tasks", tags=["Delivery"])

class DeliveryResult(BaseModel):
    result: str # success, fail
    signer: str = None
    fail_reason: str = None
    geo_location: str = None

@router.post("/{tracking_number}/result")
def report_delivery_result(tracking_number: str, res: DeliveryResult, db: Session = Depends(get_db)):
    # 1. 查找派送任务
    task = db.query(models.DeliveryTask).filter(models.DeliveryTask.parcel_id == tracking_number).first()
    if not task:
        raise HTTPException(status_code=404, detail="Delivery task not found")
    
    # 2. 查找包裹
    parcel = db.query(models.Parcel).filter(models.Parcel.tracking_number == tracking_number).first()
    
    # 3. 更新状态
    if res.result == "success":
        task.status = "success"
        parcel.status = "delivered"
        log_desc = f"已签收, 签收人: {res.signer}"
    else:
        task.status = "fail"
        task.fail_reason = res.fail_reason
        parcel.status = "exception" # 或回退 sorting
        log_desc = f"派送失败: {res.fail_reason}"
    
    task.completed_at = datetime.datetime.now()
    
    # 4. 记录日志
    log = models.ParcelLog(
        parcel_id=tracking_number,
        action="sign_off" if res.result == "success" else "exception",
        description=log_desc,
        operator_id=task.courier_id
    )
    db.add(log)
    db.commit()
    
    return {"status": "updated"}