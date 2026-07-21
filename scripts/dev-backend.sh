#!/usr/bin/env bash
# Starts the FastAPI backend on :8000, first killing any stale process
# already bound to that port (e.g. left over from a previous codespace
# session) — this is exactly the "old prices because an old process is
# still serving" trap, automated away.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../backend"

port=8000
pid=$(fuser "${port}/tcp" 2>/dev/null | xargs echo || true)
if [ -n "$pid" ]; then
  echo "Killing stale process(es) on port ${port}: ${pid}"
  kill $pid 2>/dev/null || true
  sleep 1
  kill -9 $pid 2>/dev/null || true
fi

if [ ! -d .venv ]; then
  echo "backend/.venv not found — run: bash scripts/devcontainer-setup.sh" >&2
  exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created backend/.env from .env.example"
fi

exec uvicorn app.main:app --reload --reload-dir app --port "${port}"
