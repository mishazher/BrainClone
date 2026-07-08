# 🚀 How to Run BrainClone Locally

## 📋 Prerequisites

- **Python 3.12+** (backend)
- **Node.js 18+** and **pnpm** (frontend)
- **Docker** (optional — only for the local R2R + Postgres/pgvector stack)

> **No credentials? No problem.** The backend boots without any `.env` and serves
> sample graph data in **demo mode** (`/health` shows `"mock_data": "active"`).
> You only need the setup in step 3 for real Neo4j / document-RAG features.

## 🛠️ Setup

### 1. Backend

From the repo root:

```bash
cd backend
python -m venv .venv

# Activate — macOS/Linux:
source .venv/bin/activate
# Activate — Windows:
.venv\Scripts\activate

pip install -r requirements.txt
```

> The `r2r` package is intentionally **not** in `requirements.txt` — R2R runs as
> a separate server (Docker locally, bundled via its own venv in the production
> image). The backend talks to it over HTTP.

### 2. Frontend

```bash
cd frontend
pnpm install
```

### 3. Configuration (optional — skip for demo mode)

Create `backend/.env`:

```env
# Neo4j Aura (username/database are literally "neo4j", NOT the instance id)
NEO4J_URI=neo4j+s://<instance-id>.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=<password>
NEO4J_DATABASE=neo4j

# Gemini (powers chat, embeddings, and R2R's KG extraction)
GEMINI_API_KEY=<key>

# Local pgvector (Docker container, host port 5433)
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<password>
POSTGRES_DB=brainclone

# R2R document-RAG server
R2R_BASE_URL=http://localhost:7272
```

Start the local infra (Postgres + R2R only — skip `backend`/`nginx`, you run
those yourself):

```bash
docker compose -f docker-compose.production.yml up -d postgres r2r
```

R2R takes ~30–60s to boot. Its config lives in `r2r-config/config.toml`
(Gemini-only via LiteLLM, embeddings at 768 dims).

## ▶️ Start the Services

**Terminal 1 — backend** (from `backend/`, venv active):

```bash
uvicorn src.main:app --reload --port 8000
```

**Terminal 2 — frontend** (from `frontend/`):

```bash
pnpm dev
```

## 🌐 Access

| What | URL |
|------|-----|
| Frontend (3D graph UI) | http://localhost:3000 |
| Backend health check | http://localhost:8000/health |
| Interactive API docs | http://localhost:8000/docs |
| API base | http://localhost:8000/api/v1 |
| R2R server (if running) | http://localhost:7272 |

## 🔧 Troubleshooting

- **Port 8000 busy** — macOS/Linux: `lsof -ti:8000 | xargs kill -9`; Windows:
  `Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process`
- **`/health` shows `demo_mode`** — expected without `.env`; otherwise check the
  credentials in `backend/.env` (Neo4j `USER`/`DATABASE` must be `neo4j`, not the
  instance id).
- **`services.r2r: "unavailable"`** — the R2R container isn't up (or still
  booting); it's optional unless you're testing document upload/RAG.
- **Frontend build errors** — delete `frontend/node_modules`, re-run `pnpm install`.
- **API connection errors in the UI** — the frontend expects the backend on
  port 8000.

## ☁️ Deploying instead?

See [`backend/DEPLOY.md`](backend/DEPLOY.md) — production runs on Google Cloud
Run (backend + R2R in one container via `cloudbuild.yaml`), with Supabase as the
Postgres/pgvector layer and Neo4j Aura for the graph.
