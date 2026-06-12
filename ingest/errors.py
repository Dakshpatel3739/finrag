"""
ingest.errors — custom exception types for the ingest domain.

Using domain-specific exceptions (not bare Exception) means callers can
catch exactly what they need without accidentally swallowing unrelated errors.
"""


class IngestError(Exception):
    """Base class for all ingest-pipeline failures."""


class ParseError(IngestError):
    """Raised when Docling (or the PDF parser) cannot parse a document.

    Attributes:
        path: The file path that failed to parse.
        reason: Human-readable explanation of the failure.
    """

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Failed to parse {path!r}: {reason}")


class ChunkError(IngestError):
    """Raised when chunking produces an invalid or empty result."""
