"""
History Service — Conversation history management.
Extracted from conversation_service for single responsibility.
Supports search, pagination, and session archiving.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
import models
from utils.logger import logger


class HistoryService:

    @staticmethod
    def list_sessions(db: Session, skip: int = 0, limit: int = 50) -> List[models.ConversationSession]:
        return (
            db.query(models.ConversationSession)
            .order_by(models.ConversationSession.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_session_messages(db: Session, session_id: str) -> List[models.Message]:
        return (
            db.query(models.Message)
            .filter(models.Message.session_id == session_id)
            .order_by(models.Message.timestamp)
            .all()
        )

    @staticmethod
    def search_messages(db: Session, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Full-text search across all messages (case-insensitive)."""
        results = (
            db.query(models.Message)
            .filter(models.Message.content.ilike(f"%{query}%"))
            .order_by(models.Message.timestamp.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "message_id": m.id,
                "session_id": m.session_id,
                "role": m.role,
                "snippet": m.content[:200],
                "timestamp": m.timestamp.isoformat(),
            }
            for m in results
        ]

    @staticmethod
    def delete_session(db: Session, session_id: str) -> bool:
        session = db.query(models.ConversationSession).filter(
            models.ConversationSession.id == session_id
        ).first()
        if not session:
            return False
        db.query(models.Message).filter(models.Message.session_id == session_id).delete()
        db.delete(session)
        db.commit()
        logger.info(f"Deleted session {session_id} and its messages.")
        return True

    @staticmethod
    def get_stats(db: Session) -> Dict[str, Any]:
        total_sessions = db.query(models.ConversationSession).count()
        total_messages = db.query(models.Message).count()
        user_messages = db.query(models.Message).filter(models.Message.role == "user").count()
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "user_messages": user_messages,
            "bot_messages": total_messages - user_messages,
        }

    @staticmethod
    def auto_title_session(db: Session, session_id: str, first_message: str) -> None:
        """Set the session title from the first user message (max 60 chars)."""
        session = db.query(models.ConversationSession).filter(
            models.ConversationSession.id == session_id
        ).first()
        if session and session.title in ("New Conversation", "New Chat", ""):
            session.title = first_message[:60]
            db.commit()
