from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.db.models.payroll import PayrollStatus, ComponentType

class SalaryComponentBase(BaseModel):
    component_name: str
    component_type: ComponentType
    calculation_type: str
    amount: Decimal = Decimal('0.00')
    percentage: Decimal = Decimal('0.00')
    taxable: bool = True
    active_status: bool = True

class SalaryComponentCreate(SalaryComponentBase):
    pass

class SalaryStructureBase(BaseModel):
    effective_from: str
    effective_to: Optional[str] = None
    currency: str = "USD"
    pay_frequency: str = "MONTHLY"
    basic_salary: Decimal = Decimal('0.00')
    gross_salary: Decimal = Decimal('0.00')
    status: bool = True

class SalaryStructureCreate(SalaryStructureBase):
    employee_id: str
    components: List[SalaryComponentCreate] = []

class SalaryStructureResponse(SalaryStructureBase):
    id: str
    employee_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PayrollRecordResponse(BaseModel):
    id: str
    employee_id: str
    payroll_month: int
    payroll_year: int
    salary_structure_id: str
    
    working_days: int
    payable_days: int
    absent_days: int
    leave_days: int
    lop_days: int
    overtime_minutes: int
    
    gross_earnings: Decimal
    total_deductions: Decimal
    lop_deduction: Decimal
    net_pay: Decimal
    
    status: PayrollStatus
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class PayslipResponse(BaseModel):
    id: str
    payroll_record_id: str
    employee_id: str
    payslip_number: str
    issued_at: datetime
    document_reference: Optional[str]
    
    class Config:
        from_attributes = True
