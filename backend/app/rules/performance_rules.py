from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from fastapi import HTTPException
from app.db.models.performance import ReviewStatus

class PerformanceRulesEngine:
    @staticmethod
    def validate_rating(rating: int) -> None:
        if not isinstance(rating, int):
            raise HTTPException(status_code=400, detail="Rating must be an integer")
        if rating < 1 or rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    @staticmethod
    def validate_progress(progress: Decimal) -> None:
        if progress < Decimal('0.00') or progress > Decimal('100.00'):
            raise HTTPException(status_code=400, detail="Progress must be between 0 and 100")

    @staticmethod
    def validate_goal_weight(weight: Decimal) -> None:
        if weight < Decimal('0.00') or weight > Decimal('100.00'):
            raise HTTPException(status_code=400, detail="Weight must be between 0 and 100")

    @staticmethod
    def validate_review_transition(current_status: ReviewStatus, requested_status: ReviewStatus) -> None:
        valid_transitions = {
            ReviewStatus.PENDING: [ReviewStatus.SELF_SUBMITTED],
            ReviewStatus.SELF_SUBMITTED: [ReviewStatus.MANAGER_REVIEW],
            ReviewStatus.MANAGER_REVIEW: [ReviewStatus.FINALIZED],
            ReviewStatus.FINALIZED: []
        }
        
        if requested_status not in valid_transitions.get(current_status, []):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid review transition from {current_status.value} to {requested_status.value}"
            )

    @staticmethod
    def calculate_final_rating(self_rating: Optional[int], manager_rating: Optional[int]) -> Decimal:
        if self_rating is None or manager_rating is None:
            raise HTTPException(status_code=400, detail="Both self and manager ratings are required to finalize")
            
        # Example calculation: 40% self, 60% manager
        final = (Decimal(self_rating) * Decimal('0.4')) + (Decimal(manager_rating) * Decimal('0.6'))
        return final.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
