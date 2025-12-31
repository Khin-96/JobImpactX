# JobImpactX Platform - Quick Start Guide

## Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for local development)
- PostgreSQL 13+ (or use Docker)
- 4GB RAM minimum

## Quick Start with Docker (Recommended)

### 1. Clone and Configure

```bash
# Clone repository
git clone <repository-url>
cd JobImpactX

# Create environment file
cp .env.example .env

# Edit .env and set secure passwords
nano .env  # or your preferred editor
```

**Important:** Change these values in `.env`:
- `SECRET_KEY` - Set a secure random string (minimum 32 characters)
- `POSTGRES_PASSWORD` - Set a secure database password
- `ADMIN_PASSWORD` - Set initial admin password

### 2. Start Services

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

This will start:
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- FastAPI backend (port 8000)
- Streamlit dashboard (port 8501)

### 3. Initialize Database

```bash
# In a new terminal, initialize the database
docker-compose exec api python app/scripts/init_db.py
```

This creates all tables and a default admin user.

### 4. Ingest Sample Data

```bash
# Ingest the sample role data
docker-compose exec api python app/scripts/ingest_data.py data/samples/sample_roles.csv
```

### 5. Train Model

```bash
# Train the XGBoost model
docker-compose exec api python app/scripts/train_model.py
```

This will:
- Load data from database
- Train XGBoost model with cross-validation
- Save model to `models/checkpoints/xgboost_model.pkl`
- Display performance metrics

### 6. Access the Platform

**Dashboard:** http://localhost:8501
**API Documentation:** http://localhost:8000/docs
**API Base URL:** http://localhost:8000

**Default Login:**
- Username: `admin`
- Password: (as set in .env ADMIN_PASSWORD)

### 7. Test the API

```bash
# Get authentication token
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=YourAdminPassword"

# Use the token in subsequent requests
export TOKEN="<your-token>"

# Assess a role
curl -X POST "http://localhost:8000/api/v1/assess" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Software Engineer",
    "average_salary": 120000,
    "years_experience": 8,
    "education_level": "Bachelors",
    "ai_exposure_index": 0.65,
    "tech_growth_factor": 0.85,
    "skills": [0.8, 0.75, 0.7, 0.65, 0.8, 0.75, 0.7, 0.8, 0.75, 0.7]
  }'
```

## Local Development Setup

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Database

```bash
# Start PostgreSQL (or use Docker for DB only)
docker run -d --name jobimpactx-postgres \
  -e POSTGRES_USER=ai_platform \
  -e POSTGRES_PASSWORD=secure_password \
  -e POSTGRES_DB=ai_job_impact \
  -p 5432:5432 \
  postgres:13-alpine

# Initialize database
python app/scripts/init_db.py

# Ingest data
python app/scripts/ingest_data.py data/samples/sample_roles.csv

# Train model
python app/scripts/train_model.py
```

### 4. Run Services

```bash
# Terminal 1: Start API
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Dashboard
streamlit run app/dashboard/main.py --server.port 8501
```

## Common Commands

### Using Make

```bash
# Show all available commands
make help

# Install dependencies
make install

# Initialize database
make init-db

# Ingest data
make ingest-data CSV=data/samples/sample_roles.csv

# Train model
make train

# Run API
make run-api

# Run dashboard
make run-dashboard

# Run tests
make test

# Run with coverage
make test-cov

# Format code
make format

# Lint code
make lint

# Clean generated files
make clean
```

### Docker Commands

```bash
# Start services
docker-compose up

# Stop services
docker-compose down

# View logs
docker-compose logs -f api

# Rebuild after code changes
docker-compose up --build

# Execute command in container
docker-compose exec api python app/scripts/train_model.py

# Access database
docker-compose exec postgres psql -U ai_platform -d ai_job_impact
```

## User Management

### Create Additional Users

```bash
# Create analyst user
python app/scripts/create_user.py \
  --username analyst1 \
  --email analyst1@example.com \
  --password SecurePassword123 \
  --role Analyst

# Create viewer user
python app/scripts/create_user.py \
  --username viewer1 \
  --email viewer1@example.com \
  --password SecurePassword123 \
  --role Viewer
```

## Governance Reports

### Generate Bias Analysis

```bash
# Generate fairness report
python app/scripts/analyze_bias.py \
  --model models/checkpoints/xgboost_model.pkl \
  --output reports/bias_analysis.html \
  --sample-size 1000
```

### Generate Sensitivity Analysis

```bash
# Generate robustness report
python app/scripts/sensitivity_analysis.py \
  --model models/checkpoints/xgboost_model.pkl \
  --output reports/sensitivity_analysis.html \
  --sample-size 100
```

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View database logs
docker-compose logs postgres

# Verify connection
docker-compose exec api python -c "from app.db.session import engine; print(engine.url)"
```

### Model Loading Issues

```bash
# Check if model file exists
ls -lh models/checkpoints/xgboost_model.pkl

# Retrain if needed
docker-compose exec api python app/scripts/train_model.py

# Check API logs
docker-compose logs api | grep -i model
```

### API Authentication Issues

```bash
# Verify token endpoint
curl http://localhost:8000/auth/token

# Check admin user exists
docker-compose exec postgres psql -U ai_platform -d ai_job_impact \
  -c "SELECT username, role, is_active FROM users WHERE username='admin';"
```

## Security Recommendations

1. **Change Default Credentials:** Update admin password immediately after first login
2. **Secure SECRET_KEY:** Use a cryptographically secure random string
3. **Database Password:** Use a strong password for PostgreSQL
4. **HTTPS in Production:** Configure reverse proxy with SSL/TLS
5. **Regular Updates:** Keep dependencies updated with security patches

## Next Steps

1. **Explore Dashboard:** Navigate through all pages at http://localhost:8501
2. **Test API:** Use the Swagger UI at http://localhost:8000/docs
3. **Review Governance:** Generate and review bias/sensitivity reports
4. **Customize:** Modify model parameters, add features, or integrate with your systems
5. **Production Deploy:** Follow deployment guide for production setup

## Support

For issues, questions, or contributions:
- Check documentation in the `docs/` directory
- Review API documentation at `/docs`
- Open an issue on GitHub
- Contact: support@jobimpactx.com

## License

See LICENSE file for details.
