<!--
Purpose: Short, actionable instructions for AI coding agents working on the BrainClone monorepo.
Keep this file concise (20-50 lines) and reference concrete files and patterns in the repo.
-->

# Copilot / AI agent guidance for BrainClone (brainclone-frontend)

Quick orientation
- Monorepo with two main parts: backend (FastAPI + Python) and frontend (Next.js + React).
- Backend entry: `backend/src/main.py`. Frontend entry: `frontend/app/page.tsx` (Next.js app).

Architecture & important flows
- Backend implements an async FastAPI app that wires core services in `lifespan` (see `backend/src/main.py`). Key services: `Neo4jService` (`backend/src/services/neo4j_service.py`), `VectorService` and `R2RService` (`backend/src/services/r2r_service.py`).
- Data flow: files uploaded -> R2R (ingest, chunking, embeddings, NER) -> embeddings stored in Postgres/pgvector and entities/edges saved to Neo4j. See top-level README and `backend/README.md` diagrams.
- API surface uses prefix `api_v1_prefix` from `backend/src/config.py` (default `/api/v1`). Common endpoints: `/documents/*`, `/graph/*`, `/search/*` (see `backend/src/api/routes/*`).

Developer workflows (concrete commands)
- Backend (uses the `uv` wrapper defined in `backend/README.md`):
  - Run dev server: `uv run uvicorn src.main:app --reload --port 8000`
  - Run tests: `uv run pytest`
  - Format: `uv run black src/` and `uv run ruff check --fix src/`
- Frontend (see `frontend/package.json`):
  - Dev: `pnpm dev` (or `npm run dev`) — Next runs on :3000 by default
  - Build: `pnpm build`; Start: `pnpm start`

Repo-specific patterns & conventions
- Service lifecycle: many services are async context managers and used via FastAPI dependencies, e.g. `async def get_r2r_service(): async with R2RService() as service: yield service` in `backend/src/api/routes/*`. Respect this pattern when adding endpoints.
- App-level graceful fallback: `backend/src/main.py` initializes services in `lifespan` and may set `app.state.neo4j_service = None` if connection fails; code must handle missing graph service gracefully.
- Config via pydantic_settings: `backend/src/config.py` loads `.env`. Prefer reading settings from `settings` object rather than environment directly.
- Logging: structured logging with `structlog` and configurable format via `settings.log_format`.

Integration notes (external services)
- R2R service: default base `http://localhost:7272`. See `backend/src/services/r2r_service.py` for client usage and health-check patterns.
- Neo4j and Postgres credentials live in `backend/src/config.py` (defaults present in code). Use `.env` in dev to override.
- Frontend calls backend via `NEXT_PUBLIC_API_URL` (see `frontend/lib/api.ts`); default `http://localhost:8000/api/v1`.

Small gotchas to watch for
- Ingestion typing: `backend/src/api/routes/documents.py` sometimes passes temp file paths to R2R ingestion. Verify `R2RService.ingest_document` signature before changing ingestion code (`backend/src/services/r2r_service.py`).
- Some API calls expect the vector service and neo4j to exist; routes often attempt to call them and raise 500s if missing. When adding features, prefer non-fatal fallbacks and clear logs.

Where to look for examples
- End-to-end upload + entity extraction: `backend/src/api/routes/documents.py` -> `backend/src/services/r2r_service.py`.
- Graph creation and traversal examples: `backend/src/api/routes/graph.py` and `backend/src/services/neo4j_service.py`.
- Frontend usage and API conventions: `frontend/lib/api.ts` (axios instance, auth token interceptor) and `frontend/stores/graphStore.ts` (zustand state patterns).

If you're updating behavior
- Run backend with `uv` and the frontend with `pnpm dev` and exercise the UI flows that call the changed endpoints.
- Keep changes small and use existing dependency patterns (async context managers for services, `app.state` for long-lived service instances).

Questions or incomplete areas
- If code touches ingestion boundaries, double-check whether `ingest_document` should accept a file path or an UploadFile; the repo contains both styles.

End of file
