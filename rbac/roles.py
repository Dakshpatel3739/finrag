"""
rbac.roles — Role enum and sensitivity-based access policy.

This module IS the single source of truth for FinRAG's RBAC policy.
Every access decision must be derivable from the functions here.  No other
module should hard-code role-sensitivity relationships.

Policy (non-negotiable, encoding the security spec):
─────────────────────────────────────────────────────
  sensitivity_level │ allowed roles
  ──────────────────┼──────────────────────────────────
  public            │ owner, finance, hr, employee
  internal          │ owner, finance, hr, employee
  restricted        │ owner, finance
  ──────────────────┴──────────────────────────────────

Role capability summary:
  owner    — sees everything (public, internal, restricted)
  finance  — sees everything (public, internal, restricted)
  hr       — sees public + internal only  (NOT restricted)
  employee — sees public + internal only  (NOT restricted)

WHY dual-axis design (role + sensitivity_level):
  A chunk must pass TWO independent checks: the role allowlist AND the
  org_id tenant match (enforced separately in filter.py).  This mirrors
  real enterprise IAM: a principal has a role, and a resource has a
  classification.  The intersection is the access decision.
  - Using sensitivity_level as a second axis means the access policy can be
    audited by reading this file — no scattered if/else blocks needed.
  - allowed_roles is denormalised onto every chunk (not a separate ACL
    table) so the Milvus ARRAY_CONTAINS filter can run inside the vector
    search without a secondary lookup.

WHY SensitivityLevel is imported (not duplicated):
  SensitivityLevel is part of the chunk schema, defined in ingest.models.
  Duplicating it here would create two sources of truth for the same enum.
  The import ensures that schema changes propagate automatically.

Public API
──────────
  Role                              StrEnum with 4 values
  sensitivity_to_default_roles(s)   list[Role] for a sensitivity level
  can_role_see(role, sensitivity)   bool — policy lookup
"""

from __future__ import annotations

from enum import StrEnum

# WHY import from ingest.models: SensitivityLevel is part of the chunk schema.
# Importing (not duplicating) means a schema change in models.py propagates
# here automatically without risk of the two enums drifting.
from ingest.models import SensitivityLevel


class Role(StrEnum):
    """The four roles that exist in the FinRAG RBAC model.

    These are the only valid values for the ``role`` parameter in queries
    and for the ``allowed_roles`` field on chunks.  Using StrEnum means
    ``str(Role.OWNER) == "owner"`` — safe to store as a plain string in
    Milvus without a conversion step.
    """

    OWNER = "owner"
    FINANCE = "finance"
    HR = "hr"
    EMPLOYEE = "employee"


# ── Policy table ──────────────────────────────────────────────────────────────
# This dict is the SOLE definition of which roles can see which sensitivity
# levels.  Edit here — and here alone — when the policy changes.
#
# WHY a dict (not code): a dict is a data structure that can be inspected,
# serialised, and audited without executing logic.  An if/elif chain encoding
# the same policy would require reading code to audit access decisions.
_POLICY: dict[SensitivityLevel, list[Role]] = {
    SensitivityLevel.PUBLIC: [Role.OWNER, Role.FINANCE, Role.HR, Role.EMPLOYEE],
    SensitivityLevel.INTERNAL: [Role.OWNER, Role.FINANCE, Role.HR, Role.EMPLOYEE],
    SensitivityLevel.RESTRICTED: [Role.OWNER, Role.FINANCE],
}


# ── Public API ────────────────────────────────────────────────────────────────


def sensitivity_to_default_roles(sensitivity: SensitivityLevel) -> list[Role]:
    """Return the roles allowed to access a chunk at this sensitivity level.

    This is the authoritative mapping used by rbac.classifier when tagging
    chunks at ingest time.  The returned list is a copy — callers may modify
    it without affecting the policy table.

    Args:
        sensitivity: The chunk's classification tier.

    Returns:
        A fresh list of Role values that are allowed to retrieve this chunk.
    """
    return list(_POLICY[sensitivity])


def can_role_see(role: Role, sensitivity: SensitivityLevel) -> bool:
    """Return True if ``role`` is permitted to access ``sensitivity`` chunks.

    This is the policy predicate used in tests and audit code.  The
    production enforcement path is the Milvus ARRAY_CONTAINS filter built
    by rbac.filter — this function is the human-readable equivalent.

    Args:
        role:        The querying user's role.
        sensitivity: The target chunk's sensitivity level.

    Returns:
        True if role appears in the policy list for sensitivity, else False.

    Examples:
        >>> can_role_see(Role.OWNER, SensitivityLevel.RESTRICTED)
        True
        >>> can_role_see(Role.HR, SensitivityLevel.RESTRICTED)
        False
        >>> can_role_see(Role.EMPLOYEE, SensitivityLevel.INTERNAL)
        True
    """
    return role in _POLICY[sensitivity]
