# ARCHITECTURE.md

## Enterprise AI Impact & Risk Intelligence Platform - Technical Architecture

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Client Layer                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Streamlit Dashboard (Multi-user, Role-based Access) │   │
│  │ - Risk Assessment Views                             │   │
│  │ - Explainability Explorer (SHAP/LIME)             │   │
│  │ - What-If Scenario Builder                         │   │
│  │ - Audit Trail Viewer                               │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                   API Layer (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Authentication & Authorization (JWT + RBAC)         │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ /api/v1/assess        → Role Risk Assessment        │   │
│  │ /api/v1/explain       → SHAP/LIME Explanations      │   │
│  │ /api/v1/scenario      → What-If Analysis            │   │
│  │ /api/v1/audit         → Prediction Logs             │   │
│  │ /api/v1/governance    → Bias/Sensitivity Reports    │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│          ML & Business Logic Layer                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ XGBoost Model (Automation Risk Prediction)          │   │
│  │ Input: 20+ job features → Output: Risk probability  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Explainability Layer                                │   │
│  │ ├─ SHAP (Audit-grade, primary)                     │   │
│  │ └─ LIME (Supplementary, human-friendly)            │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Governance & Analysis                               │   │
│  │ ├─ Bias Detection (Demographic Parity, Eq. Odds)   │   │
│  │ ├─ Sensitivity Analysis (Feature perturbations)    │   │
│  │ └─ Data Validation & Preprocessing                 │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│            Data & Storage Layer                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ PostgreSQL (Primary Store)                          │   │
│  │ ├─ Workforce & Role Data (normalized schema)       │   │
│  │ ├─ Predictions & Risk Assessments                  │   │
│  │ ├─ SHAP/LIME Explanations                          │   │
│  │ ├─ Audit Logs (immutable append-only)              │   │
│  │ └─ User Accounts & RBAC Policies                   │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Redis (Caching & Session Store)                     │   │
│  │ ├─ Model predictions cache (TTL: 24h)              │   │
│  │ ├─ User sessions                                    │   │
│  │ └─ Rate limiting counters                           │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow

**Request → Assessment → Explanation → Audit → Response**

```
User Request
    ↓
[FastAPI Router] → Validate & Authenticate
    ↓
[RBAC Check] → Verify user has 'assess' permission
    ↓
[Cache Check] → Look up similar past assessments in Redis
    ↓
[Preprocessing] → Normalize features, handle missing values
    ↓
[XGBoost Model] → Generate automation risk probability
    ↓
[SHAP Explainer] → Generate global & local explanations
    ↓
[LIME Explainer] → Generate supplementary explanation
    ↓
[Discrepancy Check] → Flag if SHAP/LIME differ significantly
    ↓
[Confidence Calculation] → Model confidence + calibration
    ↓
[Response Formatting] → Serialize with risk narrative
    ↓
[Audit Log] → Log prediction, user, timestamp, outcome
    ↓
[Cache Store] → Store prediction in Redis (TTL)
    ↓
[Database Store] → Persist to PostgreSQL (assessments table)
    ↓
HTTP Response → Client
```

---

## 2. Component Details

### 2.1 Data Ingestion & Preprocessing

**Input Format**: CSV with 20 columns
- Job demographics: `Job_Title`, `Average_Salary`, `Years_Experience`, `Education_Level`
- AI metrics: `AI_Exposure_Index`, `Tech_Growth_Factor`
- Skills: `Skill_1` through `Skill_10` (numeric proficiency 0-1)
- Target: `Automation_Probability_2030` (ground truth for training)

**Preprocessing Steps**:

1. **Validation**
   - Check required columns present
   - Verify data types (int, float, categorical)
   - Range validation (e.g., AI_Exposure_Index ∈ [0, 1])
   - Detect missing values; report or impute

2. **Cleaning**
   - Remove duplicates (by job_title + salary + experience)
   - Handle outliers (e.g., negative salary → flag or remove)
   - Standardize categorical values (e.g., "Master's" vs "Master")
   - Deduplicate similar job titles

3. **Feature Engineering**
   - **Experience Risk Factor**: `exp_risk = 1 / (1 + years_experience)` — newer roles riskier
   - **Salary Resilience**: `log(salary)` — captures diminishing value of experience
   - **Skill Diversity**: `std(skills)` — specialized skills = lower risk
   - **Tech Pressure**: `ai_exposure × tech_growth` — combined pressure
   - **Education Resilience**: Ordinal encode High School (0) → PhD (3)

4. **Scaling**
   - StandardScaler for numeric features (mean=0, std=1)
   - OneHotEncoder for education level
   - Preserve feature names for SHAP interpretability

```python
# app/ml/preprocessing.py
class DataPreprocessor:
    def fit(self, X_raw):
        self.scaler = StandardScaler()
        self.encoder = OneHotEncoder()
        return self
    
    def transform(self, X_raw):
        X = X_raw.copy()
        # Engineer features
        X['exp_risk'] = 1 / (1 + X['years_experience'])
        X['skill_diversity'] = X[['skill_1', ..., 'skill_10']].std(axis=1)
        # Scale
        X[numeric_cols] = self.scaler.transform(X[numeric_cols])
        return X
```

### 2.2 Model Architecture

**Algorithm**: XGBoost (Gradient Boosting Decision Trees)

**Why XGBoost?**
- Handles mixed feature types (numeric + categorical)
- Interpretable feature importance (gain, cover, frequency)
- Robust to outliers and missing data
- Fast inference (milliseconds per prediction)
- Works well with SHAP for explanations

**Model Configuration**:

```python
# app/ml/model.py
xgb_params = {
    'objective': 'reg:squarederror',  # Regression for probability
    'max_depth': 7,
    'learning_rate': 0.05,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'reg_lambda': 1.0,  # L2 regularization
    'reg_alpha': 0.5,   # L1 regularization
    'min_child_weight': 5,
    'random_state': 42
}

# Training
dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=feature_names)
dtest = xgb.DMatrix(X_test, label=y_test, feature_names=feature_names)

model = xgb.train(
    xgb_params,
    dtrain,
    num_boost_round=200,
    evals=[(dtest, 'test')],
    early_stopping_rounds=20,
    verbose_eval=10
)
```

**Hyperparameter Tuning**:
- Grid search over `max_depth`, `learning_rate`, `subsample`
- Cross-validation (5-fold) on training set
- Optimize for AUC-ROC (discrimination ability) + Brier score (calibration)

**Performance Metrics**:
- **AUC-ROC**: 0.85+ target (discrimination between high/low risk roles)
- **Brier Score**: < 0.15 (predicted probability ≈ actual outcome)
- **Calibration**: Expected Calibration Error (ECE) < 0.05
- **Fairness**: Demographic parity difference < 0.1 across protected groups

### 2.3 Explainability Architecture

#### SHAP: Audit-Grade Explanations

**TreeExplainer** (fast, exact Shapley for tree models):

```python
# app/ml/explainability.py
import shap

class ShapExplainer:
    def __init__(self, model, X_train):
        self.explainer = shap.TreeExplainer(model)
        self.X_train = X_train
    
    def explain_global(self):
        """Global feature importance across all roles"""
        shap_values = self.explainer.shap_values(self.X_train)
        # Mean absolute Shapley value
        importance = np.abs(shap_values).mean(axis=0)
        return dict(zip(feature_names, importance))
    
    def explain_local(self, X_instance):
        """Local explanation for one role"""
        shap_value = self.explainer.shap_values(X_instance)[0]
        base_value = self.explainer.expected_value
        
        return {
            'base_value': base_value,  # Average prediction
            'shap_values': shap_value,  # Feature contributions
            'features': X_instance[0],
            'prediction': base_value + shap_value.sum()
        }
```

**Interpretation**:
- `SHAP value > 0`: Feature pushed prediction toward higher risk
- `SHAP value < 0`: Feature pushed prediction toward lower risk
- Magnitude: Strength of influence
- Confidence intervals: Robust to model perturbations

#### LIME: Supplementary Human-Friendly Explanations

```python
import lime.lime_tabular

class LimeExplainer:
    def __init__(self, model, feature_names):
        self.explainer = lime.lime_tabular.LimeTabularExplainer(
            X_train, feature_names=feature_names, mode='regression'
        )
    
    def explain_instance(self, X_instance):
        """Local linear approximation"""
        explanation = self.explainer.explain_instance(
            X_instance[0], self.model.predict, num_features=10
        )
        return {
            'top_features': explanation.as_list(),
            'intercept': explanation.intercept[0],
            'score': explanation.score
        }
```

**Interpretation**:
- Simpler linear model fitted locally
- "If this role's salary increased by $10k, risk would decrease by 5%"
- Easier for non-technical stakeholders

#### Precedence & Reconciliation

**Rule 1**: SHAP is authoritative for governance and audit.

**Rule 2**: If SHAP and LIME conflict:
```python
def handle_discrepancy(shap_explanation, lime_explanation):
    """
    Discrepancy = Significant difference in top features.
    Action: Log, investigate, update model if needed.
    """
    shap_top = sorted(shap_explanation.items(), 
                     key=lambda x: abs(x[1]), reverse=True)[:5]
    lime_top = [f[0] for f in lime_explanation['top_features']]
    
    overlap = len(set([f[0] for f in shap_top]) & set(lime_top))
    if overlap < 3:  # Less than 60% agreement
        log_discrepancy(shap_top, lime_top)
```

### 2.4 FastAPI Backend

**Framework**: FastAPI + Uvicorn
**Auth**: JWT (JSON Web Tokens) + RBAC
**Database**: SQLAlchemy ORM → PostgreSQL

**Route Structure**:

```python
# app/api/main.py
from fastapi import FastAPI, Depends
from app.api.middleware import AuthMiddleware, AuditMiddleware
from app.api.routes import assess, explain, scenario, audit, governance

app = FastAPI(
    title="AI Job Impact Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware
app.add_middleware(AuthMiddleware)
app.add_middleware(AuditMiddleware)

# Routes
app.include_router(assess.router, prefix="/api/v1")
app.include_router(explain.router, prefix="/api/v1")
app.include_router(scenario.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(governance.router, prefix="/api/v1")
```

**Key Endpoints**:

```python
# app/api/routes/assess.py
@router.post("/assess")
async def assess_role(
    assessment_request: AssessmentRequest,
    current_user: User = Depends(get_current_user)
):
    # 1. Authorization
    require_permission(current_user, 'assess')
    
    # 2. Validation
    assessment_request.validate()
    
    # 3. Preprocessing
    X = preprocessor.transform(assessment_request)
    
    # 4. Prediction
    prob = model.predict(X)[0]
    risk_category = categorize_risk(prob)
    confidence = get_confidence(X, prob)
    
    # 5. Database
    assessment = Assessment(
        user_id=current_user.id,
        job_title=assessment_request.job_title,
        automation_probability=prob,
        risk_category=risk_category,
        confidence=confidence
    )
    db.add(assessment)
    db.commit()
    
    # 6. Response
    return AssessmentResponse(
        automation_probability_2030=prob,
        risk_category=risk_category,
        confidence=confidence,
        assessment_id=str(assessment.id)
    )
```

### 2.5 Database Schema

**PostgreSQL Tables**:

```sql
-- Users & Access Control
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    role VARCHAR NOT NULL,  -- 'Admin', 'Analyst', 'Viewer'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE roles_permissions (
    role VARCHAR NOT NULL,
    permission VARCHAR NOT NULL,  -- 'assess', 'explain', 'scenario', 'admin'
    PRIMARY KEY (role, permission)
);

-- Data
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    job_title VARCHAR NOT NULL,
    average_salary DECIMAL,
    years_experience INT,
    education_level VARCHAR,
    ai_exposure_index FLOAT,
    tech_growth_factor FLOAT,
    skills JSONB,  -- Array of 10 skill proficiencies
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_title, average_salary, years_experience)
);

-- Assessments
CREATE TABLE assessments (
    id UUID PRIMARY KEY,
    role_id UUID REFERENCES roles(id),
    user_id UUID REFERENCES users(id),
    automation_probability FLOAT NOT NULL,
    risk_category VARCHAR NOT NULL,  -- 'Low', 'Medium', 'High'
    confidence FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at),
    INDEX idx_risk_category (risk_category)
);

-- Explanations
CREATE TABLE explanations (
    id UUID PRIMARY KEY,
    assessment_id UUID REFERENCES assessments(id),
    shap_global JSONB,  -- Global feature importance
    shap_local JSONB,   -- Local contributions
    lime_explanation JSONB,
    discrepancy_noted BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit Logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR NOT NULL,  -- 'assessment', 'explain', 'export', etc.
    resource_type VARCHAR,
    resource_id UUID,
    status VARCHAR,  -- 'success', 'failure'
    details JSONB,
    ip_address VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_action (user_id, action),
    INDEX idx_created_at (created_at)
);

-- Model Metadata
CREATE TABLE model_versions (
    id UUID PRIMARY KEY,
    version VARCHAR UNIQUE NOT NULL,
    training_date TIMESTAMP,
    auc_roc FLOAT,
    brier_score FLOAT,
    fairness_score FLOAT,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.6 Caching Strategy

**Redis** for high-performance caching:

```python
# app/cache.py
import redis
import json

cache = redis.Redis(host='localhost', port=6379, db=0)

def cache_prediction(features_hash, assessment):
    """Cache assessment for 24 hours"""
    key = f"assessment:{features_hash}"
    cache.setex(key, 86400, json.dumps(assessment))

def get_cached_assessment(features_hash):
    """Retrieve cached assessment if exists"""
    key = f"assessment:{features_hash}"
    cached = cache.get(key)
    return json.loads(cached) if cached else None
```

**Cache Keys**:
- `assessment:{features_hash}` → Full assessment (24h TTL)
- `shap_global` → Global feature importance (7d TTL)
- `user_session:{user_id}` → Session data (12h TTL)
- `rate_limit:{user_id}` → API call counter (1h TTL)

---

## 3. Governance & Security Architecture

### 3.1 Role-Based Access Control (RBAC)

**Permission Matrix**:

| Action | Admin | Analyst | Viewer |
|--------|-------|---------|--------|
| Create Assessment | ✓ | ✓ | ✗ |
| View Explanation | ✓ | ✓ | ✓ |
| What-If Analysis | ✓ | ✓ | ✗ |
| Export Report | ✓ | ✓ | ✓ |
| View Audit Log | ✓ | ✓ (own only) | ✗ |
| Manage Users | ✓ | ✗ | ✗ |
| Configure Model | ✓ | ✗ | ✗ |

```python
# app/auth/permissions.py
def require_permission(user: User, permission: str):
    role_permissions = ROLES_PERMISSIONS.get(user.role, [])
    if permission not in role_permissions:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
```

### 3.2 Audit Logging

**Every action logged immutably**:

```python
async def log_audit(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    status: str,
    details: dict,
    request: Request
):
    """Append-only audit log"""
    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status,
        details=details,
        ip_address=request.client.host,
        created_at=datetime.utcnow()
    )
    db.add(audit_entry)
    db.commit()
