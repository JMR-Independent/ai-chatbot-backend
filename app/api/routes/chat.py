from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from datetime import datetime

from app.services.ai_service import AIService
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

ai_service = AIService()


class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    timestamp: datetime
    sources: List[str] = []


@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_message: ChatMessage,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Generate response using AI service
        response_data = await ai_service.generate_response(
            message=chat_message.message,
            user_id=chat_message.user_id,
            conversation_id=chat_message.conversation_id
        )
        
        return ChatResponse(
            response=response_data["response"],
            conversation_id=response_data["conversation_id"],
            timestamp=datetime.now(),
            sources=response_data.get("sources", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@router.get("/health")
async def chat_health():
    return {"status": "healthy", "service": "chat"}


@router.post("/feedback")
async def submit_feedback(
    conversation_id: str,
    rating: int,
    feedback: Optional[str] = None
):
    # Store feedback for future improvements
    return {"message": "Feedback received", "conversation_id": conversation_id}