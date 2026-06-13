"""eval.ragas.runner — core RAGAS evaluation harness.

Orchestrates:
    1. Load golden QA dataset via eval.loader.load_golden_qa
    2. For each question: call answer_query as the authorised role → get
       retrieved chunks + generated answer
    3. Build RAGAS SingleTurnSample (question, retrieved_contexts,
       reference_contexts, response, reference)
    4. Run RAGAS evaluate() with NIM as LLM/embedding judge
    5. Collect per-question scores into QuestionScore, aggregate into RagasReport

Per-question error isolation:
    If answer_query or the RAGAS scorer raises for one question, that question
    receives a QuestionScore with all metrics=None and error=<message>.  The
    harness continues with the remaining questions and never raises for a
    per-question failure.

RPM throttling:
    ``rpm_limit`` (default 10) inserts an inter-question sleep of
    60 / rpm_limit seconds to avoid hitting NIM rate limits when the judge
    model processes large datasets.

WHY lazy ragas imports:
    All ``from ragas import ...`` calls are inside function bodies so this
    module is importable in CI (where ragas is NOT installed) without error.
    CI tests mock the internal helpers; slow live tests use
    pytest.importorskip("ragas").
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import structlog

from eval.errors import EvalHarnessError
from eval.loader import load_golden_qa
from eval.models import GoldenQA
from eval.ragas.models import MetricThresholds, QuestionScore, RagasReport
from eval.ragas.nim_judge import make_nim_embeddings, make_nim_llm
from eval.ragas.reporter import write_report
from generation.answer import answer_query
from rbac.roles import Role
from retrieval.bm25 import BM25Index
from retrieval.vector_store import MilvusStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# Default NIM models — can be overridden by callers.
_DEFAULT_LLM_MODEL: str = "meta/llama-3.1-8b-instruct"
_DEFAULT_EMBED_MODEL: str = "nvidia/nv-embedqa-e5-v5"


async def _run_single_question(
    qa: GoldenQA,
    store: MilvusStore,
    bm25_index: BM25Index,
    org_id: str,
    role: Role,
) -> tuple[str, list[str], list[str]]:
    """Call answer_query for *qa* and return (response, retrieved_contexts, reference_contexts).

    retrieved_contexts are the chunk texts that were passed to the LLM prompt.
    reference_contexts are GoldenQA.ground_truth_contexts.

    We re-run document_search separately to capture the raw chunk texts
    because answer_query returns only the AnswerWithCitations (no raw chunks).
    Instead we capture chunks via the retrieval path directly.
    """
    from retrieval.search import document_search  # already declared in answer.py

    # Retrieve chunks (same call answer_query will make internally).
    chunks = await document_search(
        query=qa.question,
        store=store,
        bm25_index=bm25_index,
        org_id=org_id,
        role=role,
    )
    retrieved_contexts = [c.text for c in chunks]

    # Generate the answer.
    result = await answer_query(
        query=qa.question,
        store=store,
        bm25_index=bm25_index,
        org_id=org_id,
        role=role,
    )

    return result.answer, retrieved_contexts, qa.ground_truth_contexts


async def _safe_run_question(
    qa: GoldenQA,
    store: MilvusStore,
    bm25_index: BM25Index,
    org_id: str,
    role: Role,
    ragas_llm: object,
    ragas_embeddings: object,
) -> QuestionScore:
    """Run one QA pair through RAGAS and return a QuestionScore.

    Never raises — any exception is captured into QuestionScore.error so the
    harness can continue with remaining questions.

    Imports ragas lazily so this module loads cleanly in CI without ragas.
    """
    log = logger.bind(qa_id=qa.id)
    log.info("ragas.question.start")

    try:
        response, retrieved_contexts, reference_contexts = await _run_single_question(
            qa, store, bm25_index, org_id, role
        )

        # ── Lazy ragas imports ──────────────────────────────────────────────
        # WHY ragas.metrics (not ragas.metrics.collections):
        #   ragas 0.4.3 exports per-collection subpackages under
        #   ragas.metrics.collections, but those are MODULES (sub-packages),
        #   not Metric instances.  The legacy ragas.metrics path provides
        #   ready-to-use singleton Metric instances and is the correct
        #   import for evaluate() in this version.  The DeprecationWarning
        #   about moving to ragas.metrics.collections is suppressed here
        #   because the collections path itself does NOT provide singleton
        #   instances in 0.4.3 — an ADR-010 update will track the migration.
        import warnings

        try:
            from ragas import evaluate
            from ragas.dataset_schema import (
                EvaluationDataset,
                SingleTurnSample,
            )

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                from ragas.metrics import (
                    answer_relevancy,
                    context_precision,
                    context_recall,
                    faithfulness,
                )
        except ImportError as exc:
            raise EvalHarnessError(
                "ragas not installed — install with: pip install 'finrag[eval-live]'"
            ) from exc

        sample = SingleTurnSample(
            user_input=qa.question,
            retrieved_contexts=retrieved_contexts if retrieved_contexts else [""],
            reference_contexts=reference_contexts,
            response=response,
            reference=qa.ground_truth_answer,
        )
        dataset = EvaluationDataset(samples=[sample])

        result = evaluate(
            dataset=dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            llm=ragas_llm,
            embeddings=ragas_embeddings,
            raise_exceptions=False,
            show_progress=False,
        )

        # result is an EvaluationResult with dict-like access by metric name.
        scores_df = result.to_pandas()
        row = scores_df.iloc[0]

        def _safe_float(key: str) -> float | None:
            val = row.get(key)
            if val is None:
                return None
            try:
                f = float(val)
                return None if f != f else f  # NaN check
            except (TypeError, ValueError):
                return None

        score = QuestionScore(
            id=qa.id,
            question=qa.question,
            faithfulness=_safe_float("faithfulness"),
            answer_relevancy=_safe_float("answer_relevancy"),
            context_precision=_safe_float("context_precision"),
            context_recall=_safe_float("context_recall"),
        )
        log.info("ragas.question.done", score=score.to_dict())
        return score

    except Exception as exc:
        log.warning("ragas.question.error", error=str(exc))
        return QuestionScore(
            id=qa.id,
            question=qa.question,
            error=str(exc),
        )


async def run_ragas_eval(
    golden_qa_path: Path,
    org_id: str,
    role: Role,
    store: MilvusStore,
    bm25_index: BM25Index,
    nim_llm_base_url: str,
    nim_embed_base_url: str,
    nim_llm_model: str = _DEFAULT_LLM_MODEL,
    nim_embed_model: str = _DEFAULT_EMBED_MODEL,
    thresholds: MetricThresholds | None = None,
    rpm_limit: int = 10,
    reports_dir: Path | None = None,
) -> RagasReport:
    """Run the full RAGAS evaluation harness over the golden QA dataset.

    Args:
        golden_qa_path:   Path to ``golden_qa.jsonl``.
        org_id:           Tenant org_id for RBAC-filtered retrieval.
        role:             Role to query as (should match GoldenQA.required_role).
        store:            Initialised MilvusStore containing the document corpus.
        bm25_index:       Pre-built BM25 index over the visible corpus.
        nim_llm_base_url: Base URL for the NIM LLM judge endpoint.
        nim_embed_base_url: Base URL for the NIM embedding judge endpoint.
        nim_llm_model:    NIM LLM model name (default: llama-3.1-8b-instruct).
        nim_embed_model:  NIM embedding model name (default: nv-embedqa-e5-v5).
        thresholds:       Pass/fail cut-offs.  Defaults to MetricThresholds().
        rpm_limit:        Inter-question throttle (requests per minute to NIM).
        reports_dir:      Directory for JSON report.  Defaults to eval/ragas/reports/.

    Returns:
        RagasReport with per-question scores, aggregate means, and pass/fail verdict.

    Raises:
        EvalHarnessError: If ragas is not installed or dataset fails validation.
        EvalDatasetError: Propagated from load_golden_qa on bad dataset rows.
    """
    if thresholds is None:
        thresholds = MetricThresholds()

    log = logger.bind(golden_qa_path=str(golden_qa_path), org_id=org_id, role=str(role))
    log.info("ragas.eval.start")

    # Validate dataset up-front (raises EvalDatasetError on bad rows).
    dataset = load_golden_qa(golden_qa_path)
    log.info("ragas.eval.dataset_loaded", count=len(dataset))

    # Build NIM judge wrappers (ragas imported lazily inside make_nim_* functions).
    ragas_llm = make_nim_llm(base_url=nim_llm_base_url, model=nim_llm_model)
    ragas_embeddings = make_nim_embeddings(base_url=nim_embed_base_url, model=nim_embed_model)

    inter_question_delay = 60.0 / max(rpm_limit, 1)
    question_scores: list[QuestionScore] = []

    for idx, qa in enumerate(dataset):
        if idx > 0:
            # Throttle to avoid NIM rate limits.
            await asyncio.sleep(inter_question_delay)

        score = await _safe_run_question(
            qa=qa,
            store=store,
            bm25_index=bm25_index,
            org_id=org_id,
            role=role,
            ragas_llm=ragas_llm,
            ragas_embeddings=ragas_embeddings,
        )
        question_scores.append(score)

    # Write timestamped JSON report.
    if reports_dir is None:
        reports_dir = Path(__file__).parent / "reports"

    report_path = write_report(question_scores, thresholds, reports_dir)

    report = RagasReport.build(
        scores=question_scores,
        thresholds=thresholds,
        report_path=report_path,
    )

    log.info(
        "ragas.eval.done",
        passed=report.passed,
        mean_faithfulness=report.mean_faithfulness,
        mean_answer_relevancy=report.mean_answer_relevancy,
        mean_context_precision=report.mean_context_precision,
        mean_context_recall=report.mean_context_recall,
        failed_count=report.failed_count,
    )
    return report
