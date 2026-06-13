"""eval.ragas.reporter — write JSON reports and print a summary table.

Responsibilities:
  1. write_report(): serialise QuestionScore list to a timestamped JSON file
     in the reports/ directory.
  2. print_summary(): render a human-readable ASCII table to stdout showing
     per-question and aggregate scores, with a PASS/FAIL verdict.

WHY timestamped filenames:
    Multiple evaluation runs should not overwrite each other.  A timestamp
    suffix lets teams compare before/after runs and track metric trends.

WHY plain ASCII table (not rich/tabulate):
    Keeps the reporter importable without extra deps.  CI sees the table in
    captured stdout; humans see it in terminals.  rich is already a ragas
    transitive dep but we avoid depending on it here for CI-safety.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import structlog

from eval.ragas.models import MetricThresholds, QuestionScore, RagasReport

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_METRICS = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")


def write_report(
    scores: list[QuestionScore],
    thresholds: MetricThresholds,
    reports_dir: Path,
) -> Path:
    """Write a timestamped JSON report and return its path.

    Creates *reports_dir* if it doesn't exist.  The filename format is
    ``ragas_report_YYYYMMDD_HHMMSS.json``.

    Args:
        scores:      Per-question scores from the harness.
        thresholds:  MetricThresholds used to compute pass/fail.
        reports_dir: Directory where the report file is written.

    Returns:
        Path to the written report file.
    """
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    report_path = reports_dir / f"ragas_report_{timestamp}.json"

    # Build a temporary RagasReport just for serialisation.
    report = RagasReport.build(scores=scores, thresholds=thresholds, report_path=report_path)
    payload = report.to_dict()

    with report_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    logger.info("ragas.report.written", path=str(report_path))
    return report_path


def _fmt(val: float | None) -> str:
    """Format a metric score for table display."""
    if val is None:
        return "  err "
    return f"{val:6.3f}"


def print_summary(report: RagasReport) -> None:
    """Print a human-readable ASCII summary table to stdout.

    Columns: id, faithfulness, answer_relevancy, context_precision,
             context_recall, error flag.
    Last row shows aggregate means and PASS / FAIL verdict.
    """
    header = f"{'id':<28} {'faith':>7} {'ans_rel':>7} {'ctx_pre':>7} {'ctx_rec':>7}  status"
    sep = "-" * len(header)

    print()
    print("RAGAS Evaluation Report")
    print(sep)
    print(header)
    print(sep)

    for s in report.question_scores:
        status = "ERROR" if s.error else "ok"
        row = (
            f"{s.id[:28]:<28} "
            f"{_fmt(s.faithfulness)} "
            f"{_fmt(s.answer_relevancy)} "
            f"{_fmt(s.context_precision)} "
            f"{_fmt(s.context_recall)}  {status}"
        )
        print(row)

    print(sep)
    means_row = (
        f"{'MEAN':<28} "
        f"{_fmt(report.mean_faithfulness)} "
        f"{_fmt(report.mean_answer_relevancy)} "
        f"{_fmt(report.mean_context_precision)} "
        f"{_fmt(report.mean_context_recall)}  "
        f"{'PASS' if report.passed else 'FAIL'}"
    )
    print(means_row)
    print(sep)

    thresholds_row = (
        f"{'THRESHOLD':<28} "
        f"{_fmt(report.thresholds.faithfulness)} "
        f"{_fmt(report.thresholds.answer_relevancy)} "
        f"{_fmt(report.thresholds.context_precision)} "
        f"{_fmt(report.thresholds.context_recall)}"
    )
    print(thresholds_row)
    print(sep)

    if report.report_path:
        print(f"Report written to: {report.report_path}")
    print()
