"""
Bias Analysis Script.
Generate fairness and bias reports for trained models.
"""

import sys
import argparse
import logging
from pathlib import Path
import pandas as pd
import numpy as np

from app.config.logging import setup_logging
from app.db.session import SessionLocal
from app.db.models import Role
from app.ml.model import XGBoostModel
from app.ml.preprocessing import DataPreprocessor
from app.ml.bias_analysis import BiasAnalyzer

setup_logging()
logger = logging.getLogger(__name__)


def run_bias_analysis(
    model_path: str = "models/checkpoints/xgboost_model.pkl",
    output_path: str = "reports/bias_analysis.html",
    sample_size: int = 1000
):
    """
    Run bias analysis on trained model.
    
    Args:
        model_path: Path to trained model
        output_path: Path to save HTML report
        sample_size: Number of samples to analyze
    """
    
    logger.info(f"Starting bias analysis with {sample_size} samples")
    
    # Load model
    try:
        model = XGBoostModel()
        model.load(model_path)
        logger.info(f"Model loaded from {model_path}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)
    
    # Load data
    db = SessionLocal()
    try:
        roles = db.query(Role).limit(sample_size).all()
        
        if len(roles) < 100:
            logger.error("Insufficient data for bias analysis. Need at least 100 samples.")
            sys.exit(1)
        
        logger.info(f"Loaded {len(roles)} roles from database")
        
        # Prepare data
        data = []
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
        
        # Preprocess
        preprocessor = DataPreprocessor()
        df = preprocessor.validate(df)
        df = preprocessor.clean(df)
        
        # Keep sensitive features
        sensitive_features = df[['Education_Level']].copy()
        
        # Transform for prediction
        X_processed = preprocessor.fit_transform(df)[0]
        
        # Generate predictions
        predictions = model.predict(X_processed)
        
        # Generate synthetic actuals (in production, use real outcomes)
        # For demo: use predictions with some noise
        actuals = (predictions + np.random.normal(0, 0.1, len(predictions))).clip(0, 1)
        actuals = (actuals > 0.5).astype(float)
        
        logger.info("Running bias analysis...")
        
        # Run bias analysis
        analyzer = BiasAnalyzer(predictions, actuals, sensitive_features)
        
        # Generate HTML report
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        analyzer.generate_html_report(['Education_Level'], output_path)
        
        logger.info(f"Bias analysis report saved to: {output_path}")
        
        # Print summary to console
        report = analyzer.generate_report(['Education_Level'])
        print("\n" + "="*60)
        print("BIAS ANALYSIS SUMMARY")
        print("="*60)
        print(f"Total Samples: {report['summary']['total_samples']}")
        print(f"Overall Assessment: {report['overall_assessment']}")
        print("\nEducation Level Analysis:")
        
        dp = report['demographic_parity']['Education_Level']
        print(f"  Disparate Impact Ratio: {dp.get('disparate_impact_ratio', 0):.3f}")
        print(f"  Status: {dp.get('interpretation', 'N/A')}")
        
        eo = report['equalized_odds']['Education_Level']
        print(f"  TPR Max Difference: {eo.get('tpr_max_difference', 0):.3f}")
        print(f"  FPR Max Difference: {eo.get('fpr_max_difference', 0):.3f}")
        print(f"  Status: {eo.get('interpretation', 'N/A')}")
        
        cal = report['calibration']['Education_Level']
        print(f"  MCE Max Difference: {cal.get('mce_max_difference', 0):.3f}")
        print(f"  Status: {cal.get('interpretation', 'N/A')}")
        
        print("\nHTML Report: " + output_path)
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Bias analysis failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run bias analysis on trained model")
    parser.add_argument(
        "--model",
        default="models/checkpoints/xgboost_model.pkl",
        help="Path to trained model"
    )
    parser.add_argument(
        "--output",
        default="reports/bias_analysis.html",
        help="Path to save HTML report"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=1000,
        help="Number of samples to analyze"
    )
    
    args = parser.parse_args()
    
    run_bias_analysis(
        model_path=args.model,
        output_path=args.output,
        sample_size=args.sample_size
    )
