"""Report Generator — exports a completed backtest run. JSON and CSV are
fully implemented; PDF is architecture only (Sprint 5 spec: "PDF
(архитектура)") — `generate_pdf_report()` raises `NotImplementedError`
rather than silently producing nothing or a fake file.
"""

import csv
import io
import json
from dataclasses import asdict
from datetime import UTC, datetime

from app.backtesting.models.results import BacktestRunResult

CSV_COLUMNS = (
    "date",
    "symbol",
    "direction",
    "entry_price",
    "exit_price",
    "pnl",
    "pnl_percent",
    "duration_seconds",
    "exit_reason",
    "decision_score",
    "confidence",
    "planned_risk_reward",
)


def generate_json_report(result: BacktestRunResult) -> str:
    """The full run — trades, equity curve, and both metric sets — as one
    JSON document. Deterministic key order (dataclass field order) and
    stable formatting (`sort_keys=False`, fixed indent) so re-generating
    the same result always produces byte-identical output."""
    return json.dumps(asdict(result), indent=2)


def generate_csv_report(result: BacktestRunResult) -> str:
    """The Trade List as CSV — the same columns the spec's frontend Trade
    List table shows (Date/Symbol/Direction/Entry/Exit/PnL/Duration/
    Reason/Decision Score/Confidence)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_COLUMNS)
    for trade in result.trades:
        writer.writerow(
            [
                datetime.fromtimestamp(trade.entry_time, tz=UTC).isoformat(),
                trade.symbol,
                trade.direction,
                trade.entry_price,
                trade.exit_price,
                trade.pnl,
                trade.pnl_percent,
                trade.duration_seconds,
                trade.exit_reason,
                trade.decision_score,
                trade.confidence,
                trade.planned_risk_reward,
            ]
        )
    return buffer.getvalue()


def generate_pdf_report(result: BacktestRunResult) -> bytes:
    raise NotImplementedError(
        "PDF export is architecture only (Sprint 5) — use generate_json_report() or "
        "generate_csv_report() for now. See this module's docstring."
    )
