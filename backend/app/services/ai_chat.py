"""AI Chat backend — answers questions about the live terminal state.

This is intentionally separate from `app/ai_engine/`: the Decision Engine
that drives Market Score / Confidence / Direction / Risk stays
deterministic and never calls an LLM. The chat model here only narrates a
snapshot that engine already computed — it never generates its own score,
and it never places or suggests placing an order.
"""

from dataclasses import dataclass

from app.ai_engine.decision_engine import analyze_market
from app.ai_engine.market_context import build_market_context
from app.core.config import get_settings
from app.database.session import AsyncSessionLocal
from app.services.gemini_client import generate_text

NOT_CONFIGURED_MESSAGE = "AI Chat isn't configured yet — set GEMINI_API_KEY in backend/.env and restart the backend."
UPSTREAM_ERROR_MESSAGE = "I couldn't reach the AI assistant just now. Please try again in a moment."

SYSTEM_PROMPT = (
    "You are the AIMAG AI Terminal assistant, embedded in a crypto trading dashboard. "
    "You are given a snapshot of the current watchlist below, computed by a separate "
    "deterministic rules-based engine (not you) from live Binance USDT-M Futures data. "
    "Use it to answer questions about market conditions, AI signals, and the dashboard. "
    "Be concise. You are not a financial advisor and must not tell the user to buy, sell, "
    "or place any specific order — describe what the data shows and let them decide."
)

_DEFAULT_INTERVAL = "1h"


@dataclass(frozen=True)
class ChatTurn:
    role: str  # "user" | "assistant"
    content: str


async def build_watchlist_snapshot(interval: str = _DEFAULT_INTERVAL) -> str:
    """One line per watchlist symbol with the latest AI Decision Engine
    read, for use as the chat model's system-prompt context. Symbols with
    no candle history yet (fresh backfill, Binance unreachable) are
    skipped rather than shown as an error — same tolerance as
    `/api/signals`."""
    settings = get_settings()
    lines: list[str] = []

    async with AsyncSessionLocal() as db:
        for symbol in settings.symbol_list:
            ctx = await build_market_context(db, symbol, interval)
            if ctx is None:
                continue
            decision = analyze_market(ctx)
            lines.append(
                f"{symbol}: price ${ctx.last_close:,.2f}, market score {decision.market_score:.0f}/100, "
                f"confidence {decision.confidence:.0f}%, direction {decision.direction} ({interval} timeframe)"
            )

    if not lines:
        return "No live market data available yet for the watchlist."
    return "Current watchlist snapshot:\n" + "\n".join(lines)


async def send_chat_message(content: str, history: list[ChatTurn]) -> str:
    settings = get_settings()
    if not settings.gemini_api_key:
        return NOT_CONFIGURED_MESSAGE

    snapshot = await build_watchlist_snapshot()
    system_prompt = f"{SYSTEM_PROMPT}\n\n{snapshot}"

    messages = [{"role": turn.role, "content": turn.content} for turn in history]
    messages.append({"role": "user", "content": content})

    reply = await generate_text(system_prompt=system_prompt, messages=messages, max_output_tokens=1024)
    return reply if reply else UPSTREAM_ERROR_MESSAGE
