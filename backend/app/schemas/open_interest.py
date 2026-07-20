from app.schemas.base import CamelModel


class OpenInterest(CamelModel):
    symbol: str
    open_interest: float
    open_interest_value: float
    timestamp: int
