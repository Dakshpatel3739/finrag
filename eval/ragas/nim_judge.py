"""eval.ragas.nim_judge — build RAGAS-compatible LLM and embedding wrappers for NIM.

RAGAS 0.4.x uses LangchainLLMWrapper / LangchainEmbeddingsWrapper to talk to
any LLM/embedding backend that LangChain supports.  We point both wrappers at
the NVIDIA NIM OpenAI-compatible endpoints.

WHY lazy imports:
    ``from ragas import ...`` at module level would require ``ragas`` to be
    installed for any code that imports this module — including CI, which only
    has the ``[dev]`` extra.  All ragas imports are deferred to function bodies
    so this module is importable without ragas.

Asymmetric embedding note (nv-embedqa-e5-v5):
    NVIDIA's embedding models require ``input_type="query"`` for query vectors
    and ``input_type="passage"`` for document vectors.  LangChain's generic
    ``OpenAIEmbeddings`` routes ``embed_query()`` and ``embed_documents()``
    through the same endpoint without the ``input_type`` param.

    For RAGAS correctness the default NIM embedding model is ``nv-embedqa-e5-v5``.
    Callers may override ``embed_model`` with any NIM model whose endpoint
    accepts standard OpenAI ``/v1/embeddings`` format.  If the NIM model needs
    ``input_type``, configure a custom LangChain wrapper and pass the resulting
    ``LangchainEmbeddingsWrapper`` directly to ``run_ragas_eval``.
"""

from __future__ import annotations

# All ragas/langchain imports are deferred to function bodies — see WHY above.


def make_nim_llm(
    base_url: str,
    model: str,
    temperature: float = 0.0,
) -> object:
    """Return a RAGAS LangchainLLMWrapper pointed at a NIM LLM endpoint.

    Args:
        base_url:    NIM LLM base URL, e.g. ``https://nim.example.com/v1``.
        model:       NIM model name, e.g. ``"meta/llama-3.1-8b-instruct"``.
        temperature: Sampling temperature (0.0 = deterministic for judge).

    Returns:
        A ``ragas.llms.LangchainLLMWrapper`` instance.

    Raises:
        EvalHarnessError: If ragas is not installed.
    """
    try:
        from langchain_openai import ChatOpenAI
        from ragas.llms import LangchainLLMWrapper
    except ImportError as exc:
        from eval.errors import EvalHarnessError

        raise EvalHarnessError(
            "ragas is not installed. Install with: pip install 'finrag[eval-live]'"
        ) from exc

    chat = ChatOpenAI(
        base_url=base_url,
        model=model,
        temperature=temperature,
        api_key="dummy",  # NIM uses API key from env; placeholder satisfies pydantic
    )
    return LangchainLLMWrapper(chat)


def make_nim_embeddings(
    base_url: str,
    model: str,
) -> object:
    """Return a RAGAS LangchainEmbeddingsWrapper pointed at a NIM embedding endpoint.

    Args:
        base_url: NIM embedding base URL, e.g. ``https://nim.example.com/v1``.
        model:    NIM model name, e.g. ``"nvidia/nv-embedqa-e5-v5"``.

    Returns:
        A ``ragas.embeddings.LangchainEmbeddingsWrapper`` instance.

    Raises:
        EvalHarnessError: If ragas is not installed.
    """
    try:
        from langchain_openai import OpenAIEmbeddings
        from ragas.embeddings import LangchainEmbeddingsWrapper
    except ImportError as exc:
        from eval.errors import EvalHarnessError

        raise EvalHarnessError(
            "ragas is not installed. Install with: pip install 'finrag[eval-live]'"
        ) from exc

    embeddings = OpenAIEmbeddings(
        base_url=base_url,
        model=model,
        api_key="dummy",  # NIM uses env var; placeholder satisfies pydantic
    )
    return LangchainEmbeddingsWrapper(embeddings)