```

### 3.3 Bias & Fairness Analysis

**Automated Fairness Metrics**:

```python
# app/ml/bias_analysis.py
from fairlearn.metrics import demographic_parity_difference

def analyze_bias(model, X, y, protected_attribute):
    """
    Compute fairness metrics across protected groups.
    protected_attribute: e.g., 'education_level', 'salary_band'
    """
    predictions = model.predict(X)
    
    groups = X[protected_attribute].unique()
    bias_report = {}
    
    for group in groups:
        mask = X[protected_attribute] == group
        group_pred = predictions[mask]
        group_true = y[mask]
        
        # Demographic parity: |P(ŷ=1|G=g) - P(ŷ=1)|
        parity_diff = np.abs(
            group_pred.mean() - predictions.mean()
        )
        
        # Equalized odds: |FPR_g - FPR| + |TPR_g - TPR|
        fp_rate_diff = ...
        tp_rate_diff = ...
        
        bias_report[group] = {
            'demographic_parity': parity_diff,
            'equalized_odds': fp_rate_diff + tp_rate_diff,
            'n_samples': mask.sum()
        }
    
    return bias_report
```

**Thresholds**:
- Demographic Parity Difference < 0.10 (10%) → Pass
- Equalized Odds Difference < 0.15 (15%) → Pass

### 3.4 Sensitivity Analysis

**Robustness Testing**:

```python
# app/ml/sensitivity_analysis.py
def sensitivity_analysis(model, X_test, feature_idx, perturbation_range):
    """
    How robust is model to feature perturbations?
    E.g., if salary varies ±20%, how much does risk category change?
    """
    sensitivity_report = {}
    
    for feature in important_features:
        original_pred = model.predict(X_test)
        original_risk = categorize_risk(original_pred)
        
        # Perturb feature
        X_perturbed = X_test.copy()
        X_perturbed[feature] *= (1 + perturbation_range)
        
        perturbed_pred = model.predict(X_perturbed)
        perturbed_risk = categorize_risk(perturbed_pred)
        
        # How often does risk category change?
        category_changes = (original_risk != perturbed_risk).mean()
        
        sensitivity_report[feature] = {
            'category_change_rate': category_changes,
            'avg_prob_delta': np.abs(perturbed_pred - original_pred).mean()
        }
    
    return sensitivity_report
