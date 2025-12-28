# Enterprise AI Impact & Risk Intelligence Platform

**A Production-Grade Decision Support System for Understanding AI's Impact on Workforce Roles**

---

## Executive Summary

This platform enables organizations to systematically assess, govern, and communicate the impact of AI-driven automation on their workforce. Rather than making automated employment decisions, it provides explainable, audit-grade risk intelligence that empowers human decision-makers with clear understanding of how roles may be affected by AI change.

**Key Differentiators:**
- **Dual Explainability Architecture**: SHAP (audit-grade) + LIME (human-friendly) with documented precedence rules
- **Enterprise Security by Design**: RBAC, authenticated APIs, comprehensive audit logging
- **Responsible AI Governance**: Bias detection, sensitivity analysis, threat modeling, human-in-the-loop controls
- **Executive-Focused Interface**: Plain-language risk narratives, confidence indicators, counterfactual "what-if" scenarios
- **Production-Ready Stack**: Python, FastAPI, scikit-learn/XGBoost, PostgreSQL, Streamlit, Docker

---

## Table of Contents

- [Quick Start](#quick-start)
- [System Architecture](#system-architecture)
- [Core Features](#core-features)
- [Installation & Setup](#installation--setup)
- [Usage Guide](#usage-guide)
- [API Reference](#api-reference)
- [Explainability Framework](#explainability-framework)
- [Governance & Security](#governance--security)
- [Documentation](#documentation)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

---

## Quick Start

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- PostgreSQL 13+
- 4GB RAM minimum

### 5-Minute Setup

```bash
# Clone the repository
git clone <repo-url>
cd ai-job-impact-platform

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database and API credentials

# Initialize database
python scripts/init_db.py

# Ingest sample data
python scripts/ingest_data.py data/AI_Impact_on_Jobs_2030.csv

# Train baseline model
python scripts/train_model.py

# Start API server (Terminal 1)
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

# Start Streamlit dashboard (Terminal 2)
streamlit run app/dashboard/main.py

# Access services
# Dashboard: http://localhost:8501
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access services
# Dashboard: http://localhost:8501
# API: http://localhost:8000
# Database: localhost:5432
```

---

## System Architecture

```
PRESENTATION LAYER
┌─────────────────────────────────────────────────────────┐
│         Executive Dashboard (Streamlit)                 │
│  ├─ Role Risk Assessment                                │
│  ├─ What-If Scenario Explorer                           │
│  ├─ Explainability Viewer (SHAP/LIME)                   │
│  └─ Audit Trail & Governance Insights                   │
└──────────────────┬──────────────────────────────────────┘
                   │
API LAYER
┌──────────────────▼──────────────────────────────────────┐
│    FastAPI Backend (Authenticated, Audited)             │
│  ├─ /api/v1/assess - Role risk assessment              │
│  ├─ /api/v1/explain - SHAP/LIME explanations           │
│  ├─ /api/v1/scenario - What-if analysis                │
│  ├─ /api/v1/audit - Prediction audit logs              │
│  └─ /api/v1/governance - Bias & sensitivity reports    │
└──────────────────┬──────────────────────────────────────┘
                   │
ML & BUSINESS LOGIC LAYER
┌──────────────────▼──────────────────────────────────────┐
│    ML Pipeline & Explainability Layer                   │
│  ├─ Data Validation & Preprocessing                     │
│  ├─ XGBoost Automation Risk Model                       │
│  ├─ SHAP (Global & Local Explanations)                  │
│  ├─ LIME (Supplementary Explanations)                   │
│  └─ Bias & Sensitivity Analysis                         │
└──────────────────┬──────────────────────────────────────┘
                   │
DATA PERSISTENCE LAYER
┌──────────────────▼──────────────────────────────────────┐
│    PostgreSQL Database + Redis Cache                    │
│  ├─ Workforce & Role Data                              │
│  ├─ Predictions & Risk Assessments                      │
│  ├─ SHAP/LIME Explanations                             │
│  ├─ Audit Logs & Access Control                        │
│  └─ User Preferences & Governance Rules                │
└──────────────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed system design.

---

## Core Features

### 1. Automated Risk Assessment
- Predicts automation probability for each role (0-1 scale)
- Classifies risk as Low, Medium, or High
- Incorporates 20+ features: salary, experience, education, AI exposure, tech growth, skills
- Model: XGBoost with cross-validation (70/30 train/test split)

### 2. Explainability Framework
- **SHAP (SHapley Additive exPlanations)**
  - Audit-grade, theoretically sound
  - Global feature importance across all roles
  - Local explanations for individual role assessments
  - Confidence intervals and contribution ranges
  
- **LIME (Local Interpretable Model-agnostic Explanations)**
  - Human-friendly, local approximations
  - Easier for non-technical stakeholders to understand
  - Supplementary to SHAP

- **Precedence Rules**: SHAP is authoritative; LIME supports understanding. Discrepancies logged and investigated.

### 3. What-If Scenario Analysis
- Explore how changes in skills reduce automation risk
- Simulate impact of education level improvements
- Model salary vs. risk trade-offs
- Generate counterfactual narratives

### 4. Governance & Audit
- **RBAC**: Admin, Analyst, Viewer roles with granular permissions
- **Audit Logs**: All predictions, explanations, and access logged with timestamps
- **Bias Detection**: Demographic parity, equalized odds analysis
- **Sensitivity Analysis**: How robust is the model to input perturbations?
- **Threat Model**: Documented attack surfaces and mitigation strategies
- **Data Lineage**: Full traceability from raw data to predictions

### 5. Executive Dashboard
- Risk distribution by job title, education level, salary band
- Skills-to-risk heatmaps
- Trend analysis: which roles becoming higher risk over time?
- Downloadable reports with confidence indicators
- Interactive "what-if" exploration

---

## Installation & Setup

### Full Installation Guide

See [INSTALLATION.md](docs/INSTALLATION.md) for:
- Detailed environment setup
- Database initialization
- Model training with custom parameters
- GPU acceleration setup
- Troubleshooting

### Dependencies

**Core Stack:**
- `fastapi` - REST API framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `scikit-learn` - ML preprocessing, metrics
- `xgboost` - Gradient boosting model
- `shap` - Explainability
- `lime` - Supplementary explainability
- `pandas`, `numpy` - Data manipulation
- `sqlalchemy` - ORM
- `psycopg2-binary` - PostgreSQL driver
- `streamlit` - Dashboard framework
- `plotly` - Interactive visualizations
- `python-jose` - JWT authentication
- `passlib` - Password hashing
- `python-dotenv` - Environment configuration

**Development:**
- `pytest`, `pytest-cov` - Testing
- `black`, `flake8` - Code quality
- `mypy` - Type checking

See [requirements.txt](requirements.txt) for pinned versions.

---

## Usage Guide

### 1. Ingest Workforce Data

```bash
python scripts/ingest_data.py path/to/your/data.csv --validate --deduplicate
```

Expected CSV format: See [DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md)

### 2. Train/Retrain Model

```bash
# Train with default parameters
python scripts/train_model.py

# Train with custom parameters
python scripts/train_model.py --test-size 0.2 --max-depth 10 --learning-rate 0.05
```

Model checkpoints saved to `models/checkpoints/`.

### 3. Run API Server

```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

API automatically loads latest trained model. See [API.md](docs/API.md) for endpoint documentation.

### 4. Launch Executive Dashboard

```bash
streamlit run app/dashboard/main.py --server.port 8501
```

Dashboard reads from PostgreSQL and API. Supports multi-user, role-based access.

### 5. Programmatic Access (Python)

```python
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY")

# Assess a role
response = requests.post(
    f"{API_URL}/api/v1/assess",
    json={
        "job_title": "Software Engineer",
        "average_salary": 120000,
        "years_experience": 8,
        "education_level": "Bachelor's",
        "ai_exposure_index": 0.65,
        "tech_growth_factor": 0.85,
        "skills": [0.8, 0.75, 0.6, ...]  # 10 skill dimensions
    },
    headers={"Authorization": f"Bearer {API_KEY}"}
)

assessment = response.json()
print(f"Automation Risk: {assessment['automation_probability_2030']}")
print(f"Risk Category: {assessment['risk_category']}")
print(f"Confidence: {assessment['confidence']}")
```

---

## API Reference

### Authentication
All endpoints require JWT token in `Authorization: Bearer <token>` header.

```bash
# Get token (development mode, replace with your auth system)
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=<password>"
```

### Key Endpoints

**POST /api/v1/assess** - Assess a role for automation risk
```json
Request:
{
  "job_title": "Software Engineer",
  "average_salary": 120000,
  "years_experience": 8,
  "education_level": "Bachelor's",
  "ai_exposure_index": 0.65,
  "tech_growth_factor": 0.85,
  "skills": [0.8, 0.75, 0.6, 0.5, 0.7, 0.85, 0.6, 0.75, 0.8, 0.65]
}

Response:
{
  "job_title": "Software Engineer",
  "automation_probability_2030": 0.60,
  "risk_category": "Medium",
  "confidence": 0.92,
  "confidence_interval": [0.55, 0.65],
  "assessment_id": "uuid",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**POST /api/v1/explain** - Get SHAP and LIME explanations
```json
Request:
{
  "assessment_id": "uuid or assessment object"
}

Response:
{
  "assessment_id": "uuid",
  "shap_global": { ... },  // Feature importance across all roles
  "shap_local": { ... },   // Contribution to this specific prediction
  "lime_explanation": { ... },  // Simplified local explanation
  "precedence": "SHAP is authoritative",
  "discrepancies": null or explanation
}
```

**POST /api/v1/scenario** - What-if analysis
```json
Request:
{
  "assessment_id": "uuid",
  "changes": {
    "skills": [0.9, 0.8, 0.7, ...],  // hypothetical skill improvements
    "education_level": "Master's"     // hypothetical education upgrade
  }
}

Response:
{
  "original_assessment": { ... },
  "scenario_assessment": { ... },
  "delta_automation_probability": -0.15,
  "narrative": "Upgrading skills in data analysis and machine learning would reduce automation risk from 60% to 45%."
}
```

See [API.md](docs/API.md) for complete endpoint documentation.

---

## Explainability Framework

### SHAP: Audit-Grade Explanations

SHAP (SHapley Additive exPlanations) is the primary explainability method for governance and audit purposes.

**Global Explanations:**
- Feature importance ranked by average |Shapley value|
- Shows which features drive automation risk across all roles
- Visualized as waterfall charts

**Local Explanations:**
- For each role assessment, shows which features pushed probability up/down
- Force plots show feature contributions to final prediction
- Confidence intervals show stability of explanation

```python
from app.ml.explainability import ShapExplainer

explainer = ShapExplainer(model, X_train)
shap_values = explainer.explain_local(role_features)  # For one role
shap_global = explainer.explain_global()  # For all roles
```

### LIME: Human-Friendly Explanations

LIME (Local Interpretable Model-agnostic Explanations) provides supplementary, understandable local approximations.

```python
from app.ml.explainability import LimeExplainer

lime = LimeExplainer(model, feature_names)
explanation = lime.explain_instance(role_features)
```

### Handling SHAP/LIME Discrepancies

1. **Detection**: System flags when SHAP and LIME explanations differ significantly
2. **Logging**: Discrepancy logged with full context for audit
3. **Investigation**: Data team reviews; SHAP deemed authoritative
4. **Resolution**: Document finding; update documentation or model as needed

See [EXPLAINABILITY.md](docs/EXPLAINABILITY.md) for technical deep dive.

---

## Governance & Security

### Access Control (RBAC)

| Role | Permissions |
|------|------------|
| **Admin** | Create/update/delete roles, users; view all audits; configure governance rules |
| **Analyst** | Assess roles; generate reports; view explanations; request new analyses |
| **Viewer** | View published reports and dashboards; no direct assessment access |

### Audit Logging

Every action logged:
- **What**: Assessment, explanation request, data modification
- **Who**: User ID, timestamp, IP address
- **Why**: Request context, business purpose
- **Result**: Outcome, any errors or warnings

```sql
SELECT * FROM audit_logs 
WHERE action = 'assessment' 
AND created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

### Bias & Fairness Analysis

- **Demographic Parity**: Automation probability should not differ significantly by protected attributes
- **Equalized Odds**: True positive and false positive rates should be equal across groups
- **Calibration**: Predicted probabilities should match actual outcomes across all groups

Run bias analysis:
```bash
python scripts/analyze_bias.py --training-data data/train.csv --output reports/bias_report.html
```

### Sensitivity Analysis

Test model robustness to feature perturbations:
- How much can individual feature vary before risk category changes?
- Which features are "fragile" (high sensitivity)?
- Confidence intervals for each prediction

Run sensitivity analysis:
```bash
python scripts/sensitivity_analysis.py --model models/xgboost_model.pkl --output reports/sensitivity.html
```

### Threat Model & Security

See [GOVERNANCE.md](docs/GOVERNANCE.md) for:
- Attack surface analysis
- Data privacy & retention policies
- Adversarial robustness considerations
- Incident response procedures

---

## Documentation

- [README.md](README.md) - This file
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design, data flow, component interactions
- [API.md](docs/API.md) - Complete API reference with examples
- [EXPLAINABILITY.md](docs/EXPLAINABILITY.md) - SHAP/LIME framework, precedence rules
- [GOVERNANCE.md](docs/GOVERNANCE.md) - Security, bias, sensitivity, threat model
- [DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) - Feature definitions, units, ranges
- [INSTALLATION.md](docs/INSTALLATION.md) - Detailed setup & troubleshooting
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Production deployment, scaling, monitoring
- [CONTRIBUTING.md](docs/CONTRIBUTING.md) - Development workflow, testing, code standards

---

## Development

### Project Structure

```
ai-job-impact-platform/
├── README.md                          # This file
├── docs/                              # Documentation
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── EXPLAINABILITY.md
│   ├── GOVERNANCE.md
│   ├── DATA_DICTIONARY.md
│   ├── INSTALLATION.md
│   ├── DEPLOYMENT.md
│   └── CONTRIBUTING.md
├── app/
│   ├── __init__.py
│   ├── api/                           # FastAPI backend
│   │   ├── main.py                    # Entry point
│   │   ├── routes/                    # Endpoint definitions
│   │   │   ├── assess.py
│   │   │   ├── explain.py
│   │   │   ├── scenario.py
│   │   │   ├── audit.py
│   │   │   └── governance.py
│   │   ├── middleware/                # Auth, logging, CORS
│   │   ├── models/                    # Pydantic schemas
│   │   └── utils/                     # Helpers
│   ├── ml/                            # ML pipeline
│   │   ├── model.py                   # XGBoost model wrapper
│   │   ├── preprocessing.py
│   │   ├── explainability.py          # SHAP/LIME
│   │   ├── bias_analysis.py
│   │   └── sensitivity_analysis.py
│   ├── db/                            # Database
│   │   ├── session.py
│   │   ├── models.py                  # SQLAlchemy ORM
│   │   └── queries.py
│   ├── dashboard/                     # Streamlit app
│   │   ├── main.py
│   │   ├── pages/
│   │   │   ├── assess.py
│   │   │   ├── explain.py
│   │   │   ├── scenario.py
│   │   │   ├── audit.py
│   │   │   └── reports.py
│   │   └── components/
│   ├── config/
│   │   ├── settings.py                # Configuration
│   │   └── logging.py
│   └── auth/                          # JWT, RBAC
│       ├── security.py
│       └── permissions.py
├── scripts/
│   ├── init_db.py                     # Initialize database
│   ├── ingest_data.py                 # Load CSV data
│   ├── train_model.py                 # Train XGBoost model
│   ├── analyze_bias.py
│   ├── sensitivity_analysis.py
│   └── generate_reports.py
├── tests/
│   ├── test_api.py
│   ├── test_model.py
│   ├── test_explainability.py
│   ├── test_governance.py
│   └── conftest.py
├── models/
│   └── checkpoints/                   # Trained model artifacts
├── data/
│   ├── raw/
│   │   └── AI_Impact_on_Jobs_2030.csv
│   └── processed/
├── reports/
│   ├── bias_analysis.html
│   ├── sensitivity_analysis.html
│   └── model_performance.html
├── requirements.txt
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── .gitignore
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# Specific test file
pytest tests/test_model.py -v
```

### Code Quality

```bash
# Format with Black
black app/

# Lint with Flake8
flake8 app/ --max-line-length=100

# Type checking with mypy
mypy app/
```

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for:
- Development workflow
- Branching strategy
- Testing requirements
- Code style guide
- Pull request process

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Support & Contact

For questions, issues, or suggestions:
- Open an issue on GitHub
- Contact: ai-platform@example.com
- Slack: #ai-job-impact-platform

---

## Related Resources

- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [SHAP Documentation](https://shap.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**Last Updated**: January 2025  
**Version**: 1.0.0  
**Status**: Production Ready