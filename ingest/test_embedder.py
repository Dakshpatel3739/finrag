"""
Tests for ingest.embedder — embed_chunks step.

All tests mock ingest.nim_client.embed_texts so no network is required.

Test coverage:
  - Order preservation: chunk[i] receives vector[i] even for large inputs
  - Count mismatch: fewer vectors than chunks → EmbeddingError
  - Dimension consistency: inconsistent vector lengths → EmbeddingError
  - Embedding populated: output chunks have non-None embedding field
  - Empty input: empty list → empty list, no NIM call
  - input_type forwarded: "query" propagates to embed_texts
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from ingest.embedder import embed_chunks
from ingest.errors import EmbeddingError
from ingest.models import Chunk, make_chunk_id

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chunk(index: int, text: str | None = None) -> Chunk:
    """Return a minimal Chunk with deterministic fields for testing."""
    return Chunk(
        chunk_id=make_chunk_id("doc_test", 0, index),
        doc_id="doc_test",
        doc_name="test.pdf",
        page_number=0,
        section="Section A",
        text=text or f"This is test chunk number {index} for embedding.",
    )


# ---------------------------------------------------------------------------
# Fast unit tests — embed_texts is always mocked
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_chunks_returns_empty_list() -> None:
    """embed_chunks([]) must return [] without calling embed_texts."""
    with patch("ingest.embedder.embed_texts", new=AsyncMock()) as mock_embed:
        result = await embed_chunks([])

    assert result == []
    mock_embed.assert_not_called()


@pytest.mark.asyncio
async def test_embeddings_are_populated() -> None:
    """All output chunks must have a non-None embedding after embed_chunks."""
    chunks = [_make_chunk(i) for i in range(3)]
    fake_vectors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]

    with patch("ingest.embedder.embed_texts", new=AsyncMock(return_value=fake_vectors)):
        result = await embed_chunks(chunks)

    assert all(c.embedding is not None for c in result)


@pytest.mark.asyncio
async def test_order_preservation() -> None:
    """chunk[i] must receive vector[i] — order must be preserved across the full list."""
    n = 7
    chunks = [_make_chunk(i) for i in range(n)]
    # Each vector is uniquely identifiable by its first element
    fake_vectors = [[float(i), float(i + 0.5)] for i in range(n)]

    with patch("ingest.embedder.embed_texts", new=AsyncMock(return_value=fake_vectors)):
        result = await embed_chunks(chunks)

    assert len(result) == n
    for i, chunk in enumerate(result):
        assert chunk.embedding == fake_vectors[i], (
            f"chunk[{i}] got {chunk.embedding}, expected {fake_vectors[i]}"
        )


@pytest.mark.asyncio
async def test_count_mismatch_raises_embedding_error() -> None:
    """If embed_texts returns fewer vectors than chunks, EmbeddingError must be raised."""
    chunks = [_make_chunk(i) for i in range(4)]
    too_few_vectors = [[0.1, 0.2], [0.3, 0.4]]  # only 2, need 4

    with patch("ingest.embedder.embed_texts", new=AsyncMock(return_value=too_few_vectors)):
        with pytest.raises(EmbeddingError, match="mismatch"):
            await embed_chunks(chunks)


@pytest.mark.asyncio
async def test_count_mismatch_too_many_raises_embedding_error() -> None:
    """If embed_texts returns more vectors than chunks, EmbeddingError must be raised."""
    chunks = [_make_chunk(0)]
    too_many_vectors = [[0.1], [0.2], [0.3]]  # 3 vectors for 1 chunk

    with patch("ingest.embedder.embed_texts", new=AsyncMock(return_value=too_many_vectors)):
        with pytest.raises(EmbeddingError, match="mismatch"):
            await embed_chunks(chunks)


@pytest.mark.asyncio
async def test_dimension_inconsistency_raises_embedding_error() -> None:
    """Vectors with different lengths must raise EmbeddingError."""
    chunks = [_make_chunk(i) for i in range(3)]
    # First vector has dim 3, second has dim 2 — inconsistent
    bad_vectors: list[list[float]] = [[0.1, 0.2, 0.3], [0.4, 0.5], [0.6, 0.7, 0.8]]

    with patch("ingest.embedder.embed_texts", new=AsyncMock(return_value=bad_vectors)):
        with pytest.raises(EmbeddingError, match="dimension"):
            await embed_chunks(chunks)


@pytest.mark.asyncio
async def test_input_type_forwarded_to_embed_texts() -> None:
    """embed_chunks must pass its input_type argument through to embed_texts."""
    chunks = [_make_chunk(0)]
    fake_vectors = [[0.1, 0.2]]

    with patch("ingest.embedder.embed_texts", new=AsyncMock(return_value=fake_vectors)) as mock_e:
        await embed_chunks(chunks, input_type="query")

    mock_e.assert_called_once()
    _, kwargs = mock_e.call_args
    assert kwargs.get("input_type") == "query"


@pytest.mark.asyncio
async def test_original_chunks_unchanged() -> None:
    """embed_chunks must not mutate the input chunks (returns new objects via model_copy)."""
    chunk = _make_chunk(0)
    original_embedding = chunk.embedding  # None before embedding

    fake_vectors = [[0.1, 0.2, 0.3]]
    with patch("ingest.embedder.embed_texts", new=AsyncMock(return_value=fake_vectors)):
        result = await embed_chunks([chunk])

    # Original chunk is unchanged
    assert chunk.embedding == original_embedding
    # Result chunk has the new embedding
    assert result[0].embedding == [0.1, 0.2, 0.3]
    # They are different objects
    assert result[0] is not chunk


@pytest.mark.asyncio
async def test_texts_extracted_correctly() -> None:
    """embed_chunks must pass chunk.text (not chunk_id or other fields) to embed_texts."""
    texts = ["revenue was strong", "expenses were flat", "profit grew 10%"]
    chunks = [_make_chunk(i, text=t) for i, t in enumerate(texts)]
    fake_vectors = [[float(i)] for i in range(3)]

    with patch("ingest.embedder.embed_texts", new=AsyncMock(return_value=fake_vectors)) as mock_e:
        await embed_chunks(chunks)

    # First positional arg must be the list of texts
    args, _ = mock_e.call_args
    assert args[0] == texts
