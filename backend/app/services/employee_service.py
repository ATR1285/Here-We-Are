from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db.models.employee import Employee, EmploymentStatus
from app.db.models.auth import User
from app.db.models.audit import AuditLog
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeBasicUpdate
import datetime
import uuid

def create_audit_log(db: Session, user_id: str, action: str, entity: str, entity_id: str):
    audit = AuditLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(audit)
    db.commit()

class EmployeeService:
    @staticmethod
    def get_employee(db: Session, current_user: User, employee_id: str, view_all: bool):
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Resource Ownership Check
        if not view_all and employee.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden: You do not own this resource")
            
        return employee

    @staticmethod
    def get_employees(db: Session, current_user: User, view_all: bool, department_id: str = None, status: EmploymentStatus = None):
        if not view_all:
            raise HTTPException(status_code=403, detail="Forbidden: Missing HR privileges")
            
        query = db.query(Employee)
        if department_id:
            query = query.filter(Employee.department_id == department_id)
        if status:
            query = query.filter(Employee.employment_status == status)
            
        return query.all()

    @staticmethod
    def create_employee(db: Session, current_user: User, data: EmployeeCreate):
        # Validate unique employee_code
        if db.query(Employee).filter(Employee.employee_code == data.employee_code).first():
            raise HTTPException(status_code=409, detail="Employee code already exists")
            
        # Validate unique user_id mapping
        if db.query(Employee).filter(Employee.user_id == data.user_id).first():
            raise HTTPException(status_code=409, detail="User already mapped to an employee")
            
        employee = Employee(**data.model_dump())
        db.add(employee)
        db.commit()
        db.refresh(employee)
        
        create_audit_log(db, current_user.id, "EMPLOYEE_CREATED", "Employee", employee.id)
        return employee

    @staticmethod
    def update_employee(db: Session, current_user: User, employee_id: str, data: EmployeeUpdate):
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
            
        # Prevent circular or self reporting
        if data.manager_id == employee.id:
            raise HTTPException(status_code=422, detail="Employee cannot report to themselves")
            
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(employee, key, value)
            
        db.commit()
        db.refresh(employee)
        
        create_audit_log(db, current_user.id, "EMPLOYEE_UPDATED", "Employee", employee.id)
        return employee

    @staticmethod
    def update_own_employee(db: Session, current_user: User, employee_id: str, data: EmployeeBasicUpdate):
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
            
        if employee.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden: You do not own this resource")
            
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(employee, key, value)
            
        db.commit()
        db.refresh(employee)
        
        create_audit_log(db, current_user.id, "EMPLOYEE_BASIC_UPDATED", "Employee", employee.id)
        return employee

    @staticmethod
    def deactivate_employee(db: Session, current_user: User, employee_id: str):
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
            
        employee.employment_status = EmploymentStatus.INACTIVE
        db.commit()
        db.refresh(employee)
        
        create_audit_log(db, current_user.id, "EMPLOYEE_DEACTIVATED", "Employee", employee.id)
        return employee
