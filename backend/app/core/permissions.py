from fastapi import HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Callable

from app.db.database import get_db
from app.db.models.auth import User, Session as DBSession, Role, Permission, RolePermission
from app.core.logging import logger

def get_current_session_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency to retrieve the currently authenticated user from the HTTP-only cookie."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        
    db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
    expires = db_session.expires_at.replace(tzinfo=timezone.utc) if db_session.expires_at.tzinfo is None else db_session.expires_at
    if not db_session or db_session.is_revoked or expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid")
        
    user = db.query(User).filter(User.id == db_session.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is invalid or disabled")
        
    return user

def require_permission(required_permission: str) -> Callable:
    """
    Dependency factory to enforce deny-by-default authorization.
    Usage in route: current_user = Depends(require_permission("view_own_profile"))
    """
    def permission_checker(current_user: User = Depends(get_current_session_user), db: Session = Depends(get_db)) -> User:
        # Load user role
        role = db.query(Role).filter(Role.id == current_user.role_id).first()
        if not role:
            from app.api.auth import create_audit_log
            create_audit_log(db, current_user.id, "AUTHORIZATION_FAILURE", "permission", required_permission)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Role not found")
        
        # Check permissions explicitly
        has_permission = db.query(RolePermission).join(Permission).filter(
            RolePermission.role_id == role.id,
            Permission.name == required_permission
        ).first()

        if not has_permission:
            from app.api.auth import create_audit_log
            logger.warning(f"Authorization failure: User {current_user.id} attempted to access {required_permission}")
            create_audit_log(db, current_user.id, "AUTHORIZATION_FAILURE", "permission", required_permission)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Insufficient permissions")
            
        return current_user

    return permission_checker
