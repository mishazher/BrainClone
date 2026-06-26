"""Server-side Gemini chat service.

Ported from the frontend `lib/gemini.ts` `chatWithContext` so the Gemini API key
and prompt construction live on the backend instead of in the Next.js layer.
Answers a user question using the knowledge-graph as lightweight context.
"""

import asyncio
import json
import re
from typing import Any

import google.generativeai as genai
import structlog

from ..config import settings

logger = structlog.get_logger(__name__)


class GeminiServiceError(Exception):
    """Raised when the Gemini chat call fails in a non-retryable way."""


# Substrings that mean "retrying cannot help" — billing/credits/disabled.
_HARD_LIMIT_MARKERS = ("depleted", "billing", "prepayment", "service_disabled")
# Substrings that indicate a transient overload / rate-limit worth retrying.
_TRANSIENT_MARKERS = ("503", "429", "high demand", "overloaded", "rate limit")


class GeminiChatService:
    """Conversational Gemini calls with graph context (server-side)."""

    def __init__(self) -> None:
        if not settings.gemini_api_key:
            logger.warning("GEMINI_API_KEY is not set; chat will fail until configured")
        else:
            genai.configure(api_key=settings.gemini_api_key)
        self._model_name = settings.gemini_chat_model

    async def _generate_with_retry(self, prompt: str, max_retries: int = 4) -> str:
        """Call Gemini, retrying transient overload/rate-limit with exp backoff."""
        last_error: Exception | None = None
        model = genai.GenerativeModel(self._model_name)
        for attempt in range(max_retries + 1):
            try:
                # SDK call is sync; run off the event loop.
                resp = await asyncio.to_thread(model.generate_content, prompt)
                return resp.text
            except Exception as error:  # noqa: BLE001 - classify below
                last_error = error
                msg = str(error).lower()
                hard_limit = any(m in msg for m in _HARD_LIMIT_MARKERS)
                transient = not hard_limit and any(m in msg for m in _TRANSIENT_MARKERS)
                if not transient or attempt == max_retries:
                    break
                delay = 0.5 * (2 ** attempt)  # 0.5s, 1s, 2s, 4s
                logger.warning(
                    "Gemini transient error, retrying",
                    attempt=attempt + 1,
                    delay=delay,
                )
                await asyncio.sleep(delay)
        raise last_error if last_error else GeminiServiceError("Unknown Gemini error")

    async def chat_with_context(
        self,
        question: str,
        graph_data: dict[str, Any] | None = None,
        chat_history: list[dict[str, Any]] | None = None,
    ) -> str:
        """Answer `question` using graph node/link context (mirrors the old FE prompt)."""
        graph_data = graph_data or {}
        nodes = graph_data.get("nodes") or []
        links = graph_data.get("links") or []

        sample_nodes = [
            {"name": n.get("name"), "type": n.get("type", "concept")}
            for n in nodes[:10]
        ]

        prompt = f"""You are a helpful AI assistant with access to the user's memory database.

User's question: "{question}"

Memory database contains:
- {len(nodes)} nodes (concepts, people, places, events)
- {len(links)} connections between them
- Sample nodes: {json.dumps(sample_nodes)}

Use this memory data to provide a helpful, contextual response. Reference relevant memories when appropriate:"""

        try:
            text = await self._generate_with_retry(prompt)
        except Exception as error:  # noqa: BLE001 - map to friendly messages
            msg = str(error).lower()
            logger.error("Gemini chat failed", error=str(error))
            if any(m in msg for m in ("depleted", "billing", "prepayment")):
                raise GeminiServiceError(
                    "Gemini billing credits are depleted. Add credits in Google AI Studio "
                    "to re-enable AI features."
                ) from error
            if "429" in msg:
                raise GeminiServiceError(
                    "API quota exceeded. Please wait a moment and try again."
                ) from error
            if any(m in msg for m in ("503", "high demand", "overloaded")):
                raise GeminiServiceError(
                    "The AI model is temporarily overloaded. Please try again in a few seconds."
                ) from error
            raise GeminiServiceError("Failed to process chat message") from error

        # Clean up markdown formatting (same transforms as the old FE service).
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)   # **bold**
        text = re.sub(r"\*(.*?)\*", r"\1", text)        # *italic*
        text = re.sub(r"^\* ", "• ", text, flags=re.MULTILINE)  # * bullets
        return text
