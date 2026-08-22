from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Department(Base):
    __tablename__ = "departments"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    name = Column(String, unique=True, index=True, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    active_status = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    job_positions = relationship("JobPosition", back_populates="department")
    teams = relationship("Team", back_populates="department")
    employees = relationship("Employee", back_populates="department")


class JobPosition(Base):
    __tablename__ = "job_positions"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    title = Column(String, nullable=False)
    code = Column(String, unique=True, index=True, nullable=True)
    department_id = Column(String, ForeignKey("departments.id"), nullable=False)
    description = Column(String, nullable=True)
    active_status = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    department = relationship("Department", back_populates="job_positions")
    employees = relationship("Employee", back_populates="job_position")


class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True, nullable=True)
    department_id = Column(String, ForeignKey("departments.id"), nullable=False)
    description = Column(String, nullable=True)
    active_status = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    department = relationship("Department", back_populates="teams")
    employees = relationship("Employee", back_populates="team")


class WorkSchedule(Base):
    __tablename__ = "work_schedules"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    name = Column(String, nullable=False)
    working_days = Column(String, nullable=False) # e.g. "Monday-Friday"
    start_time = Column(String, nullable=False) # e.g. "09:00"
    end_time = Column(String, nullable=False) # e.g. "17:00"
    timezone = Column(String, nullable=False, default="UTC")
    active_status = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    employees = relationship("Employee", back_populates="work_schedule")
