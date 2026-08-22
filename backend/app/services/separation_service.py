from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone

from app.db.models.separation import (
    ResignationRequest, SeparationRecord, ClearanceChecklist, FinalSettlement,
    ResignationStatus, SeparationStatus, ClearanceStatus, SettlementStatus
)
from app.db.models.auth import User
from app.db.models.employee import Employee
from app.db.models.audit import AuditLog
from app.rules.separation_rules import SeparationRulesEngine

def complete_separation(db: Session, separation_id: str, current_user: User) -> SeparationRecord:
    # Transactional Lock
    separation = db.query(SeparationRecord).with_for_update().filter(SeparationRecord.id == separation_id).first()
    if not separation:
        raise HTTPException(status_code=404, detail="Separation record not found")
        
    SeparationRulesEngine.validate_separation_transition(separation.status, SeparationStatus.COMPLETED)
    
    # 1. Validate all required clearances
    clearances = db.query(ClearanceChecklist).filter(ClearanceChecklist.separation_record_id == separation.id).all()
    if any(c.status == ClearanceStatus.PENDING for c in clearances):
        raise HTTPException(status_code=400, detail="Cannot complete separation: Pending clearances exist")
        
    # 2. Validate settlement status
    settlement = db.query(FinalSettlement).filter(FinalSettlement.separation_record_id == separation.id).first()
    if not settlement or settlement.status != SettlementStatus.PROCESSED:
        raise HTTPException(status_code=400, detail="Cannot complete separation: Final Settlement is not PROCESSED")
        
    employee = db.query(Employee).with_for_update().filter(Employee.id == separation.employee_id).first()
    user = db.query(User).with_for_update().filter(User.id == employee.user_id).first()
    
    try:
        # 3. Revoke User access & invalidate active sessions
        user.is_active = False
        
        from app.db.models.auth import Session as DBSession
        active_sessions = db.query(DBSession).filter(DBSession.user_id == user.id, DBSession.is_revoked == False).all()
        for sess in active_sessions:
            sess.is_revoked = True
            sess.revoked_at = datetime.now(timezone.utc)
        
        # 4. Finalize Separation
        separation.status = SeparationStatus.COMPLETED
        
        # 6. Audit Records
        audit_deact = AuditLog(
            user_id=current_user.id,
            action="EMPLOYEE_DEACTIVATED",
            entity="Employee",
            entity_id=employee.id,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(audit_deact)
        
        audit_rev = AuditLog(
            user_id=current_user.id,
            action="ACCESS_REVOKED",
            entity="User",
            entity_id=user.id,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(audit_rev)
        
        audit_sep = AuditLog(
            user_id=current_user.id,
            action="SEPARATION_COMPLETED",
            entity="SeparationRecord",
            entity_id=separation.id,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(audit_sep)
        
        db.commit()
        db.refresh(separation)
        return separation
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Separation completion failed: {str(e)}")
