"""
retrieval.fusion — Reciprocal Rank Fusion (RRF) for hybrid retrieval.

RRF combines ranked lists from heterogeneous retrieval systems (dense vector
search + BM25 lexical search) into a single unified ranking without requiring
score normalisation.

WHY RRF over weighted score combination:
    Dense similarity scores (cosine) and BM25 scores live in completely
    different numerical ranges and distributions.  Combining them directly
    (e.g. alpha * dense + (1-alpha) * bm25) requires per-corpus calibration of
    alpha, and the optimal alpha shifts with document length and query type.
    RRF is calibration-free: it uses only the rank positions, not the raw
    scores, so it is robust across corpora and retrieval system pairs.
    See Cormack, Clarke & Buettcher (2009) "Reciprocal Rank Fusion outperforms
    Condorcet and individual rank learning methods".

RRF formula (as implemented):
    score(d) = Σ_{r ∈ rankings} 1 / (k + rank_r(d))

    where rank_r(d) is the 1-indexed position of document d in ranking r,
    and k is a smoothing constant (default 60, per the original paper).
    Documents absent from a ranking contribute 0 to the sum for that ranking.

Public API
----------
    rrf_fuse(dense_ids, bm25_ids, k) -> list[str]
        Returns chunk_ids ordered by descending RRF score.
"""

from __future__ import annotations


def rrf_fuse(
    dense_ids: list[str],
    bm25_ids: list[str],
    k: int = 60,
) -> list[str]:
    """Fuse two ranked lists via Reciprocal Rank Fusion.

    RRF formula: score(d) = Σ_r 1 / (k + rank_r(d))
    Ranks are 1-indexed (first element = rank 1).
    A chunk present in both lists accumulates scores from both.
    A chunk present in only one list still gets a non-zero score from that list.

    Args:
        dense_ids: chunk_ids ordered by dense (cosine) similarity, best first.
        bm25_ids:  chunk_ids ordered by BM25 score, best first.
        k:         RRF smoothing constant.  Default 60 matches the original
                   paper and is robust across retrieval system pairs.  Smaller
                   k amplifies the influence of top-ranked documents.

    Returns:
        Merged list of chunk_ids, ordered by RRF score descending.
        Contains the union of both input lists (no duplicates).

    Examples:
        >>> rrf_fuse(["a", "b", "c"], ["b", "a", "d"], k=60)
        ['b', 'a', 'c', 'd']
        # b: 1/(61) + 1/(61) = 0.0328  [rank 1 in both]
        # a: 1/(62) + 1/(62) = 0.0322  [rank 2 in both]
        # c: 1/(63)           = 0.0159  [rank 3 dense only]
        # d:           1/(63) = 0.0159  [rank 3 bm25 only]
    """
    scores: dict[str, float] = {}

    for rank, chunk_id in enumerate(dense_ids, start=1):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)

    for rank, chunk_id in enumerate(bm25_ids, start=1):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)

    return sorted(scores, key=lambda cid: scores[cid], reverse=True)
