# Deploying the BrainClone backend to Google Cloud Run

FastAPI + Neo4j (lean build, no r2r). The image is built from `Dockerfile` and
binds to `$PORT` (Cloud Run injects `8080`). Neo4j data lives in Neo4j Aura — only
this stateless API is deployed here.

## One-time setup

1. **Create a GCP project & enable billing** (free tier covers a demo; a card is
   required). New accounts get a $300 / 90-day credit.

2. **Authenticate and select the project** (run these yourself — they're
   interactive). In Claude Code you can run them inline with the `!` prefix:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Enable the required APIs:**
   ```bash
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
   ```

## Deploy (Option A: one-off from CLI)

Run from the **repo root** (`--source backend` points at this directory).

`CORS_ORIGINS` is a **comma-separated** list of origins, and `--set-env-vars`
also uses `,` to separate vars — so we override the delimiter with `^@^` (the
text between the first two `^` becomes the separator, here `@`), which lets the
CORS value keep its commas:

```bash
gcloud run deploy brainclone-backend \
  --source backend \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars "^@^ENVIRONMENT=production@LOG_FORMAT=json@CORS_ORIGINS=https://brainclone.work,http://localhost:3000@NEO4J_URI=neo4j+s://<id>.databases.neo4j.io@NEO4J_USER=neo4j@NEO4J_PASSWORD=<password>@NEO4J_DATABASE=neo4j"
```

First build takes ~3–5 min. The command prints an HTTPS service URL when done.

## Deploy (Option B: continuously from GitHub)

Build + deploy automatically on every push to `main` (uses Cloud Build).

1. Cloud Run Console -> **Create service** -> **Continuously deploy from a
   repository** -> **Set up with Cloud Build**.
2. Authorize GitHub, pick repo **BrainCloneTeam/Brain-clone-divhacks**, branch
   `^main$`.
3. **Build type: Dockerfile.** Because this is a monorepo, set:
   - **Build context directory:** `/backend`
   - **Dockerfile path:** `/backend/Dockerfile`
4. Set the env vars (same keys as Option A) in the **Variables & Secrets** tab —
   here `CORS_ORIGINS` is just `https://brainclone.work,http://localhost:3000`
   (no delimiter tricks needed in the UI).
5. Allow unauthenticated invocations -> **Create**.

> The changes in this repo must be **committed and pushed** first, or the build
> will use stale source. Note: any push to the repo (incl. frontend-only) will
> trigger a backend rebuild; add a Cloud Build trigger file filter later to
> limit it to `backend/**` if that becomes noisy.

### Verify
```bash
curl https://<service-url>/health        # -> {"status":"demo_mode",...}
```

## Common follow-ups

- **Keep it always warm** (no cold starts): add `--min-instances 1`.
  Default is scale-to-zero (~2–5s cold start, no idle cost).
- **Secrets via Secret Manager** (instead of plaintext env vars):
  ```bash
  echo -n '<password>' | gcloud secrets create neo4j-password --data-file=-
  gcloud run services update brainclone-backend --region us-central1 \
    --set-secrets 'NEO4J_PASSWORD=neo4j-password:latest'
  ```
- **Update CORS later** (comma-separated origins):
  ```bash
  gcloud run services update brainclone-backend --region us-central1 \
    --set-env-vars 'CORS_ORIGINS=https://brainclone.work'
  ```

## ⚠️ Neo4j credentials

Neo4j Aura's username and database name are normally both `neo4j` (the instance
id, e.g. `1b21c8b6`, is **not** the username/database). Your local `.env` sets
`NEO4J_USER` / `NEO4J_DATABASE` to the instance id — double-check these or the
connection will fail. The example above uses the typical `neo4j` values.
