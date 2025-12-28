from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.api.models import AssessmentRequest, AssessmentResponse
from app.auth.permissions import check_permission, Permission
from app.db.session import get_db
from app.db.models import User, Assessment, Role as RoleModel
from app.ml.model import XGBoostModel
from app.ml.preprocessing import DataPreprocessor
from datetime import datetime
import logging
import uuid
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Assessment"])

# Load model and preprocessor (in production, use dependency injection)
model = XGBoostModel()
model.load("models/checkpoints/xgboost_model.pkl")
preprocessor = DataPreprocessor()

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current user from request."""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@router.post("/assess", response_model=AssessmentResponse)
async def assess_role(
    request: AssessmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AssessmentResponse:
    """
    Assess a job role for AI automation risk.
    
    Returns:
    - Automation probability (0-1)
    - Risk category (Low, Medium, High)
    - Confidence score
    """
    
    # Check permission
    if not check_permission(current_user.role, Permission.ASSESS):
        logger.warning(f"Unauthorized assess attempt by {current_user.username}")
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        # Convert request to DataFrame for preprocessing
        X_dict = request.dict()
        skills = X_dict.pop('skills')
        for i, skill in enumerate(skills):
            X_dict[f'Skill_{i+1}'] = skill
        
        df = pd.DataFrame([X_dict])
        
        # Preprocess
        X_processed = preprocessor.transform(df)
        
        # Predict
        automation_prob = float(model.predict(X_processed)[0])
        
        # Categorize risk
        if automation_prob < 0.33:
            risk_category = "Low"
        elif automation_prob < 0.67:
            risk_category = "Medium"
        else:
            risk_category = "High"
        
        # Calculate confidence (simplified; in production use calibration)
        confidence = min(0.95, 0.7 + abs(automation_prob - 0.5) * 0.5)
        confidence_interval = [
            max(0, automation_prob - 0.1),
            min(1, automation_prob + 0.1)
        ]
        
        # Store in database
        assessment = Assessment(
            id=uuid.uuid4(),
            user_id=current_user.id,
            automation_probability=automation_prob,
            risk_category=risk_category,
            confidence=confidence,
            confidence_interval=confidence_interval,
            created_at=datetime.utcnow()
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        
        logger.info(
            f"Assessment created: {assessment.id} by {current_user.username} "
            f"- {request.job_title} ({risk_category})"
        )
        
        return AssessmentResponse(
            assessment_id=assessment.id,
            job_title=request.job_title,
            automation_probability_2030=automation_prob,
            risk_category=risk_category,
            confidence=confidence,
            confidence_interval=confidence_interval,
            timestamp=assessment.created_at
        )
    
    except Exception as e:
        logger.error(f"Assessment error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Assessment failed. Please try again."
        )

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}