```

---

## 4. Deployment Architecture

### 4.1 Containerization (Docker)

**Dockerfile**:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y postgresql-client

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with gunicorn for production
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "app.api.main:app"]
```

**docker-compose.yml**:

```yaml
version: '3.9'

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: ai_platform
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: ai_job_impact
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ai_platform"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://ai_platform:secure_password@postgres:5432/ai_job_impact
      REDIS_URL: redis://redis:6379/0
      ENVIRONMENT: production
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --workers 4

  dashboard:
    build: .
    ports:
      - "8501:8501"
    environment:
      DATABASE_URL: postgresql://ai_platform:secure_password@postgres:5432/ai_job_impact
      API_URL: http://api:8000
    depends_on:
      - api
    command: streamlit run app/dashboard/main.py --server.port 8501 --server.address 0.0.0.0

volumes:
  postgres_data:
```

### 4.2 Scaling Considerations

**Horizontal Scaling**:
- API runs 4 workers per container; scale horizontally behind load balancer
- PostgreSQL: Read replicas for reporting queries
- Redis: Cluster mode for distributed caching

**Performance Targets**:
- API latency: < 200ms for /assess endpoint
- Model prediction: < 10ms (cached: < 1ms)
- Dashboard load: < 2s

---

## 5. Error Handling & Resilience

