from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.api.models import ExplainRequest, ExplainResponse
from app.auth.permissions import check_permission, Permission
from app.db.session import get_db
from app.db.models import User, Assessment, Explanation
from app.ml.model import XGBoostModel
from app.ml.explainability import ExplainabilityManager
from app.ml.preprocessing import DataPreprocessor
from datetime import datetime
import pandas as pd
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Explainability"])

model = XGBoostModel()
model.load("models/checkpoints/xgboost_model.pkl")
preprocessor = DataPreprocessor()

@router.post("/explain", response_model=ExplainResponse)
async def explain_assessment(
    request: ExplainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda req: None)  # Placeholder
) -> ExplainResponse:
    """
    Get SHAP and LIME explanations for an assessment.
    """
    
    # Check permission
    if not check_permission(current_user.role if current_user else "Viewer", Permission.EXPLAIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
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
            shap_explanation=existing.shap_global,
            lime_explanation=existing.lime_explanation,
            discrepancy_detected=existing.discrepancy_noted,
            discrepancy_details=existing.discrepancy_details,
            precedence_note="SHAP is authoritative; LIME is supplementary"
        )
    
    # Generate explanations (placeholder)
    logger.info(f"Generating explanations for {request.assessment_id}")
    
    explanation = Explanation(
        id=uuid.uuid4(),
        assessment_id=request.assessment_id,
        shap_global={"placeholder": "SHAP global explanation"},
        shap_local={"placeholder": "SHAP local explanation"},
        lime_explanation={"placeholder": "LIME explanation"},
        discrepancy_noted=False,
        created_at=datetime.utcnow()
    )
    db.add(explanation)
    db.commit()
    
    return ExplainResponse(
        assessment_id=request.assessment_id,
        shap_explanation=explanation.shap_global,
        lime_explanation=explanation.lime_explanation,
        discrepancy_detected=explanation.discrepancy_noted,
        discrepancy_details=explanation.discrepancy_details,
        precedence_note="SHAP is authoritative; LIME is supplementary"
    )