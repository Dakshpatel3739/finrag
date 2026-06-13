"""eval.models — pydantic v2 schema for the golden QA dataset.

GoldenQA is the single schema consumed by:
  - eval.loader (Phase 4a): validates each row in golden_qa.jsonl
  - eval.golden.test_dataset (Phase 4a): structural assertions on the dataset
  - Phase 4b RAGAS harness: ground_truth_answer + ground_truth_contexts feed
    the faithfulness and context recall metrics

WHY a dedicated pydantic model (not a raw dict):
    Type safety at the loader boundary means downstream evaluation code can
    rely on field presence and types without defensive None-checks everywhere.
    Validation errors surface at load time with a helpful line number rather
    than mysteriously failing mid-evaluation.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class GoldenQA(BaseModel):
    """A single golden QA pair for offline retrieval and generation evaluation.

    Fields follow the RAGAS evaluation schema so Phase 4b can consume this
    dataset directly: ground_truth_answer feeds answer correctness; the
    ground_truth_contexts list feeds context recall and precision.

    Access-control fields (required_role, sensitivity_level) are used by the
    Phase 4a leak suite to assert that only authorized roles can retrieve the
    supporting contexts.
    """

    id: str = Field(..., description="Unique identifier, e.g. 'nvda-rev-fy2024'")
    question: str = Field(..., min_length=10, description="Natural-language question")
    ground_truth_answer: str = Field(..., min_length=1, description="Expected correct answer text")
    ground_truth_contexts: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "Verbatim or near-verbatim source text snippets that support the answer. "
            "Used by RAGAS context recall / precision metrics in Phase 4b."
        ),
    )
    doc_name: str = Field(..., description="Source document filename (e.g. 'live_nvidia_10k.pdf')")
    page_number: int = Field(..., ge=0, description="0-indexed source page number")
    required_role: str = Field(
        ...,
        description=(
            "Minimum role that SHOULD be able to retrieve the answer. "
            "restricted sensitivity ⇒ must be 'owner' or 'finance'."
        ),
    )
    sensitivity_level: Literal["public", "internal", "restricted"] = Field(
        ..., description="Document sensitivity classification per FinRAG RBAC policy"
    )
    tags: list[str] = Field(
        default_factory=list,
        description=(
            "Freeform labels. 'verified' = ground truth confirmed by live NIM test. "
            "'needs-verification' = plausible but not yet confirmed against source."
        ),
    )
