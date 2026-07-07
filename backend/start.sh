#!/bin/bash
set -e

# R2R lives in its own venv (see Dockerfile) — its deps conflict with the
# backend's, so it must not run under the system interpreter.
echo "Starting R2R..."
/opt/r2r/bin/r2r serve --host "${R2R_HOST:-0.0.0.0}" --port "${R2R_PORT:-7272}" &

# uvicorn replaces the shell (exec) so it receives signals directly; R2R keeps
# running as its child-turned-orphan until the container stops. If R2R dies,
# the backend stays up and /health reports services.r2r as unhealthy.
echo "Starting FastAPI backend..."
exec uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8080}"
