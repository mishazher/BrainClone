"""R2R service for document processing and RAG operations.

Talks to an external R2R server (v3.x, image `sciphiai/r2r`) over its REST API
using plain httpx — no heavyweight `r2r` SDK dependency, so the backend isn't
coupled to R2R's internal package version. R2R itself is configured Gemini-only
(see `r2r-config/config.toml`): Gemini embeddings (gemini-embedding-001 @ 768d)
and Gemini completion/KG-extraction (gemini-2.5-flash), all via LiteLLM.

Verified endpoints (R2R v3):
  POST   /v3/documents                      ingest (multipart: file | raw_text)
  POST   /v3/documents/{id}/extract         run KG entity/relation extraction
  GET    /v3/documents/{id}/chunks          chunks (+ embeddings)
  GET    /v3/documents/{id}/entities        extracted entities
  GET    /v3/documents/{id}/relationships   extracted relationships
  GET    /v3/documents/{id}                 document metadata/status
  GET    /v3/documents                      list documents
  DELETE /v3/documents/{id}                 delete
  POST   /v3/retrieval/search               hybrid/semantic search
  POST   /v3/retrieval/rag                  RAG completion
  GET    /v3/health                         health
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import httpx
import structlog
from fastapi import UploadFile

from ..config import settings

logger = structlog.get_logger(__name__)


class R2RServiceError(Exception):
    """Base exception for R2R service errors."""


class R2RConnectionError(R2RServiceError):
    """Raised when connection to R2R fails."""


class R2RIngestionError(R2RServiceError):
    """Raised when document ingestion fails."""


class R2RService:
    """Async REST client for an external R2R server."""

    SUPPORTED_FORMATS = {"pdf", "docx", "txt", "html", "md", "csv", "json"}
    ENTITY_TYPES = ["Person", "Event", "Location"]

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.r2r_base_url).rstrip("/")
        headers = {"Accept": "application/json"}
        if settings.r2r_api_key:
            headers["Authorization"] = f"Bearer {settings.r2r_api_key}"
        # Generous timeout: KG extraction calls Gemini and can take a while.
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(120.0, connect=5.0),
            headers=headers,
        )
        logger.info("R2R service initialized", base_url=self.base_url)

    # -- low-level helpers ---------------------------------------------------

    async def _request(self, method: str, path: str, *, retries: int = 2, **kwargs) -> dict[str, Any]:
        """Issue a request with simple exponential backoff on transient errors."""
        last_exc: Exception | None = None
        for attempt in range(retries + 1):
            try:
                resp = await self._http.request(method, path, **kwargs)
                resp.raise_for_status()
                return resp.json()
            except (httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError) as exc:
                last_exc = exc
                if attempt == retries:
                    break
                await asyncio.sleep(2 ** attempt)
            except httpx.HTTPStatusError as exc:
                # Don't retry 4xx; surface the server's message.
                detail = exc.response.text[:300]
                raise R2RServiceError(f"R2R {method} {path} -> {exc.response.status_code}: {detail}") from exc
        raise R2RConnectionError(f"R2R {method} {path} failed: {last_exc}") from last_exc

    @staticmethod
    def _results(payload: dict[str, Any]) -> Any:
        """R2R wraps everything in a top-level `results` key."""
        return payload.get("results", payload)

    # -- health --------------------------------------------------------------

    async def health_check(self) -> dict[str, Any]:
        try:
            payload = await self._request("GET", "/v3/health", retries=0)
            return {"status": "healthy", "connected": True, "details": self._results(payload)}
        except Exception as e:  # noqa: BLE001 - health must never raise
            logger.warning("R2R health check failed", error=str(e))
            return {"status": "unavailable", "connected": False, "error": str(e), "fallback_mode": True}

    # -- ingestion -----------------------------------------------------------

    async def ingest_document(
        self,
        file: UploadFile,
        metadata: dict[str, Any] | None = None,
        ingestion_mode: str = "fast",
    ) -> dict[str, Any]:
        """Ingest an uploaded file: chunk + embed (Gemini) into R2R/pgvector."""
        ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else ""
        if ext not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported file format: {ext!r}. Supported: {', '.join(sorted(self.SUPPORTED_FORMATS))}"
            )

        content = await file.read()
        await file.seek(0)
        files = {"file": (file.filename, content, file.content_type or "application/octet-stream")}
        data: dict[str, Any] = {"ingestion_mode": ingestion_mode}
        if metadata:
            import json
            data["metadata"] = json.dumps(metadata)

        logger.info("Ingesting document", filename=file.filename, size=len(content))
        try:
            results = self._results(await self._request("POST", "/v3/documents", files=files, data=data))
        except R2RServiceError as e:
            raise R2RIngestionError(str(e)) from e

        return {
            "document_id": results.get("document_id"),
            "status": "ingested",
            "task_id": results.get("task_id"),
            "filename": file.filename,
        }

    async def extract_graph(self, document_id: str, run_with_orchestration: bool = False) -> dict[str, Any]:
        """Run Gemini-backed KG extraction (entities + relationships) for a document."""
        results = self._results(
            await self._request(
                "POST",
                f"/v3/documents/{document_id}/extract",
                json={"run_with_orchestration": run_with_orchestration},
            )
        )
        logger.info("Graph extraction complete", document_id=document_id)
        return results

    # -- retrieval -----------------------------------------------------------

    async def get_document_chunks(self, document_id: str, limit: int = 100) -> list[dict[str, Any]]:
        payload = await self._request(
            "GET", f"/v3/documents/{document_id}/chunks", params={"limit": limit}
        )
        return self._results(payload) or []

    async def get_document_entities(
        self, document_id: str, limit: int = 100
    ) -> dict[str, Any]:
        payload = await self._request(
            "GET", f"/v3/documents/{document_id}/entities", params={"limit": limit}
        )
        entities = self._results(payload) or []
        grouped: dict[str, list[dict[str, Any]]] = {t: [] for t in self.ENTITY_TYPES}
        flat = []
        for ent in entities:
            item = {
                "name": ent.get("name"),
                "category": ent.get("category"),
                "description": ent.get("description"),
            }
            flat.append(item)
            cat = ent.get("category")
            if cat in grouped:
                grouped[cat].append(item)
        return {
            "document_id": document_id,
            "entities": flat,
            "grouped": grouped,
            "total_count": len(flat),
        }

    async def get_document_relationships(
        self, document_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        payload = await self._request(
            "GET", f"/v3/documents/{document_id}/relationships", params={"limit": limit}
        )
        return self._results(payload) or []

    async def get_document_status(self, document_id: str) -> dict[str, Any]:
        results = self._results(await self._request("GET", f"/v3/documents/{document_id}"))
        return {
            "document_id": document_id,
            "status": results.get("ingestion_status") or results.get("status", "unknown"),
            "extraction_status": results.get("extraction_status"),
            "metadata": results.get("metadata", {}),
            "created_at": results.get("created_at"),
            "updated_at": results.get("updated_at"),
        }

    async def list_documents(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        payload = await self._request(
            "GET", "/v3/documents", params={"limit": limit, "offset": offset}
        )
        docs = self._results(payload) or []
        return [
            {
                "document_id": d.get("id"),
                "title": d.get("title"),
                "ingestion_status": d.get("ingestion_status"),
                "extraction_status": d.get("extraction_status"),
                "created_at": d.get("created_at"),
                "metadata": d.get("metadata", {}),
            }
            for d in docs
        ]

    async def delete_document(self, document_id: str) -> bool:
        try:
            await self._request("DELETE", f"/v3/documents/{document_id}")
            logger.info("Document deleted", document_id=document_id)
            return True
        except R2RServiceError as e:
            logger.error("Failed to delete document", error=str(e), document_id=document_id)
            return False

    async def hybrid_search(
        self, query: str, filters: dict[str, Any] | None = None, limit: int = 20
    ) -> dict[str, Any]:
        """Hybrid (vector + full-text) search over ingested chunks."""
        body = {
            "query": query,
            "search_settings": {
                "use_hybrid_search": True,
                "use_semantic_search": True,
                "filters": filters or {},
                "limit": limit,
            },
        }
        results = self._results(await self._request("POST", "/v3/retrieval/search", json=body))
        chunks = (results or {}).get("chunk_search_results", []) if isinstance(results, dict) else []
        return {"results": chunks, "total": len(chunks), "query": query}

    async def rag_query(
        self, query: str, use_graph: bool = True, filters: dict[str, Any] | None = None
    ) -> str:
        """RAG answer grounded in ingested memories (generation on Gemini, server-side)."""
        body = {
            "query": query,
            "search_settings": {
                "use_hybrid_search": True,
                "filters": filters or {},
                "graph_search_settings": {"enabled": use_graph},
            },
        }
        results = self._results(await self._request("POST", "/v3/retrieval/rag", json=body))
        if isinstance(results, dict):
            # R2R returns either a generated_answer or an OpenAI-style completion.
            if results.get("generated_answer"):
                return results["generated_answer"]
            completion = results.get("completion", {})
            choices = completion.get("choices") if isinstance(completion, dict) else None
            if choices:
                return choices[0].get("message", {}).get("content", "")
        return ""

    # -- lifecycle -----------------------------------------------------------

    async def cleanup(self):
        await self._http.aclose()
        logger.info("R2R service cleaned up")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
