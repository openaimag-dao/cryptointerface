from app.schemas.base import CamelModel


class TradeUpdate(CamelModel):
    """Aggregate trade tick, pushed over WebSocket on the "trade" channel."""

    symbol: str
    price: float
    quantity: float
    trade_time: int
    is_buyer_maker: bool
