"""
NLG Service — Natural Language Generator
Converts structured ML/IoT results into fluent, human-readable sentences
for the chat response layer.
"""
from typing import Any, Dict, List, Optional


class NLGService:
    """
    Takes structured data dicts and renders natural language descriptions.
    Designed for Edge efficiency — no external LLM calls, pure template logic.
    """

    @staticmethod
    def describe_prediction(prediction_result: Dict[str, Any]) -> str:
        """Turn a GNN/Redacted prediction result dict into a sentence."""
        if prediction_result.get("status") != "success":
            return f"⚠️ Prediction failed: {prediction_result.get('message', 'Unknown error')}."

        preds = prediction_result.get("spatial_predictions", [])
        if not preds:
            return "Prediction completed but no spatial values were returned."

        if len(preds) == 1:
            return (
                f"The GNN model predicts a spatial temperature delta of "
                f"**{preds[0]:.3f}°C** across the monitored station."
            )
        return (
            f"The GNN model detected spatial temperature deltas of "
            f"{', '.join(f'**{p:.3f}°C**' for p in preds)} "
            f"across {len(preds)} weather stations."
        )

    @staticmethod
    def describe_iot_reading(reading: Dict[str, Any]) -> str:
        """Summarize a raw IoT sensor reading in natural language."""
        src = reading.get("source", "simulator")
        src_label = {"serial": "Raspberry Pi (serial)", "mqtt": "MQTT broker", "simulator": "IoT simulator"}.get(src, src)
        return (
            f"📡 **Live Reading** from {src_label} at `{reading.get('timestamp', 'N/A')}`:\n"
            f"- 🌡️ Temperature: **{reading.get('temperature', '?')}°C**\n"
            f"- 💧 Humidity: **{reading.get('humidity', '?')}%**\n"
            f"- 📊 Pressure: **{reading.get('pressure', '?')} hPa**\n"
            f"- 💨 Wind Speed: **{reading.get('wind_speed', '?')} m/s**\n"
            f"- 🌧️ Rainfall: **{reading.get('rainfall', '?')} mm**\n"
            f"- ☀️ Light Intensity: **{reading.get('light_intensity', '?')} lux**"
        )

    @staticmethod
    def describe_model_metrics(metrics: Dict[str, float], version: str) -> str:
        """Describe training/evaluation metrics in plain language."""
        rmse = metrics.get("rmse", 0)
        r2 = metrics.get("r2", 0)
        mae = metrics.get("mae", 0)
        quality = "excellent" if r2 > 0.90 else "good" if r2 > 0.75 else "moderate" if r2 > 0.5 else "poor"
        return (
            f"Model **{version}** shows {quality} predictive performance:\n"
            f"- R² Score: **{r2:.4f}** (explains {r2*100:.1f}% of variance)\n"
            f"- RMSE: **{rmse:.4f}** (average prediction error)\n"
            f"- MAE: **{mae:.4f}** (mean absolute error)"
        )

    @staticmethod
    def describe_feature_importances(importances: List[Dict[str, Any]], top_n: int = 5) -> str:
        """Describe the top-N most influential features."""
        top = importances[:top_n]
        lines = [f"{i+1}. **{f['feature']}** (importance: {f['importance']:.4f})" for i, f in enumerate(top)]
        return "Top influencing features for the prediction:\n" + "\n".join(lines)

    @staticmethod
    def describe_xai(xai_result: Dict[str, Any]) -> str:
        """Render XAI explanation in plain English."""
        explanations = xai_result.get("explanations", [])
        if not explanations:
            return "No explainability data available for this prediction."
        lines = []
        for item in explanations[:5]:
            direction = "increases" if item.get("impact", 0) > 0 else "decreases"
            lines.append(
                f"• **{item['feature']}** {direction} the prediction by {abs(item.get('impact', 0)):.3f}"
            )
        return "**Why this prediction?**\n" + "\n".join(lines)

    @staticmethod
    def describe_recommendations(recommendations: List[str]) -> str:
        """Format recommendations as a numbered suggestion list."""
        if not recommendations:
            return ""
        lines = [f"{i+1}. {r}" for i, r in enumerate(recommendations)]
        return "💡 **You might also ask:**\n" + "\n".join(lines)
