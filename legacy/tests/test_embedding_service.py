"""Unit tests for embedding service."""
from __future__ import annotations

import numpy as np
from backend.engine.embedding_service import EmbeddingService


def test_embedding_computation_and_similarity() -> None:
    """Test generating embeddings and calculating cosine similarity."""
    svc = EmbeddingService()
    vec1 = svc.get_embedding("TMT steel reinforcement rebar")
    vec2 = svc.get_embedding("Deformed steel bars for concrete")
    vec3 = svc.get_embedding("Drinking water treatment chemicals")

    assert isinstance(vec1, np.ndarray)
    assert len(vec1) > 0

    sim_related = svc.compute_similarity(vec1, vec2)
    sim_unrelated = svc.compute_similarity(vec1, vec3)

    assert sim_related > sim_unrelated
    assert sim_related > 0.15
