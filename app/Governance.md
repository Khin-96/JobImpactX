# GOVERNANCE.md

## AI Governance, Security & Responsible AI Framework

---

## 1. Governance Principles

This platform is built on five core governance principles:

### 1.1 **Explainability First**
All predictions must be explainable and auditable. SHAP provides theoretically-sound explanations; LIME provides human-friendly context. Every assessment includes a confidence indicator and explanation.

### 1.2 **Human Decision-Making**
This platform **informs** decisions; it does not **make** decisions. Risk assessments are decision-support tools. Humans retain final authority over employment-related decisions.

### 1.3 **Transparency & Accountability**
Full audit trail of all assessments, explanations, and access. Users understand:
- What data was used
- How the model works (global feature importance)
- Why a specific role received a specific risk score (SHAP explanations)
- What confidence to place in the assessment

### 1.4 **Fairness & Non-Discrimination**
Assessments must not discriminate based on protected attributes (e.g., education level, salary band acting as proxy for identity). Continuous fairness testing ensures equitable treatment.

### 1.5 **Data Minimization & Privacy**
Collect only necessary data. Roles data is aggregated; individual worker data is not stored. Audit logs are immutable but access-controlled.

---

## 2. Security Architecture

### 2.1 Authentication & Authorization

**JWT-Based Authentication**

```python
# app/auth/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

**Role-Based Access Control (RBAC)**

```python
# app/auth/permissions.py
PERMISSION_MATRIX = {
    "Admin": ["assess", "explain", "scenario", "manage_users", "configure_model", "audit_view"],
    "Analyst": ["assess", "explain", "scenario", "audit_view_own"],
    "Viewer": ["explain", "report_view"]
}

async def check_permission(user: User, required_permission: str):
    permissions = PERMISSION_MATRIX.get(user.role, [])
    if required_permission not in permissions:
        raise HTTPException(
            status_code=403,
            detail=f"User role '{user.role}' does not have permission '{required_permission}'"
        )
    
    # Log permission check for audit
    log_audit(user.id, "permission_check", required_permission, "success")
```

### 2.2 Data Security

**In Transit**:
- HTTPS/TLS 1.3 for all communications
- JWT tokens in Authorization header (not URL)
- Database connections over SSL

**At Rest**:
- PostgreSQL: Encrypted columns for sensitive data (passwords with bcrypt)
- Redis: Password-protected, no authentication tokens in cache
- Backup: Encrypted AWS S3 or equivalent

**Access Control**:
- Row-level security: Users see only their own assessments (unless Admin)
- Column-level masking: Non-admins don't see detailed salary data

```sql
-- Row-level security in PostgreSQL
CREATE POLICY assessment_policy ON assessments
  USING (user_id = current_user_id OR current_user_role = 'Admin');

ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;
```

### 2.3 API Security

**Rate Limiting**:
```python
# app/api/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/assess")
@limiter.limit("100/hour")  # 100 requests per hour per IP
async def assess_role(request: Request, ...):
    pass
```

**CORS Configuration**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

**Input Validation**:
```python
from pydantic import BaseModel, validator

class AssessmentRequest(BaseModel):
    job_title: str = Field(..., min_length=1, max_length=100)
    average_salary: float = Field(..., ge=20000, le=500000)
    years_experience: int = Field(..., ge=0, le=70)
    education_level: str = Field(..., regex="^(High School|Bachelor's|Master's|PhD)$")
    ai_exposure_index: float = Field(..., ge=0, le=1)
    tech_growth_factor: float = Field(..., ge=0.5, le=1.5)
    skills: list = Field(..., min_items=10, max_items=10)
    
    @validator('skills')
    def validate_skills(cls, v):
        if not all(0 <= s <= 1 for s in v):
            raise ValueError("Each skill must be between 0 and 1")
        return v
