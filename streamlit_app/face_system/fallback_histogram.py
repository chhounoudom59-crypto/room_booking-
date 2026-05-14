"""Lightweight grayscale histogram fallback embeddings."""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np


class HistogramEmbeddingError(RuntimeError):
	"""Raised when histogram embedding extraction fails."""


def _normalize_histogram(hist: np.ndarray, eps: float = 1e-8) -> np.ndarray:
	hist = hist.astype(np.float32).reshape(-1)
	total = hist.sum()
	if total < eps:
		return hist
	return hist / total


def extract_histogram_embedding(
	face_bgr: np.ndarray,
	bins: int = 128,
	resize: Tuple[int, int] | None = (112, 112),
) -> np.ndarray:
	"""
	Compute a normalized grayscale histogram embedding.

	Returns a 1D float32 NumPy array.
	"""

	if face_bgr is None or not isinstance(face_bgr, np.ndarray):
		raise HistogramEmbeddingError("face_bgr must be a NumPy array.")

	if face_bgr.ndim != 3 or face_bgr.shape[2] != 3:
		raise HistogramEmbeddingError("face_bgr must be a BGR color image.")

	if resize is not None:
		face_bgr = cv2.resize(face_bgr, resize, interpolation=cv2.INTER_LINEAR)

	gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
	hist = cv2.calcHist([gray], [0], None, [bins], [0, 256])

	return _normalize_histogram(hist)

