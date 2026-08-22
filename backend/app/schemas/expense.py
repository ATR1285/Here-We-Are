from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.db.models.expense import ExpenseStatus

class ExpenseCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    daily_limit: Optional[Decimal] = None
    monthly_limit: Optional[Decimal] = None
    active_status: bool = True

class ExpenseCategoryCreate(ExpenseCategoryBase):
    pass

class ExpenseCategoryResponse(ExpenseCategoryBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ExpenseItemBase(BaseModel):
    expense_category_id: str
    expense_date: str
    description: str
    amount: Decimal
    receipt_reference: Optional[str] = None

class ExpenseItemCreate(ExpenseItemBase):
    pass

class ExpenseItemResponse(ExpenseItemBase):
    id: str
    expense_claim_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ExpenseClaimBase(BaseModel):
    pass

class ExpenseClaimCreate(ExpenseClaimBase):
    items: List[ExpenseItemCreate]

class ExpenseClaimResponse(ExpenseClaimBase):
    id: str
    employee_id: str
    claim_number: str
    claim_date: datetime
    total_amount: Decimal
    status: ExpenseStatus
    submitted_at: Optional[datetime]
    settled_at: Optional[datetime]
    payroll_record_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: List[ExpenseItemResponse]

    class Config:
        from_attributes = True

class ExpenseAuditTrailResponse(BaseModel):
    id: str
    expense_claim_id: str
    actor_id: str
    action: str
    from_status: Optional[str]
    to_status: Optional[str]
    remarks: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ExpenseRejectRequest(BaseModel):
    remarks: str
