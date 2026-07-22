"""LLM Explanation Layer (Sprint 4).

Turns an already-computed `AIDecision` (+ macro/sentiment context) into
narrative prose. This is the *only* place in the app an LLM's output
reaches the user as analysis, and it is deliberately narrow:

- `direction` and `confidence` are copied straight from `AIDecision` /
  `SentimentResult` — the model is never asked for them and can't
  override them (see `LlmExplanation`'s dataclass below: those two
  fields don't even appear in the tool schema the model responds to).
- The model is given the engine's own numbers/reasons as structured
  facts and forced (via `tool_choice`) to respond through a fixed JSON
  schema — it cannot free-associate a different shape, and the system
  prompt explicitly forbids inventing facts not present in the input.
- It never suggests placing a trade; the system prompt says so
  explicitly, same constraint as `app/services/claude_chat.py`.

This module calls Claude directly (not through `claude_chat.py`, which is
conversational chat with its own history/session concerns) but shares the
same `ANTHROPIC_API_KEY`/fail-open philosophy: no key configured, or an
upstream error, returns a clearly-labeled fallback instead of raising.
"""

from dataclasses import dataclass

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.decision_engine import analyze_market
from app.ai_engine.market_context import build_market_context
from app.ai_engine.types import Direction
from app.core.config import get_settings
from app.core.logging import get_logger
from app.intelligence.sentiment.engine import SentimentResult, compute_sentiment

logger = get_logger(__name__)

NOT_CONFIGURED_SUMMARY = (
    "LLM explanations aren't configured yet — set ANTHROPIC_API_KEY in backend/.env and restart the backend. "
    "The Direction/Confidence below are still real, computed by the deterministic AI Decision Engine; only the "
    "narrative explanation is unavailable."
)
UPSTREAM_ERROR_SUMMARY = (
    "Couldn't reach Claude to generate a narrative explanation just now. The Direction/Confidence below are "
    "still real and unaffected."
)

SYSTEM_PROMPT = (
    "You explain the output of a deterministic, rules-based crypto market analysis engine (not you) to a "
    "trading terminal's user. You will be given that engine's already-computed Market Score, Confidence, "
    "Direction, per-factor reasons, a risk plan, macro context, and a sentiment breakdown as structured facts. "
    "Call emit_explanation with a plain-English summary, key drivers, risks, opportunities, and affected assets "
    "— every claim must be traceable to a fact given to you below. Do not invent numbers, news, or events not "
    "present in the input. Do not tell the user to buy, sell, or place any specific order — describe what the "
    "data shows and let them decide."
)

EXPLANATION_TOOL = {
    "name": "emit_explanation",
    "description": "Emit the structured, human-readable explanation of the given AI Decision Engine output.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "1-3 sentence plain-English summary of the direction and why.",
            },
            "key_drivers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The factors most responsible for the current read, grounded in the input facts.",
            },
            "risks": {
                "type": "array",
                "items": {"type": "string"},
                "description": "What could invalidate this read or hurt a position taken on it.",
            },
            "opportunities": {
                "type": "array",
                "items": {"type": "string"},
                "description": "What the setup offers if it plays out, grounded in the risk plan given.",
            },
            "assets_affected": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Symbols this explanation is directly relevant to (at least the analyzed symbol).",
            },
        },
        "required": ["summary", "key_drivers", "risks", "opportunities", "assets_affected"],
    },
}


@dataclass(frozen=True)
class LlmExplanation:
    symbol: str
    interval: str
    timestamp: int
    direction: Direction
    confidence: float
    summary: str
    key_drivers: list[str]
    risks: list[str]
    opportunities: list[str]
    assets_affected: list[str]


def _fallback_explanation(sentiment: SentimentResult, summary: str) -> LlmExplanation:
    return LlmExplanation(
        symbol=sentiment.symbol,
        interval=sentiment.interval,
        timestamp=sentiment.timestamp,
        direction=sentiment.direction,
        confidence=sentiment.confidence,
        summary=summary,
        key_drivers=sentiment.reasons[:5],
        risks=[],
        opportunities=[],
        assets_affected=[sentiment.symbol],
    )


def _build_facts_payload(sentiment: SentimentResult) -> dict:
    return {
        "symbol": sentiment.symbol,
        "interval": sentiment.interval,
        "overall_direction": sentiment.direction,
        "overall_confidence": round(sentiment.confidence, 1),
        "overall_score": round(sentiment.overall_score, 1),
        "categories": {
            name: {
                "score": round(factor.score, 1),
                "direction": factor.direction,
                "confidence": round(factor.confidence, 1),
                "reasons": factor.reasons,
            }
            for name, factor in sentiment.breakdown.items()
        },
    }


async def build_llm_explanation(db: AsyncSession, symbol: str, interval: str) -> LlmExplanation | None:
    """Returns None if there isn't enough candle history yet (same gate
    `compute_sentiment`/`/api/signals` use)."""
    sentiment = await compute_sentiment(db, symbol, interval)
    if sentiment is None:
        return None

    settings = get_settings()
    if not settings.anthropic_api_key:
        return _fallback_explanation(sentiment, NOT_CONFIGURED_SUMMARY)

    ctx = await build_market_context(db, symbol, interval)
    assert ctx is not None  # compute_sentiment already confirmed this above
    decision = analyze_market(ctx)
    risk_facts = None
    if decision.risk is not None:
        risk_facts = {
            "entry": decision.risk.entry,
            "stop": decision.risk.stop,
            "take_profit_1": decision.risk.tp1,
            "take_profit_2": decision.risk.tp2,
            "take_profit_3": decision.risk.tp3,
            "risk_reward_tp2": round(decision.risk.risk_reward_tp2, 2),
        }

    facts = _build_facts_payload(sentiment)
    facts["risk_plan"] = risk_facts

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    try:
        response = await client.messages.create(
            model=settings.anthropic_chat_model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=[EXPLANATION_TOOL],
            tool_choice={"type": "tool", "name": "emit_explanation"},
            messages=[{"role": "user", "content": f"Structured facts:\n{facts}"}],
        )
    except anthropic.APIError:
        logger.warning("llm_explanation_upstream_error", exc_info=True)
        return _fallback_explanation(sentiment, UPSTREAM_ERROR_SUMMARY)
    finally:
        await client.close()

    tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
    if not tool_use_blocks:
        return _fallback_explanation(sentiment, UPSTREAM_ERROR_SUMMARY)

    tool_input = tool_use_blocks[0].input
    return LlmExplanation(
        symbol=sentiment.symbol,
        interval=sentiment.interval,
        timestamp=sentiment.timestamp,
        direction=sentiment.direction,
        confidence=sentiment.confidence,
        summary=str(tool_input.get("summary", "")),
        key_drivers=list(tool_input.get("key_drivers", [])),
        risks=list(tool_input.get("risks", [])),
        opportunities=list(tool_input.get("opportunities", [])),
        assets_affected=list(tool_input.get("assets_affected", [sentiment.symbol])),
    )
