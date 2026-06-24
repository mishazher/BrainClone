# Lean image for the BrainClone backend (FastAPI + Neo4j).
# Built for Cloud Run (injects $PORT, default 8080); also runs locally.
FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

# Install Python dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code.
COPY src ./src

EXPOSE 8080

# Bind to $PORT so the same image runs on Cloud Run and locally.
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
