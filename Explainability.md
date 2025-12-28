# EXPLAINABILITY.md

## Dual Explainability Architecture: SHAP & LIME

This document details the explainability framework that powers audit-grade and human-friendly explanations.

### SHAP: SHapley Additive exPlanations

**Why SHAP?**
- **Theoretically sound**: Based on Shapley values from cooperative game theory
- **Consistent**: Feature importance sums to prediction
- **Audit-grade**: Suitable for regulatory compliance and governance

**Global Explanations** (Features driving automation risk across ALL roles)
```python
shap_global = {
    'AI_Exposure_Index': 0.35,      # Largest impact
    'Tech_Growth_Factor': 0.25,
    'Years_Experience': 0.20,
    'Average_Salary': 0.12,
    'Education_Level': 0.08
}
```
**Interpretation**: AI exposure has 35% of total feature importance.

**Local Explanations** (Why a specific role got its score)
```python
{
    'base_value': 0.50,  # Average automation risk
    'shap_values': {
        'AI_Exposure_Index': +0.15,    # Pushed risk UP
        'Tech_Growth_Factor': +0.08,
        'Years_Experience': -0.05,     # Pushed risk DOWN
        'Average_Salary': +0.02
    },
    'prediction': 0.70   # 0.50 + (0.15 + 0.08 - 0.05 + 0.02)
}
```

### LIME: Local Interpretable Model-agnostic Explanations

**Why LIME?**
- **Human-friendly**: Simple linear approximation humans understand
- **Model-agnostic**: Works with any model (neural nets, trees, etc.)
- **Supplementary**: Easier to communicate to non-technical stakeholders

**Local Approximation** (Linear model fit around specific prediction)
```python
lime_explanation = {
    'intercept': 0.50,
    'top_features': [
        ('High AI Exposure', 0.18),
        ('Tech Growing (1.2x)', 0.12),
        ('Low Experience (5 yrs)', 0.10),
        ('Moderate Salary ($100k)', -0.05),
        ("Bachelor's Education", -0.08)
    ]
}
```
**Interpretation**: "This role has high automation risk because it has high AI exposure and fast-growing technology field."

---

### Precedence Rules: SHAP is Authoritative

**Rule 1**: For any prediction, SHAP explanation is the official, audit-grade explanation.

**Rule 2**: LIME is supplementary and easier to understand, but may differ from SHAP.

**Rule 3**: If SHAP and LIME conflict:
1. Log discrepancy with full context
2. Investigate root cause
3. Prefer SHAP for governance decisions
4. Update documentation/model if pattern persists

**Example Reconciliation**:
```
SHAP says: "Years_Experience most important (0.20)"
LIME says: "Low Experience is top feature"

Resolution: Both agree experience is important.
They differ on direction interpretation, but agree on impact.
Status: RECONCILED
```

---

# API.md

## API Reference

### Authentication

All endpoints require JWT token in `Authorization: Bearer <token>` header.

