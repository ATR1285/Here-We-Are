import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models.performance import PerformanceReview, ReviewStatus
from app.db.models.employee import Employee, EmploymentStatus
from app.db.models.auth import User, Role

def test_performance_manager_hierarchy(client: TestClient, db_session: Session):
    db_session.rollback()
    
    # 1. Setup Data: Manager A, Manager B, Employee A
    role = db_session.query(Role).filter_by(name="Manager").first()
    if not role:
        role = Role(name="Manager")
        db_session.add(role)
        db_session.commit()
        
    from app.db.models.auth import Permission, RolePermission
    perm = db_session.query(Permission).filter_by(name="finalize_performance_review").first()
    if not perm:
        perm = Permission(name="finalize_performance_review")
        db_session.add(perm)
        db_session.commit()
    rp = RolePermission(role_id=role.id, permission_id=perm.id)
    db_session.add(rp)
    db_session.commit()
    
    u_mgr_a = User(email="mgrA@test.com", hashed_password="pw", role_id=role.id)
    u_mgr_b = User(email="mgrB@test.com", hashed_password="pw", role_id=role.id)
    db_session.add_all([u_mgr_a, u_mgr_b])
    db_session.commit()

    e_mgr_a = Employee(user_id=u_mgr_a.id, email="mgrA@test.com", first_name="Mgr", last_name="A", employee_code="MGR_A", employment_status=EmploymentStatus.ACTIVE)
    e_mgr_b = Employee(user_id=u_mgr_b.id, email="mgrB@test.com", first_name="Mgr", last_name="B", employee_code="MGR_B", employment_status=EmploymentStatus.ACTIVE)
    db_session.add_all([e_mgr_a, e_mgr_b])
    db_session.commit()
    
    # Employee A belongs to Manager A
    u_emp_a = User(email="empA@test.com", hashed_password="pw", role_id=role.id)
    db_session.add(u_emp_a)
    db_session.commit()
    
    e_emp_a = Employee(user_id=u_emp_a.id, manager_id=e_mgr_a.id, email="empA@test.com", first_name="Emp", last_name="A", employee_code="EMP_A", employment_status=EmploymentStatus.ACTIVE)
    db_session.add(e_emp_a)
    db_session.commit()
    
    from app.db.models.performance import PerformanceCycle, CycleStatus
    
    cycle = PerformanceCycle(name="2026 H1", start_date="2026-01-01", end_date="2026-06-30", status=CycleStatus.OPEN)
    db_session.add(cycle)
    db_session.commit()
    
    # 2. Setup a Performance Review
    review = PerformanceReview(
        employee_id=e_emp_a.id,
        cycle_id=cycle.id,
        status=ReviewStatus.SELF_SUBMITTED,
        self_rating=4,
        self_comments="Good work"
    )
    db_session.add(review)
    db_session.commit()
    
    # 3. Manager B tries to finalize Employee A's review (IDOR attempt)
    from app.db.models.auth import Session as AuthSession
    from datetime import datetime, timedelta, timezone
    
    sess_b = AuthSession(user_id=u_mgr_b.id, expires_at=datetime.now(timezone.utc) + timedelta(days=1))
    sess_a = AuthSession(user_id=u_mgr_a.id, expires_at=datetime.now(timezone.utc) + timedelta(days=1))
    db_session.add_all([sess_b, sess_a])
    db_session.commit()
    
    headers_b = {"Cookie": f"session_id={sess_b.id}"}
    headers_a = {"Cookie": f"session_id={sess_a.id}"}
    
    payload = {
        "manager_rating": 3,
        "comments": "Finalized"
    }
    
    # Manager B attempts
    res_b = client.post(f"/api/v1/performance/reviews/{review.id}/finalize", json=payload, headers=headers_b)
    assert res_b.status_code == 403
    
    # Manager A attempts
    res_a = client.post(f"/api/v1/performance/reviews/{review.id}/finalize", json=payload, headers=headers_a)
    assert res_a.status_code == 200
