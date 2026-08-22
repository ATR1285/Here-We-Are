import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models.expense import ExpenseClaim, ExpenseStatus
from app.db.models.employee import Employee
from app.db.models.auth import User, Role, Permission, RolePermission
import threading

def test_expense_concurrent_settlement(client: TestClient, db_session: Session, test_employee, auth_headers):
    db_session.rollback()
    db_session.query(ExpenseClaim).delete()
    
    # 1. Setup role & permissions for finance to settle
    role = db_session.query(Role).filter_by(name="Finance").first()
    if not role:
        role = Role(name="Finance")
        db_session.add(role)
        db_session.commit()
    
    perm = db_session.query(Permission).filter_by(name="settle_expenses").first()
    if not perm:
        perm = Permission(name="settle_expenses")
        db_session.add(perm)
        db_session.commit()
    
    rp = db_session.query(RolePermission).filter_by(role_id=role.id, permission_id=perm.id).first()
    if not rp:
        rp = RolePermission(role_id=role.id, permission_id=perm.id)
        db_session.add(rp)
        db_session.commit()
    
    # Finance User
    finance_user = User(email="finance@test.com", hashed_password="pw", role_id=role.id)
    db_session.add(finance_user)
    db_session.commit()
    
    # Session for finance user
    from app.db.models.auth import Session as AuthSession
    from datetime import datetime, timedelta, timezone
    sess = AuthSession(user_id=finance_user.id, expires_at=datetime.now(timezone.utc) + timedelta(days=1))
    db_session.add(sess)
    db_session.commit()
    headers = {"Cookie": f"session_id={sess.id}"}
    
    # 2. Setup Expense Claim
    from app.db.models.expense import ExpenseCategory, ExpenseItem
    cat = ExpenseCategory(name="Travel")
    db_session.add(cat)
    db_session.commit()
    
    claim = ExpenseClaim(
        employee_id=test_employee.id,
        claim_number="EXP-TEST001",
        status=ExpenseStatus.FINANCE_APPROVED,
        total_amount=500.00
    )
    db_session.add(claim)
    db_session.commit()
    
    item = ExpenseItem(
        expense_claim_id=claim.id,
        expense_category_id=cat.id,
        expense_date="2026-08-22",
        description="Flight",
        amount=500.00
    )
    db_session.add(item)
    db_session.commit()
    
    # 3. Fire concurrent requests to settle
    success_count = 0
    fail_count = 0
    lock = threading.Lock()
    
    def attempt_settle():
        nonlocal success_count, fail_count
        res = client.post(f"/api/v1/expense/claims/{claim.id}/settle", headers=headers)
        with lock:
            if res.status_code == 200:
                success_count += 1
            else:
                fail_count += 1

    threads = []
    for _ in range(3):
        t = threading.Thread(target=attempt_settle)
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    assert success_count == 1
    assert fail_count == 2

