# AI Decision Engine v1.0

A fully deterministic, reproducible market-analysis engine. Given the same
candle/funding/open-interest history, it always returns the exact same
Market Score, Confidence, Direction, reasons, and risk plan — there is no
randomness, no LLM, and no learned/trained model anywhere in this module.

**Scope**: analysis only. The engine never places an order, never talks to
an exchange's trading endpoints, and never executes anything. It computes
numbers and explains them; a human (or a future execution layer, explicitly
out of scope for now) decides what to do with them.

LLM usage is intentionally deferred to a future sprint, and even then only
to turn this engine's already-computed, already-deterministic output into
friendlier natural-language prose — never to compute the score, direction,
or risk numbers themselves. That keeps the engine reproducible and testable
independent of any model's sampling behavior.

## Where it lives

```
app/ai_engine/
  types.py              shared FactorScore contract + pure math helpers
  market_context.py      one DB round-trip -> in-memory MarketContext snapshot
  market_score.py         weighted aggregation of every scoring module
  confidence_engine.py    0-100 "how much to trust this" score
  decision_engine.py      strict LONG/SHORT/WAIT gate + top-level orchestrator
  risk_engine.py           ATR + structure -> entry/stop/TP1-3/RR
  reason_generator.py     merges + guarantees >= 5 reasons
  scoring/
    trend.py       EMA20/50/100/200 alignment, EMA50 slope, HH/HL structure
    momentum.py     RSI, MACD, Stochastic RSI
    volatility.py    ATR trend, Bollinger Band width (expansion/compression)
    volume.py        volume trend, OBV, VWAP, approximated delta volume
    structure.py     pivot levels, swing support/resistance, breakout/breakdown
    funding.py       funding rate level + trend (contrarian at extremes)
    oi.py             open interest vs price divergence matrix
    macro.py          Sprint 4 stub (BTC Dominance/DXY/Gold/S&P500/NASDAQ/VIX)
    news.py           Sprint 4 stub (news/whale-wallet sentiment)
```

Every scoring module is a pure function: numpy arrays (or plain lists) in,
a `FactorScore` out. None of them touch the database — `market_context.py`
is the only place that does I/O, so the rest of the engine can be unit
tested with synthetic arrays and no Postgres connection at all (see
`backend/tests/test_ai_*.py`).

## The `FactorScore` contract

```python
FactorScore(
    name: str,                 # "trend", "momentum", ...
    score: float,               # 0-100
    direction: "LONG"|"SHORT"|"WAIT",  # derived from score, see thresholds below
    strength: float,            # 0-100, how far score sits from neutral (50)
    reasons: list[str],         # human-readable, always non-empty
    details: dict,              # module-specific numbers (ema20, rsi, nearest_support, ...)
)
```

`direction` and `strength` are always *derived* from `score`, never set
independently — `direction_from_score()` applies fixed thresholds
(`score >= 65` -> LONG, `score <= 35` -> SHORT, otherwise WAIT), and
`strength_from_score()` is `clamp(abs(score - 50) * 2)`. These thresholds
match the ones already used by the pre-Sprint-3 frontend AI-score overlay,
so a "score of 76" means the same thing everywhere in the app.

Every scoring module starts its internal score at the neutral baseline
(50) and adds/subtracts fixed point budgets for each condition it detects,
then lets `make_factor_score()` clamp the result to `[0, 100]`. The exact
point budget for each module is documented in its own docstring — see
`app/ai_engine/scoring/*.py`.

## 1. Market Score — `market_score.py`

The Market Score is a fixed-weight sum of all nine factor scores:

| Factor       | Weight | Why |
|--------------|-------:|-----|
| trend        | 0.22   | Most predictive, well-established technical factor |
| momentum     | 0.18   | Confirms/leads trend |
| structure    | 0.18   | Support/resistance and breakouts matter as much as trend |
| oi           | 0.15   | Open interest confirms whether a move has real conviction |
| volume       | 0.12   | Confirms participation behind a move |
| funding      | 0.10   | Positioning/sentiment signal, contrarian at extremes |
| volatility   | 0.05   | Directionally ambiguous on its own — low weight by design |
| macro        | 0.00   | Sprint 4 stub — zero weight until real data lands |
| news         | 0.00   | Sprint 4 stub — zero weight until real data lands |

```
market_score = clamp( sum(factor.score * weight for each factor) )
market_direction = direction_from_score(market_score)
```

Weights are hardcoded constants (`FACTOR_WEIGHTS` in `market_score.py`),
not learned or tuned by any statistical process — that's what makes the
aggregate as reproducible and auditable as each individual factor. Wiring
real macro/news data in a later sprint only requires raising their weight
here (and rebalancing the others down); nothing else in the engine changes.

## 2. Confidence Engine — `confidence_engine.py`

Confidence answers a different question than the Market Score: the score
says *which way* the market leans, confidence says *how much to trust that
read*. It's a weighted blend of two signals:

```
agreement_pct = (sum of weights of factors whose direction == market_direction)
                / (sum of all factor weights) * 100

avg_strength  = weighted average of every factor's `strength`

confidence = clamp(0.6 * agreement_pct + 0.4 * avg_strength)
```

- **Agreement** (60% of the score): if most of the weight is pointing the
  same way as the aggregate, that's more trustworthy than a score that
  only "wins" narrowly with factors pulling in opposite directions.
