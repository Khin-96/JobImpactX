from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from uuid import UUID
from app.api.models import ExplainRequest, ExplainResponse
from app.auth.permissions import check_permission, Permission
from app.db.session import get_db
from app.db.models import User, Assessment, Explanation, Role as RoleModel
from app.ml.model import XGBoostModel
from app.ml.explainability import ExplainabilityManager
from app.ml.preprocessing import DataPreprocessor
from datetime import datetime
import pandas as pd
import numpy as np
import logging
import uuid as uuid_module

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Explainability"])

# Model loading will be done on startup
_model = None
_preprocessor = None
_explainer = None


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current user from request."""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


def load_model_and_explainer():
    """Load model, preprocessor, and explainer on startup."""
    global _model, _preprocessor, _explainer
    
    try:
        _model = XGBoostModel()
        _model.load("models/checkpoints/xgboost_model.pkl")
        
        _preprocessor = DataPreprocessor()
        
        # Load training data for explainer (in production, cache this)
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            roles = db.query(RoleModel).limit(1000).all()
            
            if roles:
                data = []
                for role in roles:
                    row = {
                        'Job_Title': role.job_title,
                        'Average_Salary': role.average_salary,
                        'Years_Experience': role.years_experience,
                        'Education_Level': role.education_level,
                        'AI_Exposure_Index': role.ai_exposure_index,
                        'Tech_Growth_Factor': role.tech_growth_factor,
                    }
                    for i, skill in enumerate(role.skills or []):
                        row[f'Skill_{i+1}'] = skill
                    data.append(row)
                
                df = pd.DataFrame(data)
                df = _preprocessor.validate(df)
                df = _preprocessor.clean(df)
                X_train, _ = _preprocessor.fit_transform(df)
                
                _explainer = ExplainabilityManager(_model, X_train, _preprocessor.feature_names)
                logger.info("Model and explainer loaded successfully")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to load model and explainer: {e}")


@router.post("/explain", response_model=ExplainResponse)
async def explain_assessment(
    request: ExplainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ExplainResponse:
    """
    Get SHAP and LIME explanations for an assessment.
    Returns real SHAP TreeExplainer and LIME TabularExplainer results.
    """
    
    # Check permission
    if not check_permission(current_user.role, Permission.EXPLAIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Ensure model is loaded
    if _model is None or _explainer is None:
        load_model_and_explainer()
        if _model is None or _explainer is None:
            raise HTTPException(status_code=503, detail="Model not available")
    
    # Get assessment
    assessment = db.query(Assessment).filter(
        Assessment.id == request.assessment_id
    ).first()
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Check if explanation already exists
    existing = db.query(Explanation).filter(
        Explanation.assessment_id == request.assessment_id
    ).first()
    
    if existing:
        return ExplainResponse(
            assessment_id=request.assessment_id,
            shap_explanation=existing.shap_local,
            lime_explanation=existing.lime_explanation,
            discrepancy_detected=existing.discrepancy_noted,
            discrepancy_details=existing.discrepancy_details,
            precedence_note="SHAP is authoritative; LIME is supplementary"
        )
    
    # Get role data
    role = db.query(RoleModel).filter(RoleModel.id == assessment.role_id).first()
    
    if not role:
        raise HTTPException(status_code=404, detail="Role data not found for assessment")
    
    # Prepare features
    role_dict = {
        'Job_Title': role.job_title,
        'Average_Salary': role.average_salary,
        'Years_Experience': role.years_experience,
        'Education_Level': role.education_level,
        'AI_Exposure_Index': role.ai_exposure_index,
        'Tech_Growth_Factor': role.tech_growth_factor,
    }
    for i, skill in enumerate(role.skills or []):
        role_dict[f'Skill_{i+1}'] = skill
    
    df = pd.DataFrame([role_dict])
    X_processed = _preprocessor.transform(df)
    
    # Generate real SHAP and LIME explanations
    logger.info(f"Generating real explanations for assessment {request.assessment_id}")
    
    try:
        explanation_result = _explainer.explain(X_processed)
        
        # Store in database
        explanation = Explanation(
            id=uuid_module.uuid4(),
            assessment_id=request.assessment_id,
            shap_global=explanation_result['shap_explanation'],
            shap_local=explanation_result['shap_explanation'],
            lime_explanation=explanation_result['lime_explanation'],
            discrepancy_noted=explanation_result['discrepancy_detected'],
            discrepancy_details=str(explanation_result.get('discrepancy_details')),
            created_at=datetime.utcnow()
        )
        db.add(explanation)
        db.commit()
        db.refresh(explanation)
        
        logger.info(f"Explanations generated and stored for assessment {request.assessment_id}")
        
        return ExplainResponse(
            assessment_id=request.assessment_id,
            shap_explanation=explanation.shap_local,
            lime_explanation=explanation.lime_explanation,
            discrepancy_detected=explanation.discrepancy_noted,
            discrepancy_details=explanation_result.get('discrepancy_details'),
            precedence_note="SHAP is authoritative; LIME is supplementary"
        )
        
    except Exception as e:
        logger.error(f"Failed to generate explanations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Explanation generation failed: {str(e)}"
        )