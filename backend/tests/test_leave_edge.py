import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models.leave import LeaveRequest, LeaveBalance
from app.db.models.organization import WorkSchedule
from app.db.models.employee import Employee
import threading
from datetime import datetime

def test_leave_work_schedule_calculation(client: TestClient, db_session: Session, test_employee, auth_headers):
    db_session.rollback()
    db_session.query(LeaveRequest).delete()
    db_session.query(LeaveBalance).delete()
    db_session.commit()
    
    # 1. Provide employee with a specific workschedule (Wednesday-Sunday)
    schedule = WorkSchedule(
        name="Custom",
        working_days="Wednesday-Sunday",
        start_time="09:00",
        end_time="17:00"
    )
    db_session.add(schedule)
    db_session.commit()
    
    test_employee.work_schedule_id = schedule.id
    db_session.commit()
    
    # 2. Provide a leave balance of 5 days
    balance = LeaveBalance(
        employee_id=test_employee.id,
        leave_type_id="TYPE_A",
        year=2026,
        allocated_days=5,
        carried_forward_days=0,
        used_days=0,
        pending_days=0,
        available_days=5
    )
    db_session.add(balance)
    db_session.commit()
    
    # 3. Request a leave from Monday (2026-08-24) to Sunday (2026-08-30)
    # The span is 7 days. Under Wednesday-Sunday schedule, Mon/Tue are off.
    # Therefore, it should cost 5 working days.
    payload = {
        "start_date": "2026-08-24",
        "end_date": "2026-08-30",
        "leave_type_id": "TYPE_A",
        "reason": "Test WS"
    }
    res = client.post("/api/v1/leave/apply", json=payload, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["requested_days"] == 5

def test_leave_balance_exhaustion(client: TestClient, db_session: Session, test_employee, auth_headers):
    # The previous test used 5 days out of 5.
    # Attempt to request 1 more day (balance should be 0 available now)
    # Wait, the previous test might not have committed the balance update if it didn't approve the leave!
    # Let's explicitly set the balance.
    db_session.rollback()
    db_session.query(LeaveRequest).delete()
    db_session.query(LeaveBalance).delete()
    
    balance = LeaveBalance(
        employee_id=test_employee.id,
        leave_type_id="TYPE_A",
        year=2026,
        allocated_days=5,
        carried_forward_days=0,
        used_days=5,
        pending_days=0,
        available_days=0
    )
    db_session.add(balance)
    db_session.commit()
    
    payload = {
        "start_date": "2026-09-02", # Wednesday
        "end_date": "2026-09-02",
        "leave_type_id": "TYPE_A",
        "reason": "Exhaustion"
    }
    res = client.post("/api/v1/leave/apply", json=payload, headers=auth_headers)
    assert res.status_code == 409 # Insufficient balance

def test_leave_concurrency(client: TestClient, db_session: Session, test_employee, auth_headers):
    # Setup fresh balance
    db_session.rollback()
    db_session.query(LeaveRequest).delete()
    db_session.query(LeaveBalance).delete()
    
    balance = LeaveBalance(
        employee_id=test_employee.id,
        leave_type_id="TYPE_B",
        year=2026,
        allocated_days=5,
        available_days=5
    )
    db_session.add(balance)
    db_session.commit()
    
    # Request A: 4 days (Wed-Sat)
    payload_a = {
        "start_date": "2026-09-02", 
        "end_date": "2026-09-05",
        "leave_type_id": "TYPE_B",
        "reason": "Concurrent A"
    }
    
    # Request B: 4 days (Wed-Sat)
    payload_b = {
        "start_date": "2026-09-09", 
        "end_date": "2026-09-12",
        "leave_type_id": "TYPE_B",
        "reason": "Concurrent B"
    }
    
    results = []
    def req(p):
        r = client.post("/api/v1/leave/apply", json=p, headers=auth_headers)
        results.append(r.status_code)
        
    t1 = threading.Thread(target=req, args=(payload_a,))
    t2 = threading.Thread(target=req, args=(payload_b,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    # 5 days available, two 4-day requests concurrently.
    # Because of with_for_update, they should be strictly serialized.
    # One succeeds (200), the other fails with Insufficient Balance (409)
    assert 200 in results
    assert 409 in results
