from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.db.models.performance import CycleStatus, GoalStatus, ReviewStatus

class PerformanceCycleBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: str
    end_date: str

class PerformanceCycleCreate(PerformanceCycleBase):
    pass

class PerformanceCycleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class PerformanceCycleResponse(PerformanceCycleBase):
    id: str
    status: CycleStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PerformanceGoalBase(BaseModel):
    title: str
    description: Optional[str] = None
    target_value: Optional[str] = None
    measurement_unit: Optional[str] = None
    progress_value: Decimal = Decimal('0.00')
    weight: Decimal = Decimal('0.00')

class PerformanceGoalCreate(PerformanceGoalBase):
    cycle_id: str

class PerformanceGoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_value: Optional[str] = None
    measurement_unit: Optional[str] = None
    progress_value: Optional[Decimal] = None
    weight: Optional[Decimal] = None

class PerformanceGoalResponse(PerformanceGoalBase):
    id: str
    employee_id: str
    cycle_id: str
    status: GoalStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PerformanceReviewCreate(BaseModel):
    cycle_id: str

class SelfReviewSubmit(BaseModel):
    self_rating: int
    self_comments: Optional[str] = None

class ManagerReviewSubmit(BaseModel):
    manager_rating: int
    manager_comments: Optional[str] = None

class PerformanceReviewResponse(BaseModel):
    id: str
    employee_id: str
    cycle_id: str
    reviewer_id: Optional[str]
    self_rating: Optional[int]
    manager_rating: Optional[int]
    final_rating: Optional[Decimal]
    self_comments: Optional[str]
    manager_comments: Optional[str]
    status: ReviewStatus
    submitted_at: Optional[datetime]
    finalized_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PerformanceReviewHistoryResponse(BaseModel):
    id: str
    review_id: str
    actor_id: str
    action: str
    previous_state: Optional[str]
    new_state: Optional[str]
    comments: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
