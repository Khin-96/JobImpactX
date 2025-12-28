import pytest
import numpy as np
from app.ml.model import XGBoostModel
from app.ml.explainability import ShapExplainer, LimeExplainer

@pytest.fixture
def trained_model():
    """Train a simple model for explainability testing."""
    model = XGBoostModel()
    X_train = np.random.randn(100, 20)
    y_train = np.random.uniform(0, 1, 100)
    feature_names = [f'feature_{i}' for i in range(20)]
    
    model.train(X_train, y_train, feature_names=feature_names, num_boost_round=10)
    return model, X_train, feature_names

def test_shap_explainer_initialization(trained_model):
    """Verify SHAP explainer initializes correctly."""
    model, X_train, feature_names = trained_model
    
    shap_exp = ShapExplainer(model, X_train, feature_names)
    
    assert shap_exp.model is not None
    assert shap_exp.explainer is not None
    assert shap_exp.expected_value is not None

def test_shap_global_explanation(trained_model):
    """Verify SHAP global feature importance computation."""
    model, X_train, feature_names = trained_model
    
    shap_exp = ShapExplainer(model, X_train, feature_names)
    importance = shap_exp.explain_global()
    
    # Verify all features represented
    assert len(importance) == len(feature_names)
    # Verify non-negative importances
    assert all(v >= 0 for v in importance.values())
    # Verify non-zero importance exists
    assert sum(importance.values()) > 0

def test_shap_local_explanation(trained_model):
    """Verify SHAP local explanation structure and consistency."""
    model, X_train, feature_names = trained_model
    
    shap_exp = ShapExplainer(model, X_train, feature_names)
    explanation = shap_exp.explain_local(X_train[[0]])
    
    # Verify required explanation components
    assert 'base_value' in explanation
    assert 'shap_values' in explanation
    assert 'prediction' in explanation
    assert 'contributions' in explanation
    
    # Verify additivity: prediction = base + sum(contributions)
    expected_pred = explanation['base_value'] + sum(
        c['shap_value'] for c in explanation['contributions']
    )
    assert abs(explanation['prediction'] - expected_pred) < 0.01

def test_lime_explainer_initialization(trained_model):
    """Verify LIME explainer initializes correctly."""
    model, X_train, feature_names = trained_model
    
    lime_exp = LimeExplainer(model, X_train, feature_names)
    
    assert lime_exp.model is not None
    assert lime_exp.explainer is not None

def test_lime_local_explanation(trained_model):
    """Verify LIME local explanation generation."""
    model, X_train, feature_names = trained_model
    
    lime_exp = LimeExplainer(model, X_train, feature_names)
    explanation = lime_exp.explain_instance(X_train[[0]])
    
    # Verify required explanation components
    assert 'top_features' in explanation
    assert 'intercept' in explanation
    assert 'local_model_score' in explanation
    
    # Verify non-empty feature list
    assert len(explanation['top_features']) > 0