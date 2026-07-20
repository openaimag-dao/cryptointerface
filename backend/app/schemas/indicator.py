from app.schemas.base import CamelModel


class EmaValues(CamelModel):
    ema_20: float | None = None
    ema_50: float | None = None
    ema_100: float | None = None
    ema_200: float | None = None


class MacdValues(CamelModel):
    macd: float | None = None
    signal: float | None = None
    histogram: float | None = None


class BollingerBandsValues(CamelModel):
    upper: float | None = None
    middle: float | None = None
    lower: float | None = None


class StochRsiValues(CamelModel):
    k: float | None = None
    d: float | None = None


class PivotLevels(CamelModel):
    pivot: float | None = None
    r1: float | None = None
    r2: float | None = None
    r3: float | None = None
    s1: float | None = None
    s2: float | None = None
    s3: float | None = None


class IndicatorSnapshot(CamelModel):
    """All computed indicator values for one symbol/interval/candle."""

    symbol: str
    interval: str
    time: int
    ema: EmaValues
    rsi_14: float | None = None
    macd: MacdValues
    atr_14: float | None = None
    bollinger_bands: BollingerBandsValues
    vwap: float | None = None
    adx_14: float | None = None
    obv: float | None = None
    stoch_rsi: StochRsiValues
    pivot: PivotLevels
