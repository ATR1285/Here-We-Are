from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List

from app.db.database import get_db
from app.db.models.auth import User
from app.api.auth import get_current_user
from app.core.permissions import require_permission
from app.db.models.employee import Employee
from app.schemas.attendance import AttendanceRecordResponse
from app.services.attendance_service import check_in, check_out

router = APIRouter()

@router.post("/check-in", response_model=AttendanceRecordResponse)
def api_check_in(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=403, detail="User is not associated with an active employee profile")
    
    return check_in(db, employee)

@router.post("/check-out", response_model=AttendanceRecordResponse)
def api_check_out(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=403, detail="User is not associated with an active employee profile")
    
    return check_out(db, employee)

@router.get("/me", response_model=List[AttendanceRecordResponse])
def get_my_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.db.models.attendance import AttendanceRecord
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=403, detail="User is not associated with an active employee profile")
    
    return db.query(AttendanceRecord).filter(AttendanceRecord.employee_id == employee.id).order_by(AttendanceRecord.attendance_date.desc()).all()

@router.get("", response_model=List[AttendanceRecordResponse])
def get_all_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("view_all_attendance"))
):
    from app.db.models.attendance import AttendanceRecord
    return db.query(AttendanceRecord).order_by(AttendanceRecord.attendance_date.desc()).all()
