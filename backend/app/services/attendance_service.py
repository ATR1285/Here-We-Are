from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db.models.attendance import AttendanceRecord, AttendanceStatus, AttendanceRegularizationRequest, RegularizationStatus
from app.db.models.employee import Employee
from app.db.models.audit import AuditLog
from app.rules.attendance_rules import AttendanceRulesEngine

def check_in(db: Session, employee: Employee) -> AttendanceRecord:
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Check if already checked in
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
    db.commit()
    db.refresh(record)
    return record

def check_out(db: Session, employee: Employee) -> AttendanceRecord:
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    record = db.query(AttendanceRecord).filter(
        AttendanceRecord.employee_id == employee.id,
        AttendanceRecord.attendance_date == today_str
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="No check-in record found for today")
    if record.check_out_at:
        raise HTTPException(status_code=409, detail="Already checked out for today")
        
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
