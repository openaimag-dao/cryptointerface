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
Layer" section. Backtesting (Sprint 5) is real as well — it replays the
same unmodified AI Decision Engine bar by bar over historical candles
with no look-ahead bias, see backend/README.md's "Backtesting Engine"
section. Sprint 8 adds an **Asset Intelligence Dashboard** — a per-symbol
research terminal at `/assets/{symbol}` (e.g. `/assets/BTC`) with 9 tabs
(Overview, Technical, Derivatives, Whales, News, Macro, Sentiment, AI
Analysis, History) plus a persisted Watchlist, all built by aggregating
the existing engines above with no new computation — see
backend/README.md's "Asset Intelligence Dashboard" section for the full
breakdown and how to add a new tab/module. Portfolio and the Macro
economic-calendar tab remain on mock data — out of scope until a future
sprint. If Binance is unreachable from your network, a CoinGecko fallback
kicks in automatically — see backend/README.md's "CoinGecko fallback"
section.

## News Portal (public) + private terminal

`/` is now a public, SEO-indexable **news portal** — Crypto, AI,
Blockchain, and Innovation headlines aggregated from 9 real RSS sources
and classified automatically, with an AI-narrated digest per topic (real
articles only, no fabrication — see backend/README.md's "News Portal
(Public)" section). The trading terminal itself (Dashboard, Markets,
Assets, etc.) moved to `/dashboard` and friends, gated by a real login
(`/login`, `/register`) rather than a shared secret, so it stays private
while living in the same app:

| Route | Access |
|---|---|
| `/`, `/category/{crypto,ai,blockchain,innovation}`, `/article/{id}`, `/search`, `/trending` | Public |
| `/login`, `/register` | Public |
| `/dashboard`, `/markets`, `/assets/{symbol}`, `/ai-chat`, `/portfolio`, `/signals`, `/backtesting`, `/liquidations`, `/macro`, `/news`, `/sentiment`, `/settings`, `/whales`, `/saved`, `/watchlist`, `/account` | Requires a logged-in session |
| `/admin/news`, `/admin/sources`, `/admin/monitoring` | Requires a logged-in session with `role="admin"` |

`middleware.ts` verifies the same JWT the backend issues on
register/login (`lib/session.ts`, via the `jose` library so it works in
the Edge runtime) — set `JWT_SECRET_KEY` (frontend, server-only) to the
**exact same value** as the backend's `JWT_SECRET_KEY`
(backend/.env.example), or every terminal route redirects to `/login`
(fails closed by design, same reasoning the old Basic Auth gate used).
The backend and frontend are on separate domains (Railway/Vercel), so
register/login proxy through this frontend's own `/api/auth/*` Route
Handlers, which set a first-party httpOnly cookie — the raw token never
reaches client-side JS. `NEXT_PUBLIC_SITE_URL` (also frontend) is the
canonical URL used by `app/sitemap.ts`/`app/robots.ts` for absolute URLs
and OpenGraph tags.

### Portal visual identity

The public portal (`app/(portal)/`) deliberately looks nothing like the
trading terminal: a warm paper background, ink text, a serif headline
typeface (Source Serif 4, `--font-serif`), and a muted editorial
green/brick-red palette instead of the terminal's dark background and
neon-green accent. This is scoped by a `.portal-theme` class wrapping
`app/(portal)/layout.tsx`'s root element (`app/globals.css`) that
redefines the same CSS custom properties (`--background`, `--accent`,
etc.) the terminal uses — so every existing UI primitive (`Card`,
`Badge`, `Button`...) re-themes automatically with zero component
changes, and the terminal's own dark theme is completely unaffected
outside that scope. `PageHeader` takes an optional `serif` prop for
portal section headings; the terminal's dashboard-style pages leave it
off.

Article images (`NewsItem.imageUrl`) are real image URLs pulled from
each source's own RSS feed (Media RSS `<media:content>`/
`<media:thumbnail>` or a plain `<enclosure>` — see backend/README.md's
"real article images" section) — never a placeholder graphic, so a
card or the article-page hero simply omits the image entirely when the
source's feed doesn't include one. `components/portal/article-image.tsx`
handles a URL that later goes stale (the publisher deletes/moves it) by
hiding itself on load failure rather than showing a broken-image icon.

**Live prices**: `components/portal/price-ticker.tsx` reads the same
real, public `GET /api/market` endpoint the trading terminal uses
(Binance-backed via the Data Engine, no auth required) — not a separate
or mocked feed — and renders every configured symbol's price + 24h
change as a strip at the very top of every portal page.

**Multilingual (EN/RU/KK)**: `lib/portal-i18n.ts` holds the portal's UI
chrome strings (nav, buttons, empty states) for all three languages, plus
per-topic labels/descriptions. The reader's choice is a first-party
`portal_lang` cookie, set by `GET /api/locale?lang=ru&next=/path`
(`components/portal/language-switcher.tsx`'s EN/RU/KK links in the
masthead) and read by every portal page via `cookies()` to both pick the
UI strings and request translated article content from the backend
(`?lang=` on `/api/news/*` — see backend/README.md's "article translation"
section). An article without a translation yet falls back to its
original English silently — never a blank or an error.

`/admin/news` is the editorial moderation queue (backend/README.md's
"News Platform: editorial workflow + admin panel" section) — `middleware.ts`
additionally checks the JWT's `role` claim is `"admin"` before allowing
`/admin/*` through, redirecting anyone else to `/`. That check is UX-layer
only: every `/api/admin/*` Route Handler forwards the session cookie as a
Bearer token to the backend, which independently re-checks the
DB-persisted role on every request, so a stale JWT (e.g. after a demotion)
can never grant real admin access even if it slipped past the frontend
gate. The Sidebar only renders the "Admin" nav link for `role="admin"`
users (`lib/constants.ts::ADMIN_NAV_ITEM`); there's no in-app way to
become an admin — see `backend/scripts/promote_to_admin.py`.

`app/(terminal)/admin/layout.tsx` adds a News / Sources / Monitoring tab
strip shared by all `/admin/*` pages. `/admin/sources` lists the
DB-backed RSS source registry with live `enabled`/`auto-publish` toggles
(backend/README.md's "source management" section) — a change here
affects the very next poll cycle, no deploy. `/admin/monitoring` is a
read-only table of recent RSS poll attempts (`NewsFetchLog`), so a
persistently-failing source is visible rather than silently going quiet.
