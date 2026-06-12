"""
generation.errors — custom exception types for the generation domain.

Keeping domain exceptions separate means callers can catch exactly the failure
mode they care about without accidentally swallowing unrelated errors.
"""


class GenerationError(Exception):
    """Raised when the LLM NIM fails to produce a response.

    Covers permanent HTTP failures after retries, unexpected response shapes,
    empty choice lists, and other invariant violations from the chat/completions
    endpoint.
    """
