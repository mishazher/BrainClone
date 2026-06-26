# R2R image for Cloud Run.
#
# Cloud Run has no host-volume mounts, so we can't `-v ./r2r-config:/app/config`
# the way docker-compose does locally. Instead we bake the BrainClone Gemini
# config into a thin layer on top of the official R2R image.
#
# Build context is the REPO ROOT (so the COPY can see r2r-config/):
#   docker build -f deploy/cloudrun/r2r.Dockerfile -t <registry>/r2r:latest .
FROM sciphiai/r2r:latest

COPY r2r-config/config.toml /app/config/config.toml

ENV R2R_CONFIG_PATH=/app/config/config.toml \
    R2R_HOST=0.0.0.0 \
    R2R_PORT=7272
