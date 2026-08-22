from decimal import Decimal
from fastapi import HTTPException
from app.db.models.separation import (
    ResignationStatus, SeparationStatus, ClearanceStatus, SettlementStatus
)

class SeparationRulesEngine:
    @staticmethod
    def validate_resignation_transition(current: ResignationStatus, requested: ResignationStatus) -> None:
        valid = {
            ResignationStatus.SUBMITTED: [ResignationStatus.APPROVED, ResignationStatus.REJECTED, ResignationStatus.WITHDRAWN],
            ResignationStatus.APPROVED: [],
            ResignationStatus.REJECTED: [],
            ResignationStatus.WITHDRAWN: []
        }
        if requested not in valid.get(current, []):
            raise HTTPException(status_code=400, detail=f"Invalid resignation transition: {current.value} -> {requested.value}")

    @staticmethod
    def validate_separation_transition(current: SeparationStatus, requested: SeparationStatus) -> None:
        valid = {
            SeparationStatus.PENDING: [SeparationStatus.CLEARANCE_IN_PROGRESS, SeparationStatus.CANCELLED],
            SeparationStatus.CLEARANCE_IN_PROGRESS: [SeparationStatus.SETTLEMENT_PENDING, SeparationStatus.CANCELLED],
            SeparationStatus.SETTLEMENT_PENDING: [SeparationStatus.COMPLETED, SeparationStatus.CANCELLED],
            SeparationStatus.COMPLETED: [],
            SeparationStatus.CANCELLED: []
        }
        if requested not in valid.get(current, []):
            raise HTTPException(status_code=400, detail=f"Invalid separation transition: {current.value} -> {requested.value}")

    @staticmethod
    def validate_settlement_transition(current: SettlementStatus, requested: SettlementStatus) -> None:
        valid = {
            SettlementStatus.DRAFT: [SettlementStatus.PROCESSED],
            SettlementStatus.PROCESSED: [SettlementStatus.PAID],
            SettlementStatus.PAID: []
        }
        if requested not in valid.get(current, []):
            raise HTTPException(status_code=400, detail=f"Invalid settlement transition: {current.value} -> {requested.value}")

    @staticmethod
    def validate_settlement_values(final_salary: Decimal, lop_deduction: Decimal, other_deductions: Decimal, other_payments: Decimal) -> Decimal:
        if any(v < Decimal('0.00') for v in [final_salary, lop_deduction, other_deductions, other_payments]):
            raise HTTPException(status_code=400, detail="Financial values cannot be negative")
            
        net = (final_salary + other_payments) - (lop_deduction + other_deductions)
        if net < Decimal('0.00'):
            raise HTTPException(status_code=400, detail="Net settlement cannot be negative")
        return net
