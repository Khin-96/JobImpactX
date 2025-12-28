import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import logging
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)

class DataPreprocessor:
    """Data validation, cleaning, and feature engineering."""
    
    REQUIRED_COLUMNS = [
        'Job_Title', 'Average_Salary', 'Years_Experience', 'Education_Level',
        'AI_Exposure_Index', 'Tech_Growth_Factor'
    ]
    SKILL_COLUMNS = [f'Skill_{i}' for i in range(1, 11)]
    
    EDUCATION_MAPPING = {
        'High School': 0,
        "Bachelor's": 1,
        "Master's": 2,
        'PhD': 3
    }
    
    def __init__(self):
        self.scaler = None
        self.encoder = None
        self.feature_names = None
        self.numeric_features = None
        self.categorical_features = None
    
    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate CSV has required columns and valid types."""
        logger.info(f"Validating data: {len(df)} rows, {len(df.columns)} columns")
        
        # Check required columns
        missing_cols = set(self.REQUIRED_COLUMNS + self.SKILL_COLUMNS) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Check numeric ranges
        df = df.copy()
        
        # Salary: 20k-500k
        invalid_salary = df[(df['Average_Salary'] < 20000) | (df['Average_Salary'] > 500000)]
        if len(invalid_salary) > 0:
            logger.warning(f"Found {len(invalid_salary)} rows with out-of-range salary")
            df = df[(df['Average_Salary'] >= 20000) & (df['Average_Salary'] <= 500000)]
        
        # AI Exposure: 0-1
        df['AI_Exposure_Index'] = df['AI_Exposure_Index'].clip(0, 1)
        
        # Tech Growth: 0.5-1.5
        df['Tech_Growth_Factor'] = df['Tech_Growth_Factor'].clip(0.5, 1.5)
        
        # Skills: 0-1
        for skill in self.SKILL_COLUMNS:
            df[skill] = df[skill].clip(0, 1)
        
        logger.info(f"Validation complete: {len(df)} rows after cleaning")
        return df
    
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicates, handle missing values."""
        df = df.copy()
        
        # Remove exact duplicates
        initial_rows = len(df)
        df = df.drop_duplicates()
        logger.info(f"Removed {initial_rows - len(df)} exact duplicates")
        
        # Remove near-duplicates (same job + salary + experience)
        df = df.drop_duplicates(
            subset=['Job_Title', 'Average_Salary', 'Years_Experience'],
            keep='first'
        )
        logger.info(f"After dedup by job/salary/exp: {len(df)} rows")
        
        # Handle missing values
        missing_pct = df.isnull().sum() / len(df)
        if missing_pct.max() > 0:
            logger.info(f"Missing values:\n{missing_pct[missing_pct > 0]}")
            # Drop rows with missing critical columns
            df = df.dropna(subset=self.REQUIRED_COLUMNS + self.SKILL_COLUMNS)
        
        return df
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create derived features."""
        df = df.copy()
        
        # Experience risk factor: newer roles riskier
        df['experience_risk'] = 1.0 / (1.0 + df['Years_Experience'].clip(lower=0.1))
        
        # Log salary (captures diminishing value)
        df['log_salary'] = np.log1p(df['Average_Salary'])
        
        # Skill diversity (std of 10 skills)
        skill_cols = self.SKILL_COLUMNS
        df['skill_diversity'] = df[skill_cols].std(axis=1, skipna=True)
        df['skill_diversity'] = df['skill_diversity'].fillna(df['skill_diversity'].mean())
        
        # Max skill proficiency
        df['max_skill'] = df[skill_cols].max(axis=1)
        
        # Tech pressure: AI exposure × growth factor
        df['tech_pressure'] = df['AI_Exposure_Index'] * df['Tech_Growth_Factor']
        
        # Education level (ordinal)
        df['education_level_code'] = df['Education_Level'].map(self.EDUCATION_MAPPING)
        
        logger.info("Feature engineering complete")
        return df
    
    def fit(self, X: pd.DataFrame) -> 'DataPreprocessor':
        """Fit scalers and encoders on training data."""
        self.numeric_features = [
            'Average_Salary', 'Years_Experience', 'AI_Exposure_Index',
            'Tech_Growth_Factor', 'experience_risk', 'log_salary',
            'skill_diversity', 'max_skill', 'tech_pressure',
            'education_level_code'
        ] + self.SKILL_COLUMNS
        
        self.categorical_features = []
        
        # Fit scaler
        self.scaler = StandardScaler()
        self.scaler.fit(X[self.numeric_features])
        
        # Build feature names
        self.feature_names = self.numeric_features
        
        logger.info(f"Fitted preprocessor with {len(self.feature_names)} features")
        return self
    
    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transform raw data to model-ready features."""
        X = X.copy()
        
        # Engineer features
        X = self.engineer_features(X)
        
        # Scale numeric features
        X_scaled = self.scaler.transform(X[self.numeric_features])
        
        return X_scaled
    
    def fit_transform(self, X: pd.DataFrame) -> Tuple[np.ndarray, 'DataPreprocessor']:
        """Fit and transform in one step."""
        X = self.engineer_features(X)
        return self.fit(X).transform(X), self
