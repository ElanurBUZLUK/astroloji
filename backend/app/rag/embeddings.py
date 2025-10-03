"""Lightweight deterministic embedding utilities used for local development."""
from __future__ import annotations

import hashlib
import math
import random
from typing import Iterable, List

EMBEDDING_DIM = 384


def _tokenize(text: str) -> Iterable[str]:
    for token in text.lower().split():
        cleaned = "".join(ch for ch in token if ch.isalnum())
        if cleaned:
            yield cleaned


def generate_embedding(text: str) -> List[float]:
    """Return a deterministic pseudo-embedding vector for given text.

    This avoids external API calls during local development while still
    producing consistent vectors for Qdrant similarity search.
    """
    vector = [0.0] * EMBEDDING_DIM
    tokens = list(_tokenize(text))
    if not tokens:
        return vector

    for token in tokens:
        seed = int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest()[:8], "big")
        rng = random.Random(seed)
        for idx in range(EMBEDDING_DIM):
            vector[idx] += rng.uniform(-1.0, 1.0)

    # Normalize vector length to unit
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]
