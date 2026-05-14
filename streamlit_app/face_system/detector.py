"""RetinaFace-based face detection utilities for real-time webcam use."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import cv2
import numpy as np

try:
	from retinaface import RetinaFace
except Exception as exc:  # pragma: no cover - surfaced at runtime for missing dep
	RetinaFace = None  # type: ignore
	_RETINAFACE_IMPORT_ERROR = exc
else:
	_RETINAFACE_IMPORT_ERROR = None


class RetinaFaceDetectorError(RuntimeError):
	"""Raised when RetinaFace is unavailable or detection fails."""


def _ensure_retinaface_available() -> None:
	if RetinaFace is None:
		raise RetinaFaceDetectorError(
			"RetinaFace is not available. Install the 'retinaface' package."
		) from _RETINAFACE_IMPORT_ERROR


def _sanitize_bbox(
	bbox: Tuple[int, int, int, int],
	width: int,
	height: int,
) -> Tuple[int, int, int, int]:
	x1, y1, x2, y2 = bbox
	x1 = max(0, min(x1, width - 1))
	y1 = max(0, min(y1, height - 1))
	x2 = max(0, min(x2, width - 1))
	y2 = max(0, min(y2, height - 1))
	if x2 <= x1 or y2 <= y1:
		return 0, 0, 0, 0
	return x1, y1, x2, y2


def _maybe_resize_for_speed(
	image_bgr: np.ndarray,
	max_side: int,
) -> Tuple[np.ndarray, float]:
	height, width = image_bgr.shape[:2]
	if max(height, width) <= max_side:
		return image_bgr, 1.0
	scale = max_side / float(max(height, width))
	resized = cv2.resize(image_bgr, (int(width * scale), int(height * scale)))
	return resized, 1.0 / scale


def _extract_faces(
	image_bgr: np.ndarray,
	detections: Dict[str, Any],
	confidence_threshold: float,
	scale_back: float,
) -> List[Dict[str, Any]]:
	height, width = image_bgr.shape[:2]
	results: List[Dict[str, Any]] = []

	for face_id, face_data in detections.items():
		score = float(face_data.get("score", 0.0))
		if score < confidence_threshold:
			continue

		bbox = face_data.get("facial_area")
		if not bbox or len(bbox) != 4:
			continue

		landmarks = face_data.get("landmarks")

		x1, y1, x2, y2 = bbox
		if scale_back != 1.0:
			x1 = int(x1 * scale_back)
			y1 = int(y1 * scale_back)
			x2 = int(x2 * scale_back)
			y2 = int(y2 * scale_back)

		x1, y1, x2, y2 = _sanitize_bbox((x1, y1, x2, y2), width, height)
		if x2 == 0 and y2 == 0:
			continue

		if isinstance(landmarks, dict) and scale_back != 1.0:
			for key, value in landmarks.items():
				if value is None:
					continue
				landmarks[key] = (
					int(value[0] * scale_back),
					int(value[1] * scale_back),
				)

		face_crop = image_bgr[y1:y2, x1:x2].copy()
		results.append(
			{
				"id": str(face_id),
				"bbox": (x1, y1, x2, y2),
				"confidence": score,
				"crop": face_crop,
				"landmarks": landmarks,
			}
		)

	results.sort(key=lambda item: item["confidence"], reverse=True)
	return results


def detect_faces(
	image_bgr: np.ndarray,
	confidence_threshold: float = 0.9,
	max_faces: int | None = None,
	max_side: int = 960,
) -> List[Dict[str, Any]]:
	"""
	Detect faces in a BGR image using RetinaFace.

	Returns a list of dicts with keys: bbox, confidence, crop.
	Raises RetinaFaceDetectorError for invalid input or missing model.
	"""

	_ensure_retinaface_available()

	if image_bgr is None or not isinstance(image_bgr, np.ndarray):
		raise RetinaFaceDetectorError("Input image must be a NumPy array.")

	if image_bgr.ndim != 3 or image_bgr.shape[2] != 3:
		raise RetinaFaceDetectorError("Input image must be a BGR color image.")

	resized, scale_back = _maybe_resize_for_speed(image_bgr, max_side)

	detections = RetinaFace.detect_faces(resized)
	if not detections:
		return []

	faces = _extract_faces(image_bgr, detections, confidence_threshold, scale_back)

	if max_faces is not None and max_faces > 0:
		return faces[:max_faces]

	return faces


def detect_primary_face(
	image_bgr: np.ndarray,
	confidence_threshold: float = 0.9,
	max_side: int = 960,
) -> Dict[str, Any] | None:
	"""Return the highest-confidence face or None if no face is found."""

	faces = detect_faces(
		image_bgr,
		confidence_threshold=confidence_threshold,
		max_faces=1,
		max_side=max_side,
	)
	return faces[0] if faces else None

