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
places an order. This sprint ships Macro, News, Whales, Sentiment, and LLM
Explanation — all five categories are real, see below.

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
  whales/
    addresses.py         curated list of known exchange wallets to watch
    providers.py           Etherscan REST client (native + ERC-20 transfers)
    classifier.py            deterministic deposit/withdrawal classification
    service.py                 fetch_and_persist_whale_events() — one poll cycle
  sentiment/
    engine.py           compute_sentiment() — blends 5 categories
    liquidation_factor.py  real Binance liquidation data -> a FactorScore
  llm/
    explanation.py      build_llm_explanation() — Claude, forced tool-use
  scheduler/
    tasks.py             5 background loops, see app/main.py's lifespan
  cache/                 Redis key templates + TTLs for this layer

app/services/
  macro_repository.py, news_repository.py, whale_repository.py,
  sentiment_repository.py, llm_repository.py
    persistence for the five new tables (macro_data, news, whale_events,
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

### Whale Engine

Tracks large on-chain transfers touching known exchange wallets, using
Etherscan's free-tier REST API (`ETHERSCAN_API_KEY` in `.env` — get one at
[etherscan.io/apis](https://etherscan.io/apis)). Etherscan's free tier has
no chain-wide "large transactions" firehose — it's address-centric
(`txlist`/`tokentx` per address) — so this watches a curated list of
publicly-labeled exchange wallets (`app/intelligence/whales/addresses.py`:
Binance, Coinbase, Kraken, OKX) rather than scanning the whole chain.
Coverage is therefore limited to assets with an Ethereum footprint: native
ETH and one ERC-20 (LINK). BTC, SOL, DOGE, XRP, BNB etc. have no Ethereum
presence and aren't covered by this approach.

Every `WHALE_POLL_INTERVAL_SECONDS` (default 5min) cycle,
`service.py::fetch_and_persist_whale_events()` fetches native + token
transactions for each watched address, and `classifier.py` deterministically
labels each transfer:

- Transfer **to** a known exchange wallet (and not from one) -> `TO_EXCHANGE`
  ("deposit", often selling pressure), confidence `90`
- Transfer **from** a known exchange wallet (and not to one) -> `FROM_EXCHANGE`
  ("withdrawal", often accumulation), confidence `90`
- Both sides are known exchanges (inter-exchange rebalancing) -> `TO_EXCHANGE`
  at a lower confidence (`40`) — real but a less informative signal
- Neither side is a known exchange -> not classified (this free-tier
  approach has no basis to call it a "whale" event either way)

USD value is computed from the same live ticker prices the Data Engine
already tracks (`market_repository.get_market_stat`), filtered to
`WHALE_MIN_USD_THRESHOLD` (default $250k) before persisting to
`whale_events` (`app/models/whale.py`, deduped on `tx_hash`).
`app/services/whale_repository.py::get_whale_snapshot_for_symbol()` sums
24h deposit/withdrawal USD by direction; `app/ai_engine/scoring/whales.py::score_whales()`
reads that snapshot — heavy withdrawals read as accumulation (bullish),
heavy deposits read as distribution (bearish) — and carries real weight
(`0.06`) in `market_score.py`'s `FACTOR_WEIGHTS`. This is a new scoring
module (Sprint 3 had no whales stub to replace), added following the same
`FactorScore` contract as every other factor.

**To watch a new exchange wallet**: add one `WatchedAddress` to
`app/intelligence/whales/addresses.py`. **To track a new ERC-20 asset**:
add its contract address to `TOKEN_CONTRACTS` in the same file and its
symbol mapping to `SYMBOL_TO_ASSET` in `whale_repository.py`.

### Sentiment Engine

`app/intelligence/sentiment/engine.py::compute_sentiment()` blends 5
categories, each returning `score` (0-100) / `direction` / `confidence` /
`reasons` — this sits *above* `market_score.py` (which only aggregates a
single symbol's technical factors); it never feeds back into the Decision
Engine:

| Category | Weight | Source |
|---|---:|---|
| Technical | 0.50 | The Decision Engine's own Market Score/Confidence (`analyze_market()`) |
| Macro | 0.18 | `score_macro()` — same real feed as above |
| Liquidations | 0.13 | Real: trailing-24h long/short totals, contrarian read (heavy long liqs -> mild bullish, same "contrarian at extremes" logic `scoring/funding.py` already uses) |
| News | 0.09 | Real: `score_news()` — same real feed as above |
| Whales | 0.10 | Real: `score_whales()` — same real feed as above (ETH/LINK only, see Whale Engine above) |

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

Five background loops (`app/intelligence/scheduler/tasks.py`), wired
into `main.py`'s lifespan alongside the Data Engine's existing pollers —
each is a `while not stop_event.is_set()` loop, one bad cycle never
crashing the loop:

| Task | Interval (config var) | Default |
|---|---|---|
| `run_macro_poller` | `MACRO_POLL_INTERVAL_SECONDS` | 6h |
| `run_news_poller` | `NEWS_POLL_INTERVAL_SECONDS` | 10min |
| `run_whale_poller` | `WHALE_POLL_INTERVAL_SECONDS` | 5min |
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
| `GET /api/whales/transactions?count=&asset=` | Real, most recent tracked transfers (ETH/LINK only) |
| `GET /api/sentiment?symbol=&interval=` | Real, computes + persists on every call |
| `GET /api/llm/explanation/{symbol}?interval=` | Real, computes + persists live |
| `GET /api/dashboard/intelligence?symbol=&interval=` | Real; `aiExplanation` reads the scheduler's cached anchor-symbol report (fast enough to poll) |

## Backtesting Engine (Sprint 5)

`app/backtesting/` objectively evaluates the Sprint 3 AI Decision Engine
(and, in the future, any other strategy following the same contract) by
replaying it bar by bar over historical candles — analysis only, same as
every other sprint: **no order is ever placed**, there's no Binance
Trading API integration, and every computation is deterministic (no
`random` anywhere outside the explicitly-seeded Monte Carlo utility, see
below).

```
app/backtesting/
  engine.py             orchestrates one run: validate -> bulk-load -> replay -> score -> persist
  strategy_runner.py     replays analyze_market() bar by bar, no look-ahead (see below)
  trade_simulator.py     turns Decision Engine output into simulated fills
  performance.py          win rate, profit factor, expectancy, ...
  risk_metrics.py          drawdown, Sharpe/Sortino/Calmar, recovery factor
  statistics.py             shared stats helpers + Monte Carlo trade-shuffle
  walk_forward.py            basic Train/Validation/Test fold splitting
  optimizer.py                 parameter-search interface (not yet implemented)
  report_generator.py           JSON/CSV export (PDF: architecture only)
  models/                        internal dataclasses (Trade, Config, Results) —
                                  distinct from app/models (DB) and app/schemas (API),
                                  same separation app/ai_engine/types.py keeps
  utils/                          timeframe/period arithmetic + the error hierarchy

app/services/backtest_repository.py   persistence for the 5 new tables
```

### How it works

1. **Validate** — symbol/timeframe/period must be one of the supported
   combinations (`1m/5m/15m/1h/4h/1d` × `30/90/180/365` days), and the
   resulting bar count must stay under `MAX_BACKTEST_BARS` (50,000) — a
   pure-Python bar-by-bar replay that re-runs the full Decision Engine
   every bar realistically does low hundreds to low thousands of
   bars/second, so a single HTTP request shouldn't be allowed to run for
   tens of minutes. Pick a shorter period or a coarser timeframe if you
   hit this cap.
2. **Bulk-load** — candles, funding, and open interest history are
   fetched from the database **once** (not once per bar) via
   `app/services/market_repository.py`'s `as_of`-aware queries, padded
   with `DEFAULT_CANDLE_LOOKBACK` (250) extra bars of warm-up so the
   first bar actually scored already has full indicator history.
3. **Replay** — `strategy_runner.py` slides a fixed-size window over the
   bulk-loaded data and calls `app.ai_engine.decision_engine.analyze_market()`
   **completely unmodified** for every bar — the exact same function
   `/api/ai/*` calls in real time. See "How look-ahead bias is avoided"
   below for the guarantee this relies on.
4. **Simulate** — `trade_simulator.py` turns each bar's decision into
   fills: enters LONG/SHORT at the decision bar's close when the engine
   returns a directional call with a risk plan, and exits at TP1 or SL,
   whichever a later bar's high/low touches first (stop wins if both are
   touched in the same bar — see the module's docstring for why).
5. **Score** — `performance.py` and `risk_metrics.py` compute every
   metric the spec asks for (below) from the resulting trade list.
6. **Persist** — the run, its trades, its metrics, and its equity curve
   are written to `backtest_runs`/`backtest_trades`/`backtest_metrics`/`equity_curve`.

### How to add a strategy

Today there is exactly one strategy: the unmodified Sprint 3 Decision
Engine, recorded as `strategy_versions` row `v1-default-decision-engine`
(a JSON audit snapshot of its tunable constants — Market Score factor
weights, the confidence floor, ATR/R-multiple settings — for
reproducibility, not yet used to vary behavior). To add a genuinely
different strategy in the future:

1. Give it something that produces the same shape `analyze_market()`
   does — `direction`/`confidence`/a `risk` plan (`entry`/`stop`/`tp1`) —
   `trade_simulator.py` only depends on that shape, not on
   `AIDecision`/`RiskPlan` specifically.
2. Have `strategy_runner.py` (or a sibling module) call your strategy
   instead of/alongside `analyze_market()` per bar, still from the same
   bulk-loaded, no-look-ahead window.
3. Insert a new `strategy_versions` row describing it, and reference that
   row's id from `backtest_runs.strategy_version_id`.

`optimizer.py`'s `DEFAULT_PARAMETER_SPACE` already names the concrete
parameters (Market Score weights, confidence threshold, R multiples, ATR
multiplier) a future in-place variant of the *existing* strategy would
tune — that's the more likely near-term path versus a wholly separate
strategy implementation.

### How metrics are calculated

**Performance** (`performance.py`, from the closed trade list):

| Metric | Formula |
|---|---|
| Total Return % | `net_profit / initial_balance * 100` |
| Net Profit | `sum(trade.pnl)` |
| Gross Profit / Gross Loss | `sum(winning pnls)` / `sum(losing pnls)` (loss is ≤ 0) |
| Win Rate / Loss Rate | `winning_trades / total_trades * 100` (and the loss complement) |
| Avg Win / Avg Loss | mean of winning/losing trade PnL |
| Profit Factor | `gross_profit / abs(gross_loss)` (capped at 999 with zero losses — mathematically undefined, not infinite) |
| Expectancy | `win_rate% * avg_win + loss_rate% * avg_loss` — expected $ per trade |
| Avg Trade Duration | mean of `exit_time - entry_time` across trades |

**Risk** (`risk_metrics.py`, from the trade-sequential equity curve —
balance only changes when a trade closes, see `trade_simulator.py`'s
"mark-to-close only" docstring):

| Metric | Formula |
|---|---|
| Max Drawdown % | largest peak-to-trough drop in the trade-sequential balance series |
| Recovery Factor | `net_profit / max_drawdown_$` (capped at 999 with zero drawdown) |
| Sharpe Ratio | `mean(trade pnl%) / stdev(trade pnl%) * sqrt(trades_per_year)` — from trade-level returns, not a bar-level mark-to-market series (see below) |
| Sortino Ratio | same as Sharpe, but the denominator is downside deviation only (returns below 0) |
| Calmar Ratio | `annualized_return% / max_drawdown%`, where annualized return is CAGR from `total_return%` and `period_days` |
| Risk/Reward | mean of each trade's *planned* R:R (`RiskPlan.risk_reward_tp1` at entry — the Decision Engine's own target, not the realized outcome) |

Sharpe/Sortino are computed from each trade's `pnl_percent` in sequence,
annualized by how many trades the run actually produced per year — not
from a bar-by-bar mark-to-market equity series. Since the equity curve
here only changes value when a trade closes (no intrabar unrealized P&L
tracking, see the next section's limitations), a bar-level return series
would be mostly zeros and would understate volatility in a way that
doesn't reflect the strategy's real risk. This is a deliberate choice,
not an oversight.

**Equity Curve**: one point per trade close (balance, running drawdown %,
cumulative PnL, trade count so far), plus a leading point at the run's
start — exact, not downsampled, since trade count is naturally bounded
(the simulator holds at most one position at a time).

**Monte Carlo** (`statistics.py::monte_carlo_shuffle()` /
`monte_carlo_drawdown_distribution()`): architecture for a future
robustness check. Randomly reorders the *sequence* of realized trade
PnLs — never invents or alters a value — to see how differently the
equity curve's path (and therefore its drawdown) could have looked with
the same trades in a different order. Deterministic given a seed
(`random.Random(seed)`, default `42`): the same seed always reproduces
the same reshuffling, satisfying "все вычисления должны быть
воспроизводимыми" even for a randomized technique.

### How look-ahead bias is avoided

This is the correctness property the whole engine depends on, so it's
worth stating precisely:

- **Fixed-size sliding window, not a growing one.** Bar `i`'s
  `MarketContext` is built from exactly `DEFAULT_CANDLE_LOOKBACK` (250)
  candles ending at bar `i` — the *same* window size the real-time API
  uses. Nothing after bar `i` is ever included.
- **Funding/open-interest cut off at the bar's own timestamp**, via a
  two-pointer scan that only ever advances forward as bar time increases
  (`strategy_runner.py`'s `iter_decisions()`).
- **Entry fills at the decision bar's close; exits are only checked
  starting the *next* bar.** By the time a decision is known, that bar
  has already closed — there's no more of it left to trade against. A
  position opened from bar `i`'s decision is never checked for an exit
  against bar `i`'s own high/low (`trade_simulator.py`'s docstring).
- **Macro/News/Whale snapshots are always `None` during a backtest** —
  see Limitations below for why, and confirm this is deliberate, not a
  bug: passing today's "latest" reading into a bar from months ago would
  be a severe, silent look-ahead leak.
- **Verified, not just asserted**: `tests/test_backtest_strategy_runner.py`
  and `tests/test_backtest_walk_forward.py` include automated regression
  tests that truncate the *future* portion of a candle series and assert
  every overlapping historical bar's decision is byte-identical to the
  untruncated run. This was also verified manually against a live
  Postgres instance during development.

### Limitations of the current implementation

- **Macro/News/Whale factors always read neutral in a backtest.** The
  Sprint 4 Intelligence Layer's repositories only support "give me the
  latest reading," not "give me what was known as of a past timestamp" —
  and real News/Whale collection only started very recently, so there's
  essentially no historical depth for a 30-365 day backtest window
  anyway. Rather than leak "the latest news" into a bar from the past,
  `strategy_runner.py` always passes `macro_snapshot=news_snapshot=whale_snapshot=None`,
  the same neutral "no data yet" read every scoring module already falls
  back to in real time. Closable in a future sprint once enough
  historical Macro/News/Whale data has accumulated to build point-in-time
  queries for them.
- **One position at a time.** `TradeSimulatorConfig.allow_concurrent_positions`
  exists as a config field but isn't implemented — the simulator always
  waits for the current position to close before considering a new one.
- **Trailing Stop / Break-Even / Partial Take-Profit are architecture
  only.** `TradeSimulatorConfig` accepts and stores all three (and
  `backtest_runs.config` persists them for the record), but the fill
  loop in `trade_simulator.py` doesn't act on them yet — every trade
  currently exits at a static TP1 or SL set at entry. Per the Sprint 5
  spec, this is intentional scope for this stage.
- **Mark-to-close equity, not mark-to-market.** Balance only updates
  when a trade closes; there's no bar-by-bar unrealized-P&L tracking. See
  "How metrics are calculated" above for how this shapes the Sharpe/Sortino
  formula.
- **Same-bar SL/TP conflict assumes the stop fills first.** If a single
  bar's range touches both the stop and TP1, OHLC data alone can't say
  which happened first intrabar — the simulator conservatively assumes
  the worse outcome rather than guessing favorably.
- **Optimizer is interface-only.** `optimizer.py`'s `Optimizer.run()`
  raises `NotImplementedError` — no parameter search loop exists yet.
- **Walk-Forward doesn't fit anything yet.** `walk_forward.py` reports
  real Train/Validation/Test fold boundaries and scores each fold's Test
  segment for real, but no parameter is actually tuned on Train/Validation
  (there's nothing to tune until the Optimizer is real).
- **PDF export is architecture-only.** `report_generator.py::generate_pdf_report()`
  raises `NotImplementedError`; JSON and CSV export are fully implemented.
- **`MAX_BACKTEST_BARS` (50,000) caps request size.** E.g. 1-minute
  candles over 365 days (525,600 bars) exceed this and are rejected
  up front with a clear message — pick a coarser timeframe or a shorter
  period. See "How it works" above for the throughput reasoning.
- **Measured throughput: ~100 bars/second.** A full 365-day/1h backtest
  (8,761 bars, re-running the entire Decision Engine — every scoring
  module, confidence, risk plan — each bar) took 84.8s end to end against
  a local Postgres in testing. That scales roughly linearly: a
  large-but-allowed request near `MAX_BACKTEST_BARS` (e.g. 1m candles
  over 30 days, 43,200 bars) can be expected to take several minutes in a
  single synchronous HTTP request. This is an accepted, documented
  tradeoff for this sprint rather than a hidden one — a background-job
  model (submit, poll for completion) would be the natural fix and is a
  reasonable candidate for a future sprint, but every endpoint in this
  API is synchronous today (`POST /run` blocks until the run completes),
  consistent with the rest of the app's request/response style.

### Database

| Table | Purpose |
|---|---|
| `strategy_versions` | Named, versioned strategy config snapshots |
| `backtest_runs` | One row per run: parameters, status, timing |
| `backtest_trades` | One row per simulated trade |
| `backtest_metrics` | One row per run: every performance + risk metric |
| `equity_curve` | One row per trade close (+ a leading start-of-run point) |

### API endpoints

| Endpoint | Notes |
|---|---|
| `POST /api/backtesting/run` | Runs synchronously, returns the full report (run + performance + risk) |
| `GET /api/backtesting/history?symbol=&limit=&offset=` | Past runs, newest first |
| `GET /api/backtesting/report/{run_id}` | Run metadata + performance + risk |
| `GET /api/backtesting/metrics/{run_id}` | Just performance + risk (lighter payload than `/report`) |
| `GET /api/backtesting/trades/{run_id}?limit=&offset=` | The trade list |
| `GET /api/backtesting/equity/{run_id}` | The equity curve |

### Ready for Sprint 6 (Paper Trading)

The module boundaries here were chosen with the next sprint in mind:
`trade_simulator.py`'s fill logic (entry/exit rules, commission,
slippage) is decoupled from `strategy_runner.py`'s bar replay — a Paper
Trading engine driven by the *live* feed instead of historical bars can
reuse the same `TradeSimulator`/`TradeSimulatorConfig`/`ClosedTrade`
types unchanged, feeding it real-time decisions one at a time instead of
a bulk-loaded historical array. `BacktestRunResult`/`PerformanceMetrics`/`RiskMetrics`
are equally reusable for scoring a paper-trading session's live
performance with the exact same formulas documented above.

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

The frontend Dashboard's watchlist grid reads from the user's real,
browser-persisted watchlist (`store/watchlist-store.ts`) once they've added
anything — see "Asset Intelligence Dashboard" below — and only falls back
to the fixed `WATCHLIST_SYMBOLS` in `lib/constants.ts` before that. A newly
added symbol also needs an entry in the AI-score overlay in
`lib/mock/ai-overlay.ts` for the Markets table/Dashboard cards' `aiScore`
field, otherwise it falls back to a neutral WAIT/50 placeholder.

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

## Asset Intelligence Dashboard (Sprint 8)

A per-symbol research terminal at the frontend route `/assets/{symbol}`
(e.g. `/assets/BTC`) — everything a trader would want to know about one
coin, on one page. The architecture supports any symbol the Data Engine
already tracks; there is no per-coin registration step beyond "How to add
a new coin" above.

**This module adds no new computation.** Every field on every tab is
either read straight from an existing engine/repository, or is a small,
pure, deterministic transform of values those engines already produce.
That's a deliberate boundary: the AI Decision Engine (`AI_ENGINE.md`) and
Backtesting Engine (above) stay the single source of truth for scoring
and risk, and this dashboard never duplicates or forks their logic.

### Backend: the aggregation layer

`app/services/asset_service.py` is the seam — one function per tab,
each combining a handful of existing calls into the shape the tab needs.
It never talks to the database directly for anything an existing
repository/engine already fetches; it just orchestrates. The URL uses the
bare asset (`BTC`), the Data Engine's tables key off the USDT trading pair
(`BTCUSDT`) — `to_trading_pair()`/`to_base_asset()` convert between them
with a plain string suffix (every configured quote asset in this app is
USDT, so there's no lookup table to keep in sync).

Three small new modules feed tabs that didn't have an existing engine to
wrap:

- **`app/ai_engine/indicator_explain.py`** — turns each raw indicator value
  from `IndicatorSnapshot` into a `(value, status, explanation)` triple for
  the Technical tab (e.g. `RSI 78.0 → OVERBOUGHT → "RSI at 78.0, above 70
  — momentum may be stretched."`). Pure, no I/O.
- **`app/ai_engine/smart_money.py`** — Break of Structure, Equal Highs, and
  Equal Lows are computed for real from the same swing-point detector
  `scoring/structure.py` already uses. The other five ICT/SMC concepts
  (Change of Character, Order Blocks, Fair Value Gaps, Liquidity Zones,
  Liquidity Sweep) have no detector anywhere in this codebase yet and are
  reported as `NOT_YET_IMPLEMENTED` with a one-line description of what a
  real detector would need — never a fabricated read. Each concept is one
  function in the `_CONCEPT_BUILDERS` list with the same
  `(closes, highs, lows) -> SmartMoneyConcept` signature; adding a real
  detector later is a one-function swap, see "Adding a new analytical
  module" below.
- **`app/ai_engine/scenario_analysis.py`** — the AI Analysis tab's three
  Bullish/Neutral/Bearish scenarios. Probabilities are a deterministic
  function of the Decision Engine's own `market_score` and `confidence`
  (never random): `confidence` sets how much probability mass is
  "inconclusive" (Neutral), and the rest splits between Bullish/Bearish in
  proportion to how far `market_score` leans off its neutral midpoint (50).
  Conditions and price targets are built from the same `FactorScore`s and
  ATR/structure levels `risk_engine.py` already computes.
- **`app/ai_engine/risk_analysis.py`** — ATR-based Risk Level, a
  max-recommended-leverage heuristic (inversely proportional to ATR as a
  percentage of price — a transparent risk-sizing heuristic, not a broker-
  or backtest-verified guarantee), and Drawdown Risk (reuses the Risk
  Engine's stop distance).
- **`app/services/correlation_service.py`** — Pearson correlation of
  period-over-period returns vs BTC/ETH (real, computed from this app's own
  candle history) and NASDAQ/S&P 500/Gold/DXY (same computation, against
  the Sprint 4 Macro Engine's `macro_data` history — thin today since that
  poller only just started running; returns `None` below
  `CORRELATION_MIN_DATA_POINTS` matched readings rather than a number
  computed from too little data to mean anything).
- **`app/services/history_service.py`** — the History tab's Win Rate and
  average win/loss. Every `/api/ai/*` call already persists a decision to
  `ai_analysis`; this module replays each past decision that had an active
  LONG/SHORT call against the *real* candles that followed it, checking
  whether TP1 or the stop was hit first over a bounded horizon
  (`OUTCOME_HORIZON_BARS`), using the same conservative "stop wins on a
  same-bar conflict" rule `app/backtesting/trade_simulator.py` uses. This
  is a per-signal outcome check, not a continuous strategy backtest.

### API endpoints

All under `/api/assets/{symbol}` (symbol accepts either `BTC` or
`BTCUSDT`), all read-only, all returning `404` when there isn't enough
candle history yet (same convention as `/api/ai/*`):

| Endpoint | Tab | Notes |
|---|---|---|
| `GET /api/assets/{symbol}` | Top bar | price/24h/7d/30d/market cap/volume/funding/OI/AI score |
| `GET /api/assets/{symbol}/overview` | Overview | Trend/Volatility + ATR/RSI/MACD/EMA-Alignment/VWAP |
| `GET /api/assets/{symbol}/technical` | Technical | full indicator list + Smart Money + support/resistance |
| `GET /api/assets/{symbol}/derivatives` | Derivatives | funding (+history+trend), OI (+history+delta), liquidation clusters |
| `GET /api/assets/{symbol}/whales` | Whales | whale score, recent events, 24h exchange flow |
| `GET /api/assets/{symbol}/news` | News | news filtered to this symbol |
| `GET /api/assets/{symbol}/macro` | Macro | market-wide macro backdrop (not per-symbol — see the Macro Engine's own docs) |
| `GET /api/assets/{symbol}/sentiment` | Sentiment | breakdown + radar (Social is always `null` — no Social Engine exists) |
| `GET /api/assets/{symbol}/analysis` | AI Analysis | direction/confidence/market score/entry-stop-TP1-3/risk-reward/reasons/scenarios/risk |
| `GET /api/assets/{symbol}/history` | History | win rate, avg win/loss, per-signal outcomes, score/confidence history |
| `GET /api/assets/{symbol}/correlation` | History (embedded) | Pearson coefficient vs BTC/ETH/NASDAQ/SP500/GOLD/DXY |

`overview`/`technical`/`analysis`/`sentiment` accept `?interval=` (default
`1h`, one of `TIMEFRAME_SECONDS`); `whales`/`news`/`history` accept
`?limit=`.

### Frontend

`app/(terminal)/assets/[symbol]/page.tsx` is a client component that reads
`symbol` from the route, normalizes it to upper case, and renders the top
bar (`components/assets/asset-top-bar.tsx`) plus a 9-tab `Tabs` layout. Each
tab component is its own file under `components/assets/` and is loaded via
`next/dynamic` (code-split, with a `Skeleton` fallback) — a coin's page
never ships JS for a tab the user hasn't opened.

The **watchlist** (`store/watchlist-store.ts`) is a Zustand store persisted
to `localStorage`, keyed by trading pair, storing `{ pinned, note, addedAt }`
per symbol. The top bar's "Add to Watchlist" star toggles the current
symbol in/out of it. The Dashboard's `AssetCardGrid` reads from it (pinned
first, then most-recently-added) and falls back to the fixed
`WATCHLIST_SYMBOLS` list until the user has added anything; each card gets
hover-or-focus-revealed pin/note/remove controls (`components/dashboard/asset-card.tsx`).

### Adding a new analytical module

The dashboard's tabs are intentionally uniform in shape, so adding a new
one is mechanical:

1. **Backend**: write a pure function (or a small class of them) that takes
   already-available data (a `MarketContext`, an `AIDecision`, or a
   repository query result) and returns a small `@dataclass`. Put it in
   `app/ai_engine/` if it's a scoring/analysis concept, or
   `app/services/` if it's a data-aggregation concept — follow whichever
   of `scenario_analysis.py` / `correlation_service.py` is the closer
   shape. Add a wrapper in `asset_service.py` that calls
   `to_trading_pair()`, fetches whatever context it needs, and returns your
   dataclass (or `None` for "not enough data").
2. Add a `CamelModel` response schema to `app/schemas/asset.py` mirroring
   the dataclass's fields (`snake_case` in Python, auto-converted to
   `camelCase` on the wire).
3. Add a `GET /api/assets/{symbol}/<name>` endpoint to `app/api/assets.py`
   calling the new `asset_service` function and converting to the schema
   — copy the `404`-on-`None` pattern the existing endpoints use.
4. Write unit tests for the pure function(s) against a synthetic
   `MarketContext` (see `tests/test_scenario_analysis.py`) — no database
   needed unless the module reads its own repository, in which case follow
   `tests/test_asset_service.py`'s `db_session` fixture pattern.
5. **Frontend**: add the matching TypeScript interface to `types/asset.ts`,
   a `fetchAsset<Name>()` in `services/asset-service.ts`, a
   `useAsset<Name>()` hook in `hooks/use-asset.ts`, and a tab component
   under `components/assets/`. Wire it into the `TAB_ITEMS` array and a new
   `TabsContent` in `app/(terminal)/assets/[symbol]/page.tsx`, loaded via
   `next/dynamic` like the existing tabs.

The Smart Money module (`app/ai_engine/smart_money.py`) is the reference
example for "architecture ready, concept not yet real": each concept is one
function with the same signature in `_CONCEPT_BUILDERS`, so swapping a
`NOT_YET_IMPLEMENTED` placeholder for a real detector never touches the
caller.

### Known limitations

- **Smart Money**: only Break of Structure/Equal Highs/Equal Lows are real
  today (see above); the other five ICT concepts are placeholders.
- **Correlation**: BTC/ETH references are real now; NASDAQ/S&P 500/Gold/DXY
  need the Macro Engine to accumulate `CORRELATION_MIN_DATA_POINTS` (20)
  matched readings before they stop returning `null`.
- **Whale coverage**: only ETH and LINK have an Ethereum-based footprint
  (see `app/intelligence/whales/addresses.py`) — other symbols' Whales tab
  reads a neutral, zero-conviction score with no events.
- **Sentiment radar's Social axis**: always `null` — there is no Social
  Engine anywhere in this codebase yet.
- **History tab win rate**: only resolves signals that had an active
  LONG/SHORT call *and* whose TP1/stop was hit within
  `OUTCOME_HORIZON_BARS` (100) bars of the signal; older or still-open
  signals show as `OPEN`/`NO_TRADE` and are excluded from the win-rate
  denominator.
- **Scenario Analysis probabilities** are a transparent, auditable formula
  over the Decision Engine's own outputs — not a machine-learned or
  backtested probability distribution. Documented as a heuristic, not a
  forecast guarantee.

### Ready for Sprint 5 (Backtesting) and future Paper Trading

- The History tab's outcome resolution already replays TP1/stop against
  real forward candles using the exact same conservative fill rule the
  Backtesting Engine's `trade_simulator.py` uses — the two are logically
  consistent, so a future "run this symbol's history through the full
  Backtesting Engine" link is a straightforward extension, not a rewrite.
- `asset_service.py`'s per-tab functions all take a `base_asset` and
  `interval` and return typed dataclasses with no framework coupling —
  they're already usable from a background job (e.g. a Paper Trading
  engine wanting a symbol's current AI Analysis) without going through
  the HTTP layer at all.
