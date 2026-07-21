"""Parses raw Binance combined-stream payloads into typed events."""

from dataclasses import dataclass


@dataclass(frozen=True)
class KlineEvent:
    symbol: str
    interval: str
    open_time: int
    close_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float
    trades: int
    is_closed: bool


@dataclass(frozen=True)
class MarkPriceEvent:
    symbol: str
    mark_price: float
    index_price: float
    funding_rate: float
    next_funding_time: int
    event_time: int


@dataclass(frozen=True)
class MiniTickerEvent:
    symbol: str
    close: float
    open: float
    high: float
    low: float
    volume: float
    quote_volume: float
    event_time: int


@dataclass(frozen=True)
class AggTradeEvent:
    symbol: str
    price: float
    quantity: float
    trade_time: int
    is_buyer_maker: bool


@dataclass(frozen=True)
class LiquidationOrderEvent:
    """One forced-liquidation fill. `side` is the side of the *position*
    that got liquidated (LONG/SHORT) — Binance's own `S` field is the
    order side of the forced order itself (a liquidated long is force-
    SOLD, a liquidated short is force-BOUGHT), so it's inverted here to
    match what the UI actually wants to show."""

    symbol: str
    side: str  # "LONG" | "SHORT" — the liquidated position's side
    price: float
    quantity: float
    trade_time: int
    event_time: int


StreamEvent = KlineEvent | MarkPriceEvent | MiniTickerEvent | AggTradeEvent | LiquidationOrderEvent


def _parse_kline(data: dict) -> KlineEvent:
    k = data["k"]
    return KlineEvent(
        symbol=data["s"],
        interval=k["i"],
        open_time=int(k["t"]),
        close_time=int(k["T"]),
        open=float(k["o"]),
        high=float(k["h"]),
        low=float(k["l"]),
        close=float(k["c"]),
        volume=float(k["v"]),
        quote_volume=float(k["q"]),
        trades=int(k["n"]),
        is_closed=bool(k["x"]),
    )


def _parse_mark_price(data: dict) -> MarkPriceEvent:
    return MarkPriceEvent(
        symbol=data["s"],
        mark_price=float(data["p"]),
        index_price=float(data.get("i", data["p"])),
        funding_rate=float(data["r"]),
        next_funding_time=int(data["T"]),
        event_time=int(data["E"]),
    )


def _parse_mini_ticker(data: dict) -> MiniTickerEvent:
    return MiniTickerEvent(
        symbol=data["s"],
        close=float(data["c"]),
        open=float(data["o"]),
        high=float(data["h"]),
        low=float(data["l"]),
        volume=float(data["v"]),
        quote_volume=float(data["q"]),
        event_time=int(data["E"]),
    )


def _parse_agg_trade(data: dict) -> AggTradeEvent:
    return AggTradeEvent(
        symbol=data["s"],
        price=float(data["p"]),
        quantity=float(data["q"]),
        trade_time=int(data["T"]),
        is_buyer_maker=bool(data["m"]),
    )


def _parse_liquidation(data: dict) -> LiquidationOrderEvent:
    order = data["o"]
    price = float(order.get("ap") or order["p"])
    return LiquidationOrderEvent(
        symbol=order["s"],
        side="LONG" if order["S"] == "SELL" else "SHORT",
        price=price,
        quantity=float(order["z"]),
        trade_time=int(order["T"]),
        event_time=int(data["E"]),
    )


_EVENT_PARSERS = {
    "kline": _parse_kline,
    "markPriceUpdate": _parse_mark_price,
    "24hrMiniTicker": _parse_mini_ticker,
    "aggTrade": _parse_agg_trade,
    "forceOrder": _parse_liquidation,
}


def parse_stream_message(raw: dict) -> StreamEvent | None:
    """`raw` is the outer combined-stream envelope: {"stream": ..., "data": {...}}."""
    data = raw.get("data")
    if not data:
        return None

    event_type = data.get("e")
    parser = _EVENT_PARSERS.get(event_type)
    if parser is None:
        return None

    return parser(data)
