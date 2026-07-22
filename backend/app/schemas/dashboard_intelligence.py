"""Schema for the Dashboard's "Market Intelligence" card.

`overall_score` is the AI Decision Engine's own Market Score (the
Sentiment Engine's "technical" category — see
`app/intelligence/sentiment/engine.py`) since that's what "Overall Market
Score" means everywhere else in the app (`/api/ai/*`, `/api/signals`).
`sentiment_score` is the broader Sentiment Engine blend across
technical+macro+news+whales+liquidations — a distinct, wider-lens number,
which is why the card shows both rather than one duplicating the other.
"""

from app.schemas.base import CamelModel
from app.schemas.llm import LlmExplanationOut
from app.schemas.market import Direction


class DashboardIntelligence(CamelModel):
    symbol: str
    interval: str
    overall_score: float
    direction: Direction
    macro_score: float
    news_score: float
    whale_score: float
    liquidation_score: float
    sentiment_score: float
    last_updated: str
    ai_explanation: LlmExplanationOut | None
