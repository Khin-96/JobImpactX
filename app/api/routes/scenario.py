"""
Scenario Analysis API Route.
What-if analysis for role assessments.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.api.models import ScenarioRequest, ScenarioResponse, AssessmentResponse
from app.auth.permissions import check_permission, Permission
from app.db.session import get_db
from app.db.models import User, Assessment, Role as RoleModel
from app.ml.model import XGBoostModel
from app.ml.preprocessing import DataPreprocessor
from datetime import datetime
import pandas as pd
import numpy as np
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Scenario"])

# Model will be loaded on startup
_model = None
_preprocessor = None


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current user from request."""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


def load_model():
    """Load model and preprocessor."""
    global _model, _preprocessor
    
    if _model is None:
        _model = XGBoostModel()
        _model.load("models/checkpoints/xgboost_model.pkl")
        _preprocessor = DataPreprocessor()
        logger.info("Model loaded for scenario analysis")


@router.post("/scenario", response_model=ScenarioResponse)
async def analyze_scenario(
    request: ScenarioRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ScenarioResponse:
    """
    Perform what-if analysis by applying changes to features.
    
    Args:
        assessment_id: Original assessment to modify
        changes: Dictionary of feature changes (e.g., {"skills": [0.9, ...], "education_level": "Master's"})
        
    Returns:
        Comparison of original vs scenario predictions with narrative
    """
    
    # Check permission
    if not check_permission(current_user.role, Permission.SCENARIO):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Ensure model is loaded
    if _model is None:
        load_model()
    
    # Get original assessment
    original_assessment = db.query(Assessment).filter(
        Assessment.id == request.assessment_id
    ).first()
    
    if not original_assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Get role data
    role = db.query(RoleModel).filter(RoleModel.id == original_assessment.role_id).first()
    
    if not role:
        raise HTTPException(status_code=404, detail="Role data not found")
    
    # Prepare original features
    original_data = {
        'Job_Title': role.job_title,
        'Average_Salary': role.average_salary,
        'Years_Experience': role.years_experience,
        'Education_Level': role.education_level,
        'AI_Exposure_Index': role.ai_exposure_index,
        'Tech_Growth_Factor': role.tech_growth_factor,
    }
    for i, skill in enumerate(role.skills or []):
        original_data[f'Skill_{i+1}'] = skill
    
    # Apply scenario changes
    scenario_data = original_data.copy()
    
    if 'skills' in request.changes:
        skills = request.changes['skills']
        if len(skills) == 10:
            for i, skill in enumerate(skills):
                scenario_data[f'Skill_{i+1}'] = skill
    
    if 'education_level' in request.changes:
        scenario_data['Education_Level'] = request.changes['education_level']
    
    if 'average_salary' in request.changes:
        scenario_data['Average_Salary'] = request.changes['average_salary']
    
    if 'years_experience' in request.changes:
        scenario_data['Years_Experience'] = request.changes['years_experience']
    
    if 'ai_exposure_index' in request.changes:
        scenario_data['AI_Exposure_Index'] = request.changes['ai_exposure_index']
    
    if 'tech_growth_factor' in request.changes:
        scenario_data['Tech_Growth_Factor'] = request.changes['tech_growth_factor']
    
    # Preprocess and predict
    try:
        df_scenario = pd.DataFrame([scenario_data])
        X_scenario = _preprocessor.transform(df_scenario)
        
        scenario_prob = float(_model.predict(X_scenario)[0])
        
        # Categorize risk
        if scenario_prob < 0.33:
            risk_category = "Low"
        elif scenario_prob < 0.67:
            risk_category = "Medium"
        else:
            risk_category = "High"
        
        # Calculate confidence
        confidence = min(0.95, 0.7 + abs(scenario_prob - 0.5) * 0.5)
        confidence_interval = [
            max(0, scenario_prob - 0.1),
            min(1, scenario_prob + 0.1)
        ]
        
        # Create scenario assessment
        scenario_assessment = AssessmentResponse(
            assessment_id=uuid.uuid4(),
            job_title=role.job_title,
            automation_probability_2030=scenario_prob,
            risk_category=risk_category,
            confidence=confidence,
            confidence_interval=confidence_interval,
            timestamp=datetime.utcnow()
        )
        
        # Calculate delta
        delta = scenario_prob - original_assessment.automation_probability
        
        # Generate narrative
        narrative = _generate_narrative(
            original_assessment.automation_probability,
            scenario_prob,
            original_assessment.risk_category,
            risk_category,
            request.changes
        )
        
        logger.info(
            f"Scenario analysis completed: {original_assessment.automation_probability:.2f} -> "
            f"{scenario_prob:.2f} (delta: {delta:+.2f})"
        )
        
        return ScenarioResponse(
            original_assessment=AssessmentResponse(
                assessment_id=original_assessment.id,
                job_title=role.job_title,
                automation_probability_2030=original_assessment.automation_probability,
                risk_category=original_assessment.risk_category,
                confidence=original_assessment.confidence,
                confidence_interval=original_assessment.confidence_interval,
                timestamp=original_assessment.created_at
            ),
            scenario_assessment=scenario_assessment,
            delta_automation_probability=delta,
            narrative=narrative
        )
        
    except Exception as e:
        logger.error(f"Scenario analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Scenario analysis failed: {str(e)}"
        )


def _generate_narrative(
    original_prob: float,
    scenario_prob: float,
    original_category: str,
    scenario_category: str,
    changes: dict
) -> str:
    """Generate human-readable narrative for scenario results."""
    
    delta = scenario_prob - original_prob
    delta_pct = delta * 100
    
    # Build change description
    change_parts = []
    
    if 'skills' in changes:
        change_parts.append("skill enhancements")
    if 'education_level' in changes:
        change_parts.append(f"education upgrade to {changes['education_level']}")
    if 'average_salary' in changes:
        change_parts.append("salary adjustment")
    if 'years_experience' in changes:
        change_parts.append("experience level modification")
    
    change_desc = ", ".join(change_parts) if change_parts else "the proposed changes"
    
    # Build narrative
    if abs(delta) < 0.05:
        narrative = (
            f"The proposed changes ({change_desc}) would have minimal impact on automation risk, "
            f"maintaining a {original_category} risk classification. "
            f"Risk would change by only {abs(delta_pct):.1f} percentage points."
        )
    elif delta < 0:
        narrative = (
            f"Implementing {change_desc} would reduce automation risk by {abs(delta_pct):.1f} percentage points, "
            f"from {original_prob*100:.1f}% to {scenario_prob*100:.1f}%. "
        )
        
        if original_category != scenario_category:
            narrative += f"This change would improve the risk classification from {original_category} to {scenario_category}. "
        
        narrative += "These improvements would strengthen the role's resilience to automation."
        
    else:  # delta > 0
        narrative = (
            f"The proposed changes ({change_desc}) would increase automation risk by {delta_pct:.1f} percentage points, "
            f"from {original_prob*100:.1f}% to {scenario_prob*100:.1f}%. "
        )
        
        if original_category != scenario_category:
            narrative += f"This would worsen the risk classification from {original_category} to {scenario_category}. "
        
        narrative += "Consider alternative strategies to mitigate automation risk."
    
    return narrative
