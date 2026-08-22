import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models.payroll import SalaryStructure, PayrollRecord, PayrollStatus
from app.db.models.attendance import AttendanceRecord
from app.db.models.leave import LeaveRequest, LeaveStatus
from datetime import datetime, timezone
import threading

def test_payroll_reconciliation(client: TestClient, db_session: Session, test_employee, auth_headers):
    db_session.rollback()
    db_session.query(PayrollRecord).delete()
    db_session.query(SalaryStructure).delete()
    db_session.query(AttendanceRecord).delete()
    db_session.query(LeaveRequest).delete()
    
    # 1. Setup Salary Structure
    structure = SalaryStructure(
        employee_id=test_employee.id,
        effective_from="2026-01-01",
        gross_salary=10000.00,
        status=True
    )
    db_session.add(structure)
    
    # 2. Add 2 Attendance Records (Worked 2 days)
    a1 = AttendanceRecord(employee_id=test_employee.id, attendance_date="2026-09-01", check_in_at=datetime(2026,9,1,9,0,tzinfo=timezone.utc), check_out_at=datetime(2026,9,1,17,0,tzinfo=timezone.utc))
    a2 = AttendanceRecord(employee_id=test_employee.id, attendance_date="2026-09-02", check_in_at=datetime(2026,9,2,9,0,tzinfo=timezone.utc), check_out_at=datetime(2026,9,2,17,0,tzinfo=timezone.utc))
    db_session.add_all([a1, a2])
    
    # 3. Add 1 Approved Leave for 5 days
    l1 = LeaveRequest(employee_id=test_employee.id, leave_type_id="TYPE_A", start_date="2026-09-05", end_date="2026-09-09", requested_days=5, reason="Vacation", status=LeaveStatus.APPROVED)
    db_session.add(l1)
    
    db_session.commit()
    
    # Total Scheduled: 22. Worked: 2. Leave: 5. LOP = 22 - 2 - 5 = 15.
    # LOP Deduction = (10000 / 22) * 15 = 454.54 * 15 = 6818.18
    # Net = 10000 - 6818.18 = 3181.82
    
    payload = {
        "employee_id": test_employee.id,
        "month": 9,
        "year": 2026
    }
    res = client.post("/api/v1/payroll/process", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    
    assert data["lop_days"] == 15
    assert abs(data["lop_deduction"] - 6818.18) < 1.0 # Float precision tolerance
    assert abs(data["net_pay"] - 3181.82) < 1.0

def test_payroll_concurrency_duplicate(client: TestClient, db_session: Session, test_employee, auth_headers):
    # Already processed month 9 in the previous test.
    # But wait, it's PROCESSED, not FINALIZED.
    # We should finalize it first, then try to reprocess.
    db_session.rollback()
    
    pr = db_session.query(PayrollRecord).first()
    pr.status = PayrollStatus.FINALIZED
    db_session.commit()
    
    payload = {
        "employee_id": test_employee.id,
        "month": 9,
        "year": 2026
    }
    
    # Test finalized rejection
    res = client.post("/api/v1/payroll/process", json=payload, headers=auth_headers)
    assert res.status_code == 400
    assert "already finalized" in res.json()["detail"].lower()
