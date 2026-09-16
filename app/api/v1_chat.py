from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_rag import rag_service

router = APIRouter(prefix="/api/v1", tags=["Chat & RAG"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Conversational RAG endpoint with Redis memory and automatic interview booking detection.
    """
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")

    result = rag_service.generate_response(
        session_id=payload.session_id,
        user_query=payload.message,
        db=db
    )
    return result