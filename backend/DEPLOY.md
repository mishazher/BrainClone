# Deploying BrainClone (backend + R2R) to Google Cloud Run

This deploys **both the FastAPI app and the R2R sidecar in a single Cloud Run container**.

The container runs a start script (`start.sh`) that boots both services. They share a network namespace, so the backend talks to R2R over **`localhost:7272`** — the exact `R2R_BASE_URL` default the code already uses.
R2R is never exposed publicly. All durable state lives in **Neo4j Aura** and **Supabase** (Postgres + pgvector); the container itself is stateless.

```
            ┌──────────────── Cloud Run service "brainclone" ────────────────┐
 Internet → │  backend :8080  ──localhost:7272──►  r2r (background process)  │
            └───────────┬───────────────────────────────┬────────────────────┘
                        │                                │
                  Neo4j Aura                    Supabase (Postgres + pgvector)
```

> **Why a custom image?** Cloud Run allows multi-container deployments, but a unified image simplifies the `gcloud run deploy` command and lifecycle management. We build a unified image, push to Artifact Registry, and apply a service YAML (`deploy/cloudrun/service.yaml`).

---

## One-time setup

1. **GCP project + billing.** Free tier covers a low-traffic demo, but see the
   cost note below — a warm R2R sidecar is **not** free. New accounts get $300/90 days.

2. **Authenticate** (interactive — run inline with the `!` prefix in Claude Code):
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Enable APIs:**
   ```bash
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
     artifactregistry.googleapis.com secretmanager.googleapis.com
   ```

4. **Create an Artifact Registry repo** (once):
   ```bash
   gcloud artifacts repositories create brainclone \
     --repository-format=docker --location=REGION
   gcloud auth configure-docker REGION-docker.pkg.dev
   ```

---

## Step 1 — Build & push the unified image

Run from the **repo root**. Replace `PROJECT_ID` / `REGION` (e.g. `us-central1`).

```bash
# We use the repository root as the build context to include both the backend 
# and the r2r-config/config.toml file.
docker build -f backend/Dockerfile \
  -t REGION-docker.pkg.dev/PROJECT_ID/brainclone/backend:latest .
docker push REGION-docker.pkg.dev/PROJECT_ID/brainclone/backend:latest
```

> The unified image contains both FastAPI dependencies and R2R. The first push is slow. (You can also build it with Cloud Build via a small `cloudbuild.yaml` if you'd rather not push locally.)

## Step 2 — Create secrets

```bash
echo -n '<neo4j-password>'   | gcloud secrets create neo4j-password      --data-file=-
echo -n '<gemini-api-key>'   | gcloud secrets create gemini-api-key      --data-file=-
echo -n '<supabase-db-pass>' | gcloud secrets create supabase-db-password --data-file=-
```

Grant the Cloud Run runtime service account access (replace the project number):
```bash
for S in neo4j-password gemini-api-key supabase-db-password; do
  gcloud secrets add-iam-policy-binding $S \
    --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
done
```

## Step 3 — Fill in & apply the service spec

Edit `deploy/cloudrun/service.yaml` and replace the placeholders:

| Placeholder | Value |
|---|---|
| `PROJECT_ID`, `REGION` | your GCP project + region |
| `<neo4j-id>` | Neo4j Aura instance id (in the URI host) |
| `<supabase-region>` | Supabase **pooler** host, e.g. `aws-0-us-east-1` |
| `<project-ref>` | Supabase project ref → user `postgres.<project-ref>` |
| `brainclone.work` | your frontend origin(s) for CORS |

Then apply and open it up:
```bash
gcloud run services replace deploy/cloudrun/service.yaml --region REGION
gcloud run services add-iam-policy-binding brainclone --region REGION \
  --member=allUsers --role=roles/run.invoker
```

### Verify
```bash
URL=$(gcloud run services describe brainclone --region REGION --format='value(status.url)')
curl $URL/health        # services.r2r should be "healthy"
```

---

## ⚠️ Supabase connection — use the POOLER, not the direct host

The **direct** connection `db.<ref>.supabase.co:5432` is **IPv6-only** and won't
resolve from Cloud Run (IPv4 egress) — it fails with `getaddrinfo failed`. Use the
**Supavisor pooler** host instead:

- Host: `<region>.pooler.supabase.com` (from Dashboard → **Connect**)
- User: `postgres.<project-ref>` &nbsp; DB: `postgres`
- **Port 5432 = session pooler** (used here). R2R runs DDL/migrations + advisory
  locks that the **transaction pooler (6543) can break**, so session mode is safer
  for the R2R container. The backend's own asyncpg pools set `statement_cache_size=0`,
  so either pooler mode works for them.

Backend and R2R share the same Supabase database: R2R writes to a schema named
after `R2R_PROJECT_NAME` (`brainclone`); the backend's `vector_service` uses
`public`. No table collisions. Enable the extension once: `create extension if not
exists vector;`.

## 💰 Free-tier reality

R2R is heavy (~2 GB RAM, multi-GB image, 30–60s boot), so:

- **`minScale: 1`** (in the YAML) keeps R2R warm — this **leaves Always Free** and
  bills idle CPU/memory (a few $/month). Without it, every cold request waits the
  full R2R boot (likely timeouts) — bad UX but ~free at idle.
- The instance memory is the **sum** of both containers (here ~5 GiB). Tune the
  `resources.limits` down if you can; raise `maxScale` only as traffic needs.
- `cpu-throttling: false` is required so the sidecar keeps running between requests.

## Neo4j credentials

Neo4j Aura's username and database are normally both `neo4j` (the instance id,
e.g. `1b21c8b6`, is **not** the username/database). Your local `.env` currently
sets `NEO4J_USER`/`NEO4J_DATABASE` to the instance id — fix those in the YAML or
the connection will fail. The spec uses the typical `neo4j` values.

## Security note

The R2R sidecar has no `ports:` block, so it is unreachable from the internet —
only the backend can hit it over loopback. R2R auth is off in `config.toml`, which
is acceptable here. For defense-in-depth you can still enable R2R auth
(`require_authentication = true`) and pass a token via `R2R_API_KEY` to the backend.

---

## Frontend (Vercel)

The Next.js frontend deploys separately to Vercel. Point it at this service:
```
NEXT_PUBLIC_API_URL=https://<cloud-run-url>/api/v1
```
(The `/api/v1` suffix matters — the chat/graph proxies call `${NEXT_PUBLIC_API_URL}/chat`, etc.)
