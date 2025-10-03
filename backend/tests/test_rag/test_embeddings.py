"""Tests for deterministic embedding helper."""
import math

import pytest

from app.rag.embeddings import EMBEDDING_DIM, generate_embedding


def test_embedding_deterministic():
    vec1 = generate_embedding("Almuten")
    vec2 = generate_embedding("Almuten")
    assert vec1 == vec2
    assert len(vec1) == EMBEDDING_DIM

    norm = math.sqrt(sum(value * value for value in vec1))
    assert norm == pytest.approx(1.0, rel=1e-6)


def test_embedding_empty_text():
    vec = generate_embedding("")
    assert len(vec) == EMBEDDING_DIM
    assert all(value == 0.0 for value in vec)
