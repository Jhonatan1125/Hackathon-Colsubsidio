#!/usr/bin/env bash
set -e

cd SistemaPrediccion

# Add src/ to PYTHONPATH so Python can find the credit_engine package
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"

# Load root .env (Railway injects its own vars, but this ensures local .env works)
ROOT_ENV="$(cd .. && pwd)/.env"
if [ -f "$ROOT_ENV" ]; then
  while IFS='=' read -r key value; do
    # Skip comments and blank lines
    [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
    # Trim whitespace from key
    key=$(echo "$key" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
    # Trim whitespace from value
    value=$(echo "$value" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
    # Strip surrounding quotes from value
    value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
    export "$key=$value"
  done < "$ROOT_ENV"
fi

# Start the FastAPI application
uvicorn credit_engine.main:app --host 0.0.0.0 --port "${PORT:-8000}"
