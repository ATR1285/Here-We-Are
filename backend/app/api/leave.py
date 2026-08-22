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
