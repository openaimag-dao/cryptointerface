import numpy as np

from app.ai_engine.scoring.trend import score_trend


def _series(closes: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    highs = closes + 0.5
    lows = closes - 0.5
    return closes, highs, lows


def test_clean_uptrend_scores_long_at_max_score():
    closes, highs, lows = _series(np.linspace(100, 200, 300) + np.sin(np.linspace(0, 20, 300)) * 0.3)
    factor = score_trend(closes, highs, lows)

    assert factor.direction == "LONG"
    assert factor.score == 100.0
    assert factor.details["trend_direction"] == "LONG"
    assert any("EMA20 above EMA50" in reason for reason in factor.reasons)
    assert any("sloping upward" in reason for reason in factor.reasons)


def test_clean_downtrend_scores_short_at_min_score():
    closes, highs, lows = _series(np.linspace(200, 100, 300) + np.sin(np.linspace(0, 20, 300)) * 0.3)
    factor = score_trend(closes, highs, lows)

    assert factor.direction == "SHORT"
    assert factor.score == 0.0
    assert any("EMA20 below EMA50" in reason for reason in factor.reasons)
    assert any("sloping downward" in reason for reason in factor.reasons)


def test_swing_structure_confirms_higher_highs_and_higher_lows():
    # A gentle oscillation riding a mild slope produces clean, well-formed
    # swing points (unlike a steep monotonic ramp, where EMA/slope alone
    # already saturate the score before structure ever gets evaluated).
    wave = 100 + 10 * np.sin(np.linspace(0, 6 * np.pi, 250)) + np.linspace(0, 20, 250)
    closes, highs, lows = _series(wave)
    factor = score_trend(closes, highs, lows)

    assert any("Higher highs and higher lows" in reason for reason in factor.reasons)


def test_insufficient_history_is_neutral_and_says_so():
    closes, highs, lows = _series(np.full(10, 100.0))
    factor = score_trend(closes, highs, lows)

    assert factor.score == 50.0
    assert factor.direction == "WAIT"
    assert any("Not enough history" in reason for reason in factor.reasons)


def test_score_is_always_clamped_to_0_100():
    rng = np.random.default_rng(123)
    closes, highs, lows = _series(100 + np.cumsum(rng.normal(0, 2, 300)))
    factor = score_trend(closes, highs, lows)

    assert 0.0 <= factor.score <= 100.0
    assert 0.0 <= factor.strength <= 100.0


def test_deterministic_same_input_same_output():
    closes, highs, lows = _series(np.linspace(100, 150, 300))
    first = score_trend(closes, highs, lows)
    second = score_trend(closes, highs, lows)

    assert first.score == second.score
    assert first.direction == second.direction
    assert first.reasons == second.reasons
    assert first.details == second.details
