from app.schemas.base import CamelModel


class FundingRate(CamelModel):
    symbol: str
    funding_rate: float
    mark_price: float
    funding_time: int
    next_funding_time: int | None = None
