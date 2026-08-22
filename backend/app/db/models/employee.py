import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class EmploymentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ON_LEAVE = "ON_LEAVE"
    TERMINATED = "TERMINATED"

class Employee(Base):
    __tablename__ = "employees"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    employee_code = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    
    employment_status = Column(Enum(EmploymentStatus), default=EmploymentStatus.ACTIVE, nullable=False)
    
    department_id = Column(String, ForeignKey("departments.id"), nullable=True)
    job_position_id = Column(String, ForeignKey("job_positions.id"), nullable=True)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    work_schedule_id = Column(String, ForeignKey("work_schedules.id"), nullable=True)
    
    manager_id = Column(String, ForeignKey("employees.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    department = relationship("Department", back_populates="employees")
    job_position = relationship("JobPosition", back_populates="employees")
    team = relationship("Team", back_populates="employees")
    work_schedule = relationship("WorkSchedule", back_populates="employees")
    
    manager = relationship("Employee", remote_side=[id], back_populates="subordinates")
    subordinates = relationship("Employee", back_populates="manager")
