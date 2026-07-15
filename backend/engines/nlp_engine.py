"""
NLP Engine — Full intent classification and entity extraction.
Uses fast regex + keyword maps for low-latency Edge inference.
"""
import re
from typing import Any, Dict, List, Optional


class IntentType:
    GREETING = "GREETING"
    GRAPH_REQUEST = "GRAPH_REQUEST"
    DATA_QUERY = "DATA_QUERY"
    PREDICTION_REQUEST = "PREDICTION_REQUEST"
    IOT_STATUS = "IOT_STATUS"
    XAI_REQUEST = "XAI_REQUEST"
    HISTORY_QUERY = "HISTORY_QUERY"
    GENERAL_CHAT = "GENERAL_CHAT"


class EntityType:
    SENSOR = "SENSOR"
    TIME_RANGE = "TIME_RANGE"
    LOCATION = "LOCATION"
    METRIC = "METRIC"


# ── Keyword Maps ──────────────────────────────────────────────────────────────
_GREETING_WORDS = {"hi", "hello", "hey", "howdy", "good morning", "good evening", "good afternoon", "greetings"}

_GRAPH_KEYWORDS = {"plot", "graph", "chart", "visualize", "draw", "show me", "display", "heatmap", "scatter", "histogram", "trend"}

_PREDICTION_KEYWORDS = {"predict", "forecast", "tomorrow", "next hour", "future", "will it", "estimate", "projection"}

_IOT_KEYWORDS = {"live", "sensor", "station", "raspberry", "pi", "real-time", "realtime", "current reading", "telemetry", "connected"}

_XAI_KEYWORDS = {"why", "explain", "explainability", "feature importance", "shap", "reason", "because", "how did", "what caused"}

_HISTORY_KEYWORDS = {"history", "previous", "past", "earlier", "last session", "what did", "what did we", "conversation"}

_DATA_KEYWORDS = {"temperature", "humidity", "pressure", "wind", "rainfall", "data", "rmse", "accuracy", "r2", "dataset", "model", "train", "feature"}

_SENSOR_ENTITIES = {
    "temperature": ["temp", "temperature", "heat", "thermal"],
    "humidity": ["humidity", "humid", "moisture"],
    "pressure": ["pressure", "baro", "hpa"],
    "wind_speed": ["wind", "speed", "breeze"],
    "rainfall": ["rain", "rainfall", "precipitation"],
    "light_intensity": ["light", "lux", "solar", "irradiance"],
}

_TIME_PATTERNS = [
    (r"\blast\s+(\d+)\s+(hours?|days?|weeks?)\b", "relative"),
    (r"\b(today|yesterday|this week|this month)\b", "named"),
    (r"\b(\d{4}-\d{2}-\d{2})\b", "absolute"),
]

_METRIC_ENTITIES = {"rmse", "mae", "r2", "accuracy", "loss", "mse", "precision", "recall"}


class NLPEngine:
    """
    Full NLP pipeline: intent classification → entity extraction.
    Returns a structured NLP result dict used by the conversation service.
    """

    @staticmethod
    def classify_intent(message: str) -> str:
        msg = message.lower().strip()

        # 1. Greeting (exact or prefix)
        if msg in _GREETING_WORDS or any(msg.startswith(g + " ") for g in _GREETING_WORDS):
            return IntentType.GREETING

        # 2. XAI — check before general chat
        if any(kw in msg for kw in _XAI_KEYWORDS):
            return IntentType.XAI_REQUEST

        # 3. Graph / visualization
        if any(kw in msg for kw in _GRAPH_KEYWORDS):
            return IntentType.GRAPH_REQUEST

        # 4. Prediction / forecast
        if any(kw in msg for kw in _PREDICTION_KEYWORDS):
            return IntentType.PREDICTION_REQUEST

        # 5. IoT / live station
        if any(kw in msg for kw in _IOT_KEYWORDS):
            return IntentType.IOT_STATUS

        # 6. History
        if any(kw in msg for kw in _HISTORY_KEYWORDS):
            return IntentType.HISTORY_QUERY

        # 7. Data / sensor query
        if any(kw in msg for kw in _DATA_KEYWORDS):
            return IntentType.DATA_QUERY

        return IntentType.GENERAL_CHAT

    @staticmethod
    def extract_entities(message: str) -> Dict[str, Any]:
        msg = message.lower()
        entities: Dict[str, Any] = {"sensors": [], "time_range": None, "metrics": [], "location": None}

        # Sensors
        for sensor, aliases in _SENSOR_ENTITIES.items():
            if any(alias in msg for alias in aliases):
                entities["sensors"].append(sensor)

        # Metrics
        for m in _METRIC_ENTITIES:
            if m in msg:
                entities["metrics"].append(m)

        # Time range
        for pattern, kind in _TIME_PATTERNS:
            match = re.search(pattern, msg)
            if match:
                entities["time_range"] = {"kind": kind, "value": match.group(0)}
                break

        # Location (simple city detection — for refusal)
        cities = re.findall(r"\bin\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b", message)
        if cities:
            entities["location"] = cities[0]

        return entities

    @staticmethod
    def process(message: str) -> Dict[str, Any]:
        intent = NLPEngine.classify_intent(message)
        entities = NLPEngine.extract_entities(message)
        return {
            "intent": intent,
            "entities": entities,
            "raw": message,
        }
