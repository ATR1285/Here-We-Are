from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.auth import User
from app.api.auth import get_current_user
from app.core.permissions import require_permission
from app.schemas.performance import PerformanceReviewResponse, SelfReviewSubmit, ManagerReviewSubmit
from app.services.performance_service import submit_self_review, finalize_review

router = APIRouter()

@router.post("/reviews/{id}/self-submit", response_model=PerformanceReviewResponse)
def api_submit_self_review(
    id: str,
    request: SelfReviewSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return submit_self_review(db, id, request.self_rating, request.self_comments, current_user)

@router.post("/reviews/{id}/finalize", response_model=PerformanceReviewResponse)
def api_finalize_review(
    id: str,
    request: ManagerReviewSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("finalize_performance_review"))
):
    return finalize_review(db, id, request.manager_rating, request.manager_comments, current_user)
