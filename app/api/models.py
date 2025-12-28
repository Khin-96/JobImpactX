from pydantic import BaseModel, Field, validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# Request models
class AssessmentRequest(BaseModel):
    job_title: str = Field(..., min_length=1, max_length=100)
    average_salary: float = Field(..., ge=20000, le=500000, description="Annual salary in USD")
    years_experience: int = Field(..., ge=0, le=70)
    education_level: str = Field(..., description="High School, Bachelor's, Master's, PhD")
    ai_exposure_index: float = Field(..., ge=0, le=1, description="0=no exposure, 1=highly dependent")
    tech_growth_factor: float = Field(..., ge=0.5, le=1.5)
    skills: List[float] = Field(..., min_items=10, max_items=10, description="10 skill proficiencies (0-1)")
    
    @validator('education_level')
    def validate_education(cls, v):
        valid = ["High School", "Bachelor's", "Master's", "PhD"]
        if v not in valid:
            raise ValueError(f"education_level must be one of {valid}")
        return v
    
    @validator('skills')
    def validate_skills(cls, v):
        if not all(0 <= s <= 1 for s in v):
            raise ValueError("Each skill must be between 0 and 1")
        return v

class AssessmentResponse(BaseModel):
    assessment_id: UUID
    job_title: str
    automation_probability_2030: float = Field(..., ge=0, le=1)
    risk_category: str = Field(..., description="Low, Medium, or High")
    confidence: float = Field(..., ge=0, le=1, description="Model confidence in prediction")
    confidence_interval: List[float] = Field(..., description="[lower, upper] bounds")
    timestamp: datetime

class ExplainRequest(BaseModel):
    assessment_id: UUID

class ExplainResponse(BaseModel):
    assessment_id: UUID
    shap_explanation: dict = Field(..., description="SHAP local & global explanations")
    lime_explanation: dict = Field(..., description="LIME supplementary explanation")
    discrepancy_detected: bool
    discrepancy_details: Optional[dict]
    precedence_note: str

class ScenarioRequest(BaseModel):
    assessment_id: UUID
    changes: dict = Field(..., description="Feature changes (e.g., {'skills': [0.9, ...]})")

class ScenarioResponse(BaseModel):
    original_assessment: AssessmentResponse
    scenario_assessment: AssessmentResponse
    delta_automation_probability: float
    narrative: str

class ErrorResponse(BaseModel):
    detail: str
    timestamp: datetime
    error_code: Optional[str] = None
