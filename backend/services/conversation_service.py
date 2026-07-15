import uuid
from sqlalchemy.orm import Session
import models, schemas
import json
import requests
import traceback
import time
from utils.logger import logger
from services.decision_engine import DecisionEngine, IntentType

class ConversationService:
    """
    Handles conversation logic, history grouping, and friend/research modes.
    MCP-ready for swapping LLM providers.
    """
    
    @staticmethod
    def create_session(db: Session, title: str = "New Conversation") -> models.ConversationSession:
        session_id = str(uuid.uuid4())
        db_session = models.ConversationSession(id=session_id, title=title)
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        return db_session

    @staticmethod
    def add_message(db: Session, session_id: str, role: str, content: str, graphs: dict = None) -> models.Message:
        db_message = models.Message(
            session_id=session_id,
            role=role,
            content=content,
            graphs=graphs
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message

    @staticmethod
    def get_session_history(db: Session, session_id: str):
        return db.query(models.Message).filter(models.Message.session_id == session_id).order_by(models.Message.timestamp).all()

    @staticmethod
    def generate_response(db: Session, session_id: str, user_message: str, is_online: bool = False, system_mode: str = "Prime") -> dict:
        """
        Calls local Llama 3.1 8b via Ollama API.
        Strictly enforces that the bot only knows about local weather station data and ML predictions.
        Now respects Tri-Mode architecture (Historical, Live Station, Prime).
        """
        # Save user message
        ConversationService.add_message(db, session_id, role="user", content=user_message)
        
        # 1. Determine Intent via Decision Engine
        intent = DecisionEngine.determine_intent(user_message)
        logger.info(f"Processing message in '{system_mode}' | Intent: {intent} | Message: '{user_message}'")
        
        mode = system_mode.lower()
            
        # Context building based on Tri-Mode
        live_context = ""
        gnn_result = ""
        ml_context = ""
        
        # If it's a simple greeting, we skip loading heavy ML data to save Edge inference tokens
        if intent != IntentType.GREETING:
            # Fetch active model and parent dataset
            active_model = db.query(models.ModelVersion).filter(models.ModelVersion.is_active == 1).first()
            parent_ds = db.query(models.Dataset).filter(models.Dataset.id == active_model.dataset_id).first() if active_model else db.query(models.Dataset).order_by(models.Dataset.id.desc()).first()

            # Date Query Searching logic for uploaded CSV datasets
            date_record_context = ""
            active_df = None
            if parent_ds:
                try:
                    # Check if dataset CSV file can be read or parsed
                    import os, pandas as pd
                    # Look for file in root or backend dataset directory
                    possible_paths = [parent_ds.filename, f"backend/{parent_ds.filename}", f"backend/services/{parent_ds.filename}"]
                    for p in possible_paths:
                        if os.path.exists(p):
                            active_df = pd.read_csv(p)
                            break
                            
                    if active_df is not None:
                        # Search date columns
                        date_cols = [c for c in active_df.columns if 'date' in c.lower() or 'time' in c.lower()]
                        if date_cols:
                            active_df['parsed_date'] = pd.to_datetime(active_df[date_cols[0]], format='mixed', dayfirst=True, errors='coerce')
                            
                            # Date keyword search & multi-feature forecasting
                            import re
                            msg_lower = user_message.lower()
                            matched_rows = None
                            months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
                            short_months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
                            
                            day_match = re.search(r'\b(\d{1,2})(st|nd|rd|th)?\b', msg_lower)
                            month_found = None
                            month_idx = None
                            for idx_m, m in enumerate(months):
                                if m in msg_lower or short_months[idx_m] in msg_lower:
                                    month_found = m
                                    month_idx = idx_m + 1
                                    break
                                    
                            if day_match and month_idx:
                                day_num = int(day_match.group(1))
                                matched_rows = active_df[(active_df['parsed_date'].dt.day == day_num) & (active_df['parsed_date'].dt.month == month_idx)]
                            
                                if matched_rows is not None and not matched_rows.empty:
                                    sample = matched_rows.iloc[0].drop(labels=['parsed_date'], errors='ignore').to_dict()
                                    date_record_context = f"\n[EXACT HISTORICAL CSV DATE RECORD FOUND FOR QUERY]\n{json.dumps(sample, default=str)}\n"
                                else:
                                    # Future / Target Date Multi-Feature Forecasting Engine
                                    from services.ml_service import MLService
                                    forecast_res = MLService.predict_weather_for_date(active_df, day_num, month_idx)
                                    if forecast_res.get("status") == "success":
                                        date_record_context = (
                                            f"\n[PREDICTED MULTI-FEATURE FORECAST FOR REQUESTED TARGET DATE ({day_num:02d}/{month_idx:02d})]\n"
                                            f"The ML forecasting model trained on historical data projects the following predicted weather features for target date {day_num:02d}/{month_idx:02d}:\n"
                                            f"{json.dumps(forecast_res['forecasted_features'], indent=2)}\n"
                                        )
                except Exception as ex:
                    logger.warning(f"Date lookup error: {ex}")

            # Mode 1: Historical Data Mode (Only CSV/Redacted)
            # Mode 3: Prime Mode (Both)
            if mode in ["historical data mode", "prime"]:
                if active_model:
                    ds_info = f"Filename: {parent_ds.filename} | Time Span: {parent_ds.time_span} | Total Rows: {parent_ds.total_rows} | Sensors: {', '.join(parent_ds.detected_sensors or [])}" if parent_ds else "N/A"
                    ml_context = (
                        f"\n[HISTORICAL CSV MODEL INFO]\n"
                        f"Active Model Version: {active_model.version}\n"
                        f"Dataset Context: {ds_info}\n"
                        f"Model Metrics: RMSE={active_model.rmse:.4f}, R2={active_model.accuracy:.4f}, Training Time={active_model.training_time:.2f}s\n"
                        f"Feature Importances: {json.dumps(active_model.feature_importances)}\n"
                        f"{date_record_context}\n"
                    )
                else:
                    if parent_ds:
                        ml_context = f"\n[HISTORICAL CSV MODEL INFO]\nDataset uploaded: '{parent_ds.filename}' ({parent_ds.total_rows} rows, Time Span: {parent_ds.time_span}). Status: {parent_ds.status}.\n{date_record_context}\n"
                    else:
                        ml_context = "\n[HISTORICAL CSV MODEL INFO]\nNo historical datasets have been uploaded yet.\n"

            # Mode 2: Live Station Mode (Only IoT/GNN)
            # Mode 3: Prime Mode (Both)
            if mode in ["live station mode", "prime"]:
                from services.gnn_service import GNNService
                from services.iot_service import IoTService
                
                # Check actual hardware status
                hw_connected = IoTService.is_hardware_connected() if hasattr(IoTService, 'is_hardware_connected') else False
                
                if hw_connected:
                    readings = IoTService.get_multi_node_readings() if hasattr(IoTService, 'get_multi_node_readings') else []
                    nodes = GNNService.build_nodes_from_iot(readings) if readings else [[24.0, 10.0, 60.0]]
                    edges = GNNService.build_edges(len(nodes))
                    gnn_resp = GNNService.predict(nodes, edges)
                    
                    live_context = f"\n[LIVE HARDWARE TELEMETRY - Status: CONNECTED (Serial/MQTT)]\n"
                    for idx, node in enumerate(nodes):
                        live_context += f"Node {idx + 1} (Temp/Wind/Hum): {node}\n"
                    if gnn_resp.get("status") == "success":
                        gnn_result = f"[GNN SPATIAL PREDICTION (PyTorch GCN)]: Spatial deltas across live nodes: {gnn_resp['spatial_predictions']}.\n"
                else:
                    live_context = "\n[LIVE HARDWARE TELEMETRY]\nPhysical Weather Station Nodes: DISCONNECTED. No live sensor board detected on Serial or MQTT ports.\n"
            
        # Prepare context from history
        history = ConversationService.get_session_history(db, session_id)
            
        prompt = f"You are weatherBOT, a highly restricted AI Weather Intelligence Platform operating on an isolated Edge Computer in '{system_mode}'.\n"
        if intent == IntentType.GREETING:
            prompt += "CRITICAL DIRECTIVE: The user is just greeting you. Respond politely and concisely in one sentence. Do not mention data or graphs.\n"
        else:
            prompt += f"{ml_context}{live_context}{gnn_result}\n"
        
        if mode == "historical data mode":
            prompt += "CRITICAL DIRECTIVE: You are in Historical Data Mode. You MUST ignore all live station data and ONLY answer based on the Historical CSV Model Info. Refuse any requests for live predictions.\n\n"
        elif mode == "live station mode":
            prompt += "CRITICAL DIRECTIVE: You are in Live Station Mode. You MUST ignore all historical CSV data and ONLY answer based on the Live Edge Station Data and GNN Spatial Prediction. Refuse any requests for historical CSV analysis.\n\n"
        else: # Prime
            prompt += "CRITICAL DIRECTIVE: You are in Prime Mode. You have access to BOTH Historical CSV data and Live Edge Station Data (GNN). Synthesize this information gracefully.\n\n"
            
        prompt += "CRITICAL DIRECTIVE: You are strictly isolated from the real-world internet. You ONLY have knowledge of the provided context. If the user asks about the weather in cities like 'New York', 'London', or anywhere else in the real world, you MUST refuse and state that you are an isolated Edge AI and only monitor local station data. NEVER hallucinate real-world internet data.\n\n"
        prompt += "If the user asks for a graph or chart, analyze the provided Model Info. Then output a valid JSON block enclosed exactly in ```json ... ``` tags containing a Plotly.js configuration with a `data` array and a `layout` object representing the data.\n\n"
        
        for msg in history[-10:]: # last 10 msgs context
            prompt += f"{msg.role}: {msg.content}\n"
            
        bot_response = "I encountered an error connecting to my local brain (Llama 3.1)."
        try:
            logger.info("Sending prompt to Ollama (Llama 3.1) for inference...")
            start_time = time.time()
            # Assuming Ollama is running on default port 11434
            res = requests.post("http://127.0.0.1:11434/api/generate", json={
                "model": "llama3.1:8b",
                "prompt": prompt,
                "stream": False
            }, timeout=90)
            inference_time = time.time() - start_time
            if res.status_code == 200:
                bot_response = res.json().get("response", bot_response)
                logger.info(f"Ollama inference completed successfully in {inference_time:.2f} seconds.")
            else:
                logger.error(f"Ollama API returned status code {res.status_code}")
        except Exception as e:
            logger.error(f"Error connecting to Ollama: {str(e)}")
            print("Error connecting to Ollama:", e)
        
        # Parse JSON Plotly config from Llama response if it exists
        graphs = None
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', bot_response, re.DOTALL)
        if json_match:
            try:
                graphs = json.loads(json_match.group(1))
                # Remove the JSON block from the text so the user only sees natural text + rendered chart
                bot_response = bot_response.replace(json_match.group(0), "").strip()
            except json.JSONDecodeError as e:
                print("Failed to parse Llama 3 JSON graph:", e)

        # Fallback to mock graph if Llama 3 fails but NLP detects a plot request and no graph was parsed
        if graphs is None and ("plot" in user_message.lower() or "graph" in user_message.lower()):
            graphs = {
                "data": [{"x": [1, 2, 3, 4], "y": [22, 24, 21, 25], "type": "scatter", "mode": "lines+markers", "marker": {"color": "blue"}}],
                "layout": {"title": "Temperature Trend (Mock Fallback)"}
            }
            if "I have generated the requested graph." not in bot_response:
                bot_response += "\n\nI have generated a fallback graph."

        # Save bot response
        saved_msg = ConversationService.add_message(db, session_id, role="assistant", content=bot_response, graphs=graphs)
        
        return {
            "content": saved_msg.content,
            "graphs": saved_msg.graphs,
            "mode": mode
        }
