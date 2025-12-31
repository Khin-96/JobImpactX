"""
Sensitivity Analysis Script.
Generate robustness and sensitivity reports for trained models.
"""

import sys
import argparse
import logging
from pathlib import Path
import pandas as pd

from app.config.logging import setup_logging
from app.db.session import SessionLocal
from app.db.models import Role
from app.ml.model import XGBoostModel
from app.ml.preprocessing import DataPreprocessor
from app.ml.sensitivity_analysis import SensitivityAnalyzer

setup_logging()
logger = logging.getLogger(__name__)


def run_sensitivity_analysis(
    model_path: str = "models/checkpoints/xgboost_model.pkl",
    output_path: str = "reports/sensitivity_analysis.html",
    sample_size: int = 100,
    perturbation_range: float = 0.2
):
    """
    Run sensitivity analysis on trained model.
    
    Args:
        model_path: Path to trained model
        output_path: Path to save HTML report
        sample_size: Number of samples to analyze
        perturbation_range: Range of perturbation (relative)
    """
    
    logger.info(f"Starting sensitivity analysis with {sample_size} samples")
    
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
        
        if len(roles) < 10:
            logger.error("Insufficient data for sensitivity analysis. Need at least 10 samples.")
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
        
        # Transform for prediction
        X_processed = preprocessor.fit_transform(df)[0]
        
        logger.info("Running sensitivity analysis...")
        
        # Run sensitivity analysis
        analyzer = SensitivityAnalyzer(model, preprocessor, preprocessor.feature_names)
        
        # Generate HTML report
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        analyzer.generate_html_report(X_processed, output_path)
        
        logger.info(f"Sensitivity analysis report saved to: {output_path}")
        
        # Print summary to console
        report = analyzer.generate_report(X_processed, (-perturbation_range, perturbation_range))
        
        print("\n" + "="*60)
        print("SENSITIVITY ANALYSIS SUMMARY")
        print("="*60)
        print(f"Total Features: {report['sample_analysis']['summary']['total_features']}")
        print(f"Fragile Features: {report['sample_analysis']['summary']['fragile_count']}")
        print(f"Robust Features: {report['sample_analysis']['summary']['robust_count']}")
        print(f"Mean Sensitivity: {report['sample_analysis']['summary']['mean_sensitivity']:.4f}")
        print(f"Max Sensitivity: {report['sample_analysis']['summary']['max_sensitivity']:.4f}")
        
        print("\nTop 5 Most Sensitive Features:")
        for i, feature in enumerate(report['sample_analysis']['ranked_by_sensitivity'][:5], 1):
            print(f"  {i}. {feature['feature_name']}: {feature['sensitivity_score']:.4f}")
        
        print("\nConfidence Intervals:")
        print(f"  Average Interval Width: {report['confidence_intervals']['summary']['average_interval_width']:.4f}")
        print(f"  Confidence Level: {report['confidence_intervals']['summary']['confidence_level']*100:.0f}%")
        
        print("\nRecommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print("\nHTML Report: " + output_path)
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on trained model")
    parser.add_argument(
        "--model",
        default="models/checkpoints/xgboost_model.pkl",
        help="Path to trained model"
    )
    parser.add_argument(
        "--output",
        default="reports/sensitivity_analysis.html",
        help="Path to save HTML report"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=100,
        help="Number of samples to analyze"
    )
    parser.add_argument(
        "--perturbation-range",
        type=float,
        default=0.2,
        help="Range of perturbation (relative, e.g., 0.2 for +/-20%%)"
    )
    
    args = parser.parse_args()
    
    run_sensitivity_analysis(
        model_path=args.model,
        output_path=args.output,
        sample_size=args.sample_size,
        perturbation_range=args.perturbation_range
    )
