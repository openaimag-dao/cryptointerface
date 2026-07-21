# AIMAG AI Terminal — Backend (Data Engine)

FastAPI service that ingests real Binance USDT-M Futures market data (REST +
WebSocket), computes technical indicators, stores everything in Postgres,
caches the hot path in Redis, and re-broadcasts live updates to the frontend
over its own WebSocket (`/ws/market`). It also runs a deterministic AI
Decision Engine on top of that data — see **[AI_ENGINE.md](./AI_ENGINE.md)**
for how the Market Score, Confidence, Direction, and Risk plan are computed.
Automatic trade execution is **out of scope**: the engine only ever analyzes
and explains, it never places an order.

`/api/signals` batches the AI Decision Engine across the whole watchlist
(only symbols currently reading LONG/SHORT are included — a WAIT read isn't
a "signal"). `/api/liquidations` is fed by Binance's `forceOrder` WebSocket
stream in real time and persisted to Postgres; `/api/liquidations/heatmap`
buckets recent liquidations by price for one symbol (`?symbol=`, defaults to
`BTCUSDT`). `/api/chat/messages` is a real Anthropic Claude assistant
grounded in a live watchlist snapshot (see "AI Chat" below) — the AI
Decision Engine itself stays deterministic/no-LLM. Sprint 4 adds an
**Intelligence Layer** (`app/intelligence/`) — real Macro data feeding
`/api/macro` and the Decision Engine's `macro` factor, real News (RSS +
a deterministic classifier) feeding `/api/news` and the `news` factor, a
Sentiment Engine blending technical/macro/liquidations/news/whales at
`/api/sentiment`, and an LLM Explanation Layer at
`/api/llm/explanation/{symbol}` (see "Intelligence Layer" below).
`app/api/portfolio.py` and a few other
routers still serve mock data pending a future sprint.

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
pytest                # 132 tests: indicators, Binance/CoinGecko REST clients, WS client, live feed,
                       # historical loader, WS manager, the AI Decision Engine (trend/momentum/
                       # .../confidence/risk/decision), the Claude chat service, and the Sprint 4
                       # Intelligence Layer (macro + news scoring/providers/classifier, sentiment
                       # engine, LLM explanation)
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

### CoinGecko fallback (Binance-unreachable environments only)

Binance stays the only source when it's reachable. When it isn't (e.g. an
egress policy or geo-restriction blocking `fapi.binance.com`), two small,
clearly-scoped fallbacks kick in automatically — see
`app/services/coingecko/` and `app/tasks/coingecko_fallback.py`:

