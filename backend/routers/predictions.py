"""
Predictions Router — /api/predictions/...
Exposes historical Redacted, live GNN, and recommendation endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Any, Dict
from database import get_db
import models

router = APIRouter()


@router.get("/live")
def get_live_prediction(n_nodes: int = Query(default=3, ge=1, le=10)) -> Dict[str, Any]:
    """Get IoT live reading + GNN spatial prediction for n weather station nodes."""
    from services.iot_service import IoTService
    from services.gnn_service import GNNService
    from services.nlg_service import NLGService

    readings = IoTService.get_multi_node_readings(n_nodes)
    nodes = GNNService.build_nodes_from_iot(readings)
    edges = GNNService.build_edges(len(nodes))
    gnn_result = GNNService.predict(nodes, edges)

    return {
        "type": "live_gnn",
        "station_readings": readings,
        "gnn_prediction": gnn_result,
        "summary": NLGService.describe_prediction(gnn_result),
        "iot_status": IoTService.get_status(),
    }


@router.get("/historical")
def get_historical_prediction(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get the active Redacted model metrics and predictions."""
    from managers.model_manager import ModelManager
    from engines.explainable_ai_engine import ExplainableAIEngine
    from services.nlg_service import NLGService

    active = ModelManager.get_active(db)
    if not active:
        return {"error": "No active model. Upload and train a dataset first."}

    xai = ExplainableAIEngine.explain_feature_importances(active.feature_importances or [])
    metrics_summary = NLGService.describe_model_metrics(
        {"rmse": active.rmse, "r2": active.accuracy, "mae": 0.0},
        active.version,
    )
    fi_summary = NLGService.describe_feature_importances(active.feature_importances or [])

    return {
        "type": "historical_redacted",
        "version": active.version,
        "metrics": {"rmse": active.rmse, "r2": active.accuracy, "training_time": active.training_time},
        "xai_explanations": xai.get("explanations", []),
        "plot_data": active.plot_data,
        "feature_importances": active.feature_importances,
        "summary": metrics_summary,
        "feature_summary": fi_summary,
    }


@router.get("/recommendations")
def get_recommendations(
    intent: str = Query(default="GENERAL_CHAT"),
    system_mode: str = Query(default="prime"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get contextual follow-up query recommendations."""
    from engines.recommendation_engine import RecommendationEngine
    from managers.dataset_manager import DatasetManager
    from managers.model_manager import ModelManager
    from services.iot_service import IoTService

    has_dataset = DatasetManager.list_all(db) != []
    has_active_model = ModelManager.get_active(db) is not None
    iot_status = IoTService.get_status()
    iot_connected = iot_status.get("connected", False)

    suggestions = RecommendationEngine.get_recommendations(intent, system_mode)
    data_driven = RecommendationEngine.get_data_driven_recommendations(
        has_dataset, has_active_model, iot_connected
    )

    return {
        "intent_based": suggestions,
        "context_based": data_driven,
        "system_state": {
            "has_dataset": has_dataset,
            "has_active_model": has_active_model,
            "iot_connected": iot_connected,
            "iot_source": iot_status.get("source", "simulator"),
        },
    }


@router.get("/xai")
def get_xai(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get Explainable AI breakdown for the active model."""
    from engines.explainable_ai_engine import ExplainableAIEngine
    from managers.model_manager import ModelManager

    active = ModelManager.get_active(db)
    if not active:
        return {"error": "No active model found."}

    xai = ExplainableAIEngine.explain_feature_importances(active.feature_importances or [])
    attention_map = ExplainableAIEngine.generate_attention_map(active.feature_importances or [])
    scatter = ExplainableAIEngine.compare_actual_vs_predicted(active.plot_data or {})

    return {
        "explanations": xai,
        "attention_map": attention_map,
        "scatter_chart": scatter,
        "model_version": active.version,
    }
