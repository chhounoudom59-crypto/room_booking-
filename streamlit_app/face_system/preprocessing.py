"""Face preprocessing and alignment for ArcFace embeddings."""

from __future__ import annotations

from typing import Iterable, Tuple

import cv2
import numpy as np

ARC_FACE_SIZE: Tuple[int, int] = (112, 112)

ARC_FACE_TEMPLATE = np.array(
	[
		[38.2946, 51.6963],
		[73.5318, 51.5014],
		[56.0252, 71.7366],
		[41.5493, 92.3655],
		[70.7299, 92.2041],
	],
	dtype=np.float32,
)


def _to_landmarks_array(landmarks: object) -> np.ndarray | None:
	if landmarks is None:
		return None

	if isinstance(landmarks, dict):
		ordered = [
			landmarks.get("left_eye"),
			landmarks.get("right_eye"),
			landmarks.get("nose"),
			landmarks.get("mouth_left"),
			landmarks.get("mouth_right"),
		]
	else:
		ordered = list(landmarks)  # type: ignore[arg-type]

	if len(ordered) != 5 or any(point is None for point in ordered):
		return None

	try:
		pts = np.asarray(ordered, dtype=np.float32)
	except (TypeError, ValueError):
		return None

	if pts.shape != (5, 2):
		return None

	return pts


def _apply_clahe(image_bgr: np.ndarray) -> np.ndarray:
	lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
	l_channel, a_channel, b_channel = cv2.split(lab)
	clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
	l_channel = clahe.apply(l_channel)
	merged = cv2.merge((l_channel, a_channel, b_channel))
	return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


def align_face(
	face_bgr: np.ndarray,
	landmarks: object,
	output_size: Tuple[int, int] = ARC_FACE_SIZE,
) -> np.ndarray:
	"""Align a face using 5-point landmarks; falls back to resize."""

	pts = _to_landmarks_array(landmarks)
	if pts is None:
		return resize_face(face_bgr, output_size)

	target = ARC_FACE_TEMPLATE.copy()
	target[:, 0] *= output_size[0] / ARC_FACE_SIZE[0]
	target[:, 1] *= output_size[1] / ARC_FACE_SIZE[1]

	matrix, _ = cv2.estimateAffinePartial2D(pts, target, method=cv2.LMEDS)
	if matrix is None:
		return resize_face(face_bgr, output_size)

	aligned = cv2.warpAffine(
		face_bgr,
		matrix,
		output_size,
		flags=cv2.INTER_LINEAR,
		borderMode=cv2.BORDER_CONSTANT,
		borderValue=(0, 0, 0),
	)
	return aligned


def resize_face(face_bgr: np.ndarray, output_size: Tuple[int, int]) -> np.ndarray:
	return cv2.resize(face_bgr, output_size, interpolation=cv2.INTER_LINEAR)


def normalize_face(
	face_rgb: np.ndarray,
	mean: float = 127.5,
	std: float = 128.0,
) -> np.ndarray:
	"""Normalize to ArcFace float32 input scale."""

	face_rgb = face_rgb.astype(np.float32)
	return (face_rgb - mean) / std


def preprocess_for_arcface(
	face_bgr: np.ndarray,
	landmarks: object | None = None,
	output_size: Tuple[int, int] = ARC_FACE_SIZE,
	align: bool = True,
	use_clahe: bool = True,
	normalize: bool = True,
) -> np.ndarray:
	"""
	Prepare a detected face for ArcFace embeddings.

	Returns an RGB image (float32 if normalize=True, else uint8).
	"""

	if face_bgr is None or not isinstance(face_bgr, np.ndarray):
		raise ValueError("face_bgr must be a NumPy array.")

	if face_bgr.ndim != 3 or face_bgr.shape[2] != 3:
		raise ValueError("face_bgr must be a BGR color image.")

	if use_clahe:
		face_bgr = _apply_clahe(face_bgr)

	if align and landmarks is not None:
		face_bgr = align_face(face_bgr, landmarks, output_size)
	else:
		face_bgr = resize_face(face_bgr, output_size)

	face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)

	if normalize:
		return normalize_face(face_rgb)

	return face_rgb

