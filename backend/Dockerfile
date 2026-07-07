# Unified image for the BrainClone backend (FastAPI) and R2R, run together by start.sh.
# Built for Cloud Run (injects $PORT, default 8080); also runs locally.
# Note: Build context should be the repository root:
#   docker build -f backend/Dockerfile .
# 3.12, not newer: the r2r package requires Python >=3.10,<3.13 (as of 3.6.6).
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    R2R_CONFIG_PATH=/app/config/config.toml \
    R2R_HOST=0.0.0.0 \
    R2R_PORT=7272

# Install Python dependencies first for better layer caching.
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code (FastAPI)
COPY backend/src ./src

# R2R Configuration
COPY r2r-config/config.toml /app/config/config.toml

# Start script
COPY backend/start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8080

# Bind to $PORT so the same image runs on Cloud Run and locally.
CMD ["/app/start.sh"]