- **Historical backfill** (`app/tasks/historical_loader.py`): if a
  symbol/interval has zero existing candles and Binance's own retries are
  exhausted, `1h` and `4h` candles are backfilled from CoinGecko's public
  OHLC endpoint instead (`1h` is approximated by resampling CoinGecko's
  30min bars; `4h` is native granularity). `1m`/`5m`/`15m`/`1d` have no
  matching CoinGecko granularity on the free tier and are left empty.
  Volume is always `0` for these candles (CoinGecko's free OHLC endpoint
  doesn't return it) — `is_supported()` in `coingecko/candles.py` is the
  single source of truth for which intervals this covers.
- **Live ticker** (`app/tasks/coingecko_fallback.py`): a background poller
  that stays dormant while the Binance WebSocket is connected, and only
  polls CoinGecko's `/coins/markets` (every 45s) when it isn't — updating
  `market_stats` and broadcasting a `ticker` update over the same
  `/ws/market` channel Binance would have used, so the frontend still sees
  moving real prices.

What this fallback does **not** cover: funding rate and open interest are
futures-only concepts with no CoinGecko/spot equivalent, so they simply
stay empty while Binance is unreachable — the AI Decision Engine's
`funding`/`oi` scoring modules already handle "no history" gracefully
(see `backend/AI_ENGINE.md`). There's also no WebSocket on CoinGecko's
free tier, so this is REST-polled, not push-based.

`SYMBOL_TO_COINGECKO_ID` in `app/services/coingecko/symbols.py` maps the
default 7 symbols; add an entry there for any new coin you want this
fallback to cover (an unmapped symbol just gets no fallback data, which is
safe).

### AI Chat (Anthropic Claude)

`POST /api/chat/messages` (`app/services/claude_chat.py`) is a real Claude
assistant — it is **not** part of the AI Decision Engine and never
influences Market Score/Confidence/Direction/Risk, which stay fully
deterministic. Each request:

1. Builds a one-line-per-symbol snapshot of the current watchlist (price,
   market score, confidence, direction) straight from the same
   `build_market_context`/`analyze_market` the Decision Engine uses — no
   separate data path, so the assistant never disagrees with what
   `/api/signals` shows.
2. Sends that snapshot as system-prompt context, plus the conversation's
   prior turns (`history` in the request body — sessions live client-side
   only, see `store/chat-store.ts`, so the backend stays stateless), to
   `ANTHROPIC_CHAT_MODEL` (default `claude-sonnet-5`).
3. Returns the reply as-is. The system prompt explicitly tells Claude not
   to suggest placing any specific order.

Set `ANTHROPIC_API_KEY` in `.env` to enable it (get one at
[console.anthropic.com](https://console.anthropic.com/)). With no key set,
the endpoint replies with a "not configured" message instead of erroring —
same fail-open philosophy as the rest of the Data Engine.

## Intelligence Layer (Sprint 4)

`app/intelligence/` sits alongside the Data Engine and AI Decision Engine —
analysis only, same as everywhere else in this app: nothing here ever
places an order. This sprint ships Macro, News, Sentiment, and LLM
Explanation; Whales (on-chain transfer tracking) is still a Sprint 4 stub
— see the Sentiment Engine's `whales` category — pending a follow-up PR.

```
app/intelligence/
  macro/
    symbols.py       registry of every macro indicator + its provider
    providers.py      Alpha Vantage / Fear&Greed / CoinGecko REST clients
    service.py         fetch_and_persist_macro_snapshot() — one poll cycle
  news/
    sources.py         registry of RSS sources
    fetcher.py          httpx fetch + feedparser parse, per source
    classifier.py        deterministic keyword sentiment/impact/symbols/category
    service.py            fetch_and_persist_news() — one poll cycle
  sentiment/
    engine.py           compute_sentiment() — blends 5 categories
    liquidation_factor.py  real Binance liquidation data -> a FactorScore
  llm/
    explanation.py      build_llm_explanation() — Claude, forced tool-use
  scheduler/
    tasks.py             4 background loops, see app/main.py's lifespan
  cache/                 Redis key templates + TTLs for this layer

app/services/
  macro_repository.py, news_repository.py, sentiment_repository.py,
  llm_repository.py
    persistence for the four new tables (macro_data, news,
    sentiment_scores, llm_reports) — same upsert/append-only patterns as
    market_repository.py
```

### Macro Engine

10 indicators, each stored as its own history in `macro_data`
(`app/models/macro.py`, append-only — one row per fetch):

| Indicator | Provider | Notes |
|---|---|---|
| DXY, Gold, Silver, Oil, S&P 500, NASDAQ, VIX | Alpha Vantage (`TIME_SERIES_DAILY`) | ETF proxies (UUP/GLD/SLV/USO/SPY/QQQ/VIXY) — no free direct index feed exists, see `app/ai_engine/scoring/macro.py`'s docstring for why this is scored by % change, not level |
| US 10Y Yield | Alpha Vantage (`TREASURY_YIELD`) | A real yield, not a proxy |
| Crypto Fear & Greed | `alternative.me` | Free, keyless, 0-100 index, updates daily |
| BTC Dominance | CoinGecko `/global` | Free, keyless |

Set `ALPHA_VANTAGE_API_KEY` in `.env` (free tier: 25 requests/day — get one
at [alphavantage.co](https://www.alphavantage.co/support/#api-key)) to
enable the 7 ETF/treasury-proxied indicators; Fear & Greed and BTC
Dominance work regardless. `MACRO_POLL_INTERVAL_SECONDS` (default 6h) is
deliberately long to respect that quota.

Of the 10, **DXY/NASDAQ/S&P 500/VIX/US 10Y/Gold/Fear & Greed feed real
scoring** — `app/ai_engine/scoring/macro.py::score_macro()` reads the
latest snapshot (`MarketContext.macro_snapshot`, built by
`market_context.py`) and now carries real weight (`0.09`) in
`market_score.py`'s `FACTOR_WEIGHTS`, up from the Sprint 3 stub's `0.00` —
exactly the extension point that stub's docstring described. Silver, Oil,
and BTC Dominance are fetched/displayed but not scored (ambiguous or
too-narrow a signal for crypto risk sentiment — see `symbols.py`'s
`used_in_scoring` field for the reasoning per indicator).

**To add a new macro source**: add one `MacroIndicatorDef` to
`app/intelligence/macro/symbols.py`, handle its `provider` value in
`service.py` (reuse `providers.py`'s pattern — a client method that
returns `float | None` and never raises), and it starts showing up in
`/api/macro/indicators` and (if scored) `score_macro()` automatically.

### News Engine

Aggregates 3 RSS sources (CoinDesk, Cointelegraph, Decrypt —
`app/intelligence/news/sources.py`) on `NEWS_POLL_INTERVAL_SECONDS`
(default 10min, no rate-limit concern like Alpha Vantage). Each article
is classified once at ingest time by a **deterministic keyword
classifier** (`classifier.py`) — not an LLM call per article: a poll
cycle can pull dozens of articles across sources, and running each
through Claude would be slow and turn every poll into a pile of billed
API calls for a rough directional read. The classifier produces:

- `symbols` — which watchlist assets are mentioned (name/ticker alias
  matching, e.g. "Bitcoin" or "BTC" -> `BTC`)
- `sentiment` (`BULLISH`/`BEARISH`/`NEUTRAL`) — net bullish vs. bearish
  keyword hits
- `impact_score` (0-100) — base score + bonus per high-impact keyword
  (SEC, ETF, hack, bankruptcy, ...) + bonus per symbol mentioned
- `category` (`Security`/`Regulation`/`Institutional`/`DeFi`/`Technology`/`Market`)

Articles persist to a `news` table (`app/models/news.py`), deduped on
`url` (`ON CONFLICT DO NOTHING` — RSS feeds re-serve the same articles on
every poll). `app/services/news_repository.py::get_news_snapshot_for_symbol()`
builds the `ai_engine`-facing snapshot from recent articles (72h
lookback) that either mention that symbol or are broad market-wide news
(no symbol tag — e.g. a Fed/regulation story that isn't asset-specific),
weighted by `impact_score`. `app/ai_engine/scoring/news.py::score_news()`
reads that snapshot and now carries real weight (`0.08`) in
`market_score.py`'s `FACTOR_WEIGHTS`, up from the Sprint 3 stub's `0.00`.

**To add a new news source**: add one `NewsSourceDef` (RSS URL) to
`app/intelligence/news/sources.py`. Nothing else needs to change —
`service.py` iterates the registry on every poll cycle.

### Sentiment Engine

`app/intelligence/sentiment/engine.py::compute_sentiment()` blends 5
categories, each returning `score` (0-100) / `direction` / `confidence` /
`reasons` — this sits *above* `market_score.py` (which only aggregates a
single symbol's technical factors); it never feeds back into the Decision
Engine:

| Category | Weight | Source |
|---|---:|---|
| Technical | 0.55 | The Decision Engine's own Market Score/Confidence (`analyze_market()`) |
| Macro | 0.20 | `score_macro()` — same real feed as above |
| Liquidations | 0.15 | Real: trailing-24h long/short totals, contrarian read (heavy long liqs -> mild bullish, same "contrarian at extremes" logic `scoring/funding.py` already uses) |
| News | 0.10 | Real: `score_news()` — same real feed as above |
| Whales | 0.00 | Stub — neutral, `0%` confidence, pending on-chain tracking |

`overall_score`/`confidence` are the weight-blended sum/average across
all 5; `direction` is derived from `overall_score` the same
`direction_from_score()` thresholds use everywhere else in the app.

### LLM Explanation Layer

`app/intelligence/llm/explanation.py::build_llm_explanation()` is the
**only** place an LLM's output reaches the user as analysis, and it's
deliberately narrow:

- `direction`/`confidence` are copied straight from the Decision Engine /
  Sentiment Engine — Claude is never asked for them and structurally
  can't override them (they aren't even fields in the tool schema below).
- Claude is given the engine's own numbers/reasons as structured JSON and
  forced (via `tool_choice: {"type": "tool", "name": "emit_explanation"}`)
  to respond through a fixed schema — `summary`, `key_drivers`, `risks`,
  `opportunities`, `assets_affected`. It cannot free-associate a different
  shape, and the system prompt explicitly forbids inventing facts not
  present in the input or suggesting a trade.
- No key configured, or an upstream error, falls back to a clearly-labeled
  message plus the engine's own `reasons` as `key_drivers` — same
  fail-open philosophy as `claude_chat.py`.

### Scheduler

Four background loops (`app/intelligence/scheduler/tasks.py`), wired
into `main.py`'s lifespan alongside the Data Engine's existing pollers —
each is a `while not stop_event.is_set()` loop, one bad cycle never
crashing the loop:

| Task | Interval (config var) | Default |
|---|---|---|
| `run_macro_poller` | `MACRO_POLL_INTERVAL_SECONDS` | 6h |
| `run_news_poller` | `NEWS_POLL_INTERVAL_SECONDS` | 10min |
| `run_sentiment_recompute` (every watchlist symbol) | `SENTIMENT_RECOMPUTE_INTERVAL_SECONDS` | 5min |
| `run_llm_explanation_refresh` (`LLM_EXPLANATION_ANCHOR_SYMBOL` only) | `LLM_EXPLANATION_INTERVAL_SECONDS` | 30min |

The LLM refresh only runs for one configurable "anchor" symbol (default
`BTCUSDT`) — that's what feeds `/api/dashboard/intelligence`'s cached
explanation without a Claude call on every dashboard poll.
`/api/llm/explanation/{symbol}` itself still computes live, for any
symbol, on every request.

### API endpoints

| Endpoint | Notes |
|---|---|
| `GET /api/macro/indicators` | Real, all 10 indicators (see above) |
| `GET /api/macro/events` | Still mock — an economic calendar needs its own provider, out of scope this sprint |
| `GET /api/news?limit=&symbol=&category=` | Real, filterable list |
| `GET /api/news/latest?limit=` | Real, most recent N articles across all sources |
| `GET /api/news/search?q=&limit=` | Real, title/summary keyword search |
| `GET /api/sentiment?symbol=&interval=` | Real, computes + persists on every call |
| `GET /api/llm/explanation/{symbol}?interval=` | Real, computes + persists live |
| `GET /api/dashboard/intelligence?symbol=&interval=` | Real; `aiExplanation` reads the scheduler's cached anchor-symbol report (fast enough to poll) |

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
