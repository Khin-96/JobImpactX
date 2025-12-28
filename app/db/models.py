from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="Analyst")  # Admin, Analyst, Viewer
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<User {self.username}>"

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_title = Column(String, nullable=False, index=True)
    average_salary = Column(Float)
    years_experience = Column(Integer)
    education_level = Column(String)
    ai_exposure_index = Column(Float)
    tech_growth_factor = Column(Float)
    skills = Column(JSONB)  # Array of 10 skill proficiencies
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_job_salary_exp', 'job_title', 'average_salary', 'years_experience', unique=True),
    )
    
    def __repr__(self):
        return f"<Role {self.job_title}>"

class Assessment(Base):
    __tablename__ = "assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    automation_probability = Column(Float, nullable=False)
    risk_category = Column(String, nullable=False)  # Low, Medium, High
    confidence = Column(Float, nullable=False)
    confidence_interval = Column(JSONB)  # [lower, upper]
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_user_risk', 'user_id', 'risk_category'),
        Index('idx_created_date', 'created_at'),
    )

class Explanation(Base):
    __tablename__ = "explanations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey('assessments.id'), unique=True)
    shap_global = Column(JSONB)  # Global feature importance
    shap_local = Column(JSONB)   # Local contributions
    lime_explanation = Column(JSONB)
    discrepancy_noted = Column(Boolean, default=False)
    discrepancy_details = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    action = Column(String, nullable=False)  # assessment, explain, export, etc.
    resource_type = Column(String)
    resource_id = Column(UUID(as_uuid=True))
    status = Column(String)  # success, failure
    details = Column(JSONB)
    ip_address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_user_action', 'user_id', 'action'),
        Index('idx_created_date', 'created_at'),
    )

class ModelVersion(Base):
    __tablename__ = "model_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(String, unique=True, nullable=False)
    training_date = Column(DateTime)
    auc_roc = Column(Float)
    brier_score = Column(Float)
    calibration_error = Column(Float)
    fairness_score = Column(Float)
    is_active = Column(Boolean, default=False)
    promoted_by = Column(String)
    promoted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSONB)