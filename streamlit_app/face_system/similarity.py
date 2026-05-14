"""Cosine similarity utilities for face verification."""

from __future__ import annotations

from typing import Tuple

import numpy as np


class SimilarityError(RuntimeError):
	"""Raised when similarity computation fails."""


def _validate_vector(name: str, vector: np.ndarray) -> np.ndarray:
	if vector is None or not isinstance(vector, np.ndarray):
		raise SimilarityError(f"{name} must be a NumPy array.")

	vector = np.asarray(vector, dtype=np.float32).reshape(-1)
	if vector.size == 0:
		raise SimilarityError(f"{name} is empty.")

	return vector


def cosine_similarity(
	stored_embedding: np.ndarray,
	live_embedding: np.ndarray,
) -> float:
	"""
	Compute cosine similarity between two vectors.
	"""

	stored = _validate_vector("stored_embedding", stored_embedding)
	live = _validate_vector("live_embedding", live_embedding)

	if stored.shape != live.shape:
		raise SimilarityError("Embeddings must have the same shape.")

	stored_norm = np.linalg.norm(stored)
	live_norm = np.linalg.norm(live)
	if stored_norm == 0.0 or live_norm == 0.0:
		raise SimilarityError("Embeddings must be non-zero.")

	similarity = float(np.dot(stored, live) / (stored_norm * live_norm))
	return similarity


def match_embeddings(
	stored_embedding: np.ndarray,
	live_embedding: np.ndarray,
	threshold: float = 0.5,
) -> Tuple[float, bool]:
	"""
	Return (similarity_score, is_match) for cosine similarity.
	"""

	similarity = cosine_similarity(stored_embedding, live_embedding)
	return similarity, similarity >= threshold

