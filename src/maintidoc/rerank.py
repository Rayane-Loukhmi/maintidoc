"""Reranker multilingue pour les passages texte."""
from __future__ import annotations

from functools import lru_cache

from sentence_transformers import CrossEncoder

RERANK_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


@lru_cache(maxsize=1)
def reranker() -> CrossEncoder:
    return CrossEncoder(RERANK_MODEL, device="cpu")


def rerank_hits(question: str, hits: list[dict], top_k: int = 6) -> list[dict]:
    """Réordonne les passages avec un cross-encoder (question, passage)."""
    if not hits:
        return hits
    pairs = [(question, hit["text"]) for hit in hits]
    scores = reranker().predict(pairs)
    ordered = sorted(zip(hits, scores), key=lambda item: float(item[1]), reverse=True)[:top_k]
    results = []
    for rank, (hit, score) in enumerate(ordered, 1):
        item = dict(hit)
        item["rank"] = rank
        item["rerank_score"] = float(score)
        results.append(item)
    return results
