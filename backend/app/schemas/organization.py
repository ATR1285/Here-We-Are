from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DepartmentBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    active_status: bool = True

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    active_status: Optional[bool] = None

class DepartmentResponse(DepartmentBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class JobPositionBase(BaseModel):
    title: str
    code: Optional[str] = None
    department_id: str
    description: Optional[str] = None
    active_status: bool = True

class JobPositionCreate(JobPositionBase):
    pass

class JobPositionUpdate(BaseModel):
    title: Optional[str] = None
    code: Optional[str] = None
    department_id: Optional[str] = None
    description: Optional[str] = None
    active_status: Optional[bool] = None

class JobPositionResponse(JobPositionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TeamBase(BaseModel):
    name: str
    code: Optional[str] = None
    department_id: str
    description: Optional[str] = None
    active_status: bool = True

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    department_id: Optional[str] = None
    description: Optional[str] = None
    active_status: Optional[bool] = None

class TeamResponse(TeamBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WorkScheduleBase(BaseModel):
    name: str
    working_days: str
    start_time: str
    end_time: str
    timezone: str = "UTC"
    active_status: bool = True

class WorkScheduleCreate(WorkScheduleBase):
    pass

class WorkScheduleUpdate(BaseModel):
    name: Optional[str] = None
    working_days: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    timezone: Optional[str] = None
    active_status: Optional[bool] = None

class WorkScheduleResponse(WorkScheduleBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
