from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db.models.organization import Department, JobPosition, Team, WorkSchedule
from app.schemas.organization import DepartmentCreate, DepartmentUpdate, JobPositionCreate, JobPositionUpdate, TeamCreate, TeamUpdate, WorkScheduleCreate, WorkScheduleUpdate

class OrganizationService:
    @staticmethod
    def get_departments(db: Session):
        return db.query(Department).all()

    @staticmethod
    def create_department(db: Session, data: DepartmentCreate):
        department = Department(**data.model_dump())
        db.add(department)
        db.commit()
        db.refresh(department)
        return department

    @staticmethod
    def update_department(db: Session, department_id: str, data: DepartmentUpdate):
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(department, key, value)
        db.commit()
        db.refresh(department)
        return department

    @staticmethod
    def get_job_positions(db: Session):
        return db.query(JobPosition).all()

    @staticmethod
    def create_job_position(db: Session, data: JobPositionCreate):
        if not db.query(Department).filter(Department.id == data.department_id).first():
            raise HTTPException(status_code=422, detail="Invalid department_id")
        job_position = JobPosition(**data.model_dump())
        db.add(job_position)
        db.commit()
        db.refresh(job_position)
        return job_position

    @staticmethod
    def get_teams(db: Session):
        return db.query(Team).all()

    @staticmethod
    def create_team(db: Session, data: TeamCreate):
        if not db.query(Department).filter(Department.id == data.department_id).first():
            raise HTTPException(status_code=422, detail="Invalid department_id")
        team = Team(**data.model_dump())
        db.add(team)
        db.commit()
        db.refresh(team)
        return team

    @staticmethod
    def get_work_schedules(db: Session):
        return db.query(WorkSchedule).all()

    @staticmethod
    def create_work_schedule(db: Session, data: WorkScheduleCreate):
        work_schedule = WorkSchedule(**data.model_dump())
        db.add(work_schedule)
        db.commit()
        db.refresh(work_schedule)
        return work_schedule
