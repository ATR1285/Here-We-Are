# Dayflow HRMS Backend

## PROJECT OVERVIEW
Dayflow is a production-grade enterprise Human Resource Management System (HRMS) covering the complete employee lifecycle from recruitment to separation.

## BACKEND ARCHITECTURE
Built strictly on FastAPI and PostgreSQL, adhering to a strict layered architecture: Models -> Schemas -> Pure Python Rules Engine -> Service (Transactional with Row Locks) -> API (RBAC Secured).

## TECHNOLOGY STACK
- Python 3.10+
- FastAPI
- PostgreSQL (Authoritative Store)
- SQLAlchemy + Alembic
- Argon2 (Password Hashing)
- Pytest

## POSTGRESQL SETUP & ENVIRONMENT VARIABLES
Provide the following in a `.env` file at the root of `backend/`:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/dayflow
SECRET_KEY=your_secret_key
CORS_ORIGINS=http://localhost:5173
```

## DATABASE MIGRATION
To initialize the database schema, run:
```bash
alembic upgrade head
```

## HOW TO START POSTGRESQL
Ensure PostgreSQL is running locally on port 5432 or utilize the provided database service.

## HOW TO START FASTAPI
```bash
python -m venv venv
source venv/bin/activate  # Or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## HOW TO RUN TESTS
```bash
pytest -v
```

## API DOCUMENTATION
Swagger UI is natively exposed at `http://localhost:8000/docs` containing full route documentation, request/response schemas, and authorization requirements.

## SECURITY MODEL
### AUTHENTICATION
Employs secure HTTP-Only cookies backing database-stored sessions.
### RBAC
Strict Deny-by-Default authorization model. Access explicitly requires predefined roles/permissions mapped to `require_permission()`.
### IDOR
Resource endpoints enforce `current_user.id` against entity ownership preventing horizontal cross-employee contamination.

## MODULES
1. Foundation (Auth, RBAC, Sessions, Audit)
2. Identity (Employee 360, Departments)
3. Attendance & Time Tracking
4. Leave Management
5. Payroll & Loss-of-Pay
6. Performance & Goals
7. Recruitment & Onboarding
8. Offboarding & Separation
9. Expense & Reimbursement
