import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.core.security import get_password_hash
from app.db.models.auth import User, Role, Permission, RolePermission

# In-memory SQLite for testing to ensure clean state per run
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

from sqlalchemy.pool import StaticPool

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Seed Data
    role = Role(name="Employee")
    perm = Permission(name="view_own_profile")
    db.add(role)
    db.add(perm)
    db.commit()
    
    rp = RolePermission(role_id=role.id, permission_id=perm.id)
    user = User(email="test@dayflow.io", hashed_password=get_password_hash("password123"), role_id=role.id)
    user2 = User(email="noperm@dayflow.io", hashed_password=get_password_hash("password123"), role_id=role.id) # no perm assigned for this test
    
    db.add(rp)
    db.add(user)
    db.add(user2)
    db.commit()
    
    # Intentionally remove permission from role for second user testing scenario
    role_empty = Role(name="NoPerm")
    db.add(role_empty)
    db.flush() # Ensure role_empty gets an ID before assigning
    
    user2.role_id = role_empty.id
    db.commit()
    
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

client = TestClient(app, base_url="https://testserver")

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200

def test_login_success():
    response = client.post("/api/v1/auth/login", json={"email": "test@dayflow.io", "password": "password123"})
    assert response.status_code == 200
    assert "session_id" in response.cookies

def test_login_failure():
    response = client.post("/api/v1/auth/login", json={"email": "test@dayflow.io", "password": "wrong"})
    assert response.status_code == 401

def test_protected_route_without_auth():
    fresh_client = TestClient(app, base_url="https://testserver")
    response = fresh_client.get("/api/v1/auth/protected")
    assert response.status_code == 401

def test_protected_route_with_auth():
    login_response = client.post("/api/v1/auth/login", json={"email": "test@dayflow.io", "password": "password123"})
    response = client.get("/api/v1/auth/protected", cookies=login_response.cookies)
    assert response.status_code == 200

def test_deny_by_default():
    # Login as user with no permissions
    client2 = TestClient(app, base_url="https://testserver")
    login_response = client2.post("/api/v1/auth/login", json={"email": "noperm@dayflow.io", "password": "password123"})
    response = client2.get("/api/v1/auth/protected", cookies=login_response.cookies)
    assert response.status_code == 403 # Forbidden
