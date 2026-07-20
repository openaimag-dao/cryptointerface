# AIMAG AI Terminal — Backend (Data Engine)

FastAPI service that ingests real Binance USDT-M Futures market data (REST +
WebSocket), computes technical indicators, stores everything in Postgres,
caches the hot path in Redis, and re-broadcasts live updates to the frontend
over its own WebSocket (`/ws/market`). AI signal generation and trading
decisions are **out of scope** — see `app/api/signals.py`, `portfolio.py`,
etc., which still serve mock data pending a future AI sprint.

## How to run the project

### 1. Infrastructure (Postgres + Redis)

```bash
docker compose up -d      # from the repo root — starts postgres:5432 + redis:6379
```

Or point `DATABASE_URL`/`REDIS_URL` (see below) at any Postgres/Redis you
already have running.

### 2. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # edit if your DB/Redis/symbols differ
uvicorn app.main:app --reload --port 8000
```

- Health check: `curl http://localhost:8000/api/health`
- Interactive docs: `http://localhost:8000/docs`
- Engine status (DB/Redis/Binance WS connectivity, per-symbol last-seen
  timestamps): `curl http://localhost:8000/api/status`

On startup the app immediately starts serving requests while three
background tasks spin up the Data Engine (see below): historical backfill,
the live Binance WebSocket feed, and the open-interest poller. If Binance
is unreachable from your network (corporate proxy, sandboxed CI, etc.) the
API still serves — it just has no data until connectivity is available;
`/api/status` will show `binanceWsState: "disconnected"` and retry with
backoff indefinitely.

### 3. Frontend

```bash
cp .env.example .env.local   # from the repo root; defaults already point at localhost:8000
npm install
npm run dev
```

The frontend calls the backend over plain REST + WebSocket — never Binance
directly (`NEXT_PUBLIC_API_BASE_URL` / `NEXT_PUBLIC_WS_URL` in `.env.local`).

### 4. Tests / lint

```bash
cd backend
source .venv/bin/activate
pytest                # 34 tests: indicators, REST client, WS client, live feed, historical loader, WS manager
ruff check .           # lint
ruff format --check .  # formatting
```

Tests that touch Postgres/Redis use `DATABASE_URL`/`REDIS_URL` overrides set
in `tests/conftest.py` (defaults to a local `aimag_test` database and Redis
DB 1) — create that database once with
`createdb -U aimag aimag_test` (or via `psql`) before running the suite.
Binance itself is never hit in tests — the REST client is exercised against
`httpx.MockTransport` and the WS client against a local `websockets.serve`
instance standing in for Binance's servers, so the suite runs fully offline.

## How the Data Engine works

```
Binance USDT-M Futures (fapi/fstream)
        |
        |  REST (historical_loader.py)         WS (ws_client.py, combined streams)
        v                                              v
 backfill 5000 candles/timeframe/symbol       kline / markPrice / miniTicker / aggTrade
        |                                              |
        v                                              v
   market_repository.py  <-------------------  live_feed.py (dispatches by event type)
   (Postgres upserts,                                  |
    idempotent on                                       +--> indicators/engine.py (on closed candle)
    symbol+interval+time)                               |
        |                                                +--> Redis cache (core/redis.py, hot-path reads)
        v                                                |
   app/api/* REST routers                                +--> services/websocket/manager.py
   (/api/market, /candles,                                     (fans out to every connected
    /indicators, /funding,                                      browser client on /ws/market)
    /open-interest, /status)
        |
        v
   Frontend (services/*.ts REST + hooks/use-market-socket.ts WS)
```

- **`app/services/binance/`** — `rest_client.py` (klines, 24h ticker, funding/mark
  price, open interest, all paginated/retried), `ws_client.py` (combined-stream
  connection with exponential-backoff reconnect + an application-level
  heartbeat watchdog on top of the WS ping/pong the `websockets` library
  already handles), `parsers.py` (raw Binance JSON → typed dataclasses),
  `streams.py` (stream-name/URL builders).
- **`app/tasks/historical_loader.py`** — backfills up to
  `HISTORICAL_CANDLES_PER_TIMEFRAME` (default 5000) candles per
  symbol/timeframe on startup; already-backfilled pairs are skipped on
  restart, so it's idempotent and cheap to leave running every boot.
