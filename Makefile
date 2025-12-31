.PHONY: help install run test docker-up docker-down clean lint format init-db train

help:
@echo "JobImpactX Platform - Available Commands"
@echo "========================================"
@echo "install       - Install Python dependencies"
@echo "init-db       - Initialize database schema"
@echo "ingest-data   - Ingest CSV data into database"
@echo "train         - Train XGBoost model"
@echo "run-api       - Start FastAPI server"
@echo "run-dashboard - Start Streamlit dashboard"
@echo "docker-up     - Start all services with Docker Compose"
@echo "docker-down   - Stop all Docker services"
@echo "test          - Run pytest suite"
@echo "test-cov      - Run tests with coverage report"
@echo "lint          - Run flake8 linter"
@echo "format        - Format code with black"
@echo "clean         - Remove generated files"

install:
pip install -r requirements.txt

init-db:
python app/scripts/init_db.py

ingest-data:
@echo "Usage: make ingest-data CSV=path/to/data.csv"
@if [ -z "$(CSV)" ]; then \
echo "Error: CSV parameter required"; \
exit 1; \
fi
python app/scripts/ingest_data.py $(CSV)

train:
python app/scripts/train_model.py

run-api:
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload

run-dashboard:
streamlit run app/dashboard/main.py --server.port 8501

docker-up:
docker-compose up --build

docker-down:
docker-compose down

test:
pytest app/tests/ -v

test-cov:
pytest app/tests/ --cov=app --cov-report=html --cov-report=term

lint:
flake8 app/ --max-line-length=100 --exclude=__pycache__,*.pyc

format:
black app/ --line-length=100

clean:
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
rm -rf .pytest_cache .coverage htmlcov
rm -rf logs/*.log

analyze-bias:
python app/scripts/analyze_bias.py

sensitivity:
python app/scripts/sensitivity_analysis.py

create-admin:
@echo "Usage: make create-admin USERNAME=admin EMAIL=admin@example.com PASSWORD=password"
python app/scripts/create_user.py --username $(USERNAME) --email $(EMAIL) --password $(PASSWORD) --role Admin