```

### 2.4 Threat Model

**Asset**: Automated job impact assessments + audit logs
**Threats**:

| Threat | Impact | Likelihood | Mitigation |
|--------|--------|------------|-----------|
| Unauthorized API access | Attacker makes unauthorized assessments | Medium | JWT auth, rate limiting, IP whitelisting |
| Database breach | Exposed all assessments & audit logs | Low | Encryption at rest, regular audits, WAF |
| Model poisoning | Biased predictions affecting hiring decisions | Low | Input validation, data versioning, holdout test sets |
| Data exfiltration | Sensitive role data leaked | Medium | Row-level security, access logs, DLP tools |
| Denial of Service | API unavailable | Medium | Rate limiting, load balancing, monitoring |
| Privilege escalation | Regular user becomes Admin | Low | RBAC enforcement, audit all permission changes |

**Risk Acceptance**: 
- Threats with Risk = Impact × Likelihood > threshold (e.g., 6/10) require active mitigation
- All threats logged and reviewed quarterly

---

## 3. Bias & Fairness Analysis

### 3.1 Fairness Metrics

**Demographic Parity**:
Predicted positive rate should be equal across all groups.

```
P(ŷ=1 | Group=G) ≈ P(ŷ=1 | Group=G')
```

Example: Automation risk for "High School" educated roles should not differ significantly from "PhD" educated roles (controlling for actual job characteristics).

**Equalized Odds**:
True positive rate and false positive rate should be equal across groups.

```
P(ŷ=1 | y=1, Group=G) ≈ P(ŷ=1 | y=1, Group=G')  [True Positive Rate]
P(ŷ=1 | y=0, Group=G) ≈ P(ŷ=1 | y=0, Group=G')  [False Positive Rate]
```

### 3.2 Bias Detection Implementation

```python
# app/ml/bias_analysis.py
from fairlearn.metrics import demographic_parity_difference, equalized_odds_difference

class BiasAnalyzer:
    def __init__(self, model, X, y):
        self.model = model
        self.X = X
        self.y = y
    
    def analyze(self, protected_attribute):
        """
        Compute fairness metrics for protected attribute.
        protected_attribute: column name in X (e.g., 'education_level')
        """
        predictions = self.model.predict(self.X)
        groups = self.X[protected_attribute].unique()
        
        report = {
            "protected_attribute": protected_attribute,
            "groups": {},
            "overall_fairness_score": 0
        }
        
        for group in groups:
            mask = self.X[protected_attribute] == group
            group_y_pred = predictions[mask]
            group_y_true = self.y[mask]
            
            # Demographic parity
            parity_diff = demographic_parity_difference(
                group_y_true, group_y_pred, groups=self.X[protected_attribute]
            )
            
            # Equalized odds
            eq_odds = equalized_odds_difference(
                group_y_true, group_y_pred, groups=self.X[protected_attribute]
            )
            
            report["groups"][group] = {
                "n_samples": mask.sum(),
                "positive_rate": group_y_pred.mean(),
                "demographic_parity_diff": abs(parity_diff),
                "equalized_odds_diff": abs(eq_odds),
                "fairness_status": "PASS" if abs(parity_diff) < 0.10 else "FAIL"
            }
        
        report["overall_fairness_score"] = self._compute_overall_score(report["groups"])
        return report
    
    def _compute_overall_score(self, groups_report):
        """Average fairness across groups (higher = fairer)"""
        parity_diffs = [g["demographic_parity_diff"] for g in groups_report.values()]
        return 1 - np.mean(parity_diffs)
```

### 3.3 Continuous Fairness Monitoring

```python
# scripts/monitor_fairness.py
def monitor_fairness_weekly():
    """
    Run weekly fairness analysis on recent predictions.
    Alert if fairness score degrades.
    """
    recent_assessments = db.query(Assessment).filter(
        Assessment.created_at >= datetime.utcnow() - timedelta(days=7)
    ).all()
    
    X = pd.DataFrame([a.to_dict() for a in recent_assessments])
    y = X['risk_category'].map({'Low': 0, 'Medium': 0.5, 'High': 1})
    
    analyzer = BiasAnalyzer(model, X, y)
    
    for attr in ['education_level', 'salary_band']:
        report = analyzer.analyze(attr)
        
        # Log report
        log_fairness_report(report)
        
        # Alert if fairness degrades
        if report['overall_fairness_score'] < 0.85:  # Threshold
            send_alert(
                f"Fairness degradation for {attr}. Score: {report['overall_fairness_score']:.2f}"
            )
```

### 3.4 Fairness-Explainability Contract

**Promise**: If a role receives "High" risk due to a feature, that feature relationship must be fair.

**Example**:
- Model says: "Construction Worker has 0.85 automation risk"
- SHAP says: Feature "AI_Exposure_Index = 0.86" pushed risk up
- Fairness check: Is AI exposure legitimate predictor, or proxy for something unfair?
- Resolution: Yes, legitimate (actual job characteristic), not proxy for education or demographics

---

## 4. Sensitivity Analysis

### 4.1 Feature Robustness

How much can features vary before risk category changes?

```python
# app/ml/sensitivity_analysis.py
class SensitivityAnalyzer:
    def __init__(self, model, feature_names):
        self.model = model
        self.feature_names = feature_names
    
    def analyze_feature(self, X_test, feature_idx, perturbation_range=0.2):
        """
        Perturb feature by ±perturbation_range and measure impact.
        """
        original_pred = self.model.predict(X_test)
        original_risk = self._categorize(original_pred)
        
        results = {
            "feature": self.feature_names[feature_idx],
            "perturbations": {}
        }
        
        for delta in [-perturbation_range, -0.1, 0, 0.1, perturbation_range]:
            X_perturbed = X_test.copy()
            X_perturbed[:, feature_idx] *= (1 + delta)
            
            perturbed_pred = self.model.predict(X_perturbed)
            perturbed_risk = self._categorize(perturbed_pred)
            
            category_changes = (original_risk != perturbed_risk).mean()
            
            results["perturbations"][f"{delta:+.1%}"] = {
                "category_change_rate": category_changes,
                "avg_prob_delta": np.abs(perturbed_pred - original_pred).mean(),
                "max_prob_delta": np.abs(perturbed_pred - original_pred).max()
            }
        
        return results
    
    def _categorize(self, predictions):
        return np.array([
            'Low' if p < 0.33 else 'Medium' if p < 0.67 else 'High'
            for p in predictions
        ])
```

### 4.2 Interpretation

**Stable Feature**: Category doesn't change even with ±20% perturbation → Robust, reliable
**Fragile Feature**: Category changes frequently → Use with caution, explain carefully

**In Executive Dashboard**:
Show sensitivity badges next to each feature contribution:
- 🟢 Green (Stable): Feature is robust predictor
- 🟡 Yellow (Moderate): Some sensitivity, worth noting
- 🔴 Red (Fragile): Be cautious; prediction sensitive to this feature

---

## 5. Data Governance

### 5.1 Data Lineage

Track data through pipeline:

```
Raw CSV → Validation → Cleaning → Feature Engineering → Scaling → Model Input
  ↓        ✓ Rows: 3000  → Rows: 2950  → Rows: 2950  → Rows: 2950
  ✓ Cols: 20       (50 duplicates removed)
```

**Documented**:
- Data source, collection date, version
- Transformations applied (why, by whom)
- Quality checks performed
- Any data quality issues or flags

### 5.2 Data Retention & Deletion

**Retention Policy**:
- Raw data: 7 years (legal hold for investigations)
- Assessments: 7 years
- Audit logs: 10 years
- Cache: 24 hours TTL

**Right to be Forgotten**:
- User can request deletion of their assessment data
- Audit log entry created (user ID redacted in old assessments)
- Legal/compliance team approves before deletion

```python
# app/db/gdpr.py
async def delete_user_data(user_id: str):
    """
    GDPR: Right to be forgotten.
    Soft-delete: Mark assessments as deleted, preserve audit trail.
    """
    assessments = db.query(Assessment).filter(Assessment.user_id == user_id).all()
    for a in assessments:
        a.is_deleted = True
        a.deleted_at = datetime.utcnow()
    
    # Audit log (user_id redacted)
    log_audit("SYSTEM", "gdpr_deletion", "user_data", None, "success", {
        "reason": "User requested deletion",
        "n_assessments_deleted": len(assessments)
    })
    
    db.commit()
```

### 5.3 Data Quality Metrics

Continuously monitor:

```python
# app/monitoring/data_quality.py
class DataQualityMonitor:
    def check(self, df):
        report = {
            "timestamp": datetime.utcnow(),
            "checks": {}
        }
        
        # Missing values
        missing_pct = df.isnull().sum() / len(df)
        report["checks"]["missing_values"] = {
            "status": "PASS" if missing_pct.max() < 0.05 else "FAIL",
            "max_missing_pct": missing_pct.max()
        }
        
        # Outliers
        for col in df.select_dtypes(include=[np.number]).columns:
            Q1, Q3 = df[col].quantile([0.25, 0.75])
            IQR = Q3 - Q1
            outliers = ((df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)).sum()
            report["checks"][f"{col}_outliers"] = {
                "status": "PASS" if outliers / len(df) < 0.05 else "WARN",
                "outlier_pct": outliers / len(df)
            }
        
        # Distribution shift (if model_train stats available)
        report["checks"]["distribution_shift"] = self._check_shift(df)
        
        return report
```

---

## 6. Model Governance

### 6.1 Model Versioning & Registry

Every model version tracked with metadata:

```python
# app/ml/registry.py
class ModelRegistry:
    def register_model(
        self,
        model: xgb.Booster,
        metrics: dict,
        training_data_version: str,
        fairness_report: dict
    ):
        """
        Register trained model with full metadata.
        """
        version = f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Save model
        model.save_model(f"models/{version}/model.pkl")
        
        # Save metadata
        metadata = {
            "version": version,
            "created_at": datetime.utcnow().isoformat(),
            "training_data_version": training_data_version,
            "metrics": metrics,  # AUC, Brier, etc.
            "fairness_report": fairness_report,
            "is_active": False,  # Require manual promotion
            "feature_names": self.feature_names,
            "feature_importance": model.get_score(importance_type='gain')
        }
        
        with open(f"models/{version}/metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        # Log in database
        db.add(ModelVersion(version=version, **metadata))
        db.commit()
        
        return version
    
    def promote_to_production(self, version: str, approved_by: str):
        """
        Manual promotion: Require approval from model steward.
        """
        # Demote all other versions
        db.query(ModelVersion).update({"is_active": False})
        
        # Promote this version
        model_version = db.query(ModelVersion).filter(
            ModelVersion.version == version
        ).first()
        model_version.is_active = True
        model_version.promoted_by = approved_by
        model_version.promoted_at = datetime.utcnow()
        
        log_audit(approved_by, "model_promotion", "ModelVersion", version, "success", {
            "new_active_version": version
        })
        
        db.commit()
```

### 6.2 Model Retraining Schedule

- **Quarterly**: Evaluate model drift; retrain if performance degrades > 5%
- **Annually**: Full model review, fairness audit, sensitivity analysis
- **Ad-hoc**: If significant new data, feature changes, or fairness violations detected

### 6.3 Model Performance Monitoring

```python
# app/monitoring/model_drift.py
def detect_drift():
    """
    Monitor model performance on recent data.
    Alert if metrics degrade significantly.
    """
    recent_assessments = get_recent_assessments(days=30)
    
    current_metrics = evaluate_model(model, recent_assessments)
    baseline_metrics = get_baseline_metrics()  # From training data
    
    drift_report = {}
    for metric in ['auc_roc', 'brier_score', 'calibration_error']:
        current = current_metrics[metric]
        baseline = baseline_metrics[metric]
        drift = abs(current - baseline) / baseline
        
        drift_report[metric] = {
            "current": current,
            "baseline": baseline,
            "drift_pct": drift,
            "status": "PASS" if drift < 0.05 else "WARN" if drift < 0.10 else "FAIL"
        }
    
    # Log and alert
    if any(m["status"] != "PASS" for m in drift_report.values()):
        send_alert(f"Model drift detected: {drift_report}")
        log_monitoring(drift_report)
```

---

## 7. Incident Response

### 7.1 Incident Classification

| Severity | Example | Response Time |
|----------|---------|----------------|
| **Critical** | Model predictions massively biased; security breach | 1 hour |
| **High** | Significant model degradation; repeated auth failures | 4 hours |
| **Medium** | Minor fairness issue; data quality problem | 24 hours |
| **Low** | Typo in documentation; non-security configuration issue | 1 week |

### 7.2 Incident Response Checklist

**Upon Detection**:
1. ✓ Create incident ticket (auto-ticket on alert)
2. ✓ Assess severity & impact
3. ✓ Notify stakeholders (Slack, email)
4. ✓ Preserve evidence (logs, data snapshots)

**Investigation**:
5. ✓ Root cause analysis (what? why? when?)
6. ✓ Scope determination (how many assessments affected?)
7. ✓ Fairness/bias analysis (did this harm any group?)

**Remediation**:
8. ✓ Immediate fix (disable feature, rollback model, patch API)
9. ✓ Notification (inform users of biased assessments if applicable)
10. ✓ Validation (test fix; monitor for regression)

**Post-Incident**:
11. ✓ Root cause documentation
12. ✓ Process improvement (how to prevent recurrence?)
13. ✓ External communication (if required; regulatory reporting)
14. ✓ Post-mortem review (team lesson-learned session)

---

## 8. Compliance & Regulatory

### 8.1 Applicable Regulations

- **GDPR**: Data protection, right to explanation, right to be forgotten
- **Fair Credit Reporting Act (FCRA)**: If used for credit decisions (advisory only)
- **EEO Laws**: No discrimination based on protected attributes
- **Industry-Specific**: Finance (BSA/AML), Healthcare (HIPAA) as applicable

### 8.2 Audit Trail Requirements

Every decision must be reconstructable:

```sql
SELECT *
FROM audit_logs al
LEFT JOIN assessments a ON al.resource_id = a.id
WHERE a.job_title = 'Construction Worker'
AND a.created_at BETWEEN '2024-01-01' AND '2024-01-31'
ORDER BY al.created_at DESC;
```

Returns:
- Who created the assessment (user_id)
- When (timestamp)
- What input was used (serialized request)
- What output was generated (prediction, explanation)
- Who viewed it (audit log of all access)

### 8.3 Data Subject Rights

```python
# Implement GDPR Article 15: Right of Access
async def get_subject_access_request(user_id: str):
    """
    Return all personal data processed for a data subject.
    """
    assessments = db.query(Assessment).filter(
        Assessment.user_id == user_id
    ).all()
    audit_logs = db.query(AuditLog).filter(
        AuditLog.user_id == user_id
    ).all()
    
    export = {
        "assessments": [a.to_dict() for a in assessments],
        "audit_logs": [log.to_dict() for log in audit_logs],
        "export_date": datetime.utcnow().isoformat()
    }
    
    return export_to_json_with_signature(export)
```

---

## 9. Governance Dashboard

Executive-facing governance view:

```
┌─────────────────────────────────────────┐
│  AI Platform Governance Summary          │
├─────────────────────────────────────────┤
│  Model Performance                       │
│  ├─ AUC-ROC: 0.87 (↑ from 0.85)        │
│  ├─ Brier Score: 0.12 (↓ from 0.13)    │
│  └─ Calibration Error: 0.04 ✓           │
│                                         │
│  Fairness Metrics                       │
│  ├─ Demographic Parity (Education):     │
│  │  High School: 0.62 | Bachelor's: 0.58 │
│  │  Difference: 0.04 ✓ (< 0.10)        │
│  └─ Equalized Odds: 0.07 ✓             │
│                                         │
│  Audit Activity (Last 7 Days)           │
│  ├─ Assessments Created: 342            │
│  ├─ Auth Failures: 8 (blocked)          │
│  └─ SHAP/LIME Discrepancies: 2 (logged) │
│                                         │
│  Data Quality                           │
│  ├─ Missing Values: 0.2% ✓              │
│  ├─ Outliers Detected: 12 (reviewed)    │
│  └─ Distribution Shift: None ✓          │
│                                         │
│  Incidents (Last 90 Days)               │
│  ├─ Critical: 0                         │
│  ├─ High: 1 (resolved)                  │
│  └─ Medium: 2 (1 resolved, 1 open)      │
└─────────────────────────────────────────┘
```

---

## 10. Documentation & Transparency

### 10.1 Model Card

Every model version includes a "Model Card":

```markdown
# Model Card: v20250115_143022

**Model Architecture**: XGBoost Regression (200 trees, depth 7)

**Training Data**: 
- Dataset: AI_Impact_on_Jobs_2030.csv
- Rows: 2,950 (after cleaning)
- Features: 20 (job demographics, skills, AI metrics)
- Date: 2025-01-15

**Performance**:
- AUC-ROC: 0.87
- Brier Score: 0.12
- Calibration Error: 0.04

**Fairness Analysis**:
- ✓ No significant demographic parity issues (max diff: 0.08)
- ✓ Equalized odds satisfied (max diff: 0.06)
- Caveat: Education level used as feature; monitor proxy effects

**Intended Use**: Decision support for organizational workforce planning
**Not Intended For**: Automated hiring/firing decisions without human review

**Limitations**:
- Synthetic data; patterns may not reflect real-world automation
- Trained on 2030 projections; real outcomes unknown
- Features capture job characteristics, not individual worker traits

**Ethical Considerations**:
- Always explain assessment to stakeholder
- Treat as input to human decision, not substitute
- Monitor fairness quarterly; retrain if degradation detected
- User has right to explanation and audit trail access
```

---

**Last Updated**: January 2025  
**Next Review**: April 2025  
**Owner**: AI Ethics & Governance Team