- **`app/tasks/live_feed.py`** — the real-time dispatcher. A closed kline
  persists the candle, recomputes every indicator from the last ~250
  candles, and broadcasts; an in-progress kline only updates the cache and
  broadcasts (no DB write, no indicator recompute) so the chart still moves
  every tick without hammering Postgres. `markPrice` caches on every tick
  but only persists to Postgres when the funding period actually rolls
  over. `miniTicker` updates `market_stats` (one upserted row per symbol —
  what `/api/market` reads). `aggTrade` is broadcast-only.
- **`app/tasks/open_interest_poller.py`** — open interest has no Binance
  WebSocket stream, so it's polled over REST on an interval (default 60s)
  instead.
- **`app/services/indicators/`** — pure `numpy` functions (EMA, RSI, MACD,
  ATR, Bollinger Bands, VWAP, ADX, OBV, Stochastic RSI, Pivot Points), each
  independently unit-tested, orchestrated by `engine.py` into one
  `IndicatorSnapshot`.
- **`app/core/redis.py`** — caches latest ticker/funding/OI/candle per
  symbol so REST reads and the WS broadcast don't hit Postgres on every
  tick; `app/database/` is the Postgres source of truth (candles, funding,
  open interest, market stats, indicator snapshots, symbol metadata).
- **`app/services/websocket/manager.py` + `app/api/websocket.py`** — the
  frontend never talks to Binance; it connects once to `/ws/market` and
  receives `{"channel": "ticker" | "candle" | "indicators" | "funding" |
  "trade", "data": {...}}` envelopes, camelCase-serialized to match the
  REST API (see `app/schemas/base.py`'s `CamelModel`).
- **Logging** — every log line is a single structured JSON record
  (`app/core/logging.py`), with `INFO`/`WARNING`/`ERROR` used consistently
  (connects/reconnects/backfill progress at `INFO`, retried errors at
  `WARNING`, exhausted retries at `ERROR`).
- **Resilience** — `app/utils/retry.py` wraps REST calls with exponential
  backoff + jitter; the WS client reconnects the same way plus a heartbeat
  watchdog that force-reconnects a silently-dead socket. None of this ever
  crashes the FastAPI process — a fully unreachable Binance just means the
  API serves empty results until connectivity returns (see `/api/status`).

## How to add a new coin

1. Add the symbol to `SYMBOLS` in `.env` (comma-separated, Binance USDT-M
   Futures naming, e.g. `SYMBOLS=BTCUSDT,ETHUSDT,...,APTUSDT`).
2. Restart the backend. On the next boot:
   - `historical_loader.py` registers the symbol (via `/fapi/v1/exchangeInfo`,
     falling back to a naive `USDT` split if that call fails) and backfills
     its candle history for every configured timeframe.
   - `live_feed.py`'s WebSocket client automatically includes the new
     symbol's kline/markPrice/miniTicker/aggTrade streams in its combined
     connection (see `streams.build_streams`).
   - `open_interest_poller.py` picks it up on its next polling cycle.
3. Nothing else needs to change — REST endpoints and the WS feed both
   iterate over `settings.symbol_list`, and the frontend's `/api/market`
   call already renders whatever the backend returns.

If you also want it in the frontend's fixed 4-symbol Dashboard watchlist,
add it to `WATCHLIST_SYMBOLS` in `lib/constants.ts` (and optionally to the
AI-score overlay in `lib/mock/ai-overlay.ts` — otherwise it falls back to a
neutral WAIT/50 placeholder until the real AI module exists).

## How to add a new indicator

1. Write a pure function in `app/services/indicators/<name>.py` that takes
   `numpy` OHLCV arrays and returns a `numpy` array (or tuple of arrays) —
   see `ema.py` for the simplest example, `macd.py` for one that composes
   another indicator.
2. Add a **unit test** in `backend/tests/test_indicators.py` asserting at
   least one known-value or boundary case (see the existing `Test*` classes
   for the pattern).
3. Wire it into `app/services/indicators/engine.py`: call your function in
   `compute_indicators()` and add the result to the `IndicatorSnapshot` it
   returns.
4. Add the matching field(s) to `app/schemas/indicator.py`'s
   `IndicatorSnapshot` (and a nested `*Values` model if it returns more
   than one series, e.g. `MacdValues`).

No database migration is needed — `indicator_values.payload` is a JSON
column that stores whatever `IndicatorSnapshot` serializes to, so a new
indicator field just starts appearing in both `/api/indicators/{symbol}`
and the `"indicators"` WebSocket channel the next time a candle closes.
