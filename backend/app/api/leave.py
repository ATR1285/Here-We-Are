from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models.auth import User
from app.api.auth import get_current_user
from app.core.permissions import require_permission
from app.db.models.employee import Employee
from app.schemas.leave import LeaveApplicationCreate, LeaveRequestResponse, LeaveReviewRequest, LeaveBalanceResponse
from app.services.leave_service import apply_leave, approve_leave, reject_leave, cancel_leave

router = APIRouter()

@router.post("/apply", response_model=LeaveRequestResponse)
def api_apply_leave(
    request: LeaveApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=403, detail="User is not associated with an active employee profile")
        
    return apply_leave(db, employee, request.leave_type_id, request.start_date, request.end_date, request.reason)

@router.post("/{id}/cancel", response_model=LeaveRequestResponse)
def api_cancel_leave(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=403, detail="User is not associated with an active employee profile")
        
    return cancel_leave(db, id, employee)

@router.post("/{id}/approve", response_model=LeaveRequestResponse)
def api_approve_leave(
    id: str,
    request: LeaveReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("approve_leave"))
):
    return approve_leave(db, id, current_user, request.comments)

@router.post("/{id}/reject", response_model=LeaveRequestResponse)
def api_reject_leave(
    id: str,
    request: LeaveReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reject_leave"))
):
    return reject_leave(db, id, current_user, request.comments)

@router.get("/me/requests", response_model=List[LeaveRequestResponse])
def get_my_leave_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.db.models.leave import LeaveRequest
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=403, detail="User is not associated with an active employee profile")
    return db.query(LeaveRequest).filter(LeaveRequest.employee_id == employee.id).order_by(LeaveRequest.created_at.desc()).all()

@router.get("/me/balances", response_model=List[LeaveBalanceResponse])
def get_my_leave_balances(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.db.models.leave import LeaveBalance
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=403, detail="User is not associated with an active employee profile")
    return db.query(LeaveBalance).filter(LeaveBalance.employee_id == employee.id).all()

@router.get("/requests", response_model=List[LeaveRequestResponse])
def get_all_leave_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("approve_leave"))
):
    from app.db.models.leave import LeaveRequest
    return db.query(LeaveRequest).order_by(LeaveRequest.created_at.desc()).all()

# Dummy schema for LeaveType since it may not be in schemas
from pydantic import BaseModel
class LeaveTypeResponse(BaseModel):
    id: str
    name: str
    code: str
    class Config:
        from_attributes = True

@router.get("/types", response_model=List[LeaveTypeResponse])
def get_leave_types(db: Session = Depends(get_db)):
    from app.db.models.leave import LeaveType
    return db.query(LeaveType).filter(LeaveType.active_status == True).all()
