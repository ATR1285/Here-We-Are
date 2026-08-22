from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.db.models.leave import LeaveStatus, LeaveAction

class LeaveTypeBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    annual_allocation: int
    carry_forward_allowed: bool
    max_carry_forward: int
    active_status: bool = True

class LeaveTypeCreate(LeaveTypeBase):
    pass

class LeaveTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    annual_allocation: Optional[int] = None
    carry_forward_allowed: Optional[bool] = None
    max_carry_forward: Optional[int] = None
    active_status: Optional[bool] = None

class LeaveTypeResponse(LeaveTypeBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LeaveBalanceResponse(BaseModel):
    id: str
    employee_id: str
    leave_type_id: str
    year: int
    allocated_days: int
    carried_forward_days: int
    used_days: int
    pending_days: int
    available_days: int

    class Config:
        from_attributes = True

class LeaveApplicationCreate(BaseModel):
    leave_type_id: str
    start_date: str
    end_date: str
    reason: str

class LeaveRequestResponse(BaseModel):
    id: str
    employee_id: str
    leave_type_id: str
    start_date: str
    end_date: str
    requested_days: int
    reason: str
    status: LeaveStatus
    reviewer_id: Optional[str]
    reviewed_at: Optional[datetime]
    rejection_reason: Optional[str]
    submitted_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LeaveApprovalResponse(BaseModel):
    id: str
    leave_request_id: str
    reviewer_id: str
    action: LeaveAction
    comments: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class LeaveReviewRequest(BaseModel):
    comments: Optional[str] = None
