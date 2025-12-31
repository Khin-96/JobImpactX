"""
Audit Log API Route.
Access and filter audit trail.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from app.auth.permissions import check_permission, Permission
from app.db.session import get_db
from app.db.models import User, AuditLog
from app.db.queries import list_audit_logs, count_audit_logs
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Audit"])


class AuditLogResponse(BaseModel):
    """Audit log entry response."""
    id: UUID
    user_id: Optional[UUID]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[UUID]
    status: str
    details: dict
    ip_address: Optional[str]
    created_at: datetime


class AuditLogsResponse(BaseModel):
    """Paginated audit logs response."""
    logs: List[AuditLogResponse]
    total: int
    page: int
    per_page: int
    pages: int


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current user from request."""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


@router.get("/audit", response_model=AuditLogsResponse)
async def get_audit_logs(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AuditLogsResponse:
    """
    Retrieve audit logs with filtering and pagination.
    
    Requires AUDIT_VIEW permission.
    """
    
    # Check permission
    if not check_permission(current_user.role, Permission.AUDIT_VIEW):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Non-admin users can only see their own logs
    if current_user.role != "Admin" and user_id != current_user.id:
        user_id = current_user.id
    
    logger.info(
        f"Audit log request by {current_user.username}: "
        f"user_id={user_id}, action={action}, page={page}"
    )
    
    # Calculate skip
    skip = (page - 1) * per_page
    
    # Fetch logs
    try:
        logs = list_audit_logs(
            db=db,
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=per_page
        )
        
        total = count_audit_logs(
            db=db,
            user_id=user_id,
            action=action
        )
        
        pages = (total + per_page - 1) // per_page
        
        log_responses = [
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                status=log.status,
                details=log.details or {},
                ip_address=log.ip_address,
                created_at=log.created_at
            )
            for log in logs
        ]
        
        return AuditLogsResponse(
            logs=log_responses,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve audit logs"
        )


@router.get("/audit/{audit_id}", response_model=AuditLogResponse)
async def get_audit_log_by_id(
    audit_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AuditLogResponse:
    """
    Retrieve a specific audit log entry by ID.
    
    Requires AUDIT_VIEW permission.
    """
    
    # Check permission
    if not check_permission(current_user.role, Permission.AUDIT_VIEW):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    log = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    # Non-admin users can only see their own logs
    if current_user.role != "Admin" and log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return AuditLogResponse(
        id=log.id,
        user_id=log.user_id,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        status=log.status,
        details=log.details or {},
        ip_address=log.ip_address,
        created_at=log.created_at
    )
