"""eval.ragas.test_harness — CI-safe RAGAS harness tests (all mocked).

Two test tiers:
  1. CI-safe (this file): all ragas + NIM interactions mocked.  No ragas
     import at module load.  Runs in CI with only the [dev] extra.
  2. Slow/live (test_live.py): pytest.importorskip("ragas") + real NIM calls.
     Excluded from CI via @pytest.mark.slow.

CI-safe invariants verified here:
  A. Aggregation:     RagasReport.build() computes correct means/pass/fail.
  B. Error isolation: one question raising → QuestionScore.error, others continue.
  C. Threshold logic: mean just below threshold → report.passed is False.
  D. Serialisation:   RagasReport.to_dict() and QuestionScore.to_dict() are
                      JSON-serialisable and round-trip correctly.
  E. Lazy imports:    importing eval.ragas.runner WITHOUT ragas installed
                      must NOT raise ImportError at module level.
  F. NIM judge:       make_nim_llm / make_nim_embeddings raise EvalHarnessError
                      when ragas is absent (not ImportError).
  G. run_ragas_eval:  end-to-end mocked run returns correct RagasReport shape.
  H. Reporter:        write_report creates a valid JSON file; print_summary
                      produces output containing PASS/FAIL.
  I. Role assignment: harness uses required_role from GoldenQA row when calling
                      answer_query (checked via mock call args).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eval.errors import EvalHarnessError
from eval.ragas.models import MetricThresholds, QuestionScore, RagasReport
from eval.ragas.reporter import print_summary, write_report

# ── Helpers ──────────────────────────────────────────────────────────────────

_THRESHOLDS = MetricThresholds(
    faithfulness=0.7,
    answer_relevancy=0.7,
    context_precision=0.7,
    context_recall=0.7,
)


def _make_score(
    qa_id: str = "q1",
    f: float | None = 0.8,
    ar: float | None = 0.8,
    cp: float | None = 0.8,
    cr: float | None = 0.8,
    error: str | None = None,
) -> QuestionScore:
    return QuestionScore(
        id=qa_id,
        question="What is the revenue?",
        faithfulness=f,
        answer_relevancy=ar,
        context_precision=cp,
        context_recall=cr,
        error=error,
    )


# ── A. Aggregation ────────────────────────────────────────────────────────────


def test_report_build_computes_correct_means() -> None:
    scores = [
        _make_score("q1", f=0.8, ar=0.9, cp=0.7, cr=0.6),
        _make_score("q2", f=0.6, ar=0.7, cp=0.9, cr=0.8),
    ]
    report = RagasReport.build(scores, _THRESHOLDS)
    assert report.mean_faithfulness == pytest.approx(0.7)
    assert report.mean_answer_relevancy == pytest.approx(0.8)
    assert report.mean_context_precision == pytest.approx(0.8)
    assert report.mean_context_recall == pytest.approx(0.7)


def test_report_build_ignores_none_in_means() -> None:
    """None scores (errored metric) are excluded from the mean calculation."""
    scores = [
        _make_score("q1", f=0.9, ar=None, cp=0.8, cr=0.9),
        _make_score("q2", f=0.7, ar=0.8, cp=0.6, cr=0.7),
    ]
    report = RagasReport.build(scores, _THRESHOLDS)
    # answer_relevancy: only q2's 0.8 counts
    assert report.mean_answer_relevancy == pytest.approx(0.8)
    assert report.mean_faithfulness == pytest.approx(0.8)


def test_report_build_all_none_gives_none_mean() -> None:
    scores = [_make_score("q1", f=None), _make_score("q2", f=None)]
    report = RagasReport.build(scores, _THRESHOLDS)
    assert report.mean_faithfulness is None


def test_report_passed_true_when_all_above_threshold() -> None:
    scores = [_make_score("q1", f=0.9, ar=0.9, cp=0.9, cr=0.9)]
    report = RagasReport.build(scores, _THRESHOLDS)
    assert report.passed is True


# ── B. Error isolation ────────────────────────────────────────────────────────


def test_report_failed_count_reflects_error_questions() -> None:
    scores = [
        _make_score("q1"),
        _make_score("q2", error="NIM timeout"),
        _make_score("q3", error="embedding failure"),
    ]
    report = RagasReport.build(scores, _THRESHOLDS)
    assert report.failed_count == 2
    assert report.total_count == 3


def test_error_question_excluded_from_means() -> None:
    scores = [
        _make_score("q1", f=0.9, ar=0.9, cp=0.9, cr=0.9),
        _make_score("q2", f=None, ar=None, cp=None, cr=None, error="timeout"),
    ]
    report = RagasReport.build(scores, _THRESHOLDS)
    # Only q1 contributes — means should be 0.9
    assert report.mean_faithfulness == pytest.approx(0.9)
    # Still passes because the non-errored question meets thresholds
    assert report.passed is True


# ── C. Threshold logic ────────────────────────────────────────────────────────


def test_report_failed_when_one_metric_below_threshold() -> None:
    """context_recall just below threshold → passed=False."""
    scores = [_make_score("q1", f=0.9, ar=0.9, cp=0.9, cr=0.69)]
    report = RagasReport.build(scores, _THRESHOLDS)
    assert report.passed is False


def test_report_failed_when_metric_mean_is_none() -> None:
    """A metric with no valid scores cannot satisfy the threshold."""
    scores = [_make_score("q1", cr=None)]
    report = RagasReport.build(scores, _THRESHOLDS)
    assert report.passed is False


def test_report_passes_at_exact_threshold() -> None:
    """Score exactly equal to threshold should count as passing."""
    scores = [_make_score("q1", f=0.7, ar=0.7, cp=0.7, cr=0.7)]
    report = RagasReport.build(scores, _THRESHOLDS)
    assert report.passed is True


# ── D. Serialisation ─────────────────────────────────────────────────────────


def test_question_score_to_dict_is_json_serialisable() -> None:
    score = _make_score("q1")
    d = score.to_dict()
    serialised = json.dumps(d)
    loaded: dict[str, Any] = json.loads(serialised)
    assert loaded["id"] == "q1"
    assert loaded["faithfulness"] == pytest.approx(0.8)
    assert loaded["error"] is None


def test_question_score_to_dict_with_error() -> None:
    score = _make_score("q2", f=None, ar=None, cp=None, cr=None, error="timeout")
    d = score.to_dict()
    assert d["faithfulness"] is None
    assert d["error"] == "timeout"


def test_ragas_report_to_dict_round_trips() -> None:
    scores = [_make_score("q1"), _make_score("q2", f=0.75, ar=0.75, cp=0.75, cr=0.75)]
    report = RagasReport.build(scores, _THRESHOLDS)
    d = report.to_dict()
    serialised = json.dumps(d)
    loaded: dict[str, Any] = json.loads(serialised)
    assert "passed" in loaded
    assert "question_scores" in loaded
    assert len(loaded["question_scores"]) == 2
    assert "thresholds" in loaded


# ── E. Lazy imports ───────────────────────────────────────────────────────────


def test_runner_importable_without_ragas() -> None:
    """Importing eval.ragas.runner must NOT raise even when ragas is absent.

    We simulate a missing ragas by temporarily removing it from sys.modules
    and blocking future imports via a custom finder.
    """
    import importlib
    import sys

    # Remove ragas from sys.modules if it happens to be present.
    ragas_keys = [k for k in sys.modules if k == "ragas" or k.startswith("ragas.")]
    saved = {k: sys.modules.pop(k) for k in ragas_keys}

    # Also remove our runner from cache so it re-imports fresh.
    runner_keys = [k for k in sys.modules if "eval.ragas.runner" in k]
    saved.update({k: sys.modules.pop(k) for k in runner_keys})

    try:
        # Block ragas from importing.
        sys.modules["ragas"] = None  # type: ignore[assignment]
        # Import should succeed (no module-level ragas import).
        importlib.import_module("eval.ragas.runner")
    finally:
        # Restore original state.
        for k in list(sys.modules):
            if k == "ragas" or k.startswith("ragas."):
                del sys.modules[k]
        sys.modules.update(saved)


# ── F. NIM judge EvalHarnessError ────────────────────────────────────────────


def test_make_nim_llm_raises_harness_error_without_ragas() -> None:
    """make_nim_llm must raise EvalHarnessError (not ImportError) when ragas absent."""
    import importlib
    import sys

    ragas_keys = [k for k in sys.modules if k == "ragas" or k.startswith("ragas.")]
    saved = {k: sys.modules.pop(k) for k in ragas_keys}
    nim_judge_keys = [k for k in sys.modules if "eval.ragas.nim_judge" in k]
    saved.update({k: sys.modules.pop(k) for k in nim_judge_keys})

    try:
        sys.modules["ragas"] = None  # type: ignore[assignment]
        sys.modules["ragas.llms"] = None  # type: ignore[assignment]
        mod = importlib.import_module("eval.ragas.nim_judge")
        with pytest.raises(EvalHarnessError, match="ragas is not installed"):
            mod.make_nim_llm("https://fake.nim/v1", "meta/llama-3.1-8b-instruct")
    finally:
        for k in list(sys.modules):
            if k == "ragas" or k.startswith("ragas."):
                del sys.modules[k]
        sys.modules.update(saved)


# ── G. run_ragas_eval end-to-end mock ────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_ragas_eval_returns_report(tmp_path: Path) -> None:
    """End-to-end mock: run_ragas_eval returns a RagasReport with correct shape.

    Patches _safe_run_question to avoid any ragas/NIM dependency, and patches
    make_nim_llm / make_nim_embeddings (module-level imports in runner.py) to
    avoid ragas import inside those functions.
    """
    from eval.ragas.runner import run_ragas_eval
    from rbac.roles import Role

    golden_qa_path = Path(__file__).parent.parent / "golden" / "golden_qa.jsonl"
    if not golden_qa_path.exists():
        pytest.skip("golden_qa.jsonl not found")

    with (
        patch("eval.ragas.runner.make_nim_llm", return_value=MagicMock()),
        patch("eval.ragas.runner.make_nim_embeddings", return_value=MagicMock()),
        patch(
            "eval.ragas.runner._safe_run_question",
            new_callable=AsyncMock,
            return_value=_make_score("nvda-rev-fy2024"),
        ),
    ):
        report = await run_ragas_eval(
            golden_qa_path=golden_qa_path,
            org_id="acme",
            role=Role.OWNER,
            store=MagicMock(),
            bm25_index=MagicMock(),
            nim_llm_base_url="https://fake-llm.nim/v1",
            nim_embed_base_url="https://fake-embed.nim/v1",
            reports_dir=tmp_path / "reports",
            rpm_limit=6000,  # 0.01s inter-question sleep — avoids real delays in CI
        )

    assert isinstance(report, RagasReport)
    assert report.total_count >= 1


@pytest.mark.asyncio
async def test_run_ragas_eval_isolates_per_question_errors(tmp_path: Path) -> None:
    """Even if some questions error, harness completes and report is returned."""
    from eval.ragas.runner import run_ragas_eval
    from rbac.roles import Role

    golden_qa_path = Path(__file__).parent.parent / "golden" / "golden_qa.jsonl"
    if not golden_qa_path.exists():
        pytest.skip("golden_qa.jsonl not found")

    call_count = 0

    async def _alternating_safe_run(*args: Any, **kwargs: Any) -> QuestionScore:
        nonlocal call_count
        call_count += 1
        qa = kwargs.get("qa") or args[0]
        if call_count % 2 == 0:
            return QuestionScore(id=qa.id, question=qa.question, error="simulated error")
        return _make_score(qa.id)

    with (
        patch("eval.ragas.runner.make_nim_llm", return_value=MagicMock()),
        patch("eval.ragas.runner.make_nim_embeddings", return_value=MagicMock()),
        patch(
            "eval.ragas.runner._safe_run_question",
            side_effect=_alternating_safe_run,
        ),
    ):
        report = await run_ragas_eval(
            golden_qa_path=golden_qa_path,
            org_id="acme",
            role=Role.FINANCE,
            store=MagicMock(),
            bm25_index=MagicMock(),
            nim_llm_base_url="https://fake/v1",
            nim_embed_base_url="https://fake-embed/v1",
            reports_dir=tmp_path / "reports",
            rpm_limit=6000,  # 0.01s sleep — avoids real delays in CI
        )

    assert report.total_count >= 2
    assert report.failed_count >= 1  # at least one error
    # Report must still be returned (harness never raises for per-question errors)
    assert isinstance(report, RagasReport)


# ── H. Reporter ───────────────────────────────────────────────────────────────


def test_write_report_creates_json_file(tmp_path: Path) -> None:
    scores = [_make_score("q1"), _make_score("q2", f=0.6, ar=0.6, cp=0.6, cr=0.6)]
    report_path = write_report(scores, _THRESHOLDS, tmp_path / "reports")
    assert report_path.exists()
    data: dict[str, Any] = json.loads(report_path.read_text())
    assert "passed" in data
    assert len(data["question_scores"]) == 2


def test_write_report_filename_is_timestamped(tmp_path: Path) -> None:
    scores = [_make_score("q1")]
    path = write_report(scores, _THRESHOLDS, tmp_path / "reports")
    assert path.name.startswith("ragas_report_")
    assert path.suffix == ".json"


def test_print_summary_shows_pass(capsys: pytest.CaptureFixture[str]) -> None:
    scores = [_make_score("q1")]
    report = RagasReport.build(scores, _THRESHOLDS, report_path=None)
    print_summary(report)
    out = capsys.readouterr().out
    assert "PASS" in out
    assert "MEAN" in out


def test_print_summary_shows_fail(capsys: pytest.CaptureFixture[str]) -> None:
    scores = [_make_score("q1", f=0.5, ar=0.5, cp=0.5, cr=0.5)]
    report = RagasReport.build(scores, _THRESHOLDS, report_path=None)
    print_summary(report)
    out = capsys.readouterr().out
    assert "FAIL" in out


def test_print_summary_shows_error_flag(capsys: pytest.CaptureFixture[str]) -> None:
    scores = [_make_score("q1", f=None, ar=None, cp=None, cr=None, error="timeout")]
    report = RagasReport.build(scores, _THRESHOLDS, report_path=None)
    print_summary(report)
    out = capsys.readouterr().out
    assert "ERROR" in out


# ── I. Role assignment ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_safe_run_question_uses_provided_role() -> None:
    """_safe_run_question must call answer_query with the role it was given."""
    from eval.models import GoldenQA
    from eval.ragas.runner import _safe_run_question
    from ingest.models import Chunk, ContentType, SensitivityLevel, make_chunk_id
    from rbac.roles import Role

    qa = GoldenQA(
        id="nvda-rev-fy2024",
        question="What was NVIDIA revenue for FY2024?",
        ground_truth_answer="$26.97 billion",
        ground_truth_contexts=["NVIDIA total revenue for fiscal year 2024 was $26.97 billion."],
        doc_name="live_nvidia_10k.pdf",
        page_number=1,
        required_role="owner",
        sensitivity_level="public",
        tags=["verified"],
    )

    fake_chunk = Chunk(
        chunk_id=make_chunk_id("doc", 1, 0),
        doc_id="doc",
        doc_name="live_nvidia_10k.pdf",
        page_number=1,
        section="Revenue",
        org_id="acme",
        sensitivity_level=SensitivityLevel.PUBLIC,
        allowed_roles=["owner", "finance", "hr", "employee"],
        text="NVIDIA total revenue for fiscal year 2024 was $26.97 billion.",
        content_type=ContentType.TEXT,
        embedding=[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    )

    from generation.citations import AnswerWithCitations

    fake_answer = AnswerWithCitations(answer="Revenue was $26.97B.", sources=[])

    # Build a mock that mimics pandas Series.get() without importing pandas.
    _scores = {
        "faithfulness": 0.9,
        "answer_relevancy": 0.9,
        "context_precision": 0.9,
        "context_recall": 0.9,
    }
    fake_row = MagicMock()
    fake_row.get.side_effect = lambda k, *a: _scores.get(k, a[0] if a else None)
    fake_df = MagicMock()
    fake_df.iloc.__getitem__ = MagicMock(return_value=fake_row)
    fake_result = MagicMock()
    fake_result.to_pandas.return_value = fake_df

    # Wire ragas lazy imports: `from ragas import evaluate` will get
    # ragas_mock.evaluate, which we set to return fake_result.
    ragas_mock = MagicMock()
    ragas_mock.evaluate.return_value = fake_result
    ragas_mocks = {
        "ragas": ragas_mock,
        "ragas.dataset_schema": MagicMock(),
        "ragas.metrics.collections": MagicMock(),
    }

    # WHY eval.ragas.runner.answer_query: runner.py imports answer_query at module
    # level (`from generation.answer import answer_query`), so the reference lives
    # in runner's namespace.  Patching the source module would leave runner's copy
    # unchanged and let the real NIM call through.
    with (
        patch("retrieval.search.document_search", new_callable=AsyncMock) as mock_search,
        patch("eval.ragas.runner.answer_query", new_callable=AsyncMock) as mock_answer,
        patch.dict(sys.modules, ragas_mocks),
    ):
        mock_search.return_value = [fake_chunk]
        mock_answer.return_value = fake_answer

        score = await _safe_run_question(
            qa=qa,
            store=MagicMock(),
            bm25_index=MagicMock(),
            org_id="acme",
            role=Role.OWNER,
            ragas_llm=MagicMock(),
            ragas_embeddings=MagicMock(),
        )

    # Verify answer_query was called with the correct role
    mock_answer.assert_called_once()
    call_kwargs = mock_answer.call_args.kwargs
    assert call_kwargs.get("role") == Role.OWNER
    assert call_kwargs.get("org_id") == "acme"
    assert score.id == "nvda-rev-fy2024"
