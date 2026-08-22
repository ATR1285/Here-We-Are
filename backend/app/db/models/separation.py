import enum
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Numeric, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class ResignationStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"

class SeparationStatus(str, enum.Enum):
    PENDING = "PENDING"
    CLEARANCE_IN_PROGRESS = "CLEARANCE_IN_PROGRESS"
    SETTLEMENT_PENDING = "SETTLEMENT_PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class ClearanceStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    NOT_APPLICABLE = "NOT_APPLICABLE"

class SettlementStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PROCESSED = "PROCESSED"
    PAID = "PAID"

class ResignationRequest(Base):
    __tablename__ = "resignation_requests"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False, index=True)
    requested_date = Column(String, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(Enum(ResignationStatus), default=ResignationStatus.SUBMITTED, nullable=False)
    reviewer_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class SeparationRecord(Base):
    __tablename__ = "separation_records"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False, unique=True)
    resignation_request_id = Column(String, ForeignKey("resignation_requests.id"), nullable=True, unique=True)
    separation_date = Column(String, nullable=False)
    status = Column(Enum(SeparationStatus), default=SeparationStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class ClearanceChecklist(Base):
    __tablename__ = "clearance_checklists"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    separation_record_id = Column(String, ForeignKey("separation_records.id"), nullable=False, index=True)
    department = Column(String, nullable=False)
    clearance_type = Column(String, nullable=False)
    assigned_to = Column(String, ForeignKey("users.id"), nullable=True)
    status = Column(Enum(ClearanceStatus), default=ClearanceStatus.PENDING, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class FinalSettlement(Base):
    __tablename__ = "final_settlements"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    separation_record_id = Column(String, ForeignKey("separation_records.id"), nullable=False, unique=True)
    payroll_record_id = Column(String, ForeignKey("payroll_records.id"), nullable=True)
    final_salary = Column(Numeric(10, 2), default=0.00, nullable=False)
    lop_deduction = Column(Numeric(10, 2), default=0.00, nullable=False)
    other_deductions = Column(Numeric(10, 2), default=0.00, nullable=False)
    other_payments = Column(Numeric(10, 2), default=0.00, nullable=False)
    net_settlement = Column(Numeric(10, 2), default=0.00, nullable=False)
    status = Column(Enum(SettlementStatus), default=SettlementStatus.DRAFT, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
