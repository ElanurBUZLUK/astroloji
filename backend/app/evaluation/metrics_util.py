"""Simple retrieval metric utilities: DCG/nDCG and Recall@k."""
from __future__ import annotations
from typing import List

def ndcg_at_k(relevances: List[float], k: int) -> float:
    rel_k = relevances[:k]
    ideal = sorted(relevances, reverse=True)[:k]
    def _dcg(arr):
        s = 0.0
        for i, rel in enumerate(arr):
            s += rel / (1.0 if i == 0 else (i + 1))
        return s
    dcg_v = _dcg(rel_k)
    idcg_v = _dcg(ideal) or 1.0
    return dcg_v / idcg_v

def recall_at_k(binary_relevances: List[int], k: int) -> float:
    total = sum(1 for r in binary_relevances if r > 0) or 1
    return sum(binary_relevances[:k]) / float(total)
