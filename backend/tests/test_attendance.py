import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta

def test_attendance_duplicate_checkin(client: TestClient, db, test_employee, auth_headers):
    # Perform first check-in
    payload = {"check_in_time": datetime.now(timezone.utc).isoformat()}
    res1 = client.post("/api/v1/attendance/check-in", json=payload, headers=auth_headers)
    assert res1.status_code == 200
    
    # Perform duplicate check-in
    res2 = client.post("/api/v1/attendance/check-in", json=payload, headers=auth_headers)
    assert res2.status_code == 400 # Should be rejected

def test_attendance_checkout_without_checkin(client: TestClient, db, test_employee2, auth_headers2):
    payload = {"check_out_time": datetime.now(timezone.utc).isoformat()}
    res = client.post("/api/v1/attendance/check-out", json=payload, headers=auth_headers2)
    assert res.status_code == 400 # Should be rejected because no check-in exists for today

def test_attendance_double_checkout(client: TestClient, db, test_employee3, auth_headers3):
    in_payload = {"check_in_time": datetime.now(timezone.utc).isoformat()}
    client.post("/api/v1/attendance/check-in", json=in_payload, headers=auth_headers3)
    
    out_payload = {"check_out_time": (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat()}
    res1 = client.post("/api/v1/attendance/check-out", json=out_payload, headers=auth_headers3)
    assert res1.status_code == 200
    
    res2 = client.post("/api/v1/attendance/check-out", json=out_payload, headers=auth_headers3)
    assert res2.status_code == 400 # Should be rejected as already checked out
