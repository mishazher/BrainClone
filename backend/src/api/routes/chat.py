"""Chatbot route — server-side Gemini call with knowledge-graph context.

Moved from the frontend Next.js `/api/chat` route so the Gemini API key and
prompt construction live on the backend. The Next.js route now proxies here.
"""

from datetime import datetime, timezone
from typing import Any, Optional

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...services.gemini_service import GeminiChatService, GeminiServiceError

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User's question")
    graph_data: Optional[dict[str, Any]] = Field(default=None, alias="graphData")
    chat_history: Optional[list[dict[str, Any]]] = Field(default=None, alias="chatHistory")

    model_config = {"populate_by_name": True}


class ChatResponse(BaseModel):
    success: bool
    response: str
    timestamp: str


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Answer a question using Gemini with the user's memory graph as context."""
    try:
        service = GeminiChatService()
        answer = await service.chat_with_context(
            question=request.message,
            graph_data=request.graph_data,
            chat_history=request.chat_history,
        )
        return ChatResponse(
            success=True,
            response=answer,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except GeminiServiceError as e:
        # User-actionable errors (quota/billing/overload) -> 503.
        logger.warning("Chat unavailable", error=str(e))
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:  # noqa: BLE001
        logger.error("Chat failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process chat message")
