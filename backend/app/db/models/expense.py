import enum
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Numeric, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class ExpenseStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    MANAGER_APPROVED = "MANAGER_APPROVED"
    FINANCE_APPROVED = "FINANCE_APPROVED"
    REJECTED = "REJECTED"
    SETTLED = "SETTLED"

class ExpenseCategory(Base):
    __tablename__ = "expense_categories"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    daily_limit = Column(Numeric(10, 2), nullable=True)
    monthly_limit = Column(Numeric(10, 2), nullable=True)
    active_status = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class ExpenseClaim(Base):
    __tablename__ = "expense_claims"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False, index=True)
    claim_number = Column(String, nullable=False, unique=True)
    claim_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    total_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    status = Column(Enum(ExpenseStatus), default=ExpenseStatus.DRAFT, nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    settled_at = Column(DateTime(timezone=True), nullable=True)
    payroll_record_id = Column(String, ForeignKey("payroll_records.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class ExpenseItem(Base):
    __tablename__ = "expense_items"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    expense_claim_id = Column(String, ForeignKey("expense_claims.id"), nullable=False, index=True)
    expense_category_id = Column(String, ForeignKey("expense_categories.id"), nullable=False)
    expense_date = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    receipt_reference = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class ExpenseAuditTrail(Base):
    __tablename__ = "expense_audit_trails"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    expense_claim_id = Column(String, ForeignKey("expense_claims.id"), nullable=False, index=True)
    actor_id = Column(String, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
