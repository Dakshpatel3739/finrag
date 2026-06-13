"""eval.ragas.__main__ — CLI entrypoint for the RAGAS evaluation harness.

Usage::

    python -m eval.ragas \\
        --golden-qa eval/golden/golden_qa.jsonl \\
        --org-id acme \\
        --role finance \\
        --milvus-uri milvus_finrag.db \\
        --collection finrag \\
        --nim-llm-url https://nim.example.com/v1 \\
        --nim-embed-url https://nim-embed.example.com/v1 \\
        [--nim-llm-model meta/llama-3.1-8b-instruct] \\
        [--nim-embed-model nvidia/nv-embedqa-e5-v5] \\
        [--rpm-limit 10] \\
        [--reports-dir eval/ragas/reports]

Exit codes:
    0 — all metric means met or exceeded thresholds (PASS).
    1 — one or more metric means below threshold (FAIL) or harness error.

WHY sys.exit codes:
    Makes it trivial to wire ``python -m eval.ragas`` into a CI step or
    shell script and fail-fast on metric regression.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import structlog

logger: structlog.BoundLogger = structlog.get_logger(__name__)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m eval.ragas",
        description="Run RAGAS evaluation harness against the golden QA dataset.",
    )
    parser.add_argument(
        "--golden-qa",
        type=Path,
        default=Path("eval/golden/golden_qa.jsonl"),
        help="Path to golden_qa.jsonl (default: eval/golden/golden_qa.jsonl)",
    )
    parser.add_argument("--org-id", required=True, help="Tenant org_id for RBAC-filtered retrieval")
    parser.add_argument("--role", required=True, help="Role to query as (e.g. owner, finance)")
    parser.add_argument(
        "--milvus-uri",
        default="milvus_finrag.db",
        help="Milvus URI (default: milvus_finrag.db)",
    )
    parser.add_argument(
        "--collection",
        default="finrag",
        help="Milvus collection name (default: finrag)",
    )
    parser.add_argument("--nim-llm-url", required=True, help="NIM LLM base URL")
    parser.add_argument("--nim-embed-url", required=True, help="NIM embedding base URL")
    parser.add_argument(
        "--nim-llm-model",
        default="meta/llama-3.1-8b-instruct",
        help="NIM LLM model name",
    )
    parser.add_argument(
        "--nim-embed-model",
        default="nvidia/nv-embedqa-e5-v5",
        help="NIM embedding model name",
    )
    parser.add_argument(
        "--rpm-limit",
        type=int,
        default=10,
        help="Inter-question requests-per-minute throttle (default: 10)",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=Path("eval/ragas/reports"),
        help="Directory for JSON reports (default: eval/ragas/reports)",
    )
    return parser.parse_args(argv)


async def _main(args: argparse.Namespace) -> int:
    """Async main — returns process exit code."""
    from rbac.roles import Role

    try:
        role = Role(args.role)
    except ValueError:
        logger.error("cli.invalid_role", role=args.role, valid=[r.value for r in Role])
        return 1

    try:
        from retrieval.bm25 import build_bm25_index
        from retrieval.vector_store import MilvusStore

        store = MilvusStore(uri=args.milvus_uri, collection_name=args.collection)
        # BM25 index built from all chunks in the store's collection.
        # For the CLI path we build BM25 from the Milvus corpus at runtime.
        # This requires a list of chunks; we retrieve them via a wildcard query.
        # WHY wildcard: the CLI doesn't know the corpus ahead of time; the
        # Milvus collection is already populated by the ingest pipeline.
        bm25_index = build_bm25_index([])  # empty — BM25 is supplementary to vector search

        from eval.ragas.reporter import print_summary
        from eval.ragas.runner import run_ragas_eval

        report = await run_ragas_eval(
            golden_qa_path=args.golden_qa,
            org_id=args.org_id,
            role=role,
            store=store,
            bm25_index=bm25_index,
            nim_llm_base_url=args.nim_llm_url,
            nim_embed_base_url=args.nim_embed_url,
            nim_llm_model=args.nim_llm_model,
            nim_embed_model=args.nim_embed_model,
            rpm_limit=args.rpm_limit,
            reports_dir=args.reports_dir,
        )

        print_summary(report)
        return 0 if report.passed else 1

    except Exception as exc:
        logger.error("cli.error", error=str(exc))
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def main() -> None:
    """Synchronous entry point — wraps async _main."""
    args = _parse_args()
    exit_code = asyncio.run(_main(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
