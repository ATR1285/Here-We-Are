from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typing import Generator
import pytest

from app.main import app
from app.db.database import get_db, Base
from app.db.models.auth import Role, Permission, RolePermission, User
from app.core.security import get_password_hash

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

client = TestClient(app, base_url="https://testserver")

@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Setup Roles and Permissions
    hr_role = Role(id="hr_role", name="HR")
    emp_role = Role(id="emp_role", name="Employee")
    
    view_all = Permission(id="view_all", name="view_all_employees")
    manage_emp = Permission(id="manage_emp", name="manage_employees")
    view_own = Permission(id="view_own", name="view_own_profile")
    edit_basic = Permission(id="edit_basic", name="edit_basic_info")
    
    db.add_all([hr_role, emp_role, view_all, manage_emp, view_own, edit_basic])
    db.commit()
    
    db.add_all([
        RolePermission(id="rp1", role_id="hr_role", permission_id="view_all"),
        RolePermission(id="rp2", role_id="hr_role", permission_id="manage_emp"),
        RolePermission(id="rp3", role_id="emp_role", permission_id="view_own"),
        RolePermission(id="rp4", role_id="emp_role", permission_id="edit_basic"),
    ])
    
    # Setup Users
    hr_user = User(id="hr_user", email="hr@dayflow.io", hashed_password=get_password_hash("pw"), role_id="hr_role")
    emp1_user = User(id="emp1_user", email="emp1@dayflow.io", hashed_password=get_password_hash("pw"), role_id="emp_role")
    emp2_user = User(id="emp2_user", email="emp2@dayflow.io", hashed_password=get_password_hash("pw"), role_id="emp_role")
    
    db.add_all([hr_user, emp1_user, emp2_user])
    db.commit()
    db.close()
    yield
    app.dependency_overrides.clear()

def test_hr_can_create_employee():
    # Login HR
    res = client.post("/api/v1/auth/login", json={"email": "hr@dayflow.io", "password": "pw"})
    cookies = res.cookies
    
    # Create employee 1
    emp1_data = {
        "employee_code": "EMP001",
        "user_id": "emp1_user",
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@dayflow.io"
    }
    res = client.post("/api/v1/employees", json=emp1_data, cookies=cookies)
    assert res.status_code == 200, res.text
    
def test_employee_idor_prevention():
    # HR creates two employees
    res_hr = client.post("/api/v1/auth/login", json={"email": "hr@dayflow.io", "password": "pw"})
    cookies_hr = res_hr.cookies
    
    emp1 = client.post("/api/v1/employees", json={"employee_code": "EMP001", "user_id": "emp1_user", "first_name": "Alice", "last_name": "S", "email": "a@d.io"}, cookies=cookies_hr).json()
    emp2 = client.post("/api/v1/employees", json={"employee_code": "EMP002", "user_id": "emp2_user", "first_name": "Bob", "last_name": "J", "email": "b@d.io"}, cookies=cookies_hr).json()
    
    # Login Emp1
    res_emp1 = client.post("/api/v1/auth/login", json={"email": "emp1@dayflow.io", "password": "pw"})
    cookies_emp1 = res_emp1.cookies
    
    # Emp1 accesses own profile via /me
    res = client.get("/api/v1/employees/me", cookies=cookies_emp1)
    assert res.status_code == 200
    
    # Emp1 attempts to access Emp2 profile via IDOR
    res = client.get(f"/api/v1/employees/{emp2['id']}", cookies=cookies_emp1)
    assert res.status_code == 403 # Forbidden
