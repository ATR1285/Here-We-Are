from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app.db.database import get_db
from app.db.models.auth import User, Session as DBSession, Role
from app.db.models.audit import AuditLog
from app.schemas.auth import UserLogin, UserResponse
from app.core.security import verify_password
from app.core.permissions import get_current_session_user, require_permission
import uuid
import json

router = APIRouter()

def create_audit_log(db: Session, user_id: str, action: str, entity: str = None, entity_id: str = None):
    audit = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id
    )
    db.add(audit)
    db.commit()

@router.post("/login", response_model=UserResponse)
def login(login_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        # We might not have a user_id if email was wrong, but if we do, log the failure
        if user:
            create_audit_log(db, user.id, "LOGIN_FAILED")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is disabled")
    
    # Create DB Session
    expires = datetime.now(timezone.utc) + timedelta(days=1)
    new_session = DBSession(
        user_id=user.id,
        expires_at=expires
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    # Set HTTP-only cookie
    response.set_cookie(
        key="session_id",
        value=new_session.id,
        httponly=True,
        samesite="lax",
        secure=True,
        expires=expires
    )
    
    create_audit_log(db, user.id, "LOGIN_SUCCESS", "session", new_session.id)
    return user

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    if session_id:
        db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
        if db_session:
            db_session.is_revoked = True
            db_session.revoked_at = datetime.now(timezone.utc)
            db.commit()
            create_audit_log(db, db_session.user_id, "LOGOUT", "session", session_id)
            
    response.delete_cookie("session_id")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
def get_current_user(current_user: User = Depends(get_current_session_user)):
    # Simply return the user verified by the dependency
    return current_user

@router.get("/protected")
def protected_route(current_user: User = Depends(require_permission("view_own_profile"))):
    return {"message": "You have access to this protected route.", "user_id": current_user.id}
