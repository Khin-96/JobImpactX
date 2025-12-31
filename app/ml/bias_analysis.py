"""
Bias and Fairness Analysis Module.
Implements demographic parity, equalized odds, and calibration analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from sklearn.metrics import confusion_matrix
import logging

logger = logging.getLogger(__name__)


class BiasAnalyzer:
    """Analyze model predictions for fairness and bias."""
    
    def __init__(self, predictions: np.ndarray, actuals: np.ndarray, sensitive_features: pd.DataFrame):
        """
        Initialize bias analyzer.
        
        Args:
            predictions: Model predictions (probabilities 0-1)
            actuals: Actual outcomes (0-1)
            sensitive_features: DataFrame with sensitive attributes (e.g., age_group, education)
        """
        self.predictions = predictions
        self.actuals = actuals
        self.sensitive_features = sensitive_features
        self.threshold = 0.5
    
    def demographic_parity(self, attribute: str) -> Dict[str, Any]:
        """
        Calculate demographic parity: P(prediction=1 | group=A) should equal P(prediction=1 | group=B).
        
        Returns disparate impact ratio and detailed breakdown by group.
        """
        logger.info(f"Calculating demographic parity for attribute: {attribute}")
        
        if attribute not in self.sensitive_features.columns:
            raise ValueError(f"Attribute {attribute} not found in sensitive features")
        
        groups = self.sensitive_features[attribute].unique()
        group_stats = {}
        
        for group in groups:
            mask = self.sensitive_features[attribute] == group
            group_preds = self.predictions[mask]
            positive_rate = (group_preds >= self.threshold).mean()
            group_stats[str(group)] = {
                "count": int(mask.sum()),
                "positive_rate": float(positive_rate)
            }
        
        # Calculate disparate impact (min/max ratio)
        rates = [stats["positive_rate"] for stats in group_stats.values()]
        disparate_impact = min(rates) / max(rates) if max(rates) > 0 else 0.0
        
        # Typically, disparate impact < 0.8 indicates potential bias
        passes_threshold = disparate_impact >= 0.8
        
        return {
            "attribute": attribute,
            "disparate_impact_ratio": float(disparate_impact),
            "passes_threshold_0.8": passes_threshold,
            "group_statistics": group_stats,
            "interpretation": "Pass" if passes_threshold else "Potential bias detected"
        }
    
    def equalized_odds(self, attribute: str) -> Dict[str, Any]:
        """
        Calculate equalized odds: TPR and FPR should be equal across groups.
        
        Returns true positive rate and false positive rate for each group.
        """
        logger.info(f"Calculating equalized odds for attribute: {attribute}")
        
        if attribute not in self.sensitive_features.columns:
            raise ValueError(f"Attribute {attribute} not found in sensitive features")
        
        groups = self.sensitive_features[attribute].unique()
        group_stats = {}
        
        for group in groups:
            mask = self.sensitive_features[attribute] == group
            group_preds = self.predictions[mask]
            group_actuals = self.actuals[mask]
            
            # Binarize predictions
            binary_preds = (group_preds >= self.threshold).astype(int)
            
            # Calculate TPR and FPR
            tn, fp, fn, tp = confusion_matrix(group_actuals, binary_preds, labels=[0, 1]).ravel()
            
            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            
            group_stats[str(group)] = {
                "count": int(mask.sum()),
                "true_positive_rate": float(tpr),
                "false_positive_rate": float(fpr),
                "true_positives": int(tp),
                "false_positives": int(fp),
                "true_negatives": int(tn),
                "false_negatives": int(fn)
            }
        
        # Calculate max difference in TPR and FPR
        tprs = [stats["true_positive_rate"] for stats in group_stats.values()]
        fprs = [stats["false_positive_rate"] for stats in group_stats.values()]
        
        tpr_diff = max(tprs) - min(tprs) if tprs else 0.0
        fpr_diff = max(fprs) - min(fprs) if fprs else 0.0
        
        # Typically, differences < 0.1 are considered acceptable
        passes_threshold = tpr_diff < 0.1 and fpr_diff < 0.1
        
        return {
            "attribute": attribute,
            "tpr_max_difference": float(tpr_diff),
            "fpr_max_difference": float(fpr_diff),
            "passes_threshold_0.1": passes_threshold,
            "group_statistics": group_stats,
            "interpretation": "Pass" if passes_threshold else "Significant disparity detected"
        }
    
    def calibration_analysis(self, attribute: str, n_bins: int = 10) -> Dict[str, Any]:
        """
        Analyze calibration: predicted probabilities should match actual outcomes.
        
        Returns calibration metrics for each group.
        """
        logger.info(f"Calculating calibration for attribute: {attribute}")
        
        if attribute not in self.sensitive_features.columns:
            raise ValueError(f"Attribute {attribute} not found in sensitive features")
        
        groups = self.sensitive_features[attribute].unique()
        group_calibration = {}
        
        for group in groups:
            mask = self.sensitive_features[attribute] == group
            group_preds = self.predictions[mask]
            group_actuals = self.actuals[mask]
            
            # Create bins
            bins = np.linspace(0, 1, n_bins + 1)
            bin_indices = np.digitize(group_preds, bins[:-1]) - 1
            bin_indices = np.clip(bin_indices, 0, n_bins - 1)
            
            calibration_data = []
            for i in range(n_bins):
                bin_mask = bin_indices == i
                if bin_mask.sum() > 0:
                    predicted_prob = group_preds[bin_mask].mean()
                    actual_rate = group_actuals[bin_mask].mean()
                    count = bin_mask.sum()
                    
                    calibration_data.append({
                        "bin": i,
                        "predicted_probability": float(predicted_prob),
                        "actual_rate": float(actual_rate),
                        "count": int(count),
                        "calibration_error": float(abs(predicted_prob - actual_rate))
                    })
            
            # Calculate mean calibration error
            if calibration_data:
                mce = np.mean([item["calibration_error"] for item in calibration_data])
            else:
                mce = 0.0
            
            group_calibration[str(group)] = {
                "count": int(mask.sum()),
                "mean_calibration_error": float(mce),
                "bins": calibration_data
            }
        
        # Check if calibration is similar across groups
        mces = [stats["mean_calibration_error"] for stats in group_calibration.values()]
        mce_diff = max(mces) - min(mces) if mces else 0.0
        passes_threshold = mce_diff < 0.05
        
        return {
            "attribute": attribute,
            "mce_max_difference": float(mce_diff),
            "passes_threshold_0.05": passes_threshold,
            "group_calibration": group_calibration,
            "interpretation": "Well calibrated" if passes_threshold else "Calibration disparity detected"
        }
    
    def generate_report(self, attributes: List[str]) -> Dict[str, Any]:
        """
        Generate comprehensive bias analysis report.
        
        Args:
            attributes: List of sensitive attributes to analyze
            
        Returns:
            Complete bias analysis report
        """
        logger.info(f"Generating bias analysis report for attributes: {attributes}")
        
        report = {
            "summary": {
                "total_samples": len(self.predictions),
                "threshold": self.threshold,
                "attributes_analyzed": attributes
            },
            "demographic_parity": {},
            "equalized_odds": {},
            "calibration": {},
            "overall_assessment": ""
        }
        
        all_pass = True
        
        for attr in attributes:
            try:
                report["demographic_parity"][attr] = self.demographic_parity(attr)
                report["equalized_odds"][attr] = self.equalized_odds(attr)
                report["calibration"][attr] = self.calibration_analysis(attr)
                
                # Check if any test failed
                if not report["demographic_parity"][attr]["passes_threshold_0.8"]:
                    all_pass = False
                if not report["equalized_odds"][attr]["passes_threshold_0.1"]:
                    all_pass = False
                if not report["calibration"][attr]["passes_threshold_0.05"]:
                    all_pass = False
                    
            except Exception as e:
                logger.error(f"Error analyzing attribute {attr}: {e}")
                report["demographic_parity"][attr] = {"error": str(e)}
                report["equalized_odds"][attr] = {"error": str(e)}
                report["calibration"][attr] = {"error": str(e)}
                all_pass = False
        
        if all_pass:
            report["overall_assessment"] = "PASS: Model shows no significant bias across analyzed attributes"
        else:
            report["overall_assessment"] = "ATTENTION REQUIRED: Potential bias detected in one or more fairness metrics"
        
        return report
    
    def generate_html_report(self, attributes: List[str], output_path: str) -> str:
        """
        Generate HTML bias analysis report.
        
        Args:
            attributes: List of sensitive attributes to analyze
            output_path: Path to save HTML report
            
        Returns:
            Path to generated report
        """
        report = self.generate_report(attributes)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Bias Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; margin-top: 30px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .pass {{ color: green; font-weight: bold; }}
                .fail {{ color: red; font-weight: bold; }}
                .metric {{ background-color: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>Bias Analysis Report</h1>
            <div class="metric">
                <h2>Summary</h2>
                <p><strong>Total Samples:</strong> {report['summary']['total_samples']}</p>
                <p><strong>Classification Threshold:</strong> {report['summary']['threshold']}</p>
                <p><strong>Overall Assessment:</strong> <span class="{'pass' if 'PASS' in report['overall_assessment'] else 'fail'}">{report['overall_assessment']}</span></p>
            </div>
        """
        
        for attr in attributes:
            html_content += f"""
            <h2>Analysis for: {attr}</h2>
            
            <div class="metric">
                <h3>Demographic Parity</h3>
                <p><strong>Disparate Impact Ratio:</strong> {report['demographic_parity'][attr].get('disparate_impact_ratio', 'N/A'):.3f}</p>
                <p><strong>Result:</strong> <span class="{'pass' if report['demographic_parity'][attr].get('passes_threshold_0.8', False) else 'fail'}">{report['demographic_parity'][attr].get('interpretation', 'N/A')}</span></p>
            </div>
            
            <div class="metric">
                <h3>Equalized Odds</h3>
                <p><strong>TPR Max Difference:</strong> {report['equalized_odds'][attr].get('tpr_max_difference', 'N/A'):.3f}</p>
                <p><strong>FPR Max Difference:</strong> {report['equalized_odds'][attr].get('fpr_max_difference', 'N/A'):.3f}</p>
                <p><strong>Result:</strong> <span class="{'pass' if report['equalized_odds'][attr].get('passes_threshold_0.1', False) else 'fail'}">{report['equalized_odds'][attr].get('interpretation', 'N/A')}</span></p>
            </div>
            
            <div class="metric">
                <h3>Calibration</h3>
                <p><strong>MCE Max Difference:</strong> {report['calibration'][attr].get('mce_max_difference', 'N/A'):.3f}</p>
                <p><strong>Result:</strong> <span class="{'pass' if report['calibration'][attr].get('passes_threshold_0.05', False) else 'fail'}">{report['calibration'][attr].get('interpretation', 'N/A')}</span></p>
            </div>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {output_path}")
        return output_path
