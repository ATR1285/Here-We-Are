from decimal import Decimal
from fastapi import HTTPException
from app.db.models.recruitment import (
    RequisitionStatus, PostingStatus, ApplicationStatus, 
    InterviewStatus, OfferStatus, OnboardingStatus
)

class RecruitmentRulesEngine:
    @staticmethod
    def validate_requisition_transition(current: RequisitionStatus, requested: RequisitionStatus) -> None:
        valid = {
            RequisitionStatus.DRAFT: [RequisitionStatus.PENDING_APPROVAL, RequisitionStatus.OPEN, RequisitionStatus.CANCELLED],
            RequisitionStatus.PENDING_APPROVAL: [RequisitionStatus.APPROVED, RequisitionStatus.CANCELLED],
            RequisitionStatus.APPROVED: [RequisitionStatus.OPEN, RequisitionStatus.CANCELLED],
            RequisitionStatus.OPEN: [RequisitionStatus.CLOSED, RequisitionStatus.CANCELLED],
            RequisitionStatus.CLOSED: [],
            RequisitionStatus.CANCELLED: []
        }
        if requested not in valid.get(current, []):
            raise HTTPException(status_code=400, detail=f"Invalid requisition transition: {current.value} -> {requested.value}")

    @staticmethod
    def validate_application_transition(current: ApplicationStatus, requested: ApplicationStatus) -> None:
        valid = {
            ApplicationStatus.APPLIED: [ApplicationStatus.SCREENING, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN],
            ApplicationStatus.SCREENING: [ApplicationStatus.INTERVIEW, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN],
            ApplicationStatus.INTERVIEW: [ApplicationStatus.OFFER, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN],
            ApplicationStatus.OFFER: [ApplicationStatus.HIRED, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN],
            ApplicationStatus.HIRED: [],
            ApplicationStatus.REJECTED: [],
            ApplicationStatus.WITHDRAWN: []
        }
        if requested not in valid.get(current, []):
            raise HTTPException(status_code=400, detail=f"Invalid application transition: {current.value} -> {requested.value}")

    @staticmethod
    def validate_offer_transition(current: OfferStatus, requested: OfferStatus) -> None:
        valid = {
            OfferStatus.DRAFT: [OfferStatus.ISSUED, OfferStatus.EXPIRED],
            OfferStatus.ISSUED: [OfferStatus.ACCEPTED, OfferStatus.DECLINED, OfferStatus.EXPIRED],
            OfferStatus.ACCEPTED: [],
            OfferStatus.DECLINED: [],
            OfferStatus.EXPIRED: []
        }
        if requested not in valid.get(current, []):
            raise HTTPException(status_code=400, detail=f"Invalid offer transition: {current.value} -> {requested.value}")

    @staticmethod
    def validate_salary(salary: Decimal) -> None:
        if salary < Decimal('0.00'):
            raise HTTPException(status_code=400, detail="Salary cannot be negative")

    @staticmethod
    def validate_candidate_conversion(application_status: ApplicationStatus, offer_status: OfferStatus, onboarding_status: OnboardingStatus, employee_already_converted: bool) -> None:
        if employee_already_converted:
            raise HTTPException(status_code=400, detail="Candidate has already been converted to an Employee")
        if application_status != ApplicationStatus.HIRED:
            raise HTTPException(status_code=400, detail="Application must be in HIRED state to convert")
        if offer_status != OfferStatus.ACCEPTED:
            raise HTTPException(status_code=400, detail="JobOffer must be ACCEPTED to convert")
        if onboarding_status != OnboardingStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Onboarding must be COMPLETED to convert")
