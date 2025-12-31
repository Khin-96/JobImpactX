"""
Database query utilities for CRUD operations.
Provides reusable query functions for all database models.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from app.db.models import User, Role, Assessment, Explanation, AuditLog, ModelVersion

logger = logging.getLogger(__name__)


# User Queries
def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    """Retrieve user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Retrieve user by username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieve user by email."""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, username: str, email: str, hashed_password: str, role: str = "Analyst") -> User:
    """Create a new user."""
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Created user: {username} with role {role}")
    return user


def list_users(db: Session, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[User]:
    """List all users with pagination."""
    query = db.query(User)
    if active_only:
        query = query.filter(User.is_active == True)
    return query.offset(skip).limit(limit).all()


def update_user_role(db: Session, user_id: UUID, new_role: str) -> Optional[User]:
    """Update user role."""
    user = get_user_by_id(db, user_id)
    if user:
        user.role = new_role
        db.commit()
        db.refresh(user)
        logger.info(f"Updated user {user.username} role to {new_role}")
    return user


def deactivate_user(db: Session, user_id: UUID) -> Optional[User]:
    """Deactivate user account."""
    user = get_user_by_id(db, user_id)
    if user:
        user.is_active = False
        db.commit()
        db.refresh(user)
        logger.info(f"Deactivated user: {user.username}")
    return user


# Role Queries
def get_role_by_id(db: Session, role_id: UUID) -> Optional[Role]:
    """Retrieve role by ID."""
    return db.query(Role).filter(Role.id == role_id).first()


def get_roles_by_job_title(db: Session, job_title: str) -> List[Role]:
    """Retrieve roles by job title."""
    return db.query(Role).filter(Role.job_title == job_title).all()


def create_role(db: Session, role_data: Dict[str, Any]) -> Role:
    """Create a new role entry."""
    role = Role(**role_data)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def list_roles(db: Session, skip: int = 0, limit: int = 100) -> List[Role]:
    """List all roles with pagination."""
    return db.query(Role).offset(skip).limit(limit).all()


def count_roles(db: Session) -> int:
    """Count total number of roles."""
    return db.query(Role).count()


# Assessment Queries
def get_assessment_by_id(db: Session, assessment_id: UUID) -> Optional[Assessment]:
    """Retrieve assessment by ID."""
    return db.query(Assessment).filter(
        and_(Assessment.id == assessment_id, Assessment.is_deleted == False)
    ).first()


def create_assessment(db: Session, assessment_data: Dict[str, Any]) -> Assessment:
    """Create a new assessment."""
    assessment = Assessment(**assessment_data)
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    logger.info(f"Created assessment: {assessment.id}")
    return assessment


def list_assessments_by_user(
    db: Session, user_id: UUID, skip: int = 0, limit: int = 50
) -> List[Assessment]:
    """List assessments for a specific user."""
    return db.query(Assessment).filter(
        and_(Assessment.user_id == user_id, Assessment.is_deleted == False)
    ).order_by(desc(Assessment.created_at)).offset(skip).limit(limit).all()


def list_assessments_by_risk(
    db: Session, risk_category: str, skip: int = 0, limit: int = 50
) -> List[Assessment]:
    """List assessments by risk category."""
    return db.query(Assessment).filter(
        and_(Assessment.risk_category == risk_category, Assessment.is_deleted == False)
    ).order_by(desc(Assessment.created_at)).offset(skip).limit(limit).all()


def get_assessment_statistics(db: Session) -> Dict[str, Any]:
    """Get assessment statistics."""
    total = db.query(Assessment).filter(Assessment.is_deleted == False).count()
    low_risk = db.query(Assessment).filter(
        and_(Assessment.risk_category == "Low", Assessment.is_deleted == False)
    ).count()
    medium_risk = db.query(Assessment).filter(
        and_(Assessment.risk_category == "Medium", Assessment.is_deleted == False)
    ).count()
    high_risk = db.query(Assessment).filter(
        and_(Assessment.risk_category == "High", Assessment.is_deleted == False)
    ).count()
    
    return {
        "total": total,
        "low_risk": low_risk,
        "medium_risk": medium_risk,
        "high_risk": high_risk,
        "low_risk_pct": (low_risk / total * 100) if total > 0 else 0,
        "medium_risk_pct": (medium_risk / total * 100) if total > 0 else 0,
        "high_risk_pct": (high_risk / total * 100) if total > 0 else 0
    }


def soft_delete_assessment(db: Session, assessment_id: UUID) -> Optional[Assessment]:
    """Soft delete an assessment."""
    assessment = get_assessment_by_id(db, assessment_id)
    if assessment:
        assessment.is_deleted = True
        assessment.deleted_at = datetime.utcnow()
        db.commit()
        db.refresh(assessment)
        logger.info(f"Soft deleted assessment: {assessment_id}")
    return assessment


# Explanation Queries
def get_explanation_by_assessment_id(db: Session, assessment_id: UUID) -> Optional[Explanation]:
    """Retrieve explanation for an assessment."""
    return db.query(Explanation).filter(Explanation.assessment_id == assessment_id).first()


def create_explanation(db: Session, explanation_data: Dict[str, Any]) -> Explanation:
    """Create a new explanation."""
    explanation = Explanation(**explanation_data)
    db.add(explanation)
    db.commit()
    db.refresh(explanation)
    logger.info(f"Created explanation for assessment: {explanation.assessment_id}")
    return explanation


# Audit Log Queries
def create_audit_log(db: Session, audit_data: Dict[str, Any]) -> AuditLog:
    """Create audit log entry."""
    audit = AuditLog(**audit_data)
    db.add(audit)
    db.commit()
    return audit


def list_audit_logs(
    db: Session,
    user_id: Optional[UUID] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[AuditLog]:
    """List audit logs with filters."""
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    return query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()


def count_audit_logs(
    db: Session,
    user_id: Optional[UUID] = None,
    action: Optional[str] = None
) -> int:
    """Count audit logs with filters."""
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    
    return query.count()


# Model Version Queries
def get_active_model_version(db: Session) -> Optional[ModelVersion]:
    """Get the currently active model version."""
    return db.query(ModelVersion).filter(ModelVersion.is_active == True).first()


def create_model_version(db: Session, version_data: Dict[str, Any]) -> ModelVersion:
    """Create a new model version."""
    model_version = ModelVersion(**version_data)
    db.add(model_version)
    db.commit()
    db.refresh(model_version)
    logger.info(f"Created model version: {model_version.version}")
    return model_version


def promote_model_version(db: Session, version_id: UUID, promoted_by: str) -> Optional[ModelVersion]:
    """Promote a model version to active."""
    # Deactivate all other versions
    db.query(ModelVersion).update({"is_active": False})
    
    # Activate the target version
    model_version = db.query(ModelVersion).filter(ModelVersion.id == version_id).first()
    if model_version:
        model_version.is_active = True
        model_version.promoted_by = promoted_by
        model_version.promoted_at = datetime.utcnow()
        db.commit()
        db.refresh(model_version)
        logger.info(f"Promoted model version: {model_version.version}")
    
    return model_version


def list_model_versions(db: Session, limit: int = 10) -> List[ModelVersion]:
    """List recent model versions."""
    return db.query(ModelVersion).order_by(desc(ModelVersion.created_at)).limit(limit).all()
