"""
Governance API Route.
Bias analysis and sensitivity reports.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel
from app.auth.permissions import check_permission, Permission
from app.db.session import get_db
from app.db.models import User, Role, Assessment
from app.ml.model import XGBoostModel
from app.ml.preprocessing import DataPreprocessor
from app.ml.bias_analysis import BiasAnalyzer
from app.ml.sensitivity_analysis import SensitivityAnalyzer
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/governance", tags=["Governance"])

# Model will be loaded on startup
_model = None
_preprocessor = None


class BiasReportResponse(BaseModel):
    """Bias analysis report response."""
    summary: Dict[str, Any]
    demographic_parity: Dict[str, Any]
    equalized_odds: Dict[str, Any]
    calibration: Dict[str, Any]
    overall_assessment: str


class SensitivityReportResponse(BaseModel):
    """Sensitivity analysis report response."""
    sample_analysis: Dict[str, Any]
    confidence_intervals: Dict[str, Any]
    recommendations: List[str]


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
        logger.info("Model loaded for governance analysis")


@router.get("/bias", response_model=BiasReportResponse)
async def get_bias_report(
    attributes: List[str] = Query(["Education_Level"], description="Sensitive attributes to analyze"),
    sample_size: int = Query(500, ge=100, le=10000, description="Number of samples to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> BiasReportResponse:
    """
    Generate bias and fairness analysis report.
    
    Analyzes demographic parity, equalized odds, and calibration.
    Requires CONFIGURE_MODEL permission.
    """
    
    # Check permission (Admin only for governance reports)
    if not check_permission(current_user.role, Permission.CONFIGURE_MODEL):
        raise HTTPException(status_code=403, detail="Insufficient permissions - Admin only")
    
    # Ensure model is loaded
    if _model is None:
        load_model()
    
    logger.info(f"Generating bias report for attributes: {attributes}")
    
    try:
        # Load role data
        roles = db.query(Role).limit(sample_size).all()
        
        if len(roles) < 100:
            raise HTTPException(
                status_code=400,
                detail="Insufficient data for bias analysis. Need at least 100 samples."
            )
        
        # Prepare data
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
        
        # Keep sensitive features
        sensitive_features = df[attributes].copy()
        
        # Transform features for prediction
        X = df.copy()
        X_processed = _preprocessor.transform(X)
        
        # Generate predictions
        predictions = _model.predict(X_processed)
        
        # Generate synthetic actuals (in production, use real outcomes)
        # For demo: use predictions with some noise
        actuals = (predictions + np.random.normal(0, 0.1, len(predictions))).clip(0, 1)
        actuals = (actuals > 0.5).astype(float)
        
        # Run bias analysis
        analyzer = BiasAnalyzer(predictions, actuals, sensitive_features)
        report = analyzer.generate_report(attributes)
        
        logger.info(f"Bias report generated: {report['overall_assessment']}")
        
        return BiasReportResponse(**report)
        
    except Exception as e:
        logger.error(f"Failed to generate bias report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Bias analysis failed: {str(e)}"
        )


@router.get("/sensitivity", response_model=SensitivityReportResponse)
async def get_sensitivity_report(
    sample_size: int = Query(100, ge=10, le=1000, description="Number of samples to analyze"),
    perturbation_range: float = Query(0.2, ge=0.05, le=0.5, description="Perturbation range (relative)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SensitivityReportResponse:
    """
    Generate sensitivity and robustness analysis report.
    
    Tests model response to feature perturbations.
    Requires CONFIGURE_MODEL permission.
    """
    
    # Check permission (Admin only for governance reports)
    if not check_permission(current_user.role, Permission.CONFIGURE_MODEL):
        raise HTTPException(status_code=403, detail="Insufficient permissions - Admin only")
    
    # Ensure model is loaded
    if _model is None:
        load_model()
    
    logger.info(f"Generating sensitivity report for {sample_size} samples")
    
    try:
        # Load role data
        roles = db.query(Role).limit(sample_size).all()
        
        if len(roles) < 10:
            raise HTTPException(
                status_code=400,
                detail="Insufficient data for sensitivity analysis. Need at least 10 samples."
            )
        
        # Prepare data
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
        
        # Transform features
        X_processed = _preprocessor.transform(df)
        
        # Run sensitivity analysis
        analyzer = SensitivityAnalyzer(_model, _preprocessor, _preprocessor.feature_names)
        report = analyzer.generate_report(
            X_processed,
            perturbation_range=(-perturbation_range, perturbation_range)
        )
        
        logger.info(
            f"Sensitivity report generated: "
            f"{report['sample_analysis']['summary']['fragile_count']} fragile features detected"
        )
        
        return SensitivityReportResponse(**report)
        
    except Exception as e:
        logger.error(f"Failed to generate sensitivity report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Sensitivity analysis failed: {str(e)}"
        )


@router.get("/model-info")
async def get_model_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get information about the current active model.
    
    Requires CONFIGURE_MODEL permission.
    """
    
    # Check permission
    if not check_permission(current_user.role, Permission.CONFIGURE_MODEL):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Ensure model is loaded
    if _model is None:
        load_model()
    
    try:
        from app.db.models import ModelVersion
        
        active_version = db.query(ModelVersion).filter(
            ModelVersion.is_active == True
        ).first()
        
        info = {
            "model_type": "XGBoost",
            "status": "active" if _model else "not_loaded",
            "feature_count": len(_preprocessor.feature_names) if _preprocessor else 0,
            "feature_names": _preprocessor.feature_names if _preprocessor else []
        }
        
        if active_version:
            info.update({
                "version": active_version.version,
                "training_date": active_version.training_date.isoformat() if active_version.training_date else None,
                "auc_roc": active_version.auc_roc,
                "brier_score": active_version.brier_score,
                "promoted_by": active_version.promoted_by,
                "promoted_at": active_version.promoted_at.isoformat() if active_version.promoted_at else None
            })
        
        return info
        
    except Exception as e:
        logger.error(f"Failed to get model info: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve model information"
        )
