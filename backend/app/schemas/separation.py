from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.db.models.separation import (
    ResignationStatus, SeparationStatus, ClearanceStatus, SettlementStatus
)

class ResignationRequestBase(BaseModel):
    requested_date: str
    reason: Optional[str] = None

class ResignationRequestCreate(ResignationRequestBase):
    pass

class ResignationRequestResponse(ResignationRequestBase):
    id: str
    employee_id: str
    status: ResignationStatus
    reviewer_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SeparationRecordResponse(BaseModel):
    id: str
    employee_id: str
    resignation_request_id: Optional[str]
    separation_date: str
    status: SeparationStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ClearanceChecklistResponse(BaseModel):
    id: str
    separation_record_id: str
    department: str
    clearance_type: str
    assigned_to: Optional[str]
    status: ClearanceStatus
    completed_at: Optional[datetime]
    remarks: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FinalSettlementResponse(BaseModel):
    id: str
    separation_record_id: str
    payroll_record_id: Optional[str]
    final_salary: Decimal
    lop_deduction: Decimal
    other_deductions: Decimal
    other_payments: Decimal
    net_settlement: Decimal
    status: SettlementStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
