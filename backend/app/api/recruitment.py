from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db.database import get_db
from app.db.models.auth import User
from app.api.auth import get_current_user
from app.core.permissions import require_permission
from app.services.recruitment_service import convert_candidate_to_employee

router = APIRouter()

@router.post("/onboarding/{id}/convert-to-employee", response_model=Dict[str, Any])
def api_convert_candidate(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_onboarding"))
):
    employee = convert_candidate_to_employee(db, id, current_user)
    return {"message": "Candidate successfully converted to Employee", "employee_id": employee.id}
