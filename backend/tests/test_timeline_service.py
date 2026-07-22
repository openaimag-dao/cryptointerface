import pytest

from app.ai_engine.decision_engine import AIDecision
from app.ai_engine.types import FactorScore
from app.models.ai_analysis import AIAnalysis
from app.services.ai_repository import insert_ai_analysis
from app.services.timeline_service import get_timeline

BASE_TIME_MS = 1_700_000_000_000
BASE_TIME_S = BASE_TIME_MS // 1000


def _factor(name: str, score: float) -> FactorScore:
    return FactorScore(name=name, score=score, direction="LONG", strength=0.0, reasons=[])


def _decision(
    *, time: int, score: float = 50.0, confidence: float = 50.0, direction: str = "WAIT", factors=None, reasons=None
) -> AIDecision:
    return AIDecision(
        symbol="TESTUSDT",
        interval="1h",
        timestamp=time,
        market_score=score,
        confidence=confidence,
        direction=direction,
        reasons=reasons if reasons is not None else ["synthetic test reason"],
        factors=factors if factors is not None else {},
        weights={},
        risk=None,
    )


@pytest.mark.asyncio
async def test_get_timeline_empty_when_no_analysis_persisted(db_session):
    timeline = await get_timeline(db_session, "NOHISTORYUSDT", "1h")

    assert timeline.entries == []


@pytest.mark.asyncio
async def test_first_entry_marked_as_first_recorded(db_session):
    await insert_ai_analysis(db_session, _decision(time=BASE_TIME_S, score=50.0, confidence=50.0))

    timeline = await get_timeline(db_session, "TESTUSDT", "1h")

    assert len(timeline.entries) == 1
    assert timeline.entries[0].change_summary == "First recorded analysis for this symbol/timeframe."


@pytest.mark.asyncio
async def test_insignificant_changes_are_skipped(db_session):
    await insert_ai_analysis(db_session, _decision(time=BASE_TIME_S, score=50.0, confidence=50.0))
    # Confidence/score barely move -> below threshold, direction unchanged -> not a change point.
    await insert_ai_analysis(db_session, _decision(time=BASE_TIME_S + 3600, score=51.0, confidence=51.0))

    timeline = await get_timeline(db_session, "TESTUSDT", "1h")

    assert len(timeline.entries) == 1


@pytest.mark.asyncio
async def test_confidence_change_above_threshold_is_reported(db_session):
    await insert_ai_analysis(db_session, _decision(time=BASE_TIME_S, score=50.0, confidence=50.0))
    await insert_ai_analysis(db_session, _decision(time=BASE_TIME_S + 3600, score=50.0, confidence=60.0))

    timeline = await get_timeline(db_session, "TESTUSDT", "1h")

    assert len(timeline.entries) == 2
    newest = timeline.entries[0]
    assert "Confidence 50 → 60" in newest.change_summary


@pytest.mark.asyncio
async def test_direction_change_is_reported(db_session):
    await insert_ai_analysis(db_session, _decision(time=BASE_TIME_S, direction="LONG"))
    await insert_ai_analysis(db_session, _decision(time=BASE_TIME_S + 3600, direction="SHORT"))

    timeline = await get_timeline(db_session, "TESTUSDT", "1h")

    assert "Direction LONG → SHORT" in timeline.entries[0].change_summary


@pytest.mark.asyncio
async def test_strengthened_and_weakened_factors_are_derived_from_real_score_deltas(db_session):
    await insert_ai_analysis(
        db_session,
        _decision(time=BASE_TIME_S, score=50.0, confidence=50.0, factors={"oi": _factor("oi", 40.0), "news": _factor("news", 60.0)}),
    )
    await insert_ai_analysis(
        db_session,
        _decision(
            time=BASE_TIME_S + 3600,
            score=60.0,
            confidence=60.0,
            factors={"oi": _factor("oi", 70.0), "news": _factor("news", 45.0)},
        ),
    )

    timeline = await get_timeline(db_session, "TESTUSDT", "1h")

    newest = timeline.entries[0]
    assert "Open Interest" in newest.strengthened_factors
    assert "News" in newest.weakened_factors


@pytest.mark.asyncio
async def test_awaiting_data_status_for_rows_without_persisted_factors(db_session):
    # Simulate a legacy pre-Sprint-6 row written before factors/reasons existed.
    db_session.add(AIAnalysis(symbol="LEGACYUSDT", interval="1h", time=BASE_TIME_S, score=50.0, confidence=50.0, direction="WAIT"))
    await db_session.commit()

    timeline = await get_timeline(db_session, "LEGACYUSDT", "1h")

    assert len(timeline.entries) == 1
    assert timeline.entries[0].data_status == "AWAITING_DATA"
    assert timeline.entries[0].reasons is None


@pytest.mark.asyncio
async def test_ok_data_status_when_factors_and_reasons_present(db_session):
    await insert_ai_analysis(db_session, _decision(time=BASE_TIME_S, reasons=["real reason"]))

    timeline = await get_timeline(db_session, "TESTUSDT", "1h")

    assert timeline.entries[0].data_status == "OK"
    assert timeline.entries[0].reasons == ["real reason"]


@pytest.mark.asyncio
async def test_entries_are_newest_first(db_session):
    await insert_ai_analysis(db_session, _decision(time=BASE_TIME_S, confidence=50.0))
    await insert_ai_analysis(db_session, _decision(time=BASE_TIME_S + 3600, confidence=70.0))

    timeline = await get_timeline(db_session, "TESTUSDT", "1h")

    assert timeline.entries[0].time > timeline.entries[1].time
