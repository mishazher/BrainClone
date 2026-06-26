#!/bin/bash
# Exit on error
set -e

echo "Starting R2R..."
# Run R2R in the background
# We assume R2R reads configuration from R2R_CONFIG_PATH
r2r serve --host 0.0.0.0 --port 7272 &
R2R_PID=$!

echo "Starting FastAPI backend..."
# Run FastAPI in the foreground
uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}
FASTAPI_PID=$!

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
