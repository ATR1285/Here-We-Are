import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import uuid

from app.main import app
from app.db.database import Base, get_db

# Use PostgreSQL instead of SQLite
# Create a dedicated test database (ensure the user running tests has permission to create/drop)
# For this execution, we use the main DB URL, but ideally it should be a separate schema or test DB
# Assuming postgresql+psycopg://postgres:postgres@localhost:5432/dayflow (or whatever is in env)
SQLALCHEMY_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/dayflow")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    
    # Warning: this drops tables on the target database.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    yield
    
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session")
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def client():
    with TestClient(app, base_url="https://testserver") as c:
        yield c

from app.db.models.auth import User, Role, Permission, RolePermission
from app.db.models.employee import Employee, EmploymentStatus
from app.db.models.organization import Department
from app.core.security import get_password_hash
from datetime import datetime, timezone
import uuid

@pytest.fixture(scope="session")
def test_employee(db_session):
    role = Role(name="Employee")
    db_session.add(role)
    db_session.commit()
    
    user = User(email="emp@dayflow.io", hashed_password=get_password_hash("password123"), role_id=role.id)
    db_session.add(user)
    db_session.commit()
    
    dept = Department(name="Engineering", code="ENG")
    db_session.add(dept)
    db_session.commit()
    
    emp = Employee(
        user_id=user.id,
        department_id=dept.id,
        first_name="Test",
        last_name="Employee",
        email="emp@dayflow.io",
        employee_code="EMP001",
        employment_status=EmploymentStatus.ACTIVE
    )
    db_session.add(emp)
    
    from app.db.models.leave import LeaveType
    lt = LeaveType(id="TYPE_A", name="Annual", code="ANN", description="Annual Leave", active_status=True)
    db_session.add(lt)
    lt2 = LeaveType(id="TYPE_B", name="Sick", code="SICK", description="Sick Leave", active_status=True)
    db_session.add(lt2)
    
    db_session.commit()
    db_session.refresh(emp)
    return emp

@pytest.fixture(scope="session")
def auth_headers(test_employee, db_session):
    from app.db.models.auth import Session as DBSession
    from datetime import timedelta
    
    new_session = DBSession(
        user_id=test_employee.user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )
    db_session.add(new_session)
    db_session.commit()
    
    return {"Cookie": f"session_id={new_session.id}"}

@pytest.fixture(scope="session")
def test_candidate(db_session):
    # Dummy mock for candidate
    return None
