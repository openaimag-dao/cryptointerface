from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import backtesting, chat, liquidations, macro, markets, news, portfolio, signals, whales

settings = get_settings()

app = FastAPI(
    title="AIMAG AI Terminal API",
    description="Backend for the AIMAG AI trading terminal. Sprint 1 serves mock data; "
    "Sprint 2 wires up live Binance market data and the AI reasoning engine.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(markets.router)
app.include_router(signals.router)
app.include_router(portfolio.router)
app.include_router(news.router)
app.include_router(whales.router)
app.include_router(liquidations.router)
app.include_router(macro.router)
app.include_router(backtesting.router)
app.include_router(chat.router)


@app.get("/api/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}
