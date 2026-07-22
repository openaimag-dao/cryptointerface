"""Optimizer — interface and infrastructure only (Sprint 5 spec:
"на данном этапе реализовать интерфейс и инфраструктуру"). No parameter
search actually runs yet.

The eventual job of this module is to search over the Decision Engine's
tunable constants — Market Score factor weights
(`app/ai_engine/market_score.py::FACTOR_WEIGHTS`), the confidence floor
(`app/ai_engine/decision_engine.py::MIN_CONFIDENCE_FOR_ACTION`), the R
multiples and ATR multiplier that drive TP/SL
(`app/ai_engine/risk_engine.py`) — by running many backtests (ideally
each fold's Train segment from `walk_forward.py`) and picking the
parameter set that scores best on some objective (Sharpe, profit factor,
...), then confirming it out-of-sample on Validation. None of that search
loop exists yet: `Optimizer.run()` intentionally raises `NotImplementedError`
rather than silently returning a fake "best" result, and the Decision
Engine's constants stay hardcoded module-level values (not parameters
threaded through function calls) until an optimizer actually needs to
vary them — so this module cannot yet change how any backtest runs.

`DEFAULT_PARAMETER_SPACE` names each parameter the spec calls out as a
future optimization target with a plausible search range, so the
resulting interface is concrete rather than speculative.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from app.backtesting.models.results import BacktestRunResult


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    min_value: float
    max_value: float
    step: float

    def __post_init__(self) -> None:
        if self.min_value > self.max_value:
            raise ValueError(f"{self.name}: min_value must be <= max_value")
        if self.step <= 0:
            raise ValueError(f"{self.name}: step must be positive")


@dataclass(frozen=True)
class ParameterSpace:
    parameters: tuple[ParameterSpec, ...]

    def grid_size(self) -> int:
        """How many parameter combinations a full grid search over this
        space would cover — informational only today."""
        size = 1
        for p in self.parameters:
            steps = int((p.max_value - p.min_value) / p.step) + 1
            size *= max(1, steps)
        return size


# Named directly after the Sprint 5 spec's own list of future optimization
# targets. Ranges are plausible starting points, not tuned values.
DEFAULT_PARAMETER_SPACE = ParameterSpace(
    parameters=(
        ParameterSpec("factor_weight_trend", 0.05, 0.30, 0.01),
        ParameterSpec("factor_weight_momentum", 0.05, 0.25, 0.01),
        ParameterSpec("factor_weight_structure", 0.05, 0.25, 0.01),
        ParameterSpec("min_confidence_for_action", 30.0, 70.0, 5.0),
        ParameterSpec("tp1_r_multiple", 1.0, 3.0, 0.25),
        ParameterSpec("tp2_r_multiple", 1.5, 4.0, 0.25),
        ParameterSpec("tp3_r_multiple", 2.5, 6.0, 0.5),
        ParameterSpec("stop_atr_multiplier", 0.75, 3.0, 0.25),
    )
)


@dataclass(frozen=True)
class OptimizationCandidate:
    params: dict[str, float]
    result: BacktestRunResult
    objective_score: float


@dataclass(frozen=True)
class OptimizationResult:
    best: OptimizationCandidate | None
    all_candidates: list[OptimizationCandidate] = field(default_factory=list)


# An objective function scores one backtest result — e.g. `lambda r:
# r.risk.sharpe_ratio` — so the search can be pointed at whichever metric
# matters for a given run, without the optimizer itself hardcoding one.
ObjectiveFn = Callable[[BacktestRunResult], float]


class Optimizer:
    """Infrastructure for a future parameter search. Holds a
    `ParameterSpace` and an objective function; `run()` is where a real
    grid/random/Bayesian search would eventually live, driving
    `walk_forward.run_walk_forward` (or `engine.run_backtest`) once per
    candidate parameter set."""

    def __init__(self, space: ParameterSpace, objective: ObjectiveFn) -> None:
        self.space = space
        self.objective = objective

    def run(self) -> OptimizationResult:
        raise NotImplementedError(
            "Optimizer.run() is architecture only (Sprint 5) — no search loop exists yet. "
            "See this module's docstring for what it will eventually drive."
        )
