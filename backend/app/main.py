from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.api import health, auth, organization, employees, attendance, leave, payroll, performance, recruitment, separation, expense

setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(organization.router, prefix=f"{settings.API_V1_STR}/organization", tags=["Organization"])
app.include_router(employees.router, prefix=f"{settings.API_V1_STR}/employees", tags=["Employees"])
app.include_router(attendance.router, prefix=f"{settings.API_V1_STR}/attendance", tags=["Attendance"])
app.include_router(leave.router, prefix=f"{settings.API_V1_STR}/leave", tags=["Leave"])
app.include_router(payroll.router, prefix=f"{settings.API_V1_STR}/payroll", tags=["Payroll"])
app.include_router(performance.router, prefix=f"{settings.API_V1_STR}/performance", tags=["Performance"])
app.include_router(recruitment.router, prefix=f"{settings.API_V1_STR}/recruitment", tags=["Recruitment"])
app.include_router(separation.router, prefix=f"{settings.API_V1_STR}/separation", tags=["Separation"])
app.include_router(expense.router, prefix=f"{settings.API_V1_STR}/expense", tags=["Expense"])

@app.get("/")
def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}
