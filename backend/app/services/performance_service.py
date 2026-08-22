from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone

from app.db.models.performance import PerformanceReview, PerformanceReviewHistory, ReviewStatus
from app.db.models.auth import User
from app.db.models.audit import AuditLog
from app.rules.performance_rules import PerformanceRulesEngine

def submit_self_review(db: Session, review_id: str, self_rating: int, comments: str, user: User) -> PerformanceReview:
    PerformanceRulesEngine.validate_rating(self_rating)
    
    review = db.query(PerformanceReview).with_for_update().filter(PerformanceReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
        
    if review.employee.user_id != user.id:
        raise HTTPException(status_code=403, detail="Employees may only submit their own self-reviews")
        
    PerformanceRulesEngine.validate_review_transition(review.status, ReviewStatus.SELF_SUBMITTED)
    
    review.self_rating = self_rating
    review.self_comments = comments
    review.status = ReviewStatus.SELF_SUBMITTED
    review.submitted_at = datetime.now(timezone.utc)
    
    history = PerformanceReviewHistory(
        review_id=review.id,
        actor_id=user.id,
        action="SELF_REVIEW_SUBMITTED",
        previous_state=ReviewStatus.PENDING.value,
        new_state=ReviewStatus.SELF_SUBMITTED.value,
        comments=comments
    )
    db.add(history)
    
    audit = AuditLog(
        user_id=user.id,
        action="SELF_REVIEW_SUBMITTED",
        entity="PerformanceReview",
        entity_id=review.id,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(audit)
    
    db.commit()
    db.refresh(review)
    return review

def finalize_review(db: Session, review_id: str, manager_rating: int, comments: str, reviewer: User) -> PerformanceReview:
    PerformanceRulesEngine.validate_rating(manager_rating)
    
    review = db.query(PerformanceReview).with_for_update().filter(PerformanceReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
        
    # Structural Ownership Check (Item 8)
    from app.db.models.employee import Employee
    reviewer_emp = db.query(Employee).filter(Employee.user_id == reviewer.id).first()
    if not reviewer_emp:
        raise HTTPException(status_code=403, detail="Reviewer does not have an active employee profile")
        
    if review.employee.manager_id != reviewer_emp.id:
        raise HTTPException(status_code=403, detail="Only the direct manager can finalize the performance review")
        
    # Example logic: Assume state went SELF_SUBMITTED -> MANAGER_REVIEW, now to FINALIZED
    if review.status == ReviewStatus.SELF_SUBMITTED:
         # Implicit transition for this example to MANAGER_REVIEW -> FINALIZED
         PerformanceRulesEngine.validate_review_transition(review.status, ReviewStatus.MANAGER_REVIEW)
         review.status = ReviewStatus.MANAGER_REVIEW
    
    PerformanceRulesEngine.validate_review_transition(review.status, ReviewStatus.FINALIZED)
    
    review.manager_rating = manager_rating
    review.manager_comments = comments
    review.reviewer_id = reviewer.id
    review.final_rating = PerformanceRulesEngine.calculate_final_rating(review.self_rating, manager_rating)
    review.status = ReviewStatus.FINALIZED
    review.finalized_at = datetime.now(timezone.utc)
    
    history = PerformanceReviewHistory(
        review_id=review.id,
        actor_id=reviewer.id,
        action="REVIEW_FINALIZED",
        previous_state=ReviewStatus.MANAGER_REVIEW.value,
        new_state=ReviewStatus.FINALIZED.value,
        comments=comments
    )
    db.add(history)
    
    audit = AuditLog(
        user_id=reviewer.id,
        action="REVIEW_FINALIZED",
        entity="PerformanceReview",
        entity_id=review.id,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(audit)
    
    db.commit()
    db.refresh(review)
    return review
