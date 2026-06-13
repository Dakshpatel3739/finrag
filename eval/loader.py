"""eval.loader — typed loader for the golden QA dataset.

Validates every row in the JSONL file through the GoldenQA pydantic model
before returning.  A single bad row raises EvalDatasetError with the
1-indexed line number so the dataset author can locate and fix it quickly.

Structured logging records file path and row count for audit/observability.
"""

from __future__ import annotations

import json
from pathlib import Path

import structlog

from eval.errors import EvalDatasetError
from eval.models import GoldenQA

logger: structlog.BoundLogger = structlog.get_logger(__name__)


def load_golden_qa(path: Path | str) -> list[GoldenQA]:
    """Load and validate the golden QA dataset from a JSONL file.

    Each non-blank line must be a valid JSON object conforming to the GoldenQA
    schema.  The entire file is validated before returning — if any row fails,
    EvalDatasetError is raised with the offending 1-indexed line number.

    WHY validate-all before returning:
        Partial returns (load 10 of 12, fail on row 11) leave callers with an
        incomplete dataset that may silently produce misleading eval metrics.
        Failing fast on ANY bad row forces the dataset author to fix the file
        before any evaluation runs.

    Args:
        path: Path to the ``.jsonl`` file.  Accepts ``str`` or ``Path``.

    Returns:
        A list of validated ``GoldenQA`` objects, one per non-blank line.

    Raises:
        EvalDatasetError: If any row fails JSON parsing or pydantic validation.
                         The message includes the 1-indexed line number.
        FileNotFoundError: If the file does not exist (raised by Path.open).
    """
    file_path = Path(path)
    log = logger.bind(file=str(file_path))
    log.info("loader.start")

    rows: list[GoldenQA] = []
    with file_path.open(encoding="utf-8") as fh:
        for lineno, raw_line in enumerate(fh, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                row = GoldenQA.model_validate(data)
            except Exception as exc:
                raise EvalDatasetError(
                    f"Golden dataset validation failed at line {lineno}: {exc}"
                ) from exc
            rows.append(row)

    log.info("loader.done", row_count=len(rows))
    return rows