- **Strength** (40% of the score): even with perfect agreement, a bunch
  of barely-off-neutral factors (all scoring ~55) is a weaker signal than
  the same agreement with everything scoring near 0/100.

No randomness anywhere in this formula — same factors in, same confidence
out, every time.

## 3. Decision Engine — `decision_engine.py`

`decide_direction()` is the engine's only path to a LONG/SHORT/WAIT call,
and it is intentionally conservative:

```python
def decide_direction(market_direction, confidence):
    if market_direction == "WAIT":
        return "WAIT"
    if confidence < MIN_CONFIDENCE_FOR_ACTION:  # 45.0
        return "WAIT"
    return market_direction
```

A Market Score that leans LONG or SHORT is only turned into an actionable
call if confidence clears the floor (45/100); otherwise the engine
downgrades to WAIT rather than act on a low-conviction read. There is no
fourth value, and no code path returns anything else — this is enforced by
the `Direction = Literal["LONG", "SHORT", "WAIT"]` type across the whole
engine.

`analyze_market(ctx: MarketContext) -> AIDecision` is the orchestration
entry point the API layer calls: it runs `compute_market_score`, then
`compute_confidence`, then `decide_direction`, then `generate_reasons`,
then `compute_risk_plan` — all in one deterministic pass over a single
`MarketContext` snapshot (so nothing can change mid-computation between
reading the score and reading the risk plan).

## 4. Risk Engine — `risk_engine.py`

Returns `None` for a WAIT decision — the engine never proposes a trade
plan without a directional call. For LONG/SHORT, every level is derived
from ATR and the Structure factor's swing levels, never a fixed percentage:

**Stop**: the nearest swing support/resistance (with a small ATR buffer
beyond it) *if* it sits within `MAX_STRUCTURE_ATR_DISTANCE` (3x ATR) of
price — otherwise a plain `STOP_ATR_MULTIPLIER` (1.5x ATR) stop. This
means the stop is meaningfully tighter when there's a real nearby level
worth respecting, and falls back to a volatility-scaled default when there
isn't.

**Targets**: `entry + R_multiple * risk_per_unit` for R multiples
1.5 / 2.5 / 4.0 (TP1/TP2/TP3), nudged to align TP2 with a real
resistance/support level when one naturally falls inside that range.

**Risk-Reward**: computed from the actual resulting distances
(`abs(tp - entry) / risk_per_unit`), not assumed — if a structure level
moved TP2, its reported RR reflects that real distance.

## 5. Reason Generator — `reason_generator.py`

Merges every factor's `reasons` list, highest-weight factor first,
de-duplicated, and pads with clearly-labeled generic fallback reasons if
the underlying factors didn't produce at least `MIN_REASONS` (5) on their
own (e.g. a symbol with very little backfilled history). In practice, a
symbol with a full candle history typically produces 15-25 reasons across
all nine factors.

## Persistence — `ai_analysis` table

Every `/api/ai/*` call recomputes a fresh analysis and appends one row to
`ai_analysis` (`app/models/ai_analysis.py`): symbol, interval, candle time,
score, confidence, direction, entry/stop/tp1-3, and the TP2 risk-reward
ratio. This is append-only history (no upsert) — it's an audit log of every
analysis ever computed, not a cache.

## API

All under `/api/ai/`, analysis only — none of these place an order:

| Endpoint | Returns |
|---|---|
| `GET /api/ai/decision/{symbol}?interval=1h` | Full `AIDecision`: score, confidence, direction, reasons, all nine factors, risk plan |
| `GET /api/ai/score/{symbol}?interval=1h` | Score, confidence, direction, factors (no reasons/risk) |
| `GET /api/ai/reasons/{symbol}?interval=1h` | Direction + the merged reasons list |
| `GET /api/ai/risk/{symbol}?interval=1h` | Direction + risk plan (`null` when direction is WAIT) |

404 if the symbol/interval has no backfilled candle history yet; 400 for
an unsupported interval.

## Reproducibility

There is no source of non-determinism anywhere in `app/ai_engine/`: no
`random`, no wall-clock reads inside the scoring math (only the DB query
in `market_context.py` is time-dependent, and that's the input, not the
computation), no floating-point-order-dependent reductions across runs.
Calling `analyze_market()` twice with the same `MarketContext` produces
bit-identical output — this is asserted directly in
`backend/tests/test_ai_decision.py::test_analyze_market_deterministic_same_input_same_output`
and in the equivalent determinism test for every individual scoring
module.

## What Sprint 4 adds

- **`macro.py`**: real BTC Dominance / DXY / Gold / S&P 500 / NASDAQ / VIX
  feeds, replacing the neutral stub. Only requires implementing the body
  of `score_macro()` and raising its weight in `FACTOR_WEIGHTS` — every
  other file in the engine is already shaped to consume a real
  `FactorScore` from it.
- **`news.py`**: real news/sentiment ingestion, same pattern.
- **Whale-wallet analysis**: a new scoring module following the exact same
  `FactorScore` contract, plugged into `market_score.py`'s weight table.
- **LLM-based explanation layer**: a new component that takes an already-
  computed `AIDecision` (score, confidence, direction, reasons, risk) and
  turns it into narrative prose for the chat/dashboard UI. It reads this
  engine's output — it never feeds back into it, so the underlying
  analysis stays deterministic regardless of what the LLM does.
