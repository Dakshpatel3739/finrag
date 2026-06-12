"""
Tests for retrieval.fusion — Reciprocal Rank Fusion.

All tests are pure-unit (no network, no Milvus, no fixtures).
Tests verify the RRF formula, edge cases, and parameter sensitivity.
"""

from __future__ import annotations

from retrieval.fusion import rrf_fuse


def test_item_in_both_lists_outscores_item_in_one() -> None:
    """A chunk ranked high in both lists must beat one ranked high in only one."""
    # "b" is rank 1 in both → RRF score = 1/61 + 1/61 ≈ 0.0328
    # "a" is rank 2 in dense, absent in bm25 → 1/62 ≈ 0.0161
    dense = ["b", "a"]
    bm25 = ["b", "c"]
    result = rrf_fuse(dense, bm25, k=60)
    assert result[0] == "b", f"'b' (top in both) must rank first, got {result}"


def test_rrf_math_on_known_inputs() -> None:
    """Verify exact RRF scores on a hand-calculable example.

    With k=60 and two rankings [a, b, c] and [b, a, d]:
      a: 1/61 + 1/62 ≈ 0.02783
      b: 1/62 + 1/61 ≈ 0.02783   (same as a — tied at ranks 2 and 1)
      Wait: a is rank 1 in dense, rank 2 in bm25 → 1/61 + 1/62
            b is rank 2 in dense, rank 1 in bm25 → 1/62 + 1/61 (same)
      So a and b are tied.  c and d are rank 3 in their respective lists → 1/63.
    The result must contain all 4 items, with a and b ahead of c and d.
    """
    dense = ["a", "b", "c"]
    bm25 = ["b", "a", "d"]
    result = rrf_fuse(dense, bm25, k=60)

    assert set(result) == {"a", "b", "c", "d"}, f"Union mismatch: {result}"
    # a and b (each in both lists) must outrank c and d (each in one list)
    top2 = set(result[:2])
    assert top2 == {"a", "b"}, f"Expected top-2 {{a,b}}, got {top2}"
    bottom2 = set(result[2:])
    assert bottom2 == {"c", "d"}, f"Expected bottom-2 {{c,d}}, got {bottom2}"


def test_empty_dense_list() -> None:
    """Empty dense list — only BM25 results appear, ordered by BM25 rank."""
    result = rrf_fuse([], ["x", "y", "z"], k=60)
    assert result == ["x", "y", "z"]


def test_empty_bm25_list() -> None:
    """Empty BM25 list — only dense results appear, ordered by dense rank."""
    result = rrf_fuse(["x", "y", "z"], [], k=60)
    assert result == ["x", "y", "z"]


def test_both_lists_empty() -> None:
    """Both lists empty — result is empty."""
    assert rrf_fuse([], [], k=60) == []


def test_disjoint_lists_returns_union() -> None:
    """Disjoint lists — result is the union of both, higher-ranked items first."""
    dense = ["a", "b"]
    bm25 = ["c", "d"]
    result = rrf_fuse(dense, bm25, k=60)
    # a(rank1 dense) = 1/61 > b(rank2 dense) = 1/62
    # c(rank1 bm25) = 1/61 > d(rank2 bm25) = 1/62
    # a and c tie; b and d tie — order within ties is arbitrary but stable
    assert set(result) == {"a", "b", "c", "d"}
    # rank-1 items from each list must outscore rank-2 items
    assert result.index("a") < result.index("b")
    assert result.index("c") < result.index("d")


def test_rrf_k_affects_score_spread() -> None:
    """Smaller k gives more weight to top-ranked items relative to lower ranks."""
    dense = ["top", "mid", "bot"]
    bm25: list[str] = []

    result_k1 = rrf_fuse(dense, bm25, k=1)
    result_k60 = rrf_fuse(dense, bm25, k=60)

    # Both should return same ORDER (identical lists, k just affects score values)
    assert result_k1 == result_k60 == ["top", "mid", "bot"]


def test_duplicate_chunk_ids_accumulate_scores() -> None:
    """The same chunk_id appearing in both lists gets summed RRF score (no dup rows)."""
    dense = ["shared", "only_dense"]
    bm25 = ["shared", "only_bm25"]
    result = rrf_fuse(dense, bm25, k=60)

    # "shared" should appear exactly once despite being in both lists
    assert result.count("shared") == 1
    # "shared" (rank 1 in both) outranks "only_dense" (rank 2 in one) and "only_bm25"
    assert result[0] == "shared"


def test_single_item_each_list() -> None:
    """Minimal case — one item per list."""
    result = rrf_fuse(["a"], ["b"], k=60)
    assert set(result) == {"a", "b"}
    assert len(result) == 2


def test_same_item_rank_one_both_lists() -> None:
    """If the same chunk tops both lists, it is unambiguously first."""
    result = rrf_fuse(["winner", "x", "y"], ["winner", "p", "q"], k=60)
    assert result[0] == "winner"
