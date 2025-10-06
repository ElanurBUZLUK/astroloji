#!/usr/bin/env python3
"""Compare dense, sparse, hybrid, and hybrid+rerank retrieval performance."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from statistics import mean
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.evaluation.metrics_util import ndcg_at_k, recall_at_k
from app.rag.re_ranker import rerank as bge_rerank
from app.rag.retriever import build_retriever_profile, pick_alpha, search_hybrid


async def _run_mode(
    examples: List[Dict],
    mode: str,
    top_k: int,
    alpha: Optional[float],
) -> Dict[str, float]:
    profile = build_retriever_profile()
    dense_store = profile.get("dense")
    sparse_store = profile.get("sparse")

    if mode == "dense" and not dense_store:
        raise RuntimeError("Dense store unavailable for 'dense' mode")
    if mode == "sparse" and not sparse_store:
        raise RuntimeError("Sparse store unavailable for 'sparse' mode")

    ndcg_scores: List[float] = []
    recall_scores: List[float] = []

    for example in examples:
        query = example["query"]
        ideal = example.get("ideal_doc_ids", [])
        query_alpha = alpha if alpha is not None else pick_alpha(query)

        if mode == "dense":
            results = await search_hybrid(query, top_k, dense_store, None)
        elif mode == "sparse":
            results = await search_hybrid(query, top_k, None, sparse_store)
        elif mode == "hybrid":
            results = await search_hybrid(
                query, top_k, dense_store, sparse_store, alpha=query_alpha
            )
        elif mode == "hybrid_rerank":
            hybrid = await search_hybrid(
                query, top_k, dense_store, sparse_store, alpha=query_alpha
            )
            results = bge_rerank(query, hybrid) or hybrid
        else:
            raise ValueError(f"Unknown mode: {mode}")

        ranked_ids = [res.source_id for res in results[:top_k]]
        relevance_float = [1.0 if rid in ideal else 0.0 for rid in ranked_ids]
        relevance_binary = [1 if rid in ideal else 0 for rid in ranked_ids]
        ndcg_scores.append(ndcg_at_k(relevance_float, top_k))
        recall_scores.append(recall_at_k(relevance_binary, top_k))

    return {
        "ndcg": mean(ndcg_scores) if ndcg_scores else 0.0,
        "recall": mean(recall_scores) if recall_scores else 0.0,
    }


def load_examples(path: Path) -> List[Dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


async def run(file_path: Path, top_k: int, alpha: Optional[float]) -> Dict[str, Dict[str, float]]:
    examples = load_examples(file_path)
    modes = ["dense", "sparse", "hybrid", "hybrid_rerank"]
    results: Dict[str, Dict[str, float]] = {}
    for mode in modes:
        try:
            results[mode] = await _run_mode(examples, mode, top_k, alpha)
        except RuntimeError as exc:
            results[mode] = {"error": str(exc)}  # type: ignore[assignment]
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate hybrid retrieval modes")
    parser.add_argument("--file", required=True, help="JSONL file with query/ideal_doc_ids")
    parser.add_argument("--k", type=int, default=5, help="Cutoff for metrics")
    parser.add_argument(
        "--alpha",
        type=float,
        default=None,
        help="Hybrid score mixing ratio (omit for adaptive heuristic)",
    )
    args = parser.parse_args()

    result = asyncio.run(run(Path(args.file), args.k, args.alpha))
    payload = {
        "k": args.k,
        "alpha": args.alpha if args.alpha is not None else "auto",
        "results": result,
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
