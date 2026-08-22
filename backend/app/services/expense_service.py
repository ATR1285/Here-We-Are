from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone
import random
import string

from app.db.models.expense import (
    ExpenseClaim, ExpenseItem, ExpenseAuditTrail, ExpenseCategory, ExpenseStatus
)
from app.db.models.auth import User
from app.db.models.employee import Employee
from app.db.models.audit import AuditLog
from app.rules.expense_rules import ExpenseRulesEngine
from app.schemas.expense import ExpenseClaimCreate

def generate_claim_number():
    return "EXP-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def log_expense_audit(db: Session, claim_id: str, actor_id: str, action: str, from_status: str, to_status: str, remarks: str = None):
    audit = ExpenseAuditTrail(
        expense_claim_id=claim_id,
        actor_id=actor_id,
        action=action,
        from_status=from_status,
        to_status=to_status,
        remarks=remarks
    )
    db.add(audit)

def create_claim(db: Session, claim_in: ExpenseClaimCreate, current_user: User) -> ExpenseClaim:
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=403, detail="Must be an employee to create an expense claim")

    try:
        # Create Claim
        claim = ExpenseClaim(
            employee_id=employee.id,
            claim_number=generate_claim_number(),
            status=ExpenseStatus.DRAFT
        )
        db.add(claim)
        db.flush()

        # Add Items & Calculate Total
        items_dict = [{"amount": item.amount} for item in claim_in.items]
        total = ExpenseRulesEngine.validate_item_amounts(items_dict)
        
        for item_in in claim_in.items:
            category = db.query(ExpenseCategory).filter(ExpenseCategory.id == item_in.expense_category_id).first()
            if not category:
                raise HTTPException(status_code=400, detail="Invalid expense category")
            ExpenseRulesEngine.validate_category_limits(item_in.amount, category)
            
            item = ExpenseItem(
                expense_claim_id=claim.id,
                expense_category_id=category.id,
                expense_date=item_in.expense_date,
                description=item_in.description,
                amount=item_in.amount,
                receipt_reference=item_in.receipt_reference
            )
            db.add(item)
            
        claim.total_amount = total
        
        log_expense_audit(db, claim.id, current_user.id, "CREATED", None, ExpenseStatus.DRAFT)
        
        db.commit()
        db.refresh(claim)
        return claim
    except Exception as e:
        db.rollback()
        raise e

def submit_claim(db: Session, claim_id: str, current_user: User) -> ExpenseClaim:
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    
    claim = db.query(ExpenseClaim).with_for_update().filter(ExpenseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    if claim.employee_id != employee.id:
        raise HTTPException(status_code=403, detail="Cannot submit another employee's claim")
        
    ExpenseRulesEngine.validate_expense_transition(claim.status, ExpenseStatus.SUBMITTED)
    
    try:
        claim.status = ExpenseStatus.SUBMITTED
        claim.submitted_at = datetime.now(timezone.utc)
        
        log_expense_audit(db, claim.id, current_user.id, "SUBMITTED", ExpenseStatus.DRAFT, ExpenseStatus.SUBMITTED)
        
        sys_audit = AuditLog(
            user_id=current_user.id,
            action="EXPENSE_SUBMITTED",
            entity="ExpenseClaim",
            entity_id=claim.id,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(sys_audit)
        
        db.commit()
        db.refresh(claim)
        return claim
    except Exception as e:
        db.rollback()
        raise e

def manager_approve_claim(db: Session, claim_id: str, current_user: User) -> ExpenseClaim:
    manager_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    
    claim = db.query(ExpenseClaim).with_for_update().filter(ExpenseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    # Enforce actual reporting relationship
    if not manager_employee:
        raise HTTPException(status_code=403, detail="Approver must be an employee")
    
    if claim.employee_id == manager_employee.id:
        raise HTTPException(status_code=403, detail="Cannot approve your own expense claim")
        
    claim_owner = db.query(Employee).filter(Employee.id == claim.employee_id).first()
    if not claim_owner or claim_owner.manager_id != manager_employee.id:
        raise HTTPException(status_code=403, detail="Can only approve claims for your direct reports")
        
    ExpenseRulesEngine.validate_expense_transition(claim.status, ExpenseStatus.MANAGER_APPROVED)
    
    try:
        claim.status = ExpenseStatus.MANAGER_APPROVED
        log_expense_audit(db, claim.id, current_user.id, "MANAGER_APPROVED", ExpenseStatus.SUBMITTED, ExpenseStatus.MANAGER_APPROVED)
        
        sys_audit = AuditLog(
            user_id=current_user.id,
            action="EXPENSE_MANAGER_APPROVED",
            entity="ExpenseClaim",
            entity_id=claim.id,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(sys_audit)
        
        db.commit()
        db.refresh(claim)
        return claim
    except Exception as e:
        db.rollback()
        raise e

def finance_approve_claim(db: Session, claim_id: str, current_user: User) -> ExpenseClaim:
    claim = db.query(ExpenseClaim).with_for_update().filter(ExpenseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    ExpenseRulesEngine.validate_expense_transition(claim.status, ExpenseStatus.FINANCE_APPROVED)
    
    try:
        claim.status = ExpenseStatus.FINANCE_APPROVED
        log_expense_audit(db, claim.id, current_user.id, "FINANCE_APPROVED", ExpenseStatus.MANAGER_APPROVED, ExpenseStatus.FINANCE_APPROVED)
        
        db.commit()
        db.refresh(claim)
        return claim
    except Exception as e:
        db.rollback()
        raise e

def settle_claim(db: Session, claim_id: str, current_user: User) -> ExpenseClaim:
    claim = db.query(ExpenseClaim).with_for_update().filter(ExpenseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    ExpenseRulesEngine.validate_expense_transition(claim.status, ExpenseStatus.SETTLED)
    
    try:
        claim.status = ExpenseStatus.SETTLED
        claim.settled_at = datetime.now(timezone.utc)
        
        log_expense_audit(db, claim.id, current_user.id, "SETTLED", ExpenseStatus.FINANCE_APPROVED, ExpenseStatus.SETTLED)
        
        sys_audit = AuditLog(
            user_id=current_user.id,
            action="EXPENSE_SETTLED",
            entity="ExpenseClaim",
            entity_id=claim.id,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(sys_audit)
        
        db.commit()
        db.refresh(claim)
        return claim
    except Exception as e:
        db.rollback()
        raise e