### 5.1 Circuit Breaker Pattern

```python
# app/api/middleware/circuit_breaker.py
from pybreaker import CircuitBreaker

db_breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

@db_breaker
async def get_assessment(assessment_id: str):
    return db.query(Assessment).filter_by(id=assessment_id).first()
```

### 5.2 Graceful Degradation

If model inference fails:
- Return cached prediction if available
- Use baseline risk (population mean) + confidence interval
- Log failure for investigation
- Alert ops team if >5% failure rate

---

## 6. Monitoring & Observability

### 6.1 Metrics to Track

- **Model Performance**: AUC, Brier score, calibration drift
- **API Performance**: Request latency, error rates, throughput
- **Data Quality**: Missing values, outliers, data drift
- **System Health**: DB connections, cache hit rates, memory usage

### 6.2 Logging

```python
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger(__name__)
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

logger.info("assessment_created", extra={
    "assessment_id": assessment_id,
    "user_id": user_id,
    "risk_category": risk_category,
    "duration_ms": duration
})
```

---

## 7. Testing Strategy

### Unit Tests
- Model preprocessing
- Feature engineering
- SHAP/LIME explanations
- RBAC enforcement

### Integration Tests
- API endpoint behavior
- Database transactions
- Cache invalidation

### System Tests
- End-to-end assessment → explanation → audit
- What-if scenario generation
- Report export

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for testing guidelines.

---

**Last Updated**: January 2025
**Version**: 1.0.0