"""
Recommendation Engine — Generates contextual follow-up query suggestions
based on the current intent, available data, and active system mode.
"""
from typing import Any, Dict, List, Optional
import random


# Context-aware suggestion templates keyed by (intent, mode)
_SUGGESTIONS: Dict[str, List[str]] = {
    "GREETING": [
        "Show me the latest temperature trend",
        "What is the current live sensor reading?",
        "Plot feature importance for the active model",
        "How accurate is the current weather prediction model?",
    ],
    "GRAPH_REQUEST": [
        "Show me the correlation heatmap",
        "Plot actual vs predicted values",
        "Display the spatial station network",
        "Show the XAI attention map",
    ],
    "DATA_QUERY": [
        "Explain why the model made this prediction",
        "Show feature importance rankings",
        "Plot temperature vs humidity correlation",
        "What is the current model RMSE?",
    ],
    "PREDICTION_REQUEST": [
        "Explain this prediction (XAI)",
        "Show actual vs predicted scatter chart",
        "What sensors influence this forecast most?",
        "Get live station reading for comparison",
    ],
    "IOT_STATUS": [
        "Run a GNN spatial prediction on current readings",
        "Compare live reading with historical dataset average",
        "Show the spatial station network graph",
        "What is the humidity trend over the last hour?",
    ],
    "XAI_REQUEST": [
        "Plot the XAI attention map",
        "Which feature matters most for temperature?",
        "Show me actual vs predicted performance",
        "What would happen if humidity increases?",
    ],
    "HISTORY_QUERY": [
        "Start a new chat session",
        "Show all conversations",
        "What was the last prediction I asked about?",
        "Delete this conversation",
    ],
    "GENERAL_CHAT": [
        "What data do you have access to?",
        "Show me the active model metrics",
        "Get live sensor data",
        "What sensors does the weather station monitor?",
    ],
}

_MODE_SPECIFIC: Dict[str, List[str]] = {
    "historical data mode": [
        "Upload a new CSV dataset",
        "Compare model versions",
        "Retrain with the latest dataset",
    ],
    "live station mode": [
        "Connect Raspberry Pi via serial",
        "Run GNN prediction on live data",
        "Show spatial node graph",
    ],
    "prime": [
        "Fuse historical and live data predictions",
        "Compare CSV model vs GNN spatial prediction",
        "Show combined weather intelligence report",
    ],
}


class RecommendationEngine:
    """
    Suggests the next 3 most relevant follow-up queries based on:
    - Current NLP intent
    - System mode (historical / live / prime)
    - Available data context
    """

    @staticmethod
    def get_recommendations(
        intent: str,
        system_mode: str = "prime",
        context: Optional[Dict[str, Any]] = None,
        n: int = 3,
    ) -> List[str]:
        pool = list(_SUGGESTIONS.get(intent, _SUGGESTIONS["GENERAL_CHAT"]))

        # Add mode-specific suggestions
        mode_key = system_mode.lower()
        pool += _MODE_SPECIFIC.get(mode_key, [])

        # Shuffle for variety and return top-n
        random.shuffle(pool)
        return pool[:n]

    @staticmethod
    def get_data_driven_recommendations(
        has_dataset: bool,
        has_active_model: bool,
        iot_connected: bool,
    ) -> List[str]:
        """Context-aware baseline recommendations based on current system state."""
        recs = []
        if not has_dataset:
            recs.append("Upload a CSV weather dataset to enable historical analysis")
        if has_dataset and not has_active_model:
            recs.append("Train a model on your uploaded dataset")
        if has_active_model:
            recs.append("Plot feature importance for the active model")
            recs.append("Show actual vs predicted scatter chart")
        if not iot_connected:
            recs.append("Connect your Raspberry Pi weather station for live data")
        else:
            recs.append("Run GNN spatial prediction on live sensor data")
        return recs[:3]
