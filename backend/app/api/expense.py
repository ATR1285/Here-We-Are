from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db.database import get_db
from app.db.models.auth import User
from app.api.auth import get_current_user
from app.core.permissions import require_permission
from app.schemas.expense import ExpenseClaimCreate, ExpenseClaimResponse
from app.services.expense_service import (
    create_claim, submit_claim, manager_approve_claim, finance_approve_claim, settle_claim
)

router = APIRouter()

@router.post("/claims", response_model=ExpenseClaimResponse)
def api_create_claim(
    claim_in: ExpenseClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_own_expenses"))
):
    return create_claim(db, claim_in, current_user)

@router.post("/claims/{id}/submit", response_model=ExpenseClaimResponse)
def api_submit_claim(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_own_expenses"))
):
    return submit_claim(db, id, current_user)

@router.post("/claims/{id}/manager-approve", response_model=ExpenseClaimResponse)
def api_manager_approve_claim(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("approve_expenses"))
):
    return manager_approve_claim(db, id, current_user)

@router.post("/claims/{id}/finance-approve", response_model=ExpenseClaimResponse)
def api_finance_approve_claim(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("finance_approve_expenses"))
):
    return finance_approve_claim(db, id, current_user)

@router.post("/claims/{id}/settle", response_model=ExpenseClaimResponse)
def api_settle_claim(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("settle_expenses"))
):
    return settle_claim(db, id, current_user)
