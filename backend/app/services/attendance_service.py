from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db.models.attendance import AttendanceRecord, AttendanceStatus, AttendanceRegularizationRequest, RegularizationStatus
from app.db.models.employee import Employee
from app.db.models.audit import AuditLog
from app.rules.attendance_rules import AttendanceRulesEngine

from sqlalchemy.exc import IntegrityError

def check_in(db: Session, employee: Employee) -> AttendanceRecord:
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Block if they have an active open shift (for overnight safety)
    open_shift = db.query(AttendanceRecord).filter(
        AttendanceRecord.employee_id == employee.id,
        AttendanceRecord.check_out_at == None
    ).first()
    if open_shift:
        raise HTTPException(status_code=409, detail="You have an active open check-in. Please check out first.")
    
    # Check if already checked in for today
    existing = db.query(AttendanceRecord).filter(
        AttendanceRecord.employee_id == employee.id,
        AttendanceRecord.attendance_date == today_str
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Already checked in for today")
    
    now = datetime.now(timezone.utc)
    record = AttendanceRecord(
        employee_id=employee.id,
        attendance_date=today_str,
        check_in_at=now,
        status=AttendanceStatus.PRESENT
    )
    db.add(record)
    
    # Audit
    audit = AuditLog(
        user_id=employee.user_id,
        action="ATTENDANCE_CHECK_IN",
        entity="AttendanceRecord",
        entity_id=record.id,
        timestamp=now
    )
    db.add(audit)
    
    try:
        db.commit()
        db.refresh(record)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Concurrent check-in detected")
        
    return record

def check_out(db: Session, employee: Employee) -> AttendanceRecord:
    # Find the active open shift (solves overnight crossing boundary)
    record = db.query(AttendanceRecord).filter(
        AttendanceRecord.employee_id == employee.id,
        AttendanceRecord.check_out_at == None
    ).order_by(AttendanceRecord.check_in_at.desc()).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="No active check-in record found to check out from")
        
    now = datetime.now(timezone.utc)
    record.check_out_at = now
    
    # Apply rules
    schedule = employee.work_schedule
    record.worked_minutes = AttendanceRulesEngine.calculate_worked_minutes(record.check_in_at, record.check_out_at)
    
    if schedule:
        record.late_minutes = AttendanceRulesEngine.calculate_late_minutes(record.check_in_at, schedule)
        record.early_departure_minutes = AttendanceRulesEngine.calculate_early_departure_minutes(record.check_out_at, schedule)
        record.overtime_minutes = AttendanceRulesEngine.calculate_overtime_minutes(record.check_out_at, schedule)
        record.status = AttendanceRulesEngine.determine_status(record.worked_minutes, schedule)

    # Audit
    audit = AuditLog(
        user_id=employee.user_id,
        action="ATTENDANCE_CHECK_OUT",
        entity="AttendanceRecord",
        entity_id=record.id,
        timestamp=now
    )
    db.add(audit)
    db.commit()
    db.refresh(record)
    return record
