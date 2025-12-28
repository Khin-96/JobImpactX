import pytest
import numpy as np
import pandas as pd
from app.ml.preprocessing import DataPreprocessor
from app.ml.model import XGBoostModel

def test_preprocessor_scaling(sample_data):
    """Verify preprocessor correctly scales features to mean~0, std~1."""
    preprocessor = DataPreprocessor()
    X = sample_data.drop('Job_Title', axis=1)
    X_processed, _ = preprocessor.fit_transform(X)
    
    # Verify no NaN or infinite values
    assert X_processed.shape[0] == len(X)
    assert not np.any(np.isnan(X_processed))
    assert not np.any(np.isinf(X_processed))

def test_preprocessor_feature_engineering(sample_data):
    """Verify feature engineering creates expected derived columns."""
    preprocessor = DataPreprocessor()
    X = sample_data.drop('Job_Title', axis=1)
    
    preprocessor.engineer_features(X)
    
    # Verify expected engineered features exist
    assert 'experience_risk' in X.columns
    assert 'log_salary' in X.columns
    assert 'skill_diversity' in X.columns

def test_xgboost_model_prediction_range():
    """Verify model predictions remain in valid probability range [0, 1]."""
    model = XGBoostModel()
    
    # Create synthetic training data
    X_train = np.random.randn(100, 20)
    y_train = np.random.uniform(0, 1, 100)
    
    model.train(X_train, y_train, num_boost_round=10)
    predictions = model.predict(X_train[:10])
    
    # Verify all predictions in valid probability range
    assert np.all(predictions >= 0)
    assert np.all(predictions <= 1)

def test_xgboost_feature_importance():
    """Verify model returns valid feature importance scores."""
    model = XGBoostModel()
    
    X_train = np.random.randn(100, 20)
    y_train = np.random.uniform(0, 1, 100)
    feature_names = [f'f{i}' for i in range(20)]
    
    model.train(X_train, y_train, feature_names=feature_names, num_boost_round=10)
    importance = model.get_feature_importance()
    
    # Verify output structure and normalization
    assert isinstance(importance, dict)
    assert len(importance) > 0
    # Normalized importance should sum to approximately 1
    assert 0.99 <= sum(importance.values()) <= 1.01