```bash
# Get token
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=<password>"

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### POST /api/v1/assess

**Assess a role for automation risk**

**Request**:
```json
{
  "job_title": "Software Engineer",
  "average_salary": 120000,
  "years_experience": 8,
  "education_level": "Bachelor's",
  "ai_exposure_index": 0.65,
  "tech_growth_factor": 0.85,
  "skills": [0.8, 0.75, 0.6, 0.5, 0.7, 0.85, 0.6, 0.75, 0.8, 0.65]
}
```

**Response** (200):
```json
{
  "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_title": "Software Engineer",
  "automation_probability_2030": 0.60,
  "risk_category": "Medium",
  "confidence": 0.92,
  "confidence_interval": [0.50, 0.70],
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Errors**:
- 400: Invalid input (salary out of range, invalid education level)
- 401: Unauthorized (invalid token)
- 403: Forbidden (user role lacks 'assess' permission)
- 500: Server error

---

### POST /api/v1/explain

**Get SHAP and LIME explanations**

**Request**:
```json
{
  "assessment_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response** (200):
```json
{
  "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
  "shap_explanation": {
    "base_value": 0.50,
    "shap_values": [0.15, 0.08, -0.05, 0.02, ...],
    "feature_names": ["AI_Exposure_Index", "Tech_Growth_Factor", ...],
    "contributions": [
      {
        "feature": "AI_Exposure_Index",
        "value": 0.65,
        "shap_value": 0.15,
        "direction": "increases_risk"
      }
    ]
  },
  "lime_explanation": {
    "top_features": [
      {
        "feature": "High AI Exposure",
        "weight": 0.18,
        "direction": "increases_risk"
      }
    ],
    "intercept": 0.50,
    "local_model_score": 0.94
  },
  "discrepancy_detected": false,
  "discrepancy_details": null,
  "precedence_note": "SHAP is authoritative for governance; LIME is supplementary"
}
```

---

### POST /api/v1/scenario

**What-if analysis: explore how changes reduce risk**

**Request**:
```json
{
  "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
  "changes": {
    "skills": [0.9, 0.85, 0.7, 0.6, 0.8, 0.95, 0.7, 0.85, 0.9, 0.75],
    "education_level": "Master's",
    "years_experience": 13
  }
}
```

**Response** (200):
```json
{
  "original_assessment": {
    "automation_probability_2030": 0.60,
    "risk_category": "Medium"
  },
  "scenario_assessment": {
    "automation_probability_2030": 0.45,
    "risk_category": "Low"
  },
  "delta_automation_probability": -0.15,
  "narrative": "Upgrading to a Master's degree and improving key technical skills would reduce automation risk from 60% (Medium) to 45% (Low). This represents a 15 percentage point reduction, moving the role from medium to low risk category."
}
```

---

### GET /api/v1/audit

**View audit logs (Admin & Analyst only)**

**Query Parameters**:
- `action`: "assessment", "explain", "scenario", "access"
- `start_date`: ISO 8601 date
- `end_date`: ISO 8601 date
- `user_id`: Filter by user
- `resource_id`: Filter by assessment
- `limit`: Max rows (default 100, max 1000)

**Response** (200):
```json
{
  "total": 245,
  "limit": 100,
  "offset": 0,
  "logs": [
    {
      "id": "uuid",
      "timestamp": "2025-01-15T10:30:00Z",
      "user": "analyst_1",
      "action": "assessment",
      "resource_type": "Assessment",
      "resource_id": "uuid",
      "status": "success",
      "details": {
        "method": "POST",
        "path": "/api/v1/assess",
        "status_code": 200,
        "duration_ms": 145,
        "job_title": "Software Engineer"
      },
      "ip_address": "192.168.1.100"
    }
  ]
}
```

---

### POST /api/v1/governance/bias-report

**Get bias analysis report**

**Response** (200):
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "metrics": {
    "demographic_parity": {
      "High School": {
        "avg_risk": 0.68,
        "n_samples": 450,
        "parity_diff": 0.08
      },
      "Bachelor's": {
        "avg_risk": 0.52,
        "n_samples": 380,
        "parity_diff": 0.08
      }
    },
    "equalized_odds": {
      "overall_diff": 0.06,
      "status": "PASS"
    }
  },
  "overall_fairness_score": 0.88,
  "recommendations": [
    "Monitor education level as potential proxy for protected attributes"
  ]
}
```

---

# DATA_DICTIONARY.md

## Data Dictionary: Feature Definitions

### Input Features (10 features required)

| Feature | Type | Range | Description | Example |
|---------|------|-------|-------------|---------|
| **Job_Title** | String | N/A | Job role name | "Software Engineer", "Truck Driver" |
| **Average_Salary** | Float | $20k - $500k | Annual salary in USD | 120000 |
| **Years_Experience** | Integer | 0-70 | Avg years in field | 8 |
| **Education_Level** | Category | {HS, BA, MA, PhD} | Highest education | "Bachelor's" |
| **AI_Exposure_Index** | Float | 0-1 | How much role uses AI tools. 0=none, 1=critical | 0.65 |
| **Tech_Growth_Factor** | Float | 0.5-1.5 | How fast tech advances in field. 0.5=slow, 1.5=rapid | 0.85 |
| **Skill_1-10** | Float | 0-1 | Job-specific skill proficiencies | 0.75 |

### Skill Dimensions (10 skills)

1. **Creativity** - Generating novel ideas and solutions
2. **Data Analysis** - Interpreting data and statistics
3. **Robotics/Automation** - Using/understanding automation tech
4. **Communication** - Explaining complex ideas clearly
5. **Problem Solving** - Troubleshooting and root cause analysis
6. **Technical Proficiency** - Using technology tools
7. **Adaptability** - Learning new skills quickly
8. **Leadership** - Managing and mentoring others
9. **Domain Expertise** - Deep knowledge in field
10. **Emotional Intelligence** - Reading and managing emotions (esp. customer-facing)

**Why these 10?** Chosen to span technical, interpersonal, and resilience skills. Jobs with high creativity, emotional intelligence, and leadership are more resilient to automation.

### Output Features (Generated)

| Feature | Description | Range |
|---------|-------------|-------|
| **Automation_Probability_2030** | Predicted probability role will be automated | 0-1 |
| **Risk_Category** | Bucketed risk | "Low" (<0.33), "Medium" (0.33-0.67), "High" (>0.67) |
| **Confidence** | Model confidence in prediction | 0-1 |
| **Confidence_Interval** | 90% CI on probability | [lower, upper] |

### Engineered Features (Created by preprocessing)

| Feature | Calculation | Rationale |
|---------|-----------|-----------|
| **experience_risk** | 1 / (1 + years_experience) | Newer entrants = higher risk |
| **log_salary** | log(salary + 1) | Captures diminishing returns of high pay |
| **skill_diversity** | std(skills_1:10) | Specialized roles more resilient |
| **max_skill** | max(skills_1:10) | Peak competency |
| **tech_pressure** | ai_exposure × tech_growth | Combined pressure from automation |

---

# CONTRIBUTING.md

## Contribution Guidelines

### Getting Started

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make changes and commit**: `git commit -m "Clear description"`
4. **Push and create Pull Request**: `git push origin feature/your-feature`

### Development Setup

```bash
# Clone and setup
git clone <your-fork>
cd ai-job-impact-platform
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v --cov=app

# Format code
black app/ scripts/ tests/
flake8 app/ scripts/ --max-line-length=100

# Type checking
mypy app/
```

### Coding Standards

**Python Style**: Follow PEP 8. Use Black for formatting.

```python
# ✓ Good
def assess_role(job_title: str, salary: float) -> Dict[str, float]:
    """Assess a role for automation risk.
    
    Args:
        job_title: Name of job role
        salary: Annual salary in USD
    
    Returns:
        Risk assessment with probability and confidence
    """
    pass

# ✗ Avoid
def assess(j, s):  # No type hints, unclear args
    pass
```

**Docstrings**: Use Google-style docstrings.

```python
def explain_assessment(assessment_id: UUID) -> ExplainResponse:
    """Get SHAP and LIME explanations.
    
    Args:
        assessment_id: ID of assessment to explain
    
    Returns:
        ExplainResponse with SHAP and LIME explanations
    
    Raises:
        HTTPException: If assessment not found
    """
```

### Testing

Write tests for all new features:

```python
# tests/test_model.py
def test_preprocessing_scaling():
    """Test that preprocessing scales features correctly."""
    preprocessor = DataPreprocessor()
    X = np.random.randn(100, 10)
    X_scaled = preprocessor.transform(X)
    
    assert X_scaled.mean() < 0.1  # Close to 0
    assert X_scaled.std() < 1.1   # Close to 1

def test_assess_endpoint():
    """Test /assess endpoint returns valid response."""
    client = TestClient(app)
    response = client.post("/api/v1/assess", json={...})
    
    assert response.status_code == 200
    data = response.json()
    assert 0 <= data['automation_probability_2030'] <= 1
    assert data['risk_category'] in ['Low', 'Medium', 'High']
```

**Coverage Target**: Maintain > 80% code coverage.

```bash
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html to see coverage
```

### Commit Messages

Use clear, descriptive commit messages:

```
# ✓ Good
git commit -m "Add SHAP explainability for individual roles

- Implement TreeExplainer for XGBoost model
- Add local explanation endpoint /api/v1/explain
- Include discrepancy detection with LIME
- Tests: test_shap_local_explanation (passing)"

# ✗ Avoid
git commit -m "fix stuff"
git commit -m "WIP"
```

### Pull Request Process

1. **Update documentation** for any new features
2. **Add tests** covering new functionality
3. **Run linting**: `make lint` (or `black app/` + `flake8 app/`)
4. **Run tests**: `make test`
5. **Create PR with clear description**:
   ```
   ## Description
   Brief explanation of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Testing
   How to test: ...
   Test coverage: XX%
   
   ## Checklist
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] Code formatted (black, flake8)
   - [ ] No breaking changes
   ```

### Areas for Contribution

**High Priority**:
- [ ] Bias detection improvements (fairlearn integration)
- [ ] Model explainability enhancements
- [ ] Dashboard features (reports, exports)
- [ ] Performance optimizations

**Medium Priority**:
- [ ] Additional test coverage
- [ ] Documentation improvements
- [ ] API endpoint enhancements
- [ ] Data quality monitoring

**Low Priority**:
- [ ] UI/UX improvements
- [ ] Additional visualization options
- [ ] Code cleanup and refactoring

### Reporting Issues

Use GitHub Issues with clear templates:

```
## Issue Type
- [ ] Bug Report
- [ ] Feature Request
- [ ] Documentation Issue

## Description
Clear description of issue

## Steps to Reproduce
1. ...
2. ...

## Expected vs Actual
Expected: ...
Actual: ...

## Environment
- OS: [Windows/Mac/Linux]
- Python: 3.10
- Branch: main
```

### Code Review Process

All PRs require at least 1 approval before merging:

1. **Automated checks**: Tests pass, lint passes
2. **Code review**: At least one team member approves
3. **Security review**: For auth/data access changes
4. **Documentation review**: For user-facing features

### Questions?

- Open a GitHub Discussion for design questions
- Ask on Slack: #ai-job-impact-platform
- Email: ai-platform@example.com

---

**Last Updated**: January 2025  
**Maintained By**: AI Platform Team