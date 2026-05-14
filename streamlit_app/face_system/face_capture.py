"""Multi-angle face enrollment utilities for Streamlit workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

from streamlit_app.face_system.detector import detect_primary_face
from streamlit_app.face_system.embedding import ArcFaceEmbedder
from streamlit_app.face_system.preprocessing import preprocess_for_arcface


ANGLES: Tuple[str, ...] = ("front", "left", "right", "upward", "downward")


class EnrollmentError(RuntimeError):
	"""Raised when enrollment fails for a specific angle."""


@dataclass
class AngleResult:
	angle: str
	path: str
	embedding: np.ndarray


@dataclass
class EnrollmentResult:
	user_id: str
	results: List[AngleResult]
	missing: List[str]


def get_user_embedding_dir(base_dir: str | Path, user_id: str) -> Path:
	base = Path(base_dir)
	return base / "embeddings" / str(user_id)


def save_embedding(path: Path, embedding: np.ndarray) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	np.save(str(path), embedding)


def _ensure_angles(frames: Dict[str, np.ndarray], required: Iterable[str]) -> List[str]:
	missing = [angle for angle in required if angle not in frames]
	return missing


def enroll_multi_angle(
	user_id: str,
	frames: Dict[str, np.ndarray],
	model_path: str,
	storage_dir: str | Path = "streamlit_app/data",
	backend: str = "onnx",
) -> EnrollmentResult:
	"""
	Enroll a user with multiple angles from BGR frames.

	Returns an EnrollmentResult with saved embeddings and any missing angles.
	"""

	missing = _ensure_angles(frames, ANGLES)
	results: List[AngleResult] = []
	if missing:
		return EnrollmentResult(user_id=user_id, results=results, missing=missing)

	embedder = ArcFaceEmbedder(model_path=model_path, backend=backend)
	user_dir = get_user_embedding_dir(storage_dir, user_id)

	for angle in ANGLES:
		frame = frames[angle]
		face = detect_primary_face(frame)
		if face is None:
			raise EnrollmentError(f"No face detected for angle '{angle}'.")

		face_rgb = preprocess_for_arcface(
			face["crop"],
			landmarks=face.get("landmarks"),
		)
		embedding = embedder.extract(face_rgb)
		file_path = user_dir / f"{angle}.npy"
		save_embedding(file_path, embedding)
		results.append(
			AngleResult(angle=angle, path=str(file_path), embedding=embedding)
		)

	return EnrollmentResult(user_id=user_id, results=results, missing=[])


def get_angle_instructions() -> Dict[str, str]:
	"""Return per-angle guidance for Streamlit prompts."""

	return {
		"front": "Look straight at the camera.",
		"left": "Turn your head slightly to the left.",
		"right": "Turn your head slightly to the right.",
		"upward": "Tilt your head slightly upward.",
		"downward": "Tilt your head slightly downward.",
	}

