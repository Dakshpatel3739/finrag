"""
rbac — FinRAG chunk-level RBAC domain module.

Phase 2: retrieval-time access control enforced via Milvus metadata filters.

Public surface:
    rbac.roles       — Role enum, sensitivity_to_default_roles, can_role_see
    rbac.classifier  — assign_access (ingest-time chunk tagging)
    rbac.filter      — build_rbac_filter (Milvus boolean expression builder)
"""
