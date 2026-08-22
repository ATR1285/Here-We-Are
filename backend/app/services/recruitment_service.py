from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone

from app.db.models.recruitment import (
    Candidate, Application, JobOffer, OnboardingRecord, 
    ApplicationStatus, OfferStatus, OnboardingStatus
)
from app.db.models.auth import User
from app.db.models.employee import Employee
from app.db.models.audit import AuditLog
from app.rules.recruitment_rules import RecruitmentRulesEngine

def convert_candidate_to_employee(db: Session, onboarding_id: str, current_user: User) -> Employee:
    # Transactional lock on OnboardingRecord
    onboarding = db.query(OnboardingRecord).with_for_update().filter(OnboardingRecord.id == onboarding_id).first()
    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding record not found")
        
    application = db.query(Application).with_for_update().filter(Application.id == onboarding.application_id).first()
    offer = db.query(JobOffer).with_for_update().filter(JobOffer.id == onboarding.offer_id).first()
    candidate = db.query(Candidate).with_for_update().filter(Candidate.id == onboarding.candidate_id).first()

    # Rule Engine enforces conversion prerequisites natively
    RecruitmentRulesEngine.validate_candidate_conversion(
        application_status=application.status,
        offer_status=offer.status,
        onboarding_status=onboarding.status,
        employee_already_converted=onboarding.converted_employee_id is not None
    )

    try:
        # Generate a strong random temporary password for converted candidates
        import secrets
        from app.core.security import get_password_hash
        temp_password = secrets.token_urlsafe(16)
        password_hash = get_password_hash(temp_password)

        # Create User identity
        new_user = User(
            email=candidate.email,
            hashed_password=password_hash,
            is_active=True
        )
        db.add(new_user)
        db.flush() # Flush to get new_user.id
        
        # Create Employee Profile mapping to existing structures
        new_employee = Employee(
            user_id=new_user.id,
            first_name=candidate.first_name,
            last_name=candidate.last_name,
            date_of_joining=offer.start_date
        )
        db.add(new_employee)
        db.flush() # Flush to get new_employee.id
        
        # Update Onboarding Record
        onboarding.converted_employee_id = new_employee.id
        
        # Audit Trail
        audit = AuditLog(
            user_id=current_user.id,
            action="CANDIDATE_CONVERTED_TO_EMPLOYEE",
            entity="OnboardingRecord",
            entity_id=onboarding.id,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(audit)
        
        db.commit()
        db.refresh(new_employee)
        return new_employee
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Employee conversion transaction failed: {str(e)}")
