import enum
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    HALF_DAY = "HALF_DAY"
    PENDING_REGULARIZATION = "PENDING_REGULARIZATION"
    LEAVE = "LEAVE"
    WEEK_OFF = "WEEK_OFF"
    HOLIDAY = "HOLIDAY"

class RegularizationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False, index=True)
    attendance_date = Column(String, nullable=False, index=True) # YYYY-MM-DD format
    
    check_in_at = Column(DateTime(timezone=True), nullable=True)
    check_out_at = Column(DateTime(timezone=True), nullable=True)
    
    worked_minutes = Column(Integer, default=0)
    late_minutes = Column(Integer, default=0)
    early_departure_minutes = Column(Integer, default=0)
    overtime_minutes = Column(Integer, default=0)
    
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.ABSENT, nullable=False)
    source = Column(String, default="SYSTEM")
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("employee_id", "attendance_date", name="uix_employee_attendance_date"),
    )

    employee = relationship("Employee")
    regularization_requests = relationship("AttendanceRegularizationRequest", back_populates="attendance_record")


class AttendanceRegularizationRequest(Base):
    __tablename__ = "attendance_regularization_requests"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    attendance_record_id = Column(String, ForeignKey("attendance_records.id"), nullable=False, index=True)
    
    requested_check_in = Column(DateTime(timezone=True), nullable=True)
    requested_check_out = Column(DateTime(timezone=True), nullable=True)
    
    reason = Column(String, nullable=False)
    status = Column(Enum(RegularizationStatus), default=RegularizationStatus.PENDING, nullable=False)
    
    reviewer_id = Column(String, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewer_comment = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    attendance_record = relationship("AttendanceRecord", back_populates="regularization_requests")
    reviewer = relationship("User")
