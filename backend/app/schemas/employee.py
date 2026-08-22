from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.db.models.employee import EmploymentStatus
from app.schemas.organization import DepartmentResponse, JobPositionResponse, TeamResponse, WorkScheduleResponse

class EmployeeBase(BaseModel):
    employee_code: str
    user_id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    employment_status: EmploymentStatus = EmploymentStatus.ACTIVE
    department_id: Optional[str] = None
    job_position_id: Optional[str] = None
    team_id: Optional[str] = None
    work_schedule_id: Optional[str] = None
    manager_id: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    # Restricted fields that only HR/Admin can update
    employee_code: Optional[str] = None
    user_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    employment_status: Optional[EmploymentStatus] = None
    department_id: Optional[str] = None
    job_position_id: Optional[str] = None
    team_id: Optional[str] = None
    work_schedule_id: Optional[str] = None
    manager_id: Optional[str] = None

class EmployeeBasicUpdate(BaseModel):
    # Fields that an employee can update themselves
    phone: Optional[str] = None
    address: Optional[str] = None

class EmployeeResponse(EmployeeBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Employee360Response(EmployeeResponse):
    department: Optional[DepartmentResponse] = None
    job_position: Optional[JobPositionResponse] = None
    team: Optional[TeamResponse] = None
    work_schedule: Optional[WorkScheduleResponse] = None
    # We won't eagerly load manager details deeply to avoid loops, just ID is fine from EmployeeBase

    class Config:
        from_attributes = True
