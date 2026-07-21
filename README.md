# AIMAG AI Terminal

A professional crypto trading terminal — Next.js frontend + a FastAPI Data
Engine that ingests real Binance market data over REST and WebSocket.

- `app/`, `components/`, `hooks/`, `services/`, `store/`, `types/` — the
  Next.js frontend (this directory is its project root: `npm install && npm
  run dev`).
- `backend/` — the FastAPI Data Engine. See **[backend/README.md](backend/README.md)**
  for how to run it, how the ingestion pipeline works, and how to add a new
  coin or indicator.

## Quick start

### Codespaces / devcontainer (recommended)

Opening this repo in a Codespace (or any devcontainer-compatible editor)
auto-installs everything and starts Postgres/Redis on every container
start — see `.devcontainer/devcontainer.json`. After it finishes:

```bash
bash scripts/dev-backend.sh    # terminal 1 — kills any stale :8000, starts uvicorn
bash scripts/dev-frontend.sh   # terminal 2 — kills any stale :3000, starts next dev
```

Both scripts kill whatever's already bound to their port first — safe to
re-run any time (e.g. after resuming a stopped codespace where an old
process from the last session got orphaned).

If you delete and recreate the codespace, `scripts/devcontainer-setup.sh`
runs again automatically (`postCreateCommand`) and rebuilds `.venv`,
`node_modules`, and `.env`/`.env.local` from scratch — nothing manual
needed beyond the two commands above.

### Manual setup

```bash
docker compose up -d                 # postgres + redis
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
uvicorn app.main:app --reload --port 8000 &

cd ..
cp .env.example .env.local           # NEXT_PUBLIC_API_BASE_URL / NEXT_PUBLIC_WS_URL
npm install && npm run dev
```

Dashboard, Markets, the price chart, the AI Analysis panel, Signals,
Liquidations, and AI Chat all pull real data from the backend (REST + a
live `/ws/market` WebSocket feed) — see
**[backend/AI_ENGINE.md](backend/AI_ENGINE.md)** for how the AI Decision
Engine's Market Score/Confidence/Direction/Risk are computed. News, Whale
Tracker, Macro, and Sentiment (Sprint 4's Intelligence Layer) are real
too — see **[backend/README.md](backend/README.md)**'s "Intelligence
Layer" section. Portfolio, Backtesting, and the Macro economic-calendar
tab remain on mock data — out of scope until a future sprint. If Binance
is unreachable from your network, a CoinGecko fallback kicks in
automatically — see backend/README.md's "CoinGecko fallback" section.
