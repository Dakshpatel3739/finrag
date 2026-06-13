"""eval.ragas.models — pydantic / dataclass schemas for the RAGAS harness.

Three public types:

    MetricThresholds  — pass/fail cut-offs per RAGAS metric (all default 0.7)
    QuestionScore     — per-question metric scores (None = metric errored)
    RagasReport       — aggregate report with pass/fail verdict

WHY dataclasses (not pydantic) for report types:
    These objects are created internally by the harness (not from untrusted
    user input), so pydantic validation overhead is unnecessary.  Dataclasses
    with typed fields give the same static-analysis benefit at lower runtime
    cost.  RagasReport.to_dict() drives JSON serialisation for on-disk reports.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MetricThresholds:
    """Minimum acceptable mean score for each RAGAS metric.

    Any metric whose mean falls below its threshold causes ``RagasReport.passed``
    to be False.  Defaults are intentionally conservative (0.7) — teams should
    calibrate these against their own NIM model after the first live run.
    """

    faithfulness: float = 0.7
    answer_relevancy: float = 0.7
    context_precision: float = 0.7
    context_recall: float = 0.7


@dataclass
class QuestionScore:
    """Per-question RAGAS metric scores for a single GoldenQA row.

    A ``None`` score means the metric evaluation failed for this question
    (e.g. LLM judge timeout, empty retrieved context).  The harness never
    raises on per-question errors; it records the error string and continues.

    Fields
    ------
    id:                  GoldenQA.id of the evaluated question.
    question:            The natural-language question text.
    faithfulness:        Score in [0, 1] or None if evaluation errored.
    answer_relevancy:    Score in [0, 1] or None if evaluation errored.
    context_precision:   Score in [0, 1] or None if evaluation errored.
    context_recall:      Score in [0, 1] or None if evaluation errored.
    error:               Exception message if the entire question failed, else None.
    """

    id: str
    question: str
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    context_precision: float | None = None
    context_recall: float | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialise to a JSON-safe dict for on-disk reports."""
        return {
            "id": self.id,
            "question": self.question,
            "faithfulness": self.faithfulness,
            "answer_relevancy": self.answer_relevancy,
            "context_precision": self.context_precision,
            "context_recall": self.context_recall,
            "error": self.error,
        }


def _mean_scores(scores: list[QuestionScore], attr: str) -> float | None:
    """Return the mean of non-None values for *attr* across all scores."""
    values = [v for s in scores if (v := getattr(s, attr)) is not None]
    return statistics.mean(values) if values else None


@dataclass
class RagasReport:
    """Aggregate RAGAS evaluation report over the full golden QA dataset.

    ``passed`` is True only when ALL four metric means meet their thresholds.
    A metric with no valid scores (all questions errored) counts as failed.

    Attributes
    ----------
    question_scores:        Per-question breakdown (one entry per GoldenQA row).
    mean_faithfulness:      Mean faithfulness across non-errored questions.
    mean_answer_relevancy:  Mean answer relevancy across non-errored questions.
    mean_context_precision: Mean context precision across non-errored questions.
    mean_context_recall:    Mean context recall across non-errored questions.
    passed:                 True iff all means meet or exceed MetricThresholds.
    thresholds:             Thresholds used for the pass/fail verdict.
    report_path:            Path where the JSON report was written, or None.
    """

    question_scores: list[QuestionScore]
    mean_faithfulness: float | None
    mean_answer_relevancy: float | None
    mean_context_precision: float | None
    mean_context_recall: float | None
    passed: bool
    thresholds: MetricThresholds
    report_path: Path | None = None

    @classmethod
    def build(
        cls,
        scores: list[QuestionScore],
        thresholds: MetricThresholds,
        report_path: Path | None = None,
    ) -> RagasReport:
        """Compute aggregate metrics and pass/fail verdict from per-question scores."""
        mf = _mean_scores(scores, "faithfulness")
        mar = _mean_scores(scores, "answer_relevancy")
        mcp = _mean_scores(scores, "context_precision")
        mcr = _mean_scores(scores, "context_recall")

        def _passes(mean: float | None, threshold: float) -> bool:
            return mean is not None and mean >= threshold

        passed = (
            _passes(mf, thresholds.faithfulness)
            and _passes(mar, thresholds.answer_relevancy)
            and _passes(mcp, thresholds.context_precision)
            and _passes(mcr, thresholds.context_recall)
        )

        return cls(
            question_scores=scores,
            mean_faithfulness=mf,
            mean_answer_relevancy=mar,
            mean_context_precision=mcp,
            mean_context_recall=mcr,
            passed=passed,
            thresholds=thresholds,
            report_path=report_path,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialise to a JSON-safe dict for on-disk reports."""
        return {
            "passed": self.passed,
            "mean_faithfulness": self.mean_faithfulness,
            "mean_answer_relevancy": self.mean_answer_relevancy,
            "mean_context_precision": self.mean_context_precision,
            "mean_context_recall": self.mean_context_recall,
            "thresholds": {
                "faithfulness": self.thresholds.faithfulness,
                "answer_relevancy": self.thresholds.answer_relevancy,
                "context_precision": self.thresholds.context_precision,
                "context_recall": self.thresholds.context_recall,
            },
            "report_path": str(self.report_path) if self.report_path else None,
            "question_scores": [s.to_dict() for s in self.question_scores],
        }

    @property
    def failed_count(self) -> int:
        """Number of questions where at least one metric errored."""
        return sum(1 for s in self.question_scores if s.error is not None)

    @property
    def total_count(self) -> int:
        """Total number of evaluated questions."""
        return len(self.question_scores)


# ── Re-export for tests that import from eval.ragas.models directly ──────────
__all__ = [
    "MetricThresholds",
    "QuestionScore",
    "RagasReport",
]
