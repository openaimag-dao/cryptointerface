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

    # Sprint 3: AI reasoning engine
    ai_provider_api_key: str = ""

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
