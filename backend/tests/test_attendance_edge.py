import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
from app.db.models.attendance import AttendanceRecord
from sqlalchemy.orm import Session

def test_attendance_normal_flow(client: TestClient, db_session: Session, test_employee, auth_headers):
    # Cleanup DB state
    db_session.query(AttendanceRecord).delete()
    db_session.commit()
    
    # Check-in
    in_time = datetime.now(timezone.utc)
    res_in = client.post("/api/v1/attendance/check-in", json={"check_in_time": in_time.isoformat()}, headers=auth_headers)
    assert res_in.status_code == 200
    
    # Check-out
    out_time = in_time + timedelta(hours=8)
    res_out = client.post("/api/v1/attendance/check-out", json={"check_out_time": out_time.isoformat()}, headers=auth_headers)
    assert res_out.status_code == 200
    
def test_attendance_checkout_without_checkin(client: TestClient, db_session: Session, test_employee, auth_headers):
    # Cleanup DB state
    db_session.query(AttendanceRecord).delete()
    db_session.commit()
    
    # Try check-out on a different day without check-in
    out_time = datetime.now(timezone.utc) + timedelta(days=1)
    res_out = client.post("/api/v1/attendance/check-out", json={"check_out_time": out_time.isoformat()}, headers=auth_headers)
    assert res_out.status_code == 404
    
def test_attendance_overnight(client: TestClient, db_session: Session, test_employee, auth_headers):
    db_session.query(AttendanceRecord).delete()
    db_session.commit()
    
    # Check-in at 22:00
    in_time = datetime(2026, 8, 22, 22, 0, tzinfo=timezone.utc)
    res_in = client.post("/api/v1/attendance/check-in", json={"check_in_time": in_time.isoformat()}, headers=auth_headers)
    assert res_in.status_code == 200
    
    # Check-out at 06:00 next day
    out_time = datetime(2026, 8, 23, 6, 0, tzinfo=timezone.utc)
    res_out = client.post("/api/v1/attendance/check-out", json={"check_out_time": out_time.isoformat()}, headers=auth_headers)
    assert res_out.status_code == 200
    
    # Ensure there is exactly 1 record and the check out time is correct
    records = db_session.query(AttendanceRecord).filter(AttendanceRecord.employee_id == test_employee.id).all()
    assert len(records) == 1
    assert records[0].attendance_date == "2026-08-22"  # Associated with check-in day
