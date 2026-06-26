"""Document ingestion + RAG routes, backed by the external R2R server (Gemini).

Upload a memory document -> R2R chunks + embeds it (Gemini embeddings, pgvector)
-> optionally runs Gemini KG extraction into the graph. All generation/embedding
happens server-side in R2R; this router is a thin async proxy.
"""

import json
from typing import Any, Optional

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ...services import R2RService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


async def get_r2r_service():
    async with R2RService() as service:
        yield service


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    extract_entities: bool = Form(True),
    r2r_service: R2RService = Depends(get_r2r_service),
):
    """Ingest a document and (optionally) run Gemini KG extraction."""
    try:
        doc_metadata = json.loads(metadata) if metadata else {}
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid metadata JSON: {e}")

    try:
        ingest = await r2r_service.ingest_document(file=file, metadata=doc_metadata)
        document_id = ingest["document_id"]

        entities: dict[str, Any] = {"total_count": 0, "entities": []}
        if extract_entities and document_id:
            await r2r_service.extract_graph(document_id)
            entities = await r2r_service.get_document_entities(document_id)

        return {
            "status": "success",
            "document_id": document_id,
            "filename": file.filename,
            "entities_extracted": entities.get("total_count", 0),
            "entities": entities.get("entities", [])[:10],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Document upload failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_documents(
    limit: int = 100,
    offset: int = 0,
    r2r_service: R2RService = Depends(get_r2r_service),
):
    """List ingested documents."""
    try:
        docs = await r2r_service.list_documents(limit=limit, offset=offset)
        return {"count": len(docs), "documents": docs}
    except Exception as e:
        logger.error("Failed to list documents", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    include_chunks: bool = False,
    r2r_service: R2RService = Depends(get_r2r_service),
):
    """Get document status/metadata, optionally with its chunks."""
    try:
        response: dict[str, Any] = await r2r_service.get_document_status(document_id)
        if include_chunks:
            chunks = await r2r_service.get_document_chunks(document_id)
            response["chunks"] = chunks
            response["chunk_count"] = len(chunks)
        return response
    except Exception as e:
        logger.error("Failed to get document", error=str(e), document_id=document_id)
        raise HTTPException(status_code=404, detail="Document not found")


@router.get("/{document_id}/entities")
async def get_document_entities(
    document_id: str,
    r2r_service: R2RService = Depends(get_r2r_service),
):
    """Get entities extracted from a document (Gemini KG extraction)."""
    try:
        return await r2r_service.get_document_entities(document_id)
    except Exception as e:
        logger.error("Failed to get document entities", error=str(e), document_id=document_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/relationships")
async def get_document_relationships(
    document_id: str,
    r2r_service: R2RService = Depends(get_r2r_service),
):
    """Get relationships extracted from a document."""
    try:
        rels = await r2r_service.get_document_relationships(document_id)
        return {"document_id": document_id, "count": len(rels), "relationships": rels}
    except Exception as e:
        logger.error("Failed to get relationships", error=str(e), document_id=document_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{document_id}/extract")
async def extract_document_graph(
    document_id: str,
    r2r_service: R2RService = Depends(get_r2r_service),
):
    """(Re)run Gemini KG extraction for an already-ingested document."""
    try:
        result = await r2r_service.extract_graph(document_id)
        entities = await r2r_service.get_document_entities(document_id)
        return {
            "status": "success",
            "document_id": document_id,
            "entities_extracted": entities.get("total_count", 0),
            "result": result,
        }
    except Exception as e:
        logger.error("Graph extraction failed", error=str(e), document_id=document_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    r2r_service: R2RService = Depends(get_r2r_service),
):
    """Delete a document and its derived chunks/graph data."""
    try:
        if await r2r_service.delete_document(document_id):
            return {"status": "success", "message": f"Document {document_id} deleted"}
        raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Document deletion failed", error=str(e), document_id=document_id)
        raise HTTPException(status_code=500, detail=str(e))
