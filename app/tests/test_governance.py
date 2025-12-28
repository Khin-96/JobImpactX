import pytest
import numpy as np
import pandas as pd
from app.ml.bias_analysis import BiasAnalyzer

def test_bias_analyzer_initialization():
    """Verify bias analyzer initializes with model and data."""
    # Create mock model
    class MockModel:
        def predict(self, X):
            return np.random.uniform(0, 1, len(X))
    
    model = MockModel()
    X = np.random.randn(100, 10)
    y = np.random.uniform(0, 1, 100)
    
    analyzer = BiasAnalyzer(model, X, y)
    assert analyzer.model is not None

def test_sensitivity_analysis():
    """Verify sensitivity analysis detects feature robustness."""
    # Placeholder for sensitivity analysis testing
    # Implementation depends on final SensitivityAnalyzer class
    pass