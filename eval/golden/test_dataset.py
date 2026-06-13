"""eval.golden.test_dataset — CI-safe schema and loader tests for golden_qa.jsonl.

Tests:
  1. Every row validates against GoldenQA (pydantic schema correctness).
  2. Dataset contains ≥2 restricted rows (required for Phase 4b RAGAS coverage).
  3. Dataset contains ≥1 row of each other sensitivity level (public, internal).
  4. No duplicate ids across rows.
  5. required_role is consistent with sensitivity_level per the RBAC policy:
       restricted ⇒ required_role in {"owner", "finance"}
       public/internal ⇒ required_role in {"owner", "finance", "hr", "employee"}
  6. EvalDatasetError raised with correct line number on a malformed row.

CI safety: no network, no NIM calls, no .env required.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from eval.errors import EvalDatasetError
from eval.loader import load_golden_qa
from eval.models import GoldenQA

_DATASET_PATH = Path(__file__).parent / "golden_qa.jsonl"

# Roles permitted per sensitivity level (mirrors rbac.roles._POLICY).
_VALID_ROLES = {"owner", "finance", "hr", "employee"}
_RESTRICTED_ROLES = {"owner", "finance"}


@pytest.fixture(scope="module")
def golden_rows() -> list[GoldenQA]:
    """Load the shipped golden_qa.jsonl once for all tests in this module."""
    return load_golden_qa(_DATASET_PATH)


def test_all_rows_validate(golden_rows: list[GoldenQA]) -> None:
    """Every row in golden_qa.jsonl must conform to the GoldenQA schema."""
    assert len(golden_rows) >= 8, f"Dataset must have ≥8 rows, found {len(golden_rows)}"


def test_minimum_two_restricted_rows(golden_rows: list[GoldenQA]) -> None:
    """Dataset must include ≥2 restricted sensitivity rows for eval coverage."""
    restricted = [r for r in golden_rows if r.sensitivity_level == "restricted"]
    assert len(restricted) >= 2, (
        f"Need ≥2 restricted rows for Phase 4b RAGAS restricted coverage; found {len(restricted)}"
    )


def test_at_least_one_public_row(golden_rows: list[GoldenQA]) -> None:
    """Dataset must include ≥1 public sensitivity row."""
    public = [r for r in golden_rows if r.sensitivity_level == "public"]
    assert len(public) >= 1, f"Need ≥1 public row; found {len(public)}"


def test_at_least_one_internal_row(golden_rows: list[GoldenQA]) -> None:
    """Dataset must include ≥1 internal sensitivity row."""
    internal = [r for r in golden_rows if r.sensitivity_level == "internal"]
    assert len(internal) >= 1, f"Need ≥1 internal row; found {len(internal)}"


def test_no_duplicate_ids(golden_rows: list[GoldenQA]) -> None:
    """All row ids must be unique across the dataset."""
    ids = [r.id for r in golden_rows]
    duplicates = {i for i in ids if ids.count(i) > 1}
    assert not duplicates, f"Duplicate ids found in golden_qa.jsonl: {duplicates}"


def test_required_role_consistent_with_sensitivity(golden_rows: list[GoldenQA]) -> None:
    """required_role must be consistent with sensitivity_level per RBAC policy.

    restricted ⇒ required_role must be 'owner' or 'finance' (only privileged roles
                 can retrieve restricted content, so the minimum role is finance).
    public/internal ⇒ required_role may be any valid role.
    """
    violations: list[str] = []
    for row in golden_rows:
        if row.required_role not in _VALID_ROLES:
            violations.append(
                f"id={row.id!r}: required_role={row.required_role!r} is not a valid role "
                f"(must be one of {sorted(_VALID_ROLES)})"
            )
        if row.sensitivity_level == "restricted" and row.required_role not in _RESTRICTED_ROLES:
            violations.append(
                f"id={row.id!r}: restricted sensitivity requires required_role in "
                f"{sorted(_RESTRICTED_ROLES)}, got {row.required_role!r}"
            )
    assert not violations, "Role/sensitivity policy violations:\n" + "\n".join(violations)


def test_verified_revenue_row_present(golden_rows: list[GoldenQA]) -> None:
    """The verified 'nvda-rev-fy2024' row must be present with correct answer."""
    row_map = {r.id: r for r in golden_rows}
    assert "nvda-rev-fy2024" in row_map, "Required row 'nvda-rev-fy2024' is missing"
    row = row_map["nvda-rev-fy2024"]
    assert "26.97" in row.ground_truth_answer, (
        f"nvda-rev-fy2024 answer must contain '26.97', got: {row.ground_truth_answer!r}"
    )
    assert "verified" in row.tags, "nvda-rev-fy2024 must be tagged 'verified'"


def test_eval_dataset_error_on_malformed_row(tmp_path: Path) -> None:
    """EvalDatasetError must be raised with the correct line number on bad rows."""
    bad_jsonl = tmp_path / "bad.jsonl"
    # Line 1: valid
    # Line 2: missing required field 'question'
    good_row = (
        '{"id": "good-row", "question": "What is 1+1?", "ground_truth_answer": "2",'
        ' "ground_truth_contexts": ["1+1=2"], "doc_name": "test.pdf", "page_number": 0,'
        ' "required_role": "employee", "sensitivity_level": "public", "tags": []}'
    )
    bad_row = '{"id": "bad-row", "ground_truth_answer": "missing question field"}'
    bad_jsonl.write_text(f"{good_row}\n{bad_row}\n", encoding="utf-8")

    with pytest.raises(EvalDatasetError) as exc_info:
        load_golden_qa(bad_jsonl)

    assert "line 2" in str(exc_info.value), (
        f"Error message must reference 'line 2'; got: {exc_info.value}"
    )


def test_eval_dataset_error_on_invalid_json(tmp_path: Path) -> None:
    """EvalDatasetError must be raised when a row is not valid JSON."""
    bad_jsonl = tmp_path / "invalid_json.jsonl"
    bad_jsonl.write_text(
        "this is not json at all\n",
        encoding="utf-8",
    )

    with pytest.raises(EvalDatasetError) as exc_info:
        load_golden_qa(bad_jsonl)

    assert "line 1" in str(exc_info.value)


def test_ground_truth_contexts_non_empty(golden_rows: list[GoldenQA]) -> None:
    """Every row must have at least one ground_truth_context string."""
    empty_ctx = [r.id for r in golden_rows if len(r.ground_truth_contexts) == 0]
    assert not empty_ctx, f"Rows with empty ground_truth_contexts: {empty_ctx}"
