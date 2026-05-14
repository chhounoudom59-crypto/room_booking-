"""Lightweight anti-spoofing heuristics for webcam face verification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import cv2
import numpy as np


class AntiSpoofingError(RuntimeError):
	"""Raised when anti-spoofing analysis fails."""


@dataclass
class AntiSpoofingMetrics:
	laplacian_variance: float
	edge_density: float
	brightness_block_std: float
	texture_std: float
	blur_score: float
	edge_score: float
	brightness_score: float
	texture_score: float


@dataclass
class AntiSpoofingConfig:
	laplacian_variance_min: float = 30.0
	edge_density_min: float = 0.02
	edge_density_max: float = 0.20
	brightness_block_std_min: float = 8.0
	texture_std_min: float = 15.0
	spoof_threshold: float = 0.5


def _laplacian_variance(gray: np.ndarray) -> float:
	laplacian = cv2.Laplacian(gray, cv2.CV_64F)
	return float(laplacian.var())


def _edge_density(gray: np.ndarray) -> float:
	edges = cv2.Canny(gray, 60, 120)
	edge_pixels = float(np.count_nonzero(edges))
	return edge_pixels / float(gray.size)


def _brightness_block_std(gray: np.ndarray, grid: Tuple[int, int] = (4, 4)) -> float:
	height, width = gray.shape[:2]
	block_h = max(1, height // grid[0])
	block_w = max(1, width // grid[1])

	means = []
	for row in range(0, height, block_h):
		for col in range(0, width, block_w):
			block = gray[row : row + block_h, col : col + block_w]
			if block.size == 0:
				continue
			means.append(float(block.mean()))

	if not means:
		return 0.0
	return float(np.std(means))


def _texture_std(gray: np.ndarray) -> float:
	return float(gray.std())


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
	return max(low, min(high, value))


def analyze_spoof(
	face_bgr: np.ndarray,
	config: AntiSpoofingConfig | None = None,
) -> Tuple[bool, float, AntiSpoofingMetrics]:
	"""
	Analyze a face crop and return (is_spoof, confidence, metrics).
	"""

	if face_bgr is None or not isinstance(face_bgr, np.ndarray):
		raise AntiSpoofingError("face_bgr must be a NumPy array.")

	if face_bgr.ndim != 3 or face_bgr.shape[2] != 3:
		raise AntiSpoofingError("face_bgr must be a BGR color image.")

	config = config or AntiSpoofingConfig()
	gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)

	lap_var = _laplacian_variance(gray)
	edge_density = _edge_density(gray)
	brightness_std = _brightness_block_std(gray)
	texture_std = _texture_std(gray)

	blur_score = _clamp((config.laplacian_variance_min - lap_var) / config.laplacian_variance_min)
	if edge_density < config.edge_density_min:
		edge_score = _clamp(
			(config.edge_density_min - edge_density) / config.edge_density_min
		)
	elif edge_density > config.edge_density_max:
		edge_score = _clamp(
			(edge_density - config.edge_density_max) / config.edge_density_max
		)
	else:
		edge_score = 0.0

	brightness_score = _clamp(
		(config.brightness_block_std_min - brightness_std)
		/ config.brightness_block_std_min
	)
	texture_score = _clamp(
		(config.texture_std_min - texture_std) / config.texture_std_min
	)

	confidence = _clamp(
		0.35 * blur_score
		+ 0.25 * edge_score
		+ 0.20 * brightness_score
		+ 0.20 * texture_score
	)

	metrics = AntiSpoofingMetrics(
		laplacian_variance=lap_var,
		edge_density=edge_density,
		brightness_block_std=brightness_std,
		texture_std=texture_std,
		blur_score=blur_score,
		edge_score=edge_score,
		brightness_score=brightness_score,
		texture_score=texture_score,
	)

	return confidence >= config.spoof_threshold, confidence, metrics


def detect_spoof(
	face_bgr: np.ndarray,
	config: AntiSpoofingConfig | None = None,
) -> Tuple[bool, float]:
	"""Return (is_spoof, confidence) for real-time usage."""

	is_spoof, confidence, _ = analyze_spoof(face_bgr, config)
	return is_spoof, confidence

