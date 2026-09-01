from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "LINKUSDT",
    "DOGEUSDT",
    "BNBUSDT",
    "XRPUSDT",
]

DEFAULT_TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]


class Settings(BaseSettings):
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    # Database
    database_url: str = "postgresql+asyncpg://aimag:aimag@localhost:5432/aimag"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Binance — USDT-M Futures endpoints (funding rate / open interest are
    # futures-only concepts; klines/ticker are available on both markets).
    binance_rest_base_url: str = "https://fapi.binance.com"
    binance_ws_base_url: str = "wss://fstream.binance.com"
    binance_api_key: str = ""
    binance_api_secret: str = ""

    # CoinGecko — public spot-market fallback used only when Binance is
    # unreachable (e.g. geo-restricted egress). No funding rate/open
    # interest equivalent, no WebSocket — REST-polled ticker + best-effort
    # OHLC candles only. See app/services/coingecko/ and
    # app/tasks/coingecko_fallback.py.
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"

    # Data engine
    symbols: str = ",".join(DEFAULT_SYMBOLS)
    timeframes: str = ",".join(DEFAULT_TIMEFRAMES)
    historical_candles_per_timeframe: int = 5000
    ws_reconnect_min_delay_seconds: float = 1.0
    ws_reconnect_max_delay_seconds: float = 60.0
    ws_heartbeat_interval_seconds: float = 30.0

    # Every AI-powered feature (chat, translation, digest, processing,
    # explanation — see app/services/gemini_client.py) shares this one
    # Gemini key. The AI Decision Engine itself (app/ai_engine/) stays
    # deterministic/no-LLM; this key never touches signal/score/direction
    # generation. Gemini over Anthropic/OpenAI specifically because it has
    # a real free tier (Google AI Studio, no card required) — the others
    # don't, and this app's actual call volume fits comfortably inside it.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Real user accounts (app/services/auth_service.py) — register/login for
    # the private dashboard, separate from the public News Portal. Blank
    # means auth is unconfigured; register/login fail closed (503) rather
    # than issuing tokens no one can safely verify. Generate one with
    # `openssl rand -hex 32` — never commit a real value.
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Sprint 4: Intelligence Layer (app/intelligence/).
    # All 10 macro indicators are free/keyless (Yahoo Finance's public
    # chart endpoint + alternative.me + CoinGecko — see
    # app/intelligence/macro/providers.py), no tiny daily quota to poll
    # around anymore, so this is on the same order as this app's other
    # scheduler intervals rather than deliberately stretched out.
    macro_poll_interval_seconds: float = 1_800.0  # 30min
    sentiment_recompute_interval_seconds: float = 300.0  # 5min
    llm_explanation_interval_seconds: float = 1_800.0  # 30min
    llm_explanation_anchor_symbol: str = "BTCUSDT"
    # RSS feeds tolerate frequent polling, so this can run far more often
    # than the macro poller — see app/intelligence/news/.
    news_poll_interval_seconds: float = 600.0  # 10min
    # News Portal AI digest (app/intelligence/llm/news_digest.py) — one
    # AI call per portal topic per cycle, so this stays hourly rather
    # than matching news_poll_interval_seconds.
    news_digest_interval_seconds: float = 3_600.0  # 1h
    # AI News Processing (app/intelligence/llm/news_processing.py) — one
    # AI call per unprocessed article per batch, so this runs often
    # enough to keep the backlog small without hammering the API.
    ai_processing_interval_seconds: float = 900.0  # 15min
    ai_processing_batch_size: int = 20

    # News Translation (app/intelligence/llm/news_translation.py) — one
    # AI call per untranslated article per language per batch, so this
    # runs on its own slower cadence rather than matching
    # ai_processing_interval_seconds (translating is a lower-priority
    # enrichment than the original summary/entities).
    translation_interval_seconds: float = 1_800.0  # 30min
    translation_batch_size: int = 10

    # Whale Engine (app/intelligence/whales/) — Etherscan free tier (5
    # req/sec, 100k/day, get a key at https://etherscan.io/apis). Leave
    # blank to disable; the poller then simply persists nothing. Only
    # transfers at or above this USD value are persisted.
    etherscan_api_key: str = ""
    whale_poll_interval_seconds: float = 300.0  # 5min
    whale_min_usd_threshold: float = 250_000.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def symbol_list(self) -> list[str]:
        return [symbol.strip().upper() for symbol in self.symbols.split(",") if symbol.strip()]

    @property
    def timeframe_list(self) -> list[str]:
        return [tf.strip() for tf in self.timeframes.split(",") if tf.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
