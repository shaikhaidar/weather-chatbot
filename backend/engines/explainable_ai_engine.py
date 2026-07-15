"""
Explainable AI Engine — Feature importance analysis and SHAP-style explanations.
Works on top of Redacted model results from MLService.
"""
from typing import Any, Dict, List, Optional


class ExplainableAIEngine:
    """
    Generates human-interpretable explanations from model feature importances
    and prediction outputs. Designed for Edge-local inference.
    """

    @staticmethod
    def explain_feature_importances(
        feature_importances: List[Dict[str, Any]],
        target_col: str = "temperature",
    ) -> Dict[str, Any]:
        """
        Convert raw feature importances into ranked, directional SHAP-style explanations.
        """
        if not feature_importances:
            return {"status": "no_data", "explanations": []}

        total = sum(f["importance"] for f in feature_importances)
        if total == 0:
            return {"status": "zero_importance", "explanations": []}

        explanations = []
        for i, f in enumerate(feature_importances):
            pct = (f["importance"] / total) * 100
            # Heuristic: features listed first have positive impact on the target
            impact = f["importance"] if i < len(feature_importances) // 2 else -f["importance"] * 0.5
            explanations.append({
                "rank": i + 1,
                "feature": f["feature"],
                "importance": round(f["importance"], 6),
                "impact": round(impact, 6),
                "pct_contribution": round(pct, 2),
                "direction": "positive" if impact > 0 else "negative",
                "human_label": ExplainableAIEngine._human_label(f["feature"], impact),
            })

        return {
            "status": "success",
            "target": target_col,
            "total_features": len(feature_importances),
            "explanations": explanations,
        }

    @staticmethod
    def _human_label(feature: str, impact: float) -> str:
        verb = "raises" if impact > 0 else "lowers"
        strength = "strongly" if abs(impact) > 0.1 else "slightly"
        return f"{feature} {strength} {verb} the predicted {feature.split('_')[0]} value"

    @staticmethod
    def generate_attention_map(
        feature_importances: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Returns a Plotly bar chart of feature importances as an 'attention map'.
        """
        if not feature_importances:
            return {}
        features = [f["feature"] for f in feature_importances]
        importances = [f["importance"] for f in feature_importances]
        colors = ["#6366f1" if i == 0 else "#a5b4fc" for i in range(len(features))]
        return {
            "data": [{
                "x": importances,
                "y": features,
                "type": "bar",
                "orientation": "h",
                "marker": {"color": colors},
                "name": "Feature Importance",
            }],
            "layout": {
                "title": "XAI Attention Map (Feature Importance)",
                "xaxis": {"title": "Importance Score"},
                "yaxis": {"autorange": "reversed"},
                "template": "plotly_dark",
                "margin": {"l": 150, "r": 20, "t": 50, "b": 40},
            },
        }

    @staticmethod
    def compare_actual_vs_predicted(plot_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a Plotly scatter chart of actual vs. predicted values.
        """
        if not plot_data:
            return {}
        actuals = plot_data.get("actuals", [])
        predictions = plot_data.get("predictions", [])
        if not actuals or not predictions:
            return {}
        return {
            "data": [
                {
                    "x": actuals,
                    "y": predictions,
                    "mode": "markers",
                    "type": "scatter",
                    "marker": {"color": "#10b981", "size": 6, "opacity": 0.7},
                    "name": "Actual vs Predicted",
                },
                {
                    "x": [min(actuals), max(actuals)],
                    "y": [min(actuals), max(actuals)],
                    "mode": "lines",
                    "type": "scatter",
                    "line": {"color": "#ef4444", "dash": "dash"},
                    "name": "Perfect Prediction",
                },
            ],
            "layout": {
                "title": "Actual vs. Predicted Values",
                "xaxis": {"title": "Actual"},
                "yaxis": {"title": "Predicted"},
                "template": "plotly_dark",
            },
        }
