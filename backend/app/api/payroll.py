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
