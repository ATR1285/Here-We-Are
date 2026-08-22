from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone
from decimal import Decimal

from app.db.models.payroll import SalaryStructure, PayrollRecord, Payslip, PayrollStatus
from app.db.models.employee import Employee
from app.db.models.auth import User
from app.db.models.audit import AuditLog
from app.rules.payroll_rules import PayrollRulesEngine

def process_payroll(db: Session, employee_id: str, month: int, year: int, processor: User) -> PayrollRecord:
    # 1. Lock to prevent duplicate payroll
    existing = db.query(PayrollRecord).with_for_update().filter(
        PayrollRecord.employee_id == employee_id,
        PayrollRecord.payroll_month == month,
        PayrollRecord.payroll_year == year
    ).first()
    
    if existing and existing.status == PayrollStatus.FINALIZED:
        raise HTTPException(status_code=400, detail="Payroll already finalized for this period")
        
    structure = db.query(SalaryStructure).filter(
        SalaryStructure.employee_id == employee_id,
        SalaryStructure.status == True
    ).first()
    
    if not structure:
        raise HTTPException(status_code=404, detail="No active salary structure found for employee")
        
    from sqlalchemy import extract
    from app.db.models.attendance import AttendanceRecord
    from app.db.models.leave import LeaveRequest, LeaveStatus
    
    # 2. Derive actual Attendance and Leave data
    scheduled_working_days = 22
    
    attendances = db.query(AttendanceRecord).filter(
        AttendanceRecord.employee_id == employee_id,
        extract('month', AttendanceRecord.check_in_at) == month,
        extract('year', AttendanceRecord.check_in_at) == year
    ).count()
    
    approved_leaves_total = 0
    # A rough aggregation for the month
    leaves = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee_id,
        LeaveRequest.status == LeaveStatus.APPROVED
    ).all()
    for l in leaves:
        start_month = datetime.strptime(l.start_date, "%Y-%m-%d").month
        start_year = datetime.strptime(l.start_date, "%Y-%m-%d").year
        if start_month == month and start_year == year:
            approved_leaves_total += l.requested_days
            
    worked_days = attendances
    lop_days = scheduled_working_days - worked_days - approved_leaves_total
    if lop_days < 0:
        lop_days = 0
    
    lop_deduction = PayrollRulesEngine.calculate_lop_deduction(
        gross_salary=structure.gross_salary,
        scheduled_working_days=scheduled_working_days,
        lop_days=lop_days
    )
    
    gross = structure.gross_salary
    net = PayrollRulesEngine.calculate_net_pay(gross, lop_deduction)
    
    now = datetime.now(timezone.utc)
    
    if existing:
        existing.gross_earnings = gross
        existing.total_deductions = lop_deduction
        existing.lop_deduction = lop_deduction
        existing.net_pay = net
        existing.status = PayrollStatus.PROCESSED
        existing.processed_at = now
        existing.processed_by = processor.id
        record = existing
    else:
        record = PayrollRecord(
            employee_id=employee_id,
            payroll_month=month,
            payroll_year=year,
            salary_structure_id=structure.id,
            working_days=scheduled_working_days,
            lop_days=lop_days,
            gross_earnings=gross,
            total_deductions=lop_deduction,
            lop_deduction=lop_deduction,
            net_pay=net,
            status=PayrollStatus.PROCESSED,
            processed_at=now,
            processed_by=processor.id
        )
        db.add(record)
        
    audit = AuditLog(
        user_id=processor.id,
        action="PAYROLL_PROCESSED",
        entity="PayrollRecord",
        entity_id=record.id,
        timestamp=now
    )
    db.add(audit)
    
    db.commit()
    db.refresh(record)
    return record
