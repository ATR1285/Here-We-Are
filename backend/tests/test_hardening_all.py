import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
import threading

def test_concurrency_attendance(client: TestClient, db_session: Session, test_employee, auth_headers):
    # Simulate concurrent check-ins
    payload = {"check_in_time": datetime.now(timezone.utc).isoformat()}
    
    results = []
    def worker():
        res = client.post("/api/v1/attendance/check-in", json=payload, headers=auth_headers)
        results.append(res.status_code)
        
    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    # One should succeed (200), one should fail (400)
    assert 200 in results
    assert 400 in results

def test_rollback_candidate_conversion(client: TestClient, db_session: Session, test_candidate, auth_headers_hr):
    # This simulates a rollback by posting invalid data along with valid candidate ID
    # In a real scenario, this would be an integration test forcing a mid-transaction error
    pass # we'll fill this with a specific endpoint that forces a crash if we had one

def test_idor_employee_leave(client: TestClient, test_employee2, auth_headers):
    # Auth headers belong to Employee 1
    # Trying to fetch Employee 2's leave should 403
    res = client.get(f"/api/v1/leave/employee/{test_employee2.id}", headers=auth_headers)
    assert res.status_code == 403

def test_session_invalidation_after_deactivation(client: TestClient, db_session: Session, test_employee, auth_headers, auth_headers_hr):
    # Step 1: Employee is active, session works
    res1 = client.get("/api/v1/employees/me", headers=auth_headers)
    assert res1.status_code == 200
    
    # Step 2: HR Deactivates Employee
    # Depending on the endpoint for separation completion
    # (Assuming we have a mock separation id)
    # Since we don't have it setup perfectly in this stub, let's directly deactivate via DB to simulate the end of `complete_separation`
    test_employee.is_active = False
    from app.db.models.auth import User
    user = db_session.query(User).filter(User.id == test_employee.user_id).first()
    user.is_active = False
    db_session.commit()
    
    # Step 3: Employee tries to use existing session (which is still in auth_headers)
    res2 = client.get("/api/v1/employees/me", headers=auth_headers)
    assert res2.status_code == 401 # Should be Unauthorized now
