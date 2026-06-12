"""
retrieval.errors — custom exception types for the vector-store domain.

Keeping domain exceptions separate from ingest exceptions means callers can
catch exactly the failure mode they care about without accidentally swallowing
unrelated errors.
"""


class VectorStoreError(Exception):
    """Base class for all vector-store failures.

    Raised by MilvusStore when:
      - A chunk is missing its embedding before insert.
      - A Milvus operation returns an unexpected result.
      - The collection schema is inconsistent with the expected layout.
    """
