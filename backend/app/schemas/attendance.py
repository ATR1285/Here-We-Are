from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.db.models.attendance import AttendanceStatus, RegularizationStatus

class AttendanceRecordBase(BaseModel):
    pass

class AttendanceRecordCreate(AttendanceRecordBase):
    pass

class AttendanceRecordResponse(AttendanceRecordBase):
    id: str
    employee_id: str
    attendance_date: str
    check_in_at: Optional[datetime] = None
    check_out_at: Optional[datetime] = None
    worked_minutes: int
    late_minutes: int
    early_departure_minutes: int
    overtime_minutes: int
    status: AttendanceStatus
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RegularizationRequestCreate(BaseModel):
    requested_check_in: Optional[datetime] = None
    requested_check_out: Optional[datetime] = None
    reason: str

class RegularizationRequestResponse(BaseModel):
    id: str
    attendance_record_id: str
    requested_check_in: Optional[datetime]
    requested_check_out: Optional[datetime]
    reason: str
    status: RegularizationStatus
    reviewer_id: Optional[str]
    reviewed_at: Optional[datetime]
    reviewer_comment: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RegularizationReviewRequest(BaseModel):
    reviewer_comment: Optional[str] = None
