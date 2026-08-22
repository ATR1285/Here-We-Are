import enum
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Boolean, UniqueConstraint, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class PayrollStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FINALIZED = "FINALIZED"

class ComponentType(str, enum.Enum):
    EARNING = "EARNING"
    DEDUCTION = "DEDUCTION"

class SalaryStructure(Base):
    __tablename__ = "salary_structures"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False, index=True)
    effective_from = Column(String, nullable=False)
    effective_to = Column(String, nullable=True)
    currency = Column(String, default="USD")
    pay_frequency = Column(String, default="MONTHLY")
    basic_salary = Column(Numeric(10, 2), default=0.00)
    gross_salary = Column(Numeric(10, 2), default=0.00)
    status = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    employee = relationship("Employee")
    components = relationship("SalaryComponent", back_populates="structure")

class SalaryComponent(Base):
    __tablename__ = "salary_components"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    salary_structure_id = Column(String, ForeignKey("salary_structures.id"), nullable=False, index=True)
    component_name = Column(String, nullable=False)
    component_type = Column(Enum(ComponentType), nullable=False)
    calculation_type = Column(String, nullable=False)  # e.g., 'FIXED', 'PERCENTAGE'
    amount = Column(Numeric(10, 2), default=0.00)
    percentage = Column(Numeric(5, 2), default=0.00)
    taxable = Column(Boolean, default=True)
    active_status = Column(Boolean, default=True)

    structure = relationship("SalaryStructure", back_populates="components")

class PayrollRecord(Base):
    __tablename__ = "payroll_records"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False, index=True)
    payroll_month = Column(Integer, nullable=False)
    payroll_year = Column(Integer, nullable=False)
    salary_structure_id = Column(String, ForeignKey("salary_structures.id"), nullable=False)
    
    working_days = Column(Integer, default=0)
    payable_days = Column(Integer, default=0)
    absent_days = Column(Integer, default=0)
    leave_days = Column(Integer, default=0)
    lop_days = Column(Integer, default=0)
    overtime_minutes = Column(Integer, default=0)
    
    gross_earnings = Column(Numeric(10, 2), default=0.00)
    total_deductions = Column(Numeric(10, 2), default=0.00)
    lop_deduction = Column(Numeric(10, 2), default=0.00)
    net_pay = Column(Numeric(10, 2), default=0.00)
    
    status = Column(Enum(PayrollStatus), default=PayrollStatus.DRAFT, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processed_by = Column(String, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("employee_id", "payroll_month", "payroll_year", name="uix_employee_payroll_period"),
    )

    employee = relationship("Employee")
    salary_structure = relationship("SalaryStructure")
    processor = relationship("User")

class Payslip(Base):
    __tablename__ = "payslips"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    payroll_record_id = Column(String, ForeignKey("payroll_records.id"), nullable=False, unique=True)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False, index=True)
    payslip_number = Column(String, unique=True, nullable=False)
    issued_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    generated_by = Column(String, ForeignKey("users.id"), nullable=False)
    document_reference = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    payroll_record = relationship("PayrollRecord")
    employee = relationship("Employee")
    generator = relationship("User")
