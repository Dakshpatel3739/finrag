"""
Tests for rbac.roles — policy table, sensitivity_to_default_roles, can_role_see.

These tests are the FORMAL SPECIFICATION of the FinRAG access policy.
If they fail, the policy has changed.  Every change to the policy table
in roles.py MUST have a corresponding test update here.

Policy under test:
  sensitivity  │ owner  finance  hr  employee
  ─────────────┼────────────────────────────
  public       │  ✓       ✓      ✓     ✓
  internal     │  ✓       ✓      ✓     ✓
  restricted   │  ✓       ✓      ✗     ✗
"""

from __future__ import annotations

import pytest

from ingest.models import SensitivityLevel
from rbac.roles import Role, can_role_see, sensitivity_to_default_roles

# ---------------------------------------------------------------------------
# Role enum
# ---------------------------------------------------------------------------


def test_role_string_values() -> None:
    """Role enum values must match the spec strings."""
    assert str(Role.OWNER) == "owner"
    assert str(Role.FINANCE) == "finance"
    assert str(Role.HR) == "hr"
    assert str(Role.EMPLOYEE) == "employee"


def test_all_four_roles_exist() -> None:
    """There are exactly 4 roles."""
    assert set(Role) == {Role.OWNER, Role.FINANCE, Role.HR, Role.EMPLOYEE}


# ---------------------------------------------------------------------------
# sensitivity_to_default_roles
# ---------------------------------------------------------------------------


def test_public_allows_all_roles() -> None:
    """PUBLIC chunks are readable by every role."""
    roles = sensitivity_to_default_roles(SensitivityLevel.PUBLIC)
    assert set(roles) == {Role.OWNER, Role.FINANCE, Role.HR, Role.EMPLOYEE}


def test_internal_allows_all_roles() -> None:
    """INTERNAL chunks are readable by every role."""
    roles = sensitivity_to_default_roles(SensitivityLevel.INTERNAL)
    assert set(roles) == {Role.OWNER, Role.FINANCE, Role.HR, Role.EMPLOYEE}


def test_restricted_allows_only_owner_and_finance() -> None:
    """RESTRICTED chunks are readable only by owner and finance."""
    roles = sensitivity_to_default_roles(SensitivityLevel.RESTRICTED)
    assert set(roles) == {Role.OWNER, Role.FINANCE}
    assert Role.HR not in roles
    assert Role.EMPLOYEE not in roles


def test_sensitivity_to_default_roles_returns_copy() -> None:
    """Mutating the returned list must not affect the policy table."""
    roles = sensitivity_to_default_roles(SensitivityLevel.RESTRICTED)
    roles.clear()
    # Policy table must be intact after mutation
    fresh = sensitivity_to_default_roles(SensitivityLevel.RESTRICTED)
    assert len(fresh) == 2


# ---------------------------------------------------------------------------
# can_role_see — exhaustive table
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "role, sensitivity, expected",
    [
        # ── public: all roles can see ──────────────────────────────────────
        (Role.OWNER, SensitivityLevel.PUBLIC, True),
        (Role.FINANCE, SensitivityLevel.PUBLIC, True),
        (Role.HR, SensitivityLevel.PUBLIC, True),
        (Role.EMPLOYEE, SensitivityLevel.PUBLIC, True),
        # ── internal: all roles can see ───────────────────────────────────
        (Role.OWNER, SensitivityLevel.INTERNAL, True),
        (Role.FINANCE, SensitivityLevel.INTERNAL, True),
        (Role.HR, SensitivityLevel.INTERNAL, True),
        (Role.EMPLOYEE, SensitivityLevel.INTERNAL, True),
        # ── restricted: ONLY owner + finance ──────────────────────────────
        (Role.OWNER, SensitivityLevel.RESTRICTED, True),
        (Role.FINANCE, SensitivityLevel.RESTRICTED, True),
        (Role.HR, SensitivityLevel.RESTRICTED, False),  # THE KEY SECURITY BOUNDARY
        (Role.EMPLOYEE, SensitivityLevel.RESTRICTED, False),  # THE KEY SECURITY BOUNDARY
    ],
)
def test_can_role_see_policy_table(
    role: Role,
    sensitivity: SensitivityLevel,
    expected: bool,
) -> None:
    """can_role_see must match the policy table exactly for all 12 combinations."""
    assert can_role_see(role, sensitivity) == expected, (
        f"Policy violation: can_role_see({role!r}, {sensitivity!r}) should be {expected}"
    )


def test_hr_cannot_see_restricted_explicit() -> None:
    """HR CANNOT see RESTRICTED — explicit named test for clarity in reports."""
    assert can_role_see(Role.HR, SensitivityLevel.RESTRICTED) is False


def test_employee_cannot_see_restricted_explicit() -> None:
    """EMPLOYEE CANNOT see RESTRICTED — explicit named test for clarity in reports."""
    assert can_role_see(Role.EMPLOYEE, SensitivityLevel.RESTRICTED) is False


def test_owner_can_see_all_sensitivities() -> None:
    """OWNER can see every sensitivity level."""
    for sensitivity in SensitivityLevel:
        assert can_role_see(Role.OWNER, sensitivity), f"Owner should see {sensitivity}"


def test_finance_can_see_all_sensitivities() -> None:
    """FINANCE can see every sensitivity level."""
    for sensitivity in SensitivityLevel:
        assert can_role_see(Role.FINANCE, sensitivity), f"Finance should see {sensitivity}"


def test_hr_cannot_see_restricted_only() -> None:
    """HR can see public and internal but NOT restricted."""
    assert can_role_see(Role.HR, SensitivityLevel.PUBLIC) is True
    assert can_role_see(Role.HR, SensitivityLevel.INTERNAL) is True
    assert can_role_see(Role.HR, SensitivityLevel.RESTRICTED) is False


def test_employee_cannot_see_restricted_only() -> None:
    """EMPLOYEE can see public and internal but NOT restricted."""
    assert can_role_see(Role.EMPLOYEE, SensitivityLevel.PUBLIC) is True
    assert can_role_see(Role.EMPLOYEE, SensitivityLevel.INTERNAL) is True
    assert can_role_see(Role.EMPLOYEE, SensitivityLevel.RESTRICTED) is False
