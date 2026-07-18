from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import get_db
from services.conversation_service import ConversationService
from services.history_service import HistoryService
from engines.recommendation_engine import RecommendationEngine
from engines.nlp_engine import NLPEngine
from typing import List, Dict, Any

router = APIRouter()


@router.post("/sessions", response_model=schemas.ConversationSessionResponse)
def create_session(session: schemas.ConversationSessionBase, db: Session = Depends(get_db)):
    return ConversationService.create_session(db, title=session.title)


@router.get("/sessions", response_model=List[schemas.ConversationSessionResponse])
def get_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return HistoryService.list_sessions(db, skip, limit)


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    success = HistoryService.delete_session(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted", "session_id": session_id}


@router.delete("/sessions")
def delete_all_sessions(db: Session = Depends(get_db)):
    count = HistoryService.delete_all_sessions(db)
    return {"status": "deleted_all", "count": count}


@router.post("/sessions/{session_id}/message")
def send_message(session_id: str, message: schemas.MessageCreate, db: Session = Depends(get_db)):
    session = db.query(models.ConversationSession).filter(models.ConversationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Auto-title session from first message
    HistoryService.auto_title_session(db, session_id, message.content)

    # Generate response via conversation service
    response = ConversationService.generate_response(
        db, session_id, message.content, message.is_online
    )

    # Enrich response with recommendations and XAI via NLP intent
    nlp_result = NLPEngine.process(message.content)
    intent = nlp_result.get("intent", "GENERAL_CHAT")
    recommendations = RecommendationEngine.get_recommendations(intent)

    response["recommendations"] = recommendations
    response["intent"] = intent
    response["entities"] = nlp_result.get("entities", {})

    return response


@router.get("/sessions/{session_id}/messages", response_model=List[schemas.MessageResponse])
def get_messages(session_id: str, db: Session = Depends(get_db)):
    return HistoryService.get_session_messages(db, session_id)


@router.get("/sessions/{session_id}/xai")
def get_session_xai(session_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get XAI data for the active model — relevant to messages in this session."""
    from engines.explainable_ai_engine import ExplainableAIEngine
    from managers.model_manager import ModelManager
    active = ModelManager.get_active(db)
    if not active:
        return {"error": "No active model for XAI"}
    return {
        "explanations": ExplainableAIEngine.explain_feature_importances(active.feature_importances or []),
        "attention_map": ExplainableAIEngine.generate_attention_map(active.feature_importances or []),
        "actual_vs_predicted": ExplainableAIEngine.compare_actual_vs_predicted(active.plot_data or {}),
    }


@router.get("/stats")
def get_history_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Conversation history statistics."""
    return HistoryService.get_stats(db)


@router.get("/search")
def search_history(q: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Search across all messages."""
    results = HistoryService.search_messages(db, q)
    return {"query": q, "results": results, "count": len(results)}
