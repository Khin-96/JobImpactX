import xgboost as xgb
import numpy as np
import pickle
import logging
from typing import Dict, Any
from sklearn.metrics import roc_auc_score, mean_squared_error
from pathlib import Path

logger = logging.getLogger(__name__)

class XGBoostModel:
    """XGBoost model for automation risk prediction."""
    
    DEFAULT_PARAMS = {
        'objective': 'reg:squarederror',
        'max_depth': 7,
        'learning_rate': 0.05,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'reg_lambda': 1.0,
        'reg_alpha': 0.5,
        'min_child_weight': 5,
        'random_state': 42,
        'verbosity': 0
    }
    
    def __init__(self, params: Dict[str, Any] = None):
        self.params = {**self.DEFAULT_PARAMS, **(params or {})}
        self.model = None
        self.feature_names = None
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray = None,
        y_val: np.ndarray = None,
        feature_names: list = None,
        num_boost_round: int = 200,
        early_stopping_rounds: int = 20
    ) -> Dict[str, float]:
        """Train XGBoost model."""
        
        self.feature_names = feature_names or [f'f{i}' for i in range(X_train.shape[1])]
        
        dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=self.feature_names)
        
        evals = [(dtrain, 'train')]
        eval_names = ['train']
        
        if X_val is not None and y_val is not None:
            dval = xgb.DMatrix(X_val, label=y_val, feature_names=self.feature_names)
            evals.append((dval, 'val'))
            eval_names.append('val')
        
        logger.info(f"Training XGBoost with params: {self.params}")
        
        self.model = xgb.train(
            self.params,
            dtrain,
            num_boost_round=num_boost_round,
            evals=evals,
            early_stopping_rounds=early_stopping_rounds,
            verbose_eval=10
        )
        
        # Evaluate
        metrics = self._evaluate(X_train, y_train, X_val, y_val)
        logger.info(f"Training metrics: {metrics}")
        
        return metrics
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict automation probability."""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        dtest = xgb.DMatrix(X, feature_names=self.feature_names)
        predictions = self.model.predict(dtest)
        
        # Clip to [0, 1] probability range
        return np.clip(predictions, 0, 1)
    
    def get_feature_importance(self, importance_type: str = 'gain') -> Dict[str, float]:
        """Get feature importance scores."""
        importance = self.model.get_score(importance_type=importance_type)
        # Normalize
        total = sum(importance.values())
        return {k: v / total for k, v in importance.items()}
    
    def save(self, filepath: str):
        """Save model to disk."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        self.model.save_model(filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load(self, filepath: str):
        """Load model from disk."""
        self.model = xgb.Booster()
        self.model.load_model(filepath)
        logger.info(f"Model loaded from {filepath}")
        return self
    
    def _evaluate(self, X_train, y_train, X_val=None, y_val=None) -> Dict[str, float]:
        """Calculate evaluation metrics."""
        train_pred = self.predict(X_train)
        metrics = {
            'train_auc': roc_auc_score(y_train, train_pred),
            'train_brier': mean_squared_error(y_train, train_pred),
            'train_rmse': np.sqrt(mean_squared_error(y_train, train_pred))
        }
        
        if X_val is not None and y_val is not None:
            val_pred = self.predict(X_val)
            metrics['val_auc'] = roc_auc_score(y_val, val_pred)
            metrics['val_brier'] = mean_squared_error(y_val, val_pred)
            metrics['val_rmse'] = np.sqrt(mean_squared_error(y_val, val_pred))
        
        return metrics