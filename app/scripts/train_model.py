import pandas as pd
import numpy as np
import logging
import sys
from pathlib import Path
from sklearn.model_selection import train_test_split
from app.config.logging import setup_logging
from app.db.session import SessionLocal
from app.db.models import Role
from app.ml.model import XGBoostModel
from app.ml.preprocessing import DataPreprocessor
from datetime import datetime

setup_logging()
logger = logging.getLogger(__name__)

def train_model(
    test_size: float = 0.3,
    max_depth: int = 7,
    learning_rate: float = 0.05,
    output_path: str = "models/checkpoints/xgboost_model.pkl"
):
    """Train XGBoost model on roles data."""
    
    # Load data
    db = SessionLocal()
    roles = db.query(Role).all()
    db.close()
    
    if not roles:
        logger.error("No roles found in database. Run ingest_data.py first.")
        sys.exit(1)
    
    logger.info(f"Loaded {len(roles)} roles from database")
    
    # Convert to DataFrame
    data = []
    skill_cols = [f'Skill_{i}' for i in range(1, 11)]
    
    for role in roles:
        row = {
            'Job_Title': role.job_title,
            'Average_Salary': role.average_salary,
            'Years_Experience': role.years_experience,
            'Education_Level': role.education_level,
            'AI_Exposure_Index': role.ai_exposure_index,
            'Tech_Growth_Factor': role.tech_growth_factor,
        }
        for i, skill in enumerate(role.skills or []):
            row[f'Skill_{i+1}'] = skill
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Synthetic target (in real scenario, use actual automation data)
    # For demo: combine features to create synthetic target
    df['Automation_Probability_2030'] = (
        df['AI_Exposure_Index'] * 0.4 +
        df['Tech_Growth_Factor'] * 0.3 +
        (1 - df['Years_Experience'] / df['Years_Experience'].max()) * 0.2 +
        (df['Average_Salary'] / df['Average_Salary'].max()) * 0.1
    ).clip(0, 1)
    
    logger.info(f"Data shape: {df.shape}")
    logger.info(f"Target distribution - Low: {(df['Automation_Probability_2030'] < 0.33).mean():.2%}, "
               f"Medium: {((df['Automation_Probability_2030'] >= 0.33) & (df['Automation_Probability_2030'] < 0.67)).mean():.2%}, "
               f"High: {(df['Automation_Probability_2030'] >= 0.67).mean():.2%}")
    
    # Preprocess
    logger.info("Preprocessing data...")
    preprocessor = DataPreprocessor()
    df = preprocessor.validate(df)
    df = preprocessor.clean(df)
    
    X = df.drop('Automation_Probability_2030', axis=1)
    y = df['Automation_Probability_2030'].values
    
    X_processed, preprocessor = preprocessor.fit_transform(X)
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_processed, y, test_size=test_size, random_state=42
    )
    
    logger.info(f"Train: {len(X_train)}, Test: {len(X_test)}")
    
    # Train model
    logger.info("Training XGBoost model...")
    model = XGBoostModel(params={
        'max_depth': max_depth,
        'learning_rate': learning_rate,
    })
    
    metrics = model.train(
        X_train, y_train,
        X_test, y_test,
        feature_names=preprocessor.feature_names,
        num_boost_round=200,
        early_stopping_rounds=20
    )
    
    logger.info(f"Training complete. Metrics: {metrics}")
    
    # Save model
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    model.save(output_path)
    logger.info(f"Model saved to {output_path}")
    
    return model, metrics

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-size", type=float, default=0.3)
    parser.add_argument("--max-depth", type=int, default=7)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--output", default="models/checkpoints/xgboost_model.pkl")
    args = parser.parse_args()
    
    train_model(
        test_size=args.test_size,
        max_depth=args.max_depth,
        learning_rate=args.learning_rate,
        output_path=args.output
    )