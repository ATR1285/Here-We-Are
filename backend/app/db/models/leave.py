import enum
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class LeaveStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class LeaveAction(str, enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class LeaveType(Base):
    __tablename__ = "leave_types"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    annual_allocation = Column(Integer, default=0)
    carry_forward_allowed = Column(Boolean, default=False)
    max_carry_forward = Column(Integer, default=0)
    active_status = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False, index=True)
    leave_type_id = Column(String, ForeignKey("leave_types.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    
    allocated_days = Column(Integer, default=0)
    carried_forward_days = Column(Integer, default=0)
    used_days = Column(Integer, default=0)
    pending_days = Column(Integer, default=0)
    available_days = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("employee_id", "leave_type_id", "year", name="uix_employee_leave_type_year"),
    )
    
    employee = relationship("Employee")
    leave_type = relationship("LeaveType")

class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False, index=True)
    leave_type_id = Column(String, ForeignKey("leave_types.id"), nullable=False, index=True)
    
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    requested_days = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING, nullable=False)
    
    reviewer_id = Column(String, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(String, nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    employee = relationship("Employee")
    leave_type = relationship("LeaveType")
    reviewer = relationship("User")
    approvals = relationship("LeaveApproval", back_populates="leave_request")

class LeaveApproval(Base):
    __tablename__ = "leave_approvals"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    leave_request_id = Column(String, ForeignKey("leave_requests.id"), nullable=False, index=True)
    reviewer_id = Column(String, ForeignKey("users.id"), nullable=False)
    action = Column(Enum(LeaveAction), nullable=False)
    comments = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    leave_request = relationship("LeaveRequest", back_populates="approvals")
    reviewer = relationship("User")
