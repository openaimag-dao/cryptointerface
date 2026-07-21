import csv
import io
import json
from dataclasses import replace

import pytest

from app.backtesting.models.results import BacktestRunResult, EquityPoint, PerformanceMetrics, RiskMetrics
from app.backtesting.models.trade import ClosedTrade
from app.backtesting.report_generator import generate_csv_report, generate_json_report, generate_pdf_report


def _result() -> BacktestRunResult:
    trades = [
        ClosedTrade(
            symbol="TESTUSDT",
            direction="LONG",
            entry_time=0,
            entry_price=100.0,
            exit_time=3600,
            exit_price=103.0,
            quantity=10.0,
            pnl=30.0,
            pnl_percent=0.3,
            exit_reason="TP1",
            duration_seconds=3600,
            decision_score=60.0,
            confidence=55.0,
            planned_risk_reward=1.5,
        )
    ]
    performance = PerformanceMetrics(
        total_trades=1,
        winning_trades=1,
        losing_trades=0,
        total_return_percent=0.3,
        net_profit=30.0,
        gross_profit=30.0,
        gross_loss=0.0,
        win_rate=100.0,
        loss_rate=0.0,
        avg_win=30.0,
        avg_loss=0.0,
        profit_factor=999.0,
        expectancy=30.0,
        avg_trade_duration_seconds=3600.0,
    )
    risk = RiskMetrics(
        max_drawdown_percent=0.0,
        max_drawdown_duration_seconds=0,
        recovery_factor=999.0,
        sharpe_ratio=1.0,
        sortino_ratio=1.0,
        calmar_ratio=1.0,
        avg_risk_reward=1.5,
        final_balance=10_030.0,
        peak_balance=10_030.0,
    )
    equity_curve = [
        EquityPoint(time=0, balance=10_000.0, drawdown_percent=0.0, cumulative_pnl=0.0, trade_count=0),
        EquityPoint(time=3600, balance=10_030.0, drawdown_percent=0.0, cumulative_pnl=30.0, trade_count=1),
    ]
    return BacktestRunResult(
        symbol="TESTUSDT",
        timeframe="1h",
        period_days=30,
        start_time=0,
        end_time=3600,
        strategy_version_name="v1-default-decision-engine",
        trades=trades,
        equity_curve=equity_curve,
        performance=performance,
        risk=risk,
        bars_analyzed=2,
    )


def test_generate_json_report_round_trips():
    result = _result()
    payload = json.loads(generate_json_report(result))
    assert payload["symbol"] == "TESTUSDT"
    assert payload["performance"]["total_trades"] == 1
    assert payload["risk"]["sharpe_ratio"] == 1.0
    assert len(payload["trades"]) == 1
    assert payload["trades"][0]["pnl"] == 30.0


def test_generate_json_report_is_deterministic():
    result = _result()
    assert generate_json_report(result) == generate_json_report(result)


def test_generate_csv_report_has_header_and_one_row_per_trade():
    result = _result()
    csv_text = generate_csv_report(result)
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["symbol"] == "TESTUSDT"
    assert rows[0]["direction"] == "LONG"
    assert float(rows[0]["pnl"]) == 30.0


def test_generate_csv_report_empty_trades_still_has_header():
    result = _result()
    empty = replace(result, trades=[])
    csv_text = generate_csv_report(empty)
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    assert len(rows) == 1  # header only


def test_generate_pdf_report_not_implemented():
    with pytest.raises(NotImplementedError):
        generate_pdf_report(_result())
