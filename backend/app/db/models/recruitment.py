import enum
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Numeric, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class RequisitionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

class PostingStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"

class CandidateStatus(str, enum.Enum):
    NEW = "NEW"
    IN_PROCESS = "IN_PROCESS"
    HIRED = "HIRED"
    REJECTED = "REJECTED"

class ApplicationStatus(str, enum.Enum):
    APPLIED = "APPLIED"
    SCREENING = "SCREENING"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    HIRED = "HIRED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"

class InterviewStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class OfferStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"

class OnboardingStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class JobRequisition(Base):
    __tablename__ = "job_requisitions"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    department_id = Column(String, ForeignKey("departments.id"), nullable=False)
    job_position_id = Column(String, ForeignKey("job_positions.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    openings = Column(Integer, default=1)
    employment_type = Column(String, nullable=True)
    status = Column(Enum(RequisitionStatus), default=RequisitionStatus.DRAFT, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    approved_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    requisition_id = Column(String, ForeignKey("job_requisitions.id"), nullable=False, unique=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(PostingStatus), default=PostingStatus.DRAFT, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    phone = Column(String, nullable=True)
    resume_reference = Column(String, nullable=True)
    source = Column(String, nullable=True)
    status = Column(Enum(CandidateStatus), default=CandidateStatus.NEW, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Application(Base):
    __tablename__ = "applications"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False)
    job_posting_id = Column(String, ForeignKey("job_postings.id"), nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.APPLIED, nullable=False)
    applied_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    current_stage = Column(String, nullable=True)
    recruiter_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    application_id = Column(String, ForeignKey("applications.id"), nullable=False)
    interviewer_id = Column(String, ForeignKey("users.id"), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=60)
    interview_type = Column(String, nullable=True)
    status = Column(Enum(InterviewStatus), default=InterviewStatus.SCHEDULED, nullable=False)
    feedback = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class JobOffer(Base):
    __tablename__ = "job_offers"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    application_id = Column(String, ForeignKey("applications.id"), nullable=False, unique=True)
    salary = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD")
    start_date = Column(String, nullable=False)
    employment_type = Column(String, nullable=False)
    status = Column(Enum(OfferStatus), default=OfferStatus.DRAFT, nullable=False)
    issued_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class OnboardingRecord(Base):
    __tablename__ = "onboarding_records"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    application_id = Column(String, ForeignKey("applications.id"), nullable=False, unique=True)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False)
    offer_id = Column(String, ForeignKey("job_offers.id"), nullable=False, unique=True)
    status = Column(Enum(OnboardingStatus), default=OnboardingStatus.NOT_STARTED, nullable=False)
    onboarding_start_date = Column(String, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    converted_employee_id = Column(String, ForeignKey("employees.id"), nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
