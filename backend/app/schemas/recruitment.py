from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.db.models.recruitment import (
    RequisitionStatus, PostingStatus, CandidateStatus, 
    ApplicationStatus, InterviewStatus, OfferStatus, OnboardingStatus
)

class JobRequisitionBase(BaseModel):
    department_id: str
    job_position_id: str
    title: str
    description: Optional[str] = None
    openings: int = 1
    employment_type: Optional[str] = None

class JobRequisitionCreate(JobRequisitionBase):
    pass

class JobRequisitionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    openings: Optional[int] = None

class JobRequisitionResponse(JobRequisitionBase):
    id: str
    status: RequisitionStatus
    created_by: str
    approved_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class JobPostingBase(BaseModel):
    title: str
    description: Optional[str] = None
    expires_at: Optional[datetime] = None

class JobPostingCreate(JobPostingBase):
    requisition_id: str

class JobPostingResponse(JobPostingBase):
    id: str
    requisition_id: str
    status: PostingStatus
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CandidateBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    resume_reference: Optional[str] = None
    source: Optional[str] = None

class CandidateCreate(CandidateBase):
    pass

class CandidateResponse(CandidateBase):
    id: str
    status: CandidateStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ApplicationBase(BaseModel):
    candidate_id: str
    job_posting_id: str
    current_stage: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationResponse(ApplicationBase):
    id: str
    status: ApplicationStatus
    applied_at: datetime
    recruiter_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InterviewBase(BaseModel):
    application_id: str
    interviewer_id: str
    scheduled_at: datetime
    duration_minutes: int = 60
    interview_type: Optional[str] = None

class InterviewCreate(InterviewBase):
    pass

class InterviewUpdate(BaseModel):
    feedback: Optional[str] = None
    rating: Optional[int] = None

class InterviewResponse(InterviewBase):
    id: str
    status: InterviewStatus
    feedback: Optional[str]
    rating: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class JobOfferBase(BaseModel):
    application_id: str
    salary: Decimal
    currency: str = "USD"
    start_date: str
    employment_type: str

class JobOfferCreate(JobOfferBase):
    pass

class JobOfferResponse(JobOfferBase):
    id: str
    status: OfferStatus
    issued_at: Optional[datetime]
    accepted_at: Optional[datetime]
    rejected_at: Optional[datetime]
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OnboardingBase(BaseModel):
    application_id: str
    candidate_id: str
    offer_id: str
    onboarding_start_date: Optional[str] = None

class OnboardingCreate(OnboardingBase):
    pass

class OnboardingUpdate(BaseModel):
    onboarding_start_date: Optional[str] = None

class OnboardingResponse(OnboardingBase):
    id: str
    status: OnboardingStatus
    completed_at: Optional[datetime]
    converted_employee_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
