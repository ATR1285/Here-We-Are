from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models.auth import User
from app.db.models.employee import Employee, EmploymentStatus
from app.core.permissions import get_current_session_user, require_permission
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeBasicUpdate, EmployeeResponse, Employee360Response
from app.services.employee_service import EmployeeService

router = APIRouter()

@router.get("/me", response_model=Employee360Response)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("view_own_profile"))
):
    # Determine employee_id from user mapping
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return EmployeeService.get_employee(db, current_user, employee.id, view_all=False)

@router.get("", response_model=List[EmployeeResponse])
def get_employees(
    department_id: str = None,
    status: EmploymentStatus = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("view_all_employees"))
):
    return EmployeeService.get_employees(db, current_user, view_all=True, department_id=department_id, status=status)

@router.post("", response_model=EmployeeResponse)
def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_employees"))
):
    return EmployeeService.create_employee(db, current_user, data)

@router.get("/{employee_id}", response_model=Employee360Response)
def get_employee(
    employee_id: str,
    db: Session = Depends(get_db),
    # If the user has view_all_employees, we let them proceed and the service checks view_all=True
    # Since we can't easily do dynamic dependency fallback here, we use the base dependency and check inside the service.
    current_user: User = Depends(get_current_session_user)
):
    # In a full system, we'd check if user has view_all_employees role directly here or in service.
    # For simplicity, we just pass view_all=True if they have the manage role.
    has_manage = current_user.role.name in ["HR", "Admin"]
    return EmployeeService.get_employee(db, current_user, employee_id, view_all=has_manage)

@router.patch("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: str,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_employees"))
):
    return EmployeeService.update_employee(db, current_user, employee_id, data)

@router.patch("/{employee_id}/basic", response_model=EmployeeResponse)
def update_own_employee(
    employee_id: str,
    data: EmployeeBasicUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("edit_basic_info"))
):
    return EmployeeService.update_own_employee(db, current_user, employee_id, data)

@router.delete("/{employee_id}")
def deactivate_employee(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_employees"))
):
    return EmployeeService.deactivate_employee(db, current_user, employee_id)
