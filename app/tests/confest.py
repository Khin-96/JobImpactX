import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base
from app.db.session import get_db
from app.api.main import app
from fastapi.testclient import TestClient
import pandas as pd
import numpy as np

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine with all tables."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db(test_engine):
    """Provide isolated database session for each test."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    db = TestingSessionLocal()
    
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield db
    db.close()

@pytest.fixture
def client(test_db):
    """Provide FastAPI test client with database override."""
    return TestClient(app)

@pytest.fixture
def sample_data():
    """Provide sample role data for testing."""
    return pd.DataFrame({
        'Job_Title': ['Software Engineer', 'Truck Driver', 'Doctor'],
        'Average_Salary': [120000, 50000, 150000],
        'Years_Experience': [8, 15, 12],
        'Education_Level': ["Bachelor's", "High School", "PhD"],
        'AI_Exposure_Index': [0.65, 0.1, 0.3],
        'Tech_Growth_Factor': [0.85, 0.6, 0.8],
        'Skill_1': [0.8, 0.3, 0.7],
        'Skill_2': [0.75, 0.2, 0.8],
        'Skill_3': [0.6, 0.4, 0.5],
        'Skill_4': [0.5, 0.9, 0.6],
        'Skill_5': [0.7, 0.5, 0.9],
        'Skill_6': [0.85, 0.4, 0.7],
        'Skill_7': [0.6, 0.3, 0.8],
        'Skill_8': [0.75, 0.2, 0.9],
        'Skill_9': [0.8, 0.5, 0.7],
        'Skill_10': [0.65, 0.4, 0.8],
    })

@pytest.fixture
def sample_assessment_request():
    """Provide sample assessment request payload."""
    return {
        "job_title": "Software Engineer",
        "average_salary": 120000,
        "years_experience": 8,
        "education_level": "Bachelor's",
        "ai_exposure_index": 0.65,
        "tech_growth_factor": 0.85,
        "skills": [0.8, 0.75, 0.6, 0.5, 0.7, 0.85, 0.6, 0.75, 0.8, 0.65]
    }