"""eval.errors — domain-specific exceptions for the evaluation subsystem.

Following the FinRAG convention of one custom exception class per domain so
callers can catch eval-specific failures without catching broad base classes.
"""

from __future__ import annotations


class EvalDatasetError(Exception):
    """Raised when a golden QA dataset row fails pydantic validation.

    The exception message always includes the 1-indexed line number of the
    offending row so the caller can locate and fix it quickly.

    Example::

        EvalDatasetError("Golden dataset validation failed at line 7: ...")
    """


class EvalLeakError(Exception):
    """Raised when an RBAC leak is detected in the automated leak suite.

    Separate from AssertionError so callers can distinguish security policy
    violations (EvalLeakError) from test infrastructure failures.
    """


class EvalHarnessError(Exception):
    """Raised when the RAGAS evaluation harness cannot be initialised.

    Typical causes:
    - ragas package not installed (install with ``pip install 'finrag[eval-live]'``)
    - NIM LLM or embedding endpoint unreachable
    - Golden QA dataset fails schema validation

    Separate from EvalDatasetError so callers can distinguish harness setup
    failures from dataset content errors.
    """
