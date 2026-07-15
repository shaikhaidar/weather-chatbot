"""
MCP Service Router — Central dispatcher that routes requests to the appropriate microservice.
This is the architectural heart of the weatherBOT system.

Routes based on 'service' field:
  - csv      → CSVService
  - graph    → GraphService
  - gnn      → GNNService
  - history  → HistoryService
  - iot      → IoTService
  - nlp      → NLPEngine
  - xai      → ExplainableAIEngine
  - research → ResearchEngine
  - model    → ModelManager
  - dataset  → DatasetManager
"""
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from utils.logger import logger


class MCPRouter:
    """
    Routes MCP tool calls to appropriate microservices.
    Each route is a standardized dict: {"service": str, "action": str, **kwargs}
    """

    @staticmethod
    def route(request: Dict[str, Any], db: Optional[Session] = None) -> Dict[str, Any]:
        service = request.get("service", "").lower()
        action = request.get("action", "").lower()
        params = request.get("params", {})

        logger.info(f"MCP Router: service={service}, action={action}")

        try:
            if service == "iot":
                return MCPRouter._route_iot(action, params)
            elif service == "gnn":
                return MCPRouter._route_gnn(action, params)
            elif service == "csv":
                return MCPRouter._route_csv(action, params)
            elif service == "graph":
                return MCPRouter._route_graph(action, params, db)
            elif service == "history":
                return MCPRouter._route_history(action, params, db)
            elif service == "nlp":
                return MCPRouter._route_nlp(action, params)
            elif service == "xai":
                return MCPRouter._route_xai(action, params, db)
            elif service == "research":
                return MCPRouter._route_research(action, params, db)
            elif service == "model":
                return MCPRouter._route_model(action, params, db)
            elif service == "dataset":
                return MCPRouter._route_dataset(action, params, db)
            else:
                return {"error": f"Unknown service: '{service}'", "available": MCPRouter.list_tools()}
        except Exception as e:
            logger.error(f"MCP Router error [{service}/{action}]: {e}")
            return {"error": str(e), "service": service, "action": action}

    # ── IoT ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _route_iot(action: str, params: Dict) -> Dict:
        from services.iot_service import IoTService
        if action == "reading":
            return IoTService.get_reading()
        elif action == "multi_node":
            n = params.get("n_nodes", 3)
            return {"nodes": IoTService.get_multi_node_readings(n)}
        elif action == "status":
            return IoTService.get_status()
        elif action == "connect_serial":
            return IoTService.connect_serial(params.get("port", "COM3"), params.get("baud", 9600))
        elif action == "connect_mqtt":
            return IoTService.connect_mqtt(params.get("host", "192.168.1.100"), params.get("port", 1883))
        elif action == "configure_simulator":
            IoTService.configure_simulator(params.get("noise_level", 0.5))
            return {"status": "ok", "noise_level": params.get("noise_level", 0.5)}
        return {"error": f"Unknown IoT action: {action}"}

    # ── GNN ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _route_gnn(action: str, params: Dict) -> Dict:
        from services.gnn_service import GNNService
        from services.iot_service import IoTService
        if action == "predict_live":
            n = params.get("n_nodes", 3)
            readings = IoTService.get_multi_node_readings(n)
            nodes = GNNService.build_nodes_from_iot(readings)
            edges = GNNService.build_edges(len(nodes))
            result = GNNService.predict(nodes, edges)
            result["readings"] = readings
            return result
        elif action == "predict":
            nodes = params.get("nodes", [[24.0, 5.0, 60.0], [23.5, 4.8, 62.0], [24.2, 5.2, 58.0]])
            edges = params.get("edges", [[0, 1], [1, 2], [1, 0], [2, 1]])
            return GNNService.predict(nodes, edges)
        return {"error": f"Unknown GNN action: {action}"}

    # ── CSV ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _route_csv(action: str, params: Dict) -> Dict:
        from services.csv_service import CSVService
        import os, glob
        # Find latest CSV
        upload_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
        csvs = glob.glob(os.path.join(upload_dir, "*.csv")) if os.path.exists(upload_dir) else []
        filepath = params.get("filepath") or (csvs[-1] if csvs else None)
        if not filepath:
            return {"error": "No CSV file found. Upload a dataset first."}
        import pandas as pd
        df = pd.read_csv(filepath)
        if action == "profile":
            return CSVService.profile(df)
        elif action == "trend":
            col = params.get("column", df.select_dtypes(include="number").columns[0] if len(df.select_dtypes(include="number").columns) > 0 else "")
            return CSVService.generate_trend_chart(df, col)
        elif action == "correlation_heatmap":
            return CSVService.generate_correlation_heatmap(df)
        elif action == "distribution":
            col = params.get("column", df.columns[0])
            return CSVService.generate_distribution_chart(df, col)
        return {"error": f"Unknown CSV action: {action}"}

    # ── Graph ─────────────────────────────────────────────────────────────────
    @staticmethod
    def _route_graph(action: str, params: Dict, db: Optional[Session]) -> Dict:
        from services.graph_service import GraphService
        from services.iot_service import IoTService
        if action == "feature_graph" and db:
            import models
            active = db.query(models.ModelVersion).filter(models.ModelVersion.is_active == 1).first()
            if not active or not active.feature_importances:
                return {"error": "No active model with feature importances found."}
            return GraphService.build_correlation_graph(active.feature_importances)
        elif action == "spatial_graph":
            n = params.get("n_nodes", 3)
            readings = IoTService.get_multi_node_readings(n)
            return GraphService.build_spatial_node_graph(readings)
        return {"error": f"Unknown Graph action: {action}"}

    # ── History ───────────────────────────────────────────────────────────────
    @staticmethod
    def _route_history(action: str, params: Dict, db: Optional[Session]) -> Dict:
        from services.history_service import HistoryService
        if not db:
            return {"error": "Database session required"}
        if action == "stats":
            return HistoryService.get_stats(db)
        elif action == "search":
            query = params.get("query", "")
            return {"results": HistoryService.search_messages(db, query)}
        elif action == "list_sessions":
            sessions = HistoryService.list_sessions(db)
            return {"sessions": [{"id": s.id, "title": s.title, "created_at": s.created_at.isoformat()} for s in sessions]}
        return {"error": f"Unknown History action: {action}"}

    # ── NLP ───────────────────────────────────────────────────────────────────
    @staticmethod
    def _route_nlp(action: str, params: Dict) -> Dict:
        from engines.nlp_engine import NLPEngine
        message = params.get("message", "")
        if action == "process":
            return NLPEngine.process(message)
        elif action == "classify":
            return {"intent": NLPEngine.classify_intent(message)}
        elif action == "entities":
            return NLPEngine.extract_entities(message)
        return {"error": f"Unknown NLP action: {action}"}

    # ── XAI ───────────────────────────────────────────────────────────────────
    @staticmethod
    def _route_xai(action: str, params: Dict, db: Optional[Session]) -> Dict:
        from engines.explainable_ai_engine import ExplainableAIEngine
        if db:
            import models
            active = db.query(models.ModelVersion).filter(models.ModelVersion.is_active == 1).first()
            fi = active.feature_importances if active else []
            pd_ = active.plot_data if active else {}
        else:
            fi, pd_ = [], {}
        if action == "explain":
            return ExplainableAIEngine.explain_feature_importances(fi or [])
        elif action == "attention_map":
            return ExplainableAIEngine.generate_attention_map(fi or [])
        elif action == "actual_vs_predicted":
            return ExplainableAIEngine.compare_actual_vs_predicted(pd_ or {})
        return {"error": f"Unknown XAI action: {action}"}

    # ── Research ──────────────────────────────────────────────────────────────
    @staticmethod
    def _route_research(action: str, params: Dict, db: Optional[Session]) -> Dict:
        from managers.research_engine import ResearchEngine
        import os, glob, pandas as pd
        upload_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
        csvs = glob.glob(os.path.join(upload_dir, "*.csv")) if os.path.exists(upload_dir) else []
        filepath = params.get("filepath") or (csvs[-1] if csvs else None)
        if not filepath:
            return {"error": "No dataset available for research analysis."}
        df = pd.read_csv(filepath)
        if action == "full_report":
            return ResearchEngine.full_report(df)
        elif action == "correlation":
            return ResearchEngine.correlation_analysis(df)
        elif action == "outliers":
            return ResearchEngine.detect_outliers(df)
        elif action == "trend":
            col = params.get("column", df.select_dtypes(include="number").columns[0])
            return ResearchEngine.trend_analysis(df, col)
        return {"error": f"Unknown Research action: {action}"}

    # ── Model ─────────────────────────────────────────────────────────────────
    @staticmethod
    def _route_model(action: str, params: Dict, db: Optional[Session]) -> Dict:
        from managers.model_manager import ModelManager
        if not db:
            return {"error": "Database required"}
        if action == "list":
            return {"versions": ModelManager.compare_versions(db)}
        elif action == "summary":
            return ModelManager.get_registry_summary(db)
        elif action == "promote":
            success = ModelManager.promote(db, params.get("model_id"))
            return {"status": "promoted" if success else "failed"}
        return {"error": f"Unknown Model action: {action}"}

    # ── Dataset ───────────────────────────────────────────────────────────────
    @staticmethod
    def _route_dataset(action: str, params: Dict, db: Optional[Session]) -> Dict:
        from managers.dataset_manager import DatasetManager
        if not db:
            return {"error": "Database required"}
        if action == "list":
            datasets = DatasetManager.list_all(db)
            return {"datasets": [{"id": d.id, "filename": d.filename, "status": d.status, "rows": d.total_rows} for d in datasets]}
        elif action == "active":
            ds = DatasetManager.get_active_dataset(db)
            return {"dataset": {"id": ds.id, "filename": ds.filename, "rows": ds.total_rows} if ds else None}
        return {"error": f"Unknown Dataset action: {action}"}

    @staticmethod
    def list_tools() -> Dict[str, Any]:
        """Return the complete capability manifest (used by MCP server)."""
        return {
            "iot": ["reading", "multi_node", "status", "connect_serial", "connect_mqtt", "configure_simulator"],
            "gnn": ["predict_live", "predict"],
            "csv": ["profile", "trend", "correlation_heatmap", "distribution"],
            "graph": ["feature_graph", "spatial_graph"],
            "history": ["stats", "search", "list_sessions"],
            "nlp": ["process", "classify", "entities"],
            "xai": ["explain", "attention_map", "actual_vs_predicted"],
            "research": ["full_report", "correlation", "outliers", "trend"],
            "model": ["list", "summary", "promote"],
            "dataset": ["list", "active"],
        }
