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

```bash
docker compose up -d                 # postgres + redis
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
uvicorn app.main:app --reload --port 8000 &

cd ..
cp .env.example .env.local           # NEXT_PUBLIC_API_BASE_URL / NEXT_PUBLIC_WS_URL
npm install && npm run dev
```

Dashboard, Markets, and the price chart pull real data from the backend
(REST + a live `/ws/market` WebSocket feed). AI Score/Direction, Portfolio,
Signals, News, Whale Tracker, Liquidations, Macro, Backtesting, and AI Chat
remain on mock data — they're out of scope until the AI module ships.
