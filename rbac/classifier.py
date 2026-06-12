"""
rbac.classifier — ingest-time access metadata assignment.

Provides assign_access(), which stamps a Chunk with the org_id,
sensitivity_level, and allowed_roles it needs for the Milvus RBAC filter.

Two classification paths:

  (a) Explicit — caller provides sensitivity_level.
      Use this when the sensitivity comes from document metadata, an upload
      form, or a trust-level policy.  The provided level is accepted as-is
      and the allowed_roles are derived from the policy table in roles.py.

  (b) Heuristic — caller provides None for sensitivity_level.
      A lightweight keyword scanner inspects the chunk's text and section
      heading for signals that suggest executive-compensation or otherwise
      restricted content and returns RESTRICTED; everything else defaults to
      INTERNAL.

WHY the heuristic is deliberately simple:
  The heuristic is a convenience default for the development and demo path.
  A production deployment will always classify documents explicitly using
  the uploader's clearance level (Phase 3 JWT) or a document-level policy
  set at upload time.  Keeping the heuristic simple makes it easy to replace
  without touching surrounding logic.  It is documented as "best-effort" and
  clearly marked with a comment so future engineers don't mistake it for a
  production security control.

WHY allowed_roles is ALWAYS derived (never passed in):
  Allowing callers to directly set allowed_roles bypasses the policy table
  and creates a vector for privilege escalation errors ("typo grants owner
  access to a restricted chunk").  The only way to set allowed_roles is via
  the policy map in roles.py, which is the single source of truth.

Public API
──────────
  assign_access(chunk, org_id, sensitivity_level) -> Chunk
"""

from __future__ import annotations

import structlog

from ingest.models import Chunk, SensitivityLevel
from rbac.roles import Role, sensitivity_to_default_roles

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# ── Heuristic signals ─────────────────────────────────────────────────────────
# WHY frozenset: immutable, O(1) membership test, hashable.
# These keywords trigger RESTRICTED classification in the heuristic path.
# They are intentionally broad — false positives (over-restricting) are safer
# than false negatives (under-restricting).
_RESTRICTED_SIGNALS: frozenset[str] = frozenset(
    [
        "salary",
        "salaries",
        "compensation",
        "executive compensation",
        "bonus",
        "bonuses",
        "payroll",
        "severance",
        "board compensation",
        "confidential",
        "non-public",
        "nonpublic",
    ]
)


def _heuristic_sensitivity(chunk: Chunk) -> SensitivityLevel:
    """Return a best-effort SensitivityLevel based on chunk content.

    Scans the combined chunk text + section heading for any restricted keyword
    from _RESTRICTED_SIGNALS.  If found, returns RESTRICTED; otherwise INTERNAL.

    WHY INTERNAL (not PUBLIC) as the default:
        Defaulting to INTERNAL (rather than PUBLIC) means unclassified content
        is seen by all four roles but is never accidentally world-readable if a
        document is shared across orgs.  The policy table gives INTERNAL the
        same allowed_roles as PUBLIC, so this default does not restrict access
        in Phase 1/2.  Phase 3 will restrict INTERNAL to authenticated users only.

    This is a HEURISTIC — it will mis-classify.  It is a development convenience,
    not a production security control.  Callers who need correct classification
    MUST pass an explicit sensitivity_level.

    Args:
        chunk: The chunk to classify.

    Returns:
        SensitivityLevel.RESTRICTED if any signal is found, else INTERNAL.
    """
    combined = (chunk.text + " " + chunk.section).lower()
    for signal in _RESTRICTED_SIGNALS:
        if signal in combined:
            logger.debug(
                "classifier.heuristic_restricted",
                chunk_id=chunk.chunk_id,
                matched_signal=signal,
            )
            return SensitivityLevel.RESTRICTED
    return SensitivityLevel.INTERNAL


def assign_access(
    chunk: Chunk,
    org_id: str,
    sensitivity_level: SensitivityLevel | None = None,
) -> Chunk:
    """Stamp a Chunk with org_id, sensitivity_level, and allowed_roles.

    Replaces the Phase 1 dev defaults (org_id="dev", allowed_roles=["owner"])
    with real access metadata derived from the policy table in roles.py.

    WHY allowed_roles is not a parameter:
        Callers specifying allowed_roles directly bypass the policy table,
        creating a risk of privilege-escalation errors (see module docstring).
        The only way to influence allowed_roles is via sensitivity_level →
        policy map → roles.

    Args:
        chunk:             The chunk to classify (immutable; a copy is returned).
        org_id:            Tenant organisation identifier (from the uploader's
                           JWT in Phase 3; caller-provided in Phase 1/2).
        sensitivity_level: Explicit classification tier.  Pass None to invoke
                           the heuristic classifier (best-effort, see docstring).

    Returns:
        A new Chunk (pydantic model_copy) with org_id, sensitivity_level, and
        allowed_roles populated according to the policy.
    """
    if sensitivity_level is None:
        # WHY heuristic: convenience path for dev/demo when the caller doesn't
        # supply an explicit sensitivity.  Never used in production flows where
        # the uploader's clearance level drives classification.
        sensitivity_level = _heuristic_sensitivity(chunk)

    roles: list[Role] = sensitivity_to_default_roles(sensitivity_level)
    role_strings: list[str] = [str(r) for r in roles]

    updated = chunk.model_copy(
        update={
            "org_id": org_id,
            "sensitivity_level": sensitivity_level,
            "allowed_roles": role_strings,
        }
    )

    logger.debug(
        "classifier.assigned",
        chunk_id=chunk.chunk_id,
        org_id=org_id,
        sensitivity=str(sensitivity_level),
        allowed_roles=role_strings,
    )
    return updated
