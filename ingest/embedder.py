"""
ingest.embedder — fills Chunk.embedding by calling the NeMo Embedding NIM.

This is an explicit pipeline step, separate from ingest_pdf (parse + chunk).
Callers compose the two steps:

    chunks = ingest_pdf(path)
    chunks = await embed_chunks(chunks)
    # chunks[i].embedding is now a non-None float vector
    # next step: milvus_write(chunks)

Keeping embedding separate from ingest_pdf means:
  - ingest_pdf tests need no network (embedding is mocked or skipped).
  - The embedding step can be retried independently without re-parsing.
  - Future batch-ingest jobs can parallelise parsing and embedding.

Public API
----------
    embed_chunks(chunks, input_type) -> list[Chunk]
"""

from __future__ import annotations

import structlog

from ingest.errors import EmbeddingError
from ingest.models import Chunk
from ingest.nim_client import InputType, embed_texts

logger: structlog.BoundLogger = structlog.get_logger(__name__)


async def embed_chunks(
    chunks: list[Chunk],
    input_type: InputType = "passage",
) -> list[Chunk]:
    """Embed all chunks and return new Chunk objects with embedding populated.

    Extracts chunk.text from every chunk, calls embed_texts in one batched
    NIM call, then returns new Chunk instances (via model_copy) with the
    embedding field filled.

    WHY model_copy instead of mutation: Pydantic BaseModel instances support
    direct assignment, but model_copy(update=...) is explicit about intent and
    makes the transformation easy to trace — each call returns a new object.

    Order guarantee: chunks[i] always receives vectors[i].  This is enforced by
    both nim_client (pre-allocated result slots) and the zip here.

    Args:
        chunks:     Schema-complete Chunk objects (embedding may be None).
        input_type: Must be "passage" for document chunks.  Pass "query" only
                    when embedding a search query (retrieval slice).

    Returns:
        New list of Chunk objects with embedding populated (never None).

    Raises:
        EmbeddingError: If the NIM call fails, if the returned vector count does
                        not match the chunk count, or if vectors have inconsistent
                        dimensions across chunks.
    """
    if not chunks:
        return []

    log = logger.bind(chunk_count=len(chunks), input_type=input_type)
    log.info("embedder.start")

    texts = [chunk.text for chunk in chunks]
    vectors = await embed_texts(texts, input_type=input_type)

    # Count invariant: one vector per chunk — anything else is a NIM contract violation
    if len(vectors) != len(chunks):
        raise EmbeddingError(f"Vector count mismatch: expected {len(chunks)}, got {len(vectors)}")

    # Dimension consistency: all vectors must have the same length so Milvus
    # sees a uniform schema.  A partial failure in the NIM batch could produce
    # a truncated vector that passes count check but breaks the index.
    if vectors:
        dim = len(vectors[0])
        for i, vec in enumerate(vectors):
            if len(vec) != dim:
                raise EmbeddingError(
                    f"Embedding dimension mismatch at index {i}: expected {dim}, got {len(vec)}"
                )

    embedded = [
        chunk.model_copy(update={"embedding": vec})
        for chunk, vec in zip(chunks, vectors, strict=True)
    ]

    log.info("embedder.done", chunk_count=len(embedded), embedding_dim=len(vectors[0]))
    return embedded
