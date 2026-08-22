from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone
from app.db.models.leave import LeaveRequest, LeaveBalance, LeaveApproval, LeaveStatus, LeaveAction
from app.db.models.employee import Employee
from app.db.models.auth import User
from app.db.models.audit import AuditLog
from app.rules.leave_rules import LeaveRulesEngine

def apply_leave(db: Session, employee: Employee, leave_type_id: str, start_date: str, end_date: str, reason: str) -> LeaveRequest:
    # 1. Lock the balance transactionally (row locking would be with_for_update, simpler implementation here)
    year = datetime.strptime(start_date, "%Y-%m-%d").year
    balance = db.query(LeaveBalance).with_for_update().filter(
        LeaveBalance.employee_id == employee.id,
        LeaveBalance.leave_type_id == leave_type_id,
        LeaveBalance.year == year
    ).first()
    
    if not balance:
        raise HTTPException(status_code=404, detail="Leave balance not found for the requested type and year")
        
    # 2. Recalculate working days from authoritative rules
    calculated_days = LeaveRulesEngine.calculate_leave_days(start_date, end_date, employee.work_schedule)
    
    # 3. Validate Balance
    LeaveRulesEngine.validate_leave_balance(balance, calculated_days)
    
    # 4. Validate Overlap
    LeaveRulesEngine.validate_overlap(db, employee.id, start_date, end_date)
    
    # 5. Create Request
    req = LeaveRequest(
        employee_id=employee.id,
        leave_type_id=leave_type_id,
        start_date=start_date,
        end_date=end_date,
        requested_days=calculated_days,
        reason=reason,
        status=LeaveStatus.PENDING
    )
    db.add(req)
    
    # 6. Increment Pending Days & Recalculate Available
    balance.pending_days += calculated_days
    balance.available_days = LeaveRulesEngine.calculate_available_balance(balance)
    
    # 7. Audit Log
    now = datetime.now(timezone.utc)
    audit = AuditLog(
        user_id=employee.user_id,
        action="LEAVE_APPLIED",
        entity="LeaveRequest",
        entity_id=req.id,
        timestamp=now
    )
    db.add(audit)
    
    db.commit()
    db.refresh(req)
    return req

def approve_leave(db: Session, request_id: str, reviewer: User, comments: str = None) -> LeaveRequest:
    req = db.query(LeaveRequest).with_for_update().filter(LeaveRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Leave request not found")
        
    if req.status != LeaveStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Cannot approve request in {req.status} state")
        
    if req.employee.user_id == reviewer.id:
        raise HTTPException(status_code=403, detail="Employees cannot approve their own leave")
        
    year = datetime.strptime(req.start_date, "%Y-%m-%d").year
    balance = db.query(LeaveBalance).with_for_update().filter(
        LeaveBalance.employee_id == req.employee_id,
        LeaveBalance.leave_type_id == req.leave_type_id,
        LeaveBalance.year == year
    ).first()
    
    # Update balance
    balance.pending_days -= req.requested_days
    balance.used_days += req.requested_days
    balance.available_days = LeaveRulesEngine.calculate_available_balance(balance)
    
    # Update request
    now = datetime.now(timezone.utc)
    req.status = LeaveStatus.APPROVED
    req.reviewer_id = reviewer.id
    req.reviewed_at = now
    
    # Create Approval record
    approval = LeaveApproval(
        leave_request_id=req.id,
        reviewer_id=reviewer.id,
        action=LeaveAction.APPROVED,
        comments=comments,
        created_at=now
    )
    db.add(approval)
    
    # Audit
    audit = AuditLog(
        user_id=reviewer.id,
        action="LEAVE_APPROVED",
        entity="LeaveRequest",
        entity_id=req.id,
        timestamp=now
    )
    db.add(audit)
    
    db.commit()
    db.refresh(req)
    return req

def reject_leave(db: Session, request_id: str, reviewer: User, comments: str = None) -> LeaveRequest:
    req = db.query(LeaveRequest).with_for_update().filter(LeaveRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Leave request not found")
        
    if req.status != LeaveStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Cannot reject request in {req.status} state")
        
    year = datetime.strptime(req.start_date, "%Y-%m-%d").year
    balance = db.query(LeaveBalance).with_for_update().filter(
        LeaveBalance.employee_id == req.employee_id,
        LeaveBalance.leave_type_id == req.leave_type_id,
        LeaveBalance.year == year
    ).first()
    
    # Update balance
    balance.pending_days -= req.requested_days
    balance.available_days = LeaveRulesEngine.calculate_available_balance(balance)
    
    # Update request
    now = datetime.now(timezone.utc)
    req.status = LeaveStatus.REJECTED
    req.reviewer_id = reviewer.id
    req.reviewed_at = now
    req.rejection_reason = comments
    
    # Create Approval record
    approval = LeaveApproval(
        leave_request_id=req.id,
        reviewer_id=reviewer.id,
        action=LeaveAction.REJECTED,
        comments=comments,
        created_at=now
    )
    db.add(approval)
    
    # Audit
    audit = AuditLog(
        user_id=reviewer.id,
        action="LEAVE_REJECTED",
        entity="LeaveRequest",
        entity_id=req.id,
        timestamp=now
    )
    db.add(audit)
    
    db.commit()
    db.refresh(req)
    return req

def cancel_leave(db: Session, request_id: str, employee: Employee) -> LeaveRequest:
    req = db.query(LeaveRequest).with_for_update().filter(
        LeaveRequest.id == request_id, 
        LeaveRequest.employee_id == employee.id
    ).first()
    
    if not req:
        raise HTTPException(status_code=404, detail="Leave request not found or not owned by user")
        
    if req.status not in [LeaveStatus.PENDING, LeaveStatus.APPROVED]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel request in {req.status} state")
        
    year = datetime.strptime(req.start_date, "%Y-%m-%d").year
    balance = db.query(LeaveBalance).with_for_update().filter(
        LeaveBalance.employee_id == req.employee_id,
        LeaveBalance.leave_type_id == req.leave_type_id,
        LeaveBalance.year == year
    ).first()
    
    if req.status == LeaveStatus.PENDING:
        balance.pending_days -= req.requested_days
    elif req.status == LeaveStatus.APPROVED:
        balance.used_days -= req.requested_days
        
    balance.available_days = LeaveRulesEngine.calculate_available_balance(balance)
    
    req.status = LeaveStatus.CANCELLED
    
    now = datetime.now(timezone.utc)
    audit = AuditLog(
        user_id=employee.user_id,
        action="LEAVE_CANCELLED",
        entity="LeaveRequest",
        entity_id=req.id,
        timestamp=now
    )
    db.add(audit)
    
    db.commit()
    db.refresh(req)
    return req
