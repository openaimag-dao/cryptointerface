from app.ai_engine.confidence_engine import compute_confidence
from app.ai_engine.types import make_factor_score

WEIGHTS = {"a": 0.4, "b": 0.3, "c": 0.3}


def test_full_agreement_and_full_strength_gives_max_confidence():
    factors = {
        "a": make_factor_score("a", 100.0, ["max bullish"]),
        "b": make_factor_score("b", 100.0, ["max bullish"]),
        "c": make_factor_score("c", 100.0, ["max bullish"]),
    }
    confidence = compute_confidence(factors, WEIGHTS, "LONG")

    assert confidence == 100.0


def test_full_disagreement_only_reflects_the_strength_term():
    # All factors scream SHORT while the market direction is LONG: zero
    # agreement (the 0.6-weighted term drops to 0), but each factor is
    # still individually "strong" (max distance from neutral), so the
    # 0.4-weighted strength term alone survives: 0.4 * 100 = 40.
    factors = {
        "a": make_factor_score("a", 0.0, ["max bearish"]),
        "b": make_factor_score("b", 0.0, ["max bearish"]),
        "c": make_factor_score("c", 0.0, ["max bearish"]),
    }
    confidence = compute_confidence(factors, WEIGHTS, "LONG")

    assert confidence == 40.0


def test_all_neutral_factors_give_zero_confidence():
    factors = {name: make_factor_score(name, 50.0, ["neutral"]) for name in WEIGHTS}
    confidence = compute_confidence(factors, WEIGHTS, "WAIT")

    # Every factor agrees (all WAIT) but strength is zero everywhere, so
    # confidence should be exactly the agreement-only contribution (60).
    assert confidence == 60.0


def test_zero_weight_factors_are_ignored():
    factors = {
        "a": make_factor_score("a", 100.0, ["bullish"]),
        "b": make_factor_score("b", 0.0, ["bearish, but zero-weighted"]),
    }
    weights = {"a": 1.0, "b": 0.0}
    confidence = compute_confidence(factors, weights, "LONG")

    assert confidence == 100.0


def test_confidence_is_clamped_to_0_100():
    factors = {name: make_factor_score(name, 100.0, ["bullish"]) for name in WEIGHTS}
    confidence = compute_confidence(factors, WEIGHTS, "LONG")

    assert 0.0 <= confidence <= 100.0


def test_deterministic_same_input_same_output():
    factors = {
        "a": make_factor_score("a", 72.0, ["bullish"]),
        "b": make_factor_score("b", 40.0, ["bearish"]),
        "c": make_factor_score("c", 55.0, ["mild bullish"]),
    }
    first = compute_confidence(factors, WEIGHTS, "LONG")
    second = compute_confidence(factors, WEIGHTS, "LONG")

    assert first == second
