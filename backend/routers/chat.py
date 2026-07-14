from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import get_db
from services.conversation_service import ConversationService
from typing import List

router = APIRouter()

@router.post("/sessions", response_model=schemas.ConversationSessionResponse)
def create_session(session: schemas.ConversationSessionBase, db: Session = Depends(get_db)):
    return ConversationService.create_session(db, title=session.title)

@router.get("/sessions", response_model=List[schemas.ConversationSessionResponse])
def get_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.ConversationSession).order_by(models.ConversationSession.created_at.desc()).offset(skip).limit(limit).all()

@router.post("/sessions/{session_id}/message")
def send_message(session_id: str, message: schemas.MessageCreate, db: Session = Depends(get_db)):
    # Verify session exists
    session = db.query(models.ConversationSession).filter(models.ConversationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    response = ConversationService.generate_response(db, session_id, message.content, message.is_online, message.system_mode)
    return response

@router.get("/sessions/{session_id}/messages", response_model=List[schemas.MessageResponse])
def get_messages(session_id: str, db: Session = Depends(get_db)):
    return ConversationService.get_session_history(db, session_id)
