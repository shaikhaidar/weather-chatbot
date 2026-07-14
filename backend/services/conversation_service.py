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
            # Mode 1: Historical Data Mode (Only CSV/Redacted)
            # Mode 3: Prime Mode (Both)
            if mode in ["historical data mode", "prime"]:
                active_model = db.query(models.ModelVersion).filter(models.ModelVersion.is_active == 1).first()
                if active_model:
                    ml_context = f"\n[HISTORICAL CSV MODEL INFO]\nRMSE: {active_model.rmse}\nFeature Importances: {json.dumps(active_model.feature_importances)}\nSample Actual vs Predicted Data: {json.dumps(active_model.plot_data)}\n"

            # Mode 2: Live Station Mode (Only IoT/GNN)
            # Mode 3: Prime Mode (Both)
            if mode in ["live station mode", "prime"]:
                if is_online: # Simulating Edge IoT connection
                    # Mock local sensor data
                    nodes = [[24.2, 12, 60], [23.9, 14, 62], [24.5, 10, 58]]
                    edges = [[0, 1], [1, 2]]
                    
                    # Execute PyTorch GNN
                    from services.ml_service import SpatialWeatherGNN
                    gnn_resp = SpatialWeatherGNN.gnn_prediction(nodes, edges)
                    
                    live_context = f"\n[LIVE EDGE STATION DATA]\nNode 1 (Temp/Wind/Hum): {nodes[0]}\nNode 2: {nodes[1]}\nNode 3: {nodes[2]}\n"
                    if gnn_resp.get("status") == "success":
                        gnn_result = f"[GNN SPATIAL PREDICTION (PyTorch)]: The Graph Neural Network predicts a spatial temperature delta of {gnn_resp['spatial_predictions']} across the nodes.\n"
                else:
                    live_context = "\n[LIVE EDGE STATION DATA]\nStations Disconnected. No live telemetry available.\n"
            
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
            }, timeout=30)
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
