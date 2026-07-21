#!/usr/bin/env bash
# One-time setup, run by devcontainer.json's postCreateCommand when the
# codespace/container is first created. Safe to re-run manually — never
# overwrites an existing .env, and dependency installs are idempotent.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "== Backend =="
cd backend
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created backend/.env from .env.example — edit it if your DB/Redis/symbols differ."
fi
deactivate
cd ..

echo "== Frontend =="
npm install
if [ ! -f .env.local ]; then
  cp .env.example .env.local
  echo "Created .env.local from .env.example — defaults already point at localhost:8000."
fi

echo
echo "Setup complete. Postgres/Redis start automatically on every codespace start."
echo "To run the app:"
echo "  bash scripts/dev-backend.sh    # in one terminal"
echo "  bash scripts/dev-frontend.sh   # in another terminal"
