from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models.auth import User
from app.api.auth import get_current_user
from app.core.permissions import require_permission
from app.db.models.employee import Employee
from app.schemas.payroll import PayrollRecordResponse
from app.services.payroll_service import process_payroll

router = APIRouter()

@router.post("/process/{employee_id}/{year}/{month}", response_model=PayrollRecordResponse)
def api_process_payroll(
    employee_id: str,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("process_payroll"))
):
    return process_payroll(db, employee_id, month, year, current_user)

@router.get("/me/{year}/{month}", response_model=PayrollRecordResponse)
def get_my_payroll(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.db.models.payroll import PayrollRecord
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=403, detail="User is not associated with an active employee profile")
    record = db.query(PayrollRecord).filter(
        PayrollRecord.employee_id == employee.id,
        PayrollRecord.payroll_year == year,
        PayrollRecord.payroll_month == month
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    return record

from pydantic import BaseModel
class SalaryStructureUpdate(BaseModel):
    basic: float
    hra: float
    standard: float
    bonus: float
    lta: float
    fixed: float

@router.get("/structure/{employee_id}")
def get_salary_structure(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("process_payroll"))
):
    from app.db.models.payroll import SalaryStructure
    struct = db.query(SalaryStructure).filter(SalaryStructure.employee_id == employee_id).first()
    if not struct:
        return {}
    return struct

@router.post("/structure/{employee_id}")
def update_salary_structure(
    employee_id: str,
    data: SalaryStructureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("process_payroll"))
):
    from app.db.models.payroll import SalaryStructure
    import uuid
    from datetime import datetime, timezone
    
    struct = db.query(SalaryStructure).filter(SalaryStructure.employee_id == employee_id).first()
    gross = data.basic + data.hra + data.standard + data.bonus + data.lta + data.fixed
    if struct:
        struct.base_salary = data.basic
        struct.gross_salary = gross
        struct.allowances = data.hra + data.standard + data.bonus + data.lta + data.fixed
    else:
        struct = SalaryStructure(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            base_salary=data.basic,
            gross_salary=gross,
            allowances=data.hra + data.standard + data.bonus + data.lta + data.fixed,
            currency="USD",
            status=True,
            effective_date=datetime.now(timezone.utc)
        )
        db.add(struct)
    
    db.commit()
    db.refresh(struct)
    return struct
