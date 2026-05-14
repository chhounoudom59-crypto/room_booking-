"""Streamlit admin face enrollment page."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np
import streamlit as st
from PIL import Image

from database import get_user_by_email, verify_user_credentials
from face_system.anti_spoofing import detect_spoof
from face_system.detector import detect_primary_face
from face_system.embedding import ArcFaceEmbedder
from face_system.preprocessing import preprocess_for_arcface


ANGLE_ORDER: Tuple[str, ...] = ("front", "left", "right", "upward", "downward")
APP_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = str(APP_ROOT / "models" / "arcface" / "arc.onnx")
EMBEDDINGS_ROOT = APP_ROOT / "embeddings" / "admin_embeddings"


def _pil_to_bgr(image_input) -> np.ndarray:
	if hasattr(image_input, "read"):
		pil_image = Image.open(image_input)
	else:
		pil_image = image_input

	if pil_image.mode != "RGB":
		pil_image = pil_image.convert("RGB")

	image_rgb = np.array(pil_image)
	return cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)


def _ensure_admin_user(email: str, password: str) -> dict | None:
	if not verify_user_credentials(email, password):
		return None

	user_info = get_user_by_email(email)
	if not user_info:
		return None

	if not (user_info.get("is_staff") or user_info.get("is_superuser")):
		return None

	return user_info


def _get_admin_dir(admin_id: int) -> Path:
	return EMBEDDINGS_ROOT / f"admin_{admin_id}"


def _admin_already_enrolled(admin_id: int) -> bool:
	admin_dir = _get_admin_dir(admin_id)
	return any(admin_dir.glob("*.npy"))


def _detect_and_embed(
	image_bgr: np.ndarray,
	embedder: ArcFaceEmbedder,
) -> Tuple[np.ndarray | None, str | None]:
	is_spoof, spoof_confidence = detect_spoof(image_bgr)
	if is_spoof:
		return None, "Spoofing detected"

	face = detect_primary_face(image_bgr)
	if face is None:
		return None, "No face detected"

	face_rgb = preprocess_for_arcface(face["crop"], landmarks=face.get("landmarks"))
	embedding = embedder.extract(face_rgb)
	return embedding, None


def _save_embedding(admin_id: int, angle: str, embedding: np.ndarray) -> Path:
	admin_dir = _get_admin_dir(admin_id)
	admin_dir.mkdir(parents=True, exist_ok=True)
	file_path = admin_dir / f"{angle}.npy"
	np.save(str(file_path), embedding)
	return file_path


def _render_authentication() -> dict | None:
	st.subheader("Admin authentication")
	email = st.text_input("Email")
	password = st.text_input("Password", type="password")
	submit = st.button("Verify")

	if not submit:
		return None

	if not email or not password:
		st.error("Email and password are required.")
		return None

	user_info = _ensure_admin_user(email, password)
	if not user_info:
		st.error("Authentication failed or user is not an admin.")
		return None

	st.session_state.enroll_admin = user_info
	return user_info


def _render_capture_ui() -> Dict[str, Image.Image | None]:
	st.subheader("Capture angles")
	st.caption("Capture each angle clearly before enrollment.")

	images: Dict[str, Image.Image | None] = {}
	for angle in ANGLE_ORDER:
		label = angle.capitalize()
		images[angle] = st.camera_input(f"Capture {label}", key=f"enroll_{angle}")

	return images


def _render_progress(status: Dict[str, str]) -> None:
	st.subheader("Enrollment progress")
	for angle in ANGLE_ORDER:
		state = status.get(angle, "Pending")
		st.write(f"{angle.capitalize()}: {state}")


def main() -> None:
	st.set_page_config(page_title="Face enrollment", layout="centered")
	st.title("Face enrollment")

	user_info = st.session_state.get("enroll_admin")
	if not user_info:
		user_info = _render_authentication()
		if not user_info:
			return

	admin_id = int(user_info["id"])
	st.write(f"Admin ID: {admin_id}")

	already_enrolled = _admin_already_enrolled(admin_id)
	allow_overwrite = st.checkbox("Allow re-enrollment (overwrite existing)")

	if already_enrolled and not allow_overwrite:
		st.warning("Enrollment already exists for this admin. Enable re-enrollment to continue.")
		return

	images = _render_capture_ui()

	if st.button("Enroll", type="primary"):
		embedder = ArcFaceEmbedder(model_path=MODEL_PATH, backend="onnx")
		status: Dict[str, str] = {}
		progress = st.progress(0)
		step_total = len(ANGLE_ORDER)

		for idx, angle in enumerate(ANGLE_ORDER, start=1):
			image = images.get(angle)
			if image is None:
				status[angle] = "Missing capture"
				progress.progress(idx / step_total)
				continue

			image_bgr = _pil_to_bgr(image)
			embedding, error = _detect_and_embed(image_bgr, embedder)
			if error:
				status[angle] = error
				progress.progress(idx / step_total)
				continue

			_save_embedding(admin_id, angle, embedding)
			status[angle] = "Saved"
			progress.progress(idx / step_total)

		_render_progress(status)

		if any(value == "Saved" for value in status.values()):
			st.success("Enrollment completed for available angles.")
		else:
			st.error("Enrollment failed. No embeddings were saved.")


if __name__ == "__main__":
	main()

