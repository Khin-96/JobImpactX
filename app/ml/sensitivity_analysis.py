"""
Sensitivity Analysis Module.
Tests model robustness to feature perturbations.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class SensitivityAnalyzer:
    """Analyze model sensitivity to input perturbations."""
    
    def __init__(self, model, preprocessor, feature_names: List[str]):
        """
        Initialize sensitivity analyzer.
        
        Args:
            model: Trained model with predict method
            preprocessor: Data preprocessor
            feature_names: List of feature names
        """
        self.model = model
        self.preprocessor = preprocessor
        self.feature_names = feature_names
    
    def feature_perturbation(
        self,
        X_sample: np.ndarray,
        feature_idx: int,
        perturbation_range: Tuple[float, float] = (-0.2, 0.2),
        n_steps: int = 20
    ) -> Dict[str, Any]:
        """
        Perturb a single feature and measure prediction change.
        
        Args:
            X_sample: Single sample (1D array)
            feature_idx: Index of feature to perturb
            perturbation_range: Range of perturbation (relative)
            n_steps: Number of perturbation steps
            
        Returns:
            Dictionary with perturbation results
        """
        original_value = X_sample[feature_idx]
        base_prediction = float(self.model.predict(X_sample.reshape(1, -1))[0])
        
        perturbations = np.linspace(
            perturbation_range[0],
            perturbation_range[1],
            n_steps
        )
        
        predictions = []
        perturbed_values = []
        
        for delta in perturbations:
            X_perturbed = X_sample.copy()
            # Relative perturbation
            X_perturbed[feature_idx] = original_value * (1 + delta)
            
            pred = float(self.model.predict(X_perturbed.reshape(1, -1))[0])
            predictions.append(pred)
            perturbed_values.append(float(X_perturbed[feature_idx]))
        
        # Calculate sensitivity score (max change in prediction)
        pred_changes = np.abs(np.array(predictions) - base_prediction)
        sensitivity_score = float(pred_changes.max())
        
        # Check if risk category changes
        def get_risk_category(prob):
            if prob < 0.33:
                return "Low"
            elif prob < 0.67:
                return "Medium"
            else:
                return "High"
        
        base_category = get_risk_category(base_prediction)
        categories = [get_risk_category(p) for p in predictions]
        category_changed = any(cat != base_category for cat in categories)
        
        return {
            "feature_name": self.feature_names[feature_idx],
            "feature_index": feature_idx,
            "original_value": float(original_value),
            "base_prediction": base_prediction,
            "base_category": base_category,
            "sensitivity_score": sensitivity_score,
            "category_changed": category_changed,
            "perturbation_range": perturbation_range,
            "predictions": predictions,
            "perturbed_values": perturbed_values
        }
    
    def analyze_all_features(
        self,
        X_sample: np.ndarray,
        perturbation_range: Tuple[float, float] = (-0.2, 0.2),
        n_steps: int = 20
    ) -> Dict[str, Any]:
        """
        Analyze sensitivity for all features.
        
        Args:
            X_sample: Single sample (1D array)
            perturbation_range: Range of perturbation (relative)
            n_steps: Number of perturbation steps
            
        Returns:
            Dictionary with sensitivity results for all features
        """
        logger.info(f"Analyzing sensitivity for {len(self.feature_names)} features")
        
        results = []
        
        for i in range(len(self.feature_names)):
            try:
                result = self.feature_perturbation(
                    X_sample, i, perturbation_range, n_steps
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing feature {self.feature_names[i]}: {e}")
                results.append({
                    "feature_name": self.feature_names[i],
                    "feature_index": i,
                    "error": str(e)
                })
        
        # Sort by sensitivity score
        valid_results = [r for r in results if "sensitivity_score" in r]
        valid_results.sort(key=lambda x: x["sensitivity_score"], reverse=True)
        
        # Identify fragile features (high sensitivity)
        fragile_threshold = 0.1  # 10% change in prediction
        fragile_features = [r for r in valid_results if r["sensitivity_score"] > fragile_threshold]
        
        # Identify robust features (low sensitivity)
        robust_threshold = 0.05  # 5% change in prediction
        robust_features = [r for r in valid_results if r["sensitivity_score"] < robust_threshold]
        
        return {
            "all_features": results,
            "ranked_by_sensitivity": valid_results,
            "fragile_features": fragile_features,
            "robust_features": robust_features,
            "summary": {
                "total_features": len(self.feature_names),
                "fragile_count": len(fragile_features),
                "robust_count": len(robust_features),
                "mean_sensitivity": float(np.mean([r["sensitivity_score"] for r in valid_results])),
                "max_sensitivity": float(max([r["sensitivity_score"] for r in valid_results])),
                "min_sensitivity": float(min([r["sensitivity_score"] for r in valid_results]))
            }
        }
    
    def confidence_intervals(
        self,
        X_samples: np.ndarray,
        confidence_level: float = 0.95,
        n_bootstrap: int = 100
    ) -> Dict[str, Any]:
        """
        Calculate confidence intervals for predictions using bootstrap.
        
        Args:
            X_samples: Multiple samples (2D array)
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            n_bootstrap: Number of bootstrap iterations
            
        Returns:
            Confidence intervals for each sample
        """
        logger.info(f"Calculating confidence intervals for {len(X_samples)} samples")
        
        confidence_intervals = []
        
        for i, X_sample in enumerate(X_samples):
            predictions = []
            
            for _ in range(n_bootstrap):
                # Add small random noise to simulate uncertainty
                noise = np.random.normal(0, 0.01, X_sample.shape)
                X_perturbed = X_sample + noise
                pred = self.model.predict(X_perturbed.reshape(1, -1))[0]
                predictions.append(pred)
            
            predictions = np.array(predictions)
            
            # Calculate confidence interval
            alpha = 1 - confidence_level
            lower = np.percentile(predictions, alpha / 2 * 100)
            upper = np.percentile(predictions, (1 - alpha / 2) * 100)
            mean_pred = np.mean(predictions)
            std_pred = np.std(predictions)
            
            confidence_intervals.append({
                "sample_index": i,
                "mean_prediction": float(mean_pred),
                "std_prediction": float(std_pred),
                "confidence_interval": [float(lower), float(upper)],
                "confidence_level": confidence_level,
                "interval_width": float(upper - lower)
            })
        
        avg_interval_width = np.mean([ci["interval_width"] for ci in confidence_intervals])
        
        return {
            "confidence_intervals": confidence_intervals,
            "summary": {
                "confidence_level": confidence_level,
                "n_samples": len(X_samples),
                "n_bootstrap": n_bootstrap,
                "average_interval_width": float(avg_interval_width)
            }
        }
    
    def generate_report(
        self,
        X_samples: np.ndarray,
        perturbation_range: Tuple[float, float] = (-0.2, 0.2)
    ) -> Dict[str, Any]:
        """
        Generate comprehensive sensitivity analysis report.
        
        Args:
            X_samples: Multiple samples to analyze (2D array)
            perturbation_range: Range of perturbation for sensitivity analysis
            
        Returns:
            Complete sensitivity analysis report
        """
        logger.info(f"Generating sensitivity report for {len(X_samples)} samples")
        
        # Analyze first sample in detail
        first_sample_analysis = self.analyze_all_features(
            X_samples[0], perturbation_range
        )
        
        # Calculate confidence intervals for all samples
        confidence_analysis = self.confidence_intervals(X_samples)
        
        report = {
            "sample_analysis": first_sample_analysis,
            "confidence_intervals": confidence_analysis,
            "recommendations": self._generate_recommendations(first_sample_analysis)
        }
        
        return report
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on sensitivity analysis."""
        recommendations = []
        
        if analysis["summary"]["fragile_count"] > 0:
            fragile_names = [f["feature_name"] for f in analysis["fragile_features"][:3]]
            recommendations.append(
                f"High sensitivity detected in features: {', '.join(fragile_names)}. "
                "Consider collecting more precise data for these features or applying smoothing."
            )
        
        if analysis["summary"]["mean_sensitivity"] > 0.1:
            recommendations.append(
                "Overall model shows high sensitivity to input perturbations. "
                "Consider regularization or ensemble methods to improve robustness."
            )
        
        if analysis["summary"]["robust_count"] > len(analysis["all_features"]) * 0.8:
            recommendations.append(
                "Model shows good robustness for most features. "
                "Predictions are generally stable to small input variations."
            )
        
        if not recommendations:
            recommendations.append(
                "Model demonstrates balanced sensitivity. "
                "Continue monitoring for production deployment."
            )
        
        return recommendations
    
    def generate_html_report(self, X_samples: np.ndarray, output_path: str) -> str:
        """
        Generate HTML sensitivity analysis report.
        
        Args:
            X_samples: Samples to analyze
            output_path: Path to save HTML report
            
        Returns:
            Path to generated report
        """
        report = self.generate_report(X_samples)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sensitivity Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; margin-top: 30px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .metric {{ background-color: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .fragile {{ color: #d9534f; font-weight: bold; }}
                .robust {{ color: #5cb85c; font-weight: bold; }}
                .recommendation {{ background-color: #fff3cd; padding: 10px; margin: 5px 0; border-left: 4px solid #ffc107; }}
            </style>
        </head>
        <body>
            <h1>Sensitivity Analysis Report</h1>
            
            <div class="metric">
                <h2>Summary</h2>
                <p><strong>Total Features Analyzed:</strong> {report['sample_analysis']['summary']['total_features']}</p>
                <p><strong>Fragile Features (high sensitivity):</strong> <span class="fragile">{report['sample_analysis']['summary']['fragile_count']}</span></p>
                <p><strong>Robust Features (low sensitivity):</strong> <span class="robust">{report['sample_analysis']['summary']['robust_count']}</span></p>
                <p><strong>Mean Sensitivity Score:</strong> {report['sample_analysis']['summary']['mean_sensitivity']:.4f}</p>
                <p><strong>Max Sensitivity Score:</strong> {report['sample_analysis']['summary']['max_sensitivity']:.4f}</p>
            </div>
            
            <div class="metric">
                <h2>Top 10 Most Sensitive Features</h2>
                <table>
                    <tr>
                        <th>Rank</th>
                        <th>Feature Name</th>
                        <th>Sensitivity Score</th>
                        <th>Category Changed</th>
                    </tr>
        """
        
        for i, feature in enumerate(report['sample_analysis']['ranked_by_sensitivity'][:10], 1):
            html_content += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{feature['feature_name']}</td>
                        <td>{feature['sensitivity_score']:.4f}</td>
                        <td>{'Yes' if feature.get('category_changed', False) else 'No'}</td>
                    </tr>
            """
        
        html_content += """
                </table>
            </div>
            
            <div class="metric">
                <h2>Confidence Intervals</h2>
                <p><strong>Average Interval Width:</strong> {:.4f}</p>
                <p><strong>Confidence Level:</strong> {}%</p>
            </div>
            
            <div class="metric">
                <h2>Recommendations</h2>
        """.format(
            report['confidence_intervals']['summary']['average_interval_width'],
            report['confidence_intervals']['summary']['confidence_level'] * 100
        )
        
        for rec in report['recommendations']:
            html_content += f"""
                <div class="recommendation">{rec}</div>
            """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {output_path}")
        return output_path
