import shap
import lime.lime_tabular
import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class ShapExplainer:
    """SHAP (SHapley Additive exPlanations) explainability."""
    
    def __init__(self, model, X_train: np.ndarray, feature_names: list):
        self.model = model
        self.X_train = X_train
        self.feature_names = feature_names
        
        # TreeExplainer for XGBoost
        self.explainer = shap.TreeExplainer(model.model)
        self.expected_value = self.explainer.expected_value
        
        logger.info("SHAP TreeExplainer initialized")
    
    def explain_global(self) -> Dict[str, float]:
        """Global feature importance across all training data."""
        shap_values = self.explainer.shap_values(self.X_train)
        
        # Mean absolute Shapley value
        importance = np.abs(shap_values).mean(axis=0)
        
        return dict(zip(self.feature_names, importance))
    
    def explain_local(self, X_instance: np.ndarray, instance_idx: int = 0) -> Dict[str, Any]:
        """Local explanation for a single instance."""
        shap_values = self.explainer.shap_values(X_instance)
        
        if len(shap_values.shape) == 1:
            # Single instance
            shap_val = shap_values
            features = X_instance[0]
        else:
            # Multiple instances; take first
            shap_val = shap_values[instance_idx]
            features = X_instance[instance_idx]
        
        # Build explanation
        explanation = {
            'base_value': float(self.expected_value),
            'shap_values': shap_val.tolist(),
            'features': features.tolist(),
            'feature_names': self.feature_names,
            'prediction': float(self.expected_value + shap_val.sum()),
            'contributions': []
        }
        
        # Rank features by impact
        feature_impacts = list(zip(self.feature_names, shap_val))
        feature_impacts.sort(key=lambda x: abs(x[1]), reverse=True)
        
        for fname, shap_val in feature_impacts[:10]:  # Top 10
            explanation['contributions'].append({
                'feature': fname,
                'value': float(features[self.feature_names.index(fname)]),
                'shap_value': float(shap_val),
                'direction': 'increases_risk' if shap_val > 0 else 'decreases_risk'
            })
        
        return explanation

class LimeExplainer:
    """LIME (Local Interpretable Model-agnostic Explanations)."""
    
    def __init__(self, model, X_train: np.ndarray, feature_names: list):
        self.model = model
        self.feature_names = feature_names
        
        # LIME tabular explainer
        self.explainer = lime.lime_tabular.LimeTabularExplainer(
            X_train,
            feature_names=feature_names,
            mode='regression',
            random_state=42
        )
        
        logger.info("LIME TabularExplainer initialized")
    
    def explain_instance(self, X_instance: np.ndarray, instance_idx: int = 0) -> Dict[str, Any]:
        """Local linear approximation for a single instance."""
        
        instance = X_instance[instance_idx] if len(X_instance.shape) > 1 else X_instance
        
        # LIME explanation
        lime_exp = self.explainer.explain_instance(
            instance,
            self.model.predict,
            num_features=10,
            top_labels=1
        )
        
        explanation = {
            'top_features': [],
            'intercept': float(lime_exp.intercept[0]),
            'local_model_score': float(lime_exp.score),
        }
        
        for feature, weight in lime_exp.as_list():
            explanation['top_features'].append({
                'feature': feature,
                'weight': float(weight),
                'direction': 'increases_risk' if weight > 0 else 'decreases_risk'
            })
        
        return explanation

class ExplainabilityManager:
    """Manage SHAP/LIME explanations and handle discrepancies."""
    
    def __init__(self, model, X_train: np.ndarray, feature_names: list):
        self.shap = ShapExplainer(model, X_train, feature_names)
        self.lime = LimeExplainer(model, X_train, feature_names)
    
    def explain(self, X_instance: np.ndarray) -> Dict[str, Any]:
        """Generate both SHAP and LIME explanations."""
        
        shap_exp = self.shap.explain_local(X_instance)
        lime_exp = self.lime.explain_instance(X_instance)
        
        # Check for discrepancies
        discrepancy = self._check_discrepancy(shap_exp, lime_exp)
        
        return {
            'shap_explanation': shap_exp,
            'lime_explanation': lime_exp,
            'discrepancy_detected': discrepancy['detected'],
            'discrepancy_details': discrepancy['details'],
            'precedence_note': 'SHAP is authoritative for governance; LIME is supplementary'
        }
    
    def _check_discrepancy(self, shap_exp: Dict, lime_exp: Dict) -> Dict[str, Any]:
        """Detect if SHAP and LIME explanations significantly differ."""
        
        shap_top_features = {c['feature'] for c in shap_exp['contributions'][:5]}
        lime_top_features = {
            f.split(' ')[0] for f in [fv[0] for fv in lime_exp['top_features'][:5]]
        }
        
        # Check overlap
        overlap = len(shap_top_features & lime_top_features)
        
        discrepancy = {
            'detected': overlap < 3,  # Less than 3/5 overlap = discrepancy
            'details': {
                'shap_top_5': list(shap_top_features),
                'lime_top_5': list(lime_top_features),
                'overlap_count': overlap,
                'recommendation': 'Investigate model behavior; SHAP is authoritative'
            } if overlap < 3 else None
        }
        
        if discrepancy['detected']:
            logger.warning(f"SHAP/LIME discrepancy detected: overlap={overlap}/5")
        
        return discrepancy