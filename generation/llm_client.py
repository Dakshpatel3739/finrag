"""
generation.llm_client — async client for the NVIDIA LLM NIM (chat/completions).

Uses the OpenAI-compatible endpoint at ``{nim_llm_base_url}/chat/completions``.
All configuration is env-driven (NIM_LLM_BASE_URL, NIM_LLM_MODEL) so swapping
LLM models requires zero code edits.

WHY temperature=0.1:
    Financial document Q&A demands factual fidelity.  Low temperature keeps
    sampling near the mode of the model distribution, reducing paraphrase
    drift and hallucinated numbers.  The system prompt also constrains the
    model to cite only the provided context, but temperature is a second line
    of defense against creative reinterpretation of source text.

WHY nim_cost_log=True on the done event:
    A structured-log hook downstream can filter on ``nim_cost_log=True`` and
    sum ``prompt_tokens`` + ``completion_tokens`` across calls to estimate
    API spend without parsing arbitrary log lines.

Retry strategy mirrors ingest/nim_client.py:
    429 / 5xx → exponential backoff (1 s, 2 s, 4 s) up to _MAX_RETRIES.
    Non-retryable 4xx → raise GenerationError immediately.

Public API
----------
    generate(system_prompt, user_prompt) -> str
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Final, TypedDict

import httpx
import structlog

from config.settings import get_settings
from generation.errors import GenerationError

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_MAX_RETRIES: Final[int] = 3
_RETRY_BASE_S: Final[float] = 1.0

# WHY 0.1: grounded financial Q&A — stay near the probability mode; see module docstring.
_TEMPERATURE: Final[float] = 0.1
_MAX_TOKENS: Final[int] = 1024


# ---------------------------------------------------------------------------
# Response type (OpenAI-compatible chat/completions)
# ---------------------------------------------------------------------------


class _MessageContent(TypedDict):
    role: str
    content: str


class _Choice(TypedDict):
    index: int
    message: _MessageContent
    finish_reason: str


class _Usage(TypedDict):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class _ChatCompletionResponse(TypedDict):
    id: str
    choices: list[_Choice]
    usage: _Usage
    model: str


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def generate(system_prompt: str, user_prompt: str) -> str:
    """Call the NVIDIA LLM NIM to produce a grounded answer.

    Sends a two-message chat completion request (system + user) and returns
    the assistant's text content.  Retries on 429 and 5xx with exponential
    backoff.

    Args:
        system_prompt: Instructions for the LLM (grounding + citation rules).
        user_prompt:   The context block + user question assembled by prompt.py.

    Returns:
        The raw assistant text from the first choice.

    Raises:
        GenerationError: After exhausting retries, on a non-retryable HTTP
                         error, or if the response contains no choices.
    """
    settings = get_settings()
    api_key = settings.nim_api_key.get_secret_value()
    base_url = settings.nim_llm_base_url
    model = settings.nim_llm_model

    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": _TEMPERATURE,
        "max_tokens": _MAX_TOKENS,
    }

    log = logger.bind(model=model)
    log.info("llm_client.generate_start")
    t0 = time.monotonic()

    result = await _generate_with_retry(url=url, headers=headers, payload=payload, log=log)

    elapsed = time.monotonic() - t0
    # nim_cost_log hook: downstream cost-accounting tooling filters on this flag
    # and aggregates prompt_tokens + completion_tokens to estimate API spend.
    log.info(
        "llm_client.generate_done",
        prompt_tokens=result["usage"]["prompt_tokens"],
        completion_tokens=result["usage"]["completion_tokens"],
        total_tokens=result["usage"]["total_tokens"],
        elapsed_s=round(elapsed, 3),
        nim_cost_log=True,
    )

    choices = result["choices"]
    if not choices:
        raise GenerationError("LLM NIM returned 0 choices in chat/completions response")

    return choices[0]["message"]["content"]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


async def _generate_with_retry(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    log: structlog.BoundLogger,
) -> _ChatCompletionResponse:
    """POST to chat/completions with exponential-backoff retry.

    Retries on 429 and 5xx.  Raises GenerationError on permanent failure or
    non-retryable 4xx.
    """
    async with httpx.AsyncClient(timeout=120.0) as client:
        for attempt in range(_MAX_RETRIES):
            try:
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code == 200:
                    resp_data: _ChatCompletionResponse = response.json()
                    log.info("llm_client.request_ok", attempt=attempt)
                    return resp_data

                if response.status_code == 429 or response.status_code >= 500:
                    wait_s = _RETRY_BASE_S * (2**attempt)
                    log.warning(
                        "llm_client.retry",
                        status=response.status_code,
                        attempt=attempt,
                        wait_s=wait_s,
                    )
                    await asyncio.sleep(wait_s)
                    continue

                # Non-retryable (400, 401, 403, …)
                raise GenerationError(
                    f"LLM NIM returned non-retryable status {response.status_code}: "
                    f"{response.text[:200]}"
                )

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                wait_s = _RETRY_BASE_S * (2**attempt)
                log.warning(
                    "llm_client.network_error",
                    error=str(exc),
                    attempt=attempt,
                    wait_s=wait_s,
                )
                await asyncio.sleep(wait_s)

    raise GenerationError(f"LLM NIM failed permanently after {_MAX_RETRIES} retries")
