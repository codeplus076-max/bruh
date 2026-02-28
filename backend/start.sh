#!/bin/bash
# ------------------------------------------------------------------
# Render Deployment Hardened Start Script
# 
# Purpose: Ensures Uvicorn strictly utilizes ONE worker process.
# This prevents the ML payload (XGBoost) from multiplying in RAM,
# preventing Out-Of-Memory (OOM) crashes on the 512MB limit tier.
# ------------------------------------------------------------------

echo "Starting Upchaar Backend - Enforcing 1 Worker explicitly for 512MB RAM Limit..."

# Default to 8000 if PORT isn't provided by Render
export PORT=${PORT:-8000}

# Start the uvicorn server with limit-concurrency set to avoid thread blow-out
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 1 \
    --limit-concurrency 50 \
    --log-level warning
