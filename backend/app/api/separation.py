from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db.database import get_db
from app.db.models.auth import User
from app.api.auth import get_current_user
from app.core.permissions import require_permission
from app.schemas.separation import SeparationRecordResponse
from app.services.separation_service import complete_separation

router = APIRouter()

@router.post("/{id}/complete", response_model=SeparationRecordResponse)
def api_complete_separation(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_separation"))
):
    return complete_separation(db, id, current_user)
