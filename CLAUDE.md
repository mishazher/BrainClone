# Project Rules

## Do NOT modify backend or backend deployment files

Claude is **not allowed** to change anything in the backend or backend deployment files. This includes:

- `backend/` (entire directory)
- `cloudbuild.yaml`
- `docker-compose.production.yml`
- `nginx.conf`
- `r2r-config/`

These files may be read for context, but never edited, rewritten, or deleted. If a task seems to require changing them, stop and ask the user instead.
