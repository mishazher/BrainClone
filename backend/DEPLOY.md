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

## Deploy

Run from the **repo root** (`--source backend` points at this directory):

```bash
gcloud run deploy brainclone-backend \
  --source backend \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars 'ENVIRONMENT=production,LOG_FORMAT=json' \
  --set-env-vars 'CORS_ORIGINS=["https://brainclone.work","http://localhost:3000"]' \
  --set-env-vars 'NEO4J_URI=neo4j+s://<id>.databases.neo4j.io' \
  --set-env-vars 'NEO4J_USER=neo4j' \
  --set-env-vars 'NEO4J_PASSWORD=<password>' \
  --set-env-vars 'NEO4J_DATABASE=neo4j'
```

> Note: `,` separates vars, so the CORS JSON list (which has no commas here) is
> fine. If you ever add a comma-containing value, use a `^@^`-delimited form:
> `--set-env-vars '^@^CORS_ORIGINS=[...]@NEO4J_URI=...'`.

First build takes ~3–5 min. The command prints an HTTPS service URL when done.

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
- **Update CORS later:**
  ```bash
  gcloud run services update brainclone-backend --region us-central1 \
    --set-env-vars 'CORS_ORIGINS=["https://brainclone.work"]'
  ```

## ⚠️ Neo4j credentials

Neo4j Aura's username and database name are normally both `neo4j` (the instance
id, e.g. `1b21c8b6`, is **not** the username/database). Your local `.env` sets
`NEO4J_USER` / `NEO4J_DATABASE` to the instance id — double-check these or the
connection will fail. The example above uses the typical `neo4j` values.
