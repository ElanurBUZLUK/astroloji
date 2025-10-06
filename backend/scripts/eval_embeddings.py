"""Benchmark multilingual sentence-transformer embeddings against legacy vectors."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List

import numpy as np

try:  # SentenceTransformers may not be available in all environments
    from sentence_transformers import SentenceTransformer, util as st_util
except Exception as exc:  # pragma: no cover - optional dependency
    SentenceTransformer = None  # type: ignore
    st_util = None  # type: ignore
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

from app.rag.embeddings import generate_embedding


def _load_dataset(path: Path) -> List[Dict]:
    """Read a JSONL dataset into memory, skipping blank lines."""
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _cosine_similarity_matrix(query_vec: np.ndarray, doc_matrix: np.ndarray) -> np.ndarray:
    """Compute cosine similarities between a query vector and document matrix."""
    query_norm = np.linalg.norm(query_vec) + 1e-8
    doc_norm = np.linalg.norm(doc_matrix, axis=1, keepdims=True) + 1e-8
    return (doc_matrix @ query_vec) / (doc_norm[:, 0] * query_norm)


def _recall_at_k(ranked_ids: Iterable[str], relevant_ids: Iterable[str], k: int) -> float:
    """Return recall@k for a ranked list of document IDs."""
    top_k = list(ranked_ids)[:k]
    relevant = set(relevant_ids)
    if not relevant:
        return 0.0
    hits = sum(1 for doc_id in top_k if doc_id in relevant)
    return hits / len(relevant)


def _average_precision(ranked_ids: Iterable[str], relevant_ids: Iterable[str], k: int) -> float:
    """Compute MAP@k by averaging precision across relevant hits."""
    relevant = set(relevant_ids)
    if not relevant:
        return 0.0
    hits = 0
    precision_sum = 0.0
    for idx, doc_id in enumerate(ranked_ids, start=1):
        if idx > k:
            break
        if doc_id in relevant:
            hits += 1
            precision_sum += hits / idx
    return precision_sum / len(relevant)


def _evaluate_baseline(dataset: List[Dict], k: int) -> Dict[str, float]:
    """Benchmark the existing embedding generator against recall@k and MAP@k."""
    recalls = []
    maps = []
    for item in dataset:
        docs = item["documents"]
        doc_ids = [doc["id"] for doc in docs]
        doc_matrix = np.vstack([generate_embedding(doc.get("text", "")) for doc in docs])
        query_vec = np.array(generate_embedding(item["query"]))
        scores = _cosine_similarity_matrix(query_vec, doc_matrix)
        ranked = [doc_ids[idx] for idx in np.argsort(scores)[::-1]]
        recalls.append(_recall_at_k(ranked, item.get("relevant_ids", []), k))
        maps.append(_average_precision(ranked, item.get("relevant_ids", []), k))
    return {
        "recall@k": float(np.mean(recalls)) if recalls else 0.0,
        "map@k": float(np.mean(maps)) if maps else 0.0,
    }


def _evaluate_new_model(dataset: List[Dict], k: int, model_name: str, device: str) -> Dict[str, float]:
    """Score a SentenceTransformer model using the same recall@k and MAP@k metrics."""
    if SentenceTransformer is None or st_util is None:
        raise RuntimeError(
            "sentence-transformers is not available. Install it via `pip install sentence-transformers`.")

    model = SentenceTransformer(model_name, device=device)
    recalls = []
    maps = []
    for item in dataset:
        docs = item["documents"]
        doc_ids = [doc["id"] for doc in docs]
        doc_texts = [doc.get("text", "") for doc in docs]
        doc_embeddings = model.encode(doc_texts, convert_to_tensor=True, normalize_embeddings=True)
        query_embedding = model.encode(item["query"], convert_to_tensor=True, normalize_embeddings=True)
        hits = st_util.semantic_search(query_embedding, doc_embeddings, top_k=len(docs))[0]
        ranked = [doc_ids[hit["corpus_id"]] for hit in hits]
        recalls.append(_recall_at_k(ranked, item.get("relevant_ids", []), k))
        maps.append(_average_precision(ranked, item.get("relevant_ids", []), k))
    return {
        "recall@k": float(np.mean(recalls)) if recalls else 0.0,
        "map@k": float(np.mean(maps)) if maps else 0.0,
    }


def main() -> None:
    """CLI entry point for comparing baseline embeddings with a sentence-transformer."""
    parser = argparse.ArgumentParser(description="Evaluate multilingual embeddings against baseline")
    parser.add_argument("dataset", type=Path, help="Path to JSONL dataset (query, documents, relevant_ids)")
    parser.add_argument("--model", default="sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
    parser.add_argument("--device", default="cpu", help="Device for SentenceTransformer (cpu, cuda, mps)")
    parser.add_argument("--top-k", type=int, default=10, help="Recall@K / MAP@K cutoff")
    args = parser.parse_args()

    if _IMPORT_ERROR is not None and SentenceTransformer is None:
        raise RuntimeError(
            "sentence-transformers could not be imported. Install requirements first."
        ) from _IMPORT_ERROR

    dataset = _load_dataset(args.dataset)
    if not dataset:
        raise ValueError("Dataset is empty. Provide at least one query/document entry.")

    print(f"Loaded {len(dataset)} examples from {args.dataset} (k={args.top_k}).")

    baseline_metrics = _evaluate_baseline(dataset, args.top_k)
    print("\nBaseline (current 384-dim embeddings):")
    print(f"  Recall@{args.top_k}: {baseline_metrics['recall@k']:.2%}")
    print(f"  MAP@{args.top_k}:    {baseline_metrics['map@k']:.2%}")

    new_metrics = _evaluate_new_model(dataset, args.top_k, args.model, args.device)
    print(f"\n{args.model}:")
    print(f"  Recall@{args.top_k}: {new_metrics['recall@k']:.2%}")
    print(f"  MAP@{args.top_k}:    {new_metrics['map@k']:.2%}")

    delta_recall = new_metrics["recall@k"] - baseline_metrics["recall@k"]
    delta_map = new_metrics["map@k"] - baseline_metrics["map@k"]
    print("\nΔ Recall@{k}: {delta:.2%}".format(k=args.top_k, delta=delta_recall))
    print("Δ MAP@{k}:    {delta:.2%}".format(k=args.top_k, delta=delta_map))


if __name__ == "__main__":
    main()
