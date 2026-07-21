#!/usr/bin/env bash
# Starts the Next.js frontend on :3000, first killing any stale process
# already bound to that port (e.g. left over from a previous codespace
# session) so you never accidentally end up looking at a stale build on
# a fallback port like :3001.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

port=3000
pid=$(fuser "${port}/tcp" 2>/dev/null | xargs echo || true)
if [ -n "$pid" ]; then
  echo "Killing stale process(es) on port ${port}: ${pid}"
  kill $pid 2>/dev/null || true
  sleep 1
  kill -9 $pid 2>/dev/null || true
fi

if [ ! -d node_modules ]; then
  echo "node_modules not found — run: bash scripts/devcontainer-setup.sh" >&2
  exit 1
fi

if [ ! -f .env.local ]; then
  cp .env.example .env.local
  echo "Created .env.local from .env.example"
fi

exec npm run dev
