"""Verification pipeline using RetinaFace + ArcFace + fallback histogram."""

from __future__ import annotations

from typing import Dict, List, Tuple
from pathlib import Path
import logging

import cv2
import numpy as np
from PIL import Image

from face_system.anti_spoofing import detect_spoof
from face_system.detector import detect_primary_face
from face_system.embedding import ArcFaceEmbedder, ArcFaceEmbeddingError
from face_system.fallback_histogram import extract_histogram_embedding
from face_system.preprocessing import preprocess_for_arcface
from face_system.similarity import cosine_similarity

logger = logging.getLogger(__name__)

MODEL_PATH = str((Path(__file__).resolve().parent / "models" / "arcface" / "arc.onnx").resolve())

DEFAULT_ARCFACE_THRESHOLD = 0.35
DEFAULT_HISTOGRAM_THRESHOLD = 0.9


def pil_to_bgr(image_input) -> np.ndarray:
    """Convert PIL image or UploadedFile into OpenCV BGR format."""
    if hasattr(image_input, "read"):
        pil_image = Image.open(image_input)
    else:
        pil_image = image_input

    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")

    image_rgb = np.array(pil_image)
    return cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)


def _embedding_type(embedding: np.ndarray) -> str:
    size = np.asarray(embedding).reshape(-1).size
    if size == 512:
        return "arcface"
    if size == 128:
        return "histogram"
    return "unknown"


def _compute_arcface_embedding(
    face_bgr: np.ndarray,
    landmarks: object | None,
    model_path: str,
) -> np.ndarray:
    face_rgb = preprocess_for_arcface(face_bgr, landmarks=landmarks)
    embedder = ArcFaceEmbedder(model_path=model_path, backend="onnx")
    return embedder.extract(face_rgb)


def verify_face_image(
    image_bgr: np.ndarray,
    stored_embeddings: List[Dict],
    threshold: float = DEFAULT_ARCFACE_THRESHOLD,
    histogram_threshold: float = DEFAULT_HISTOGRAM_THRESHOLD,
    model_path: str = MODEL_PATH,
) -> Tuple[bool, Dict]:
    """
    Verify a live image against stored embeddings.

    Pipeline:
    - anti-spoofing
    - RetinaFace detection
    - ArcFace embedding + cosine similarity
    - fallback to histogram if ArcFace fails
    """

    result = {
        "verified": False,
        "best_similarity": 0.0,
        "threshold": threshold,
        "histogram_threshold": histogram_threshold,
        "method": None,
        "best_angle": None,
        "spoof_detected": False,
        "spoof_confidence": 0.0,
        "errors": None,
    }

    is_spoof, spoof_confidence = detect_spoof(image_bgr)
    result["spoof_detected"] = is_spoof
    result["spoof_confidence"] = float(spoof_confidence)
    if is_spoof:
        result["errors"] = "Spoofing detected"
        return False, result

    face = detect_primary_face(image_bgr)
    if not face:
        result["errors"] = "No face detected"
        return False, result

    best_sim = -1.0
    best_angle = None
    best_method = None

    arcface_embedding = None
    histogram_embedding = None

    try:
        arcface_embedding = _compute_arcface_embedding(
            face["crop"],
            face.get("landmarks"),
            model_path,
        )
    except ArcFaceEmbeddingError as exc:
        logger.warning("ArcFace embedding failed: %s", exc)
        arcface_embedding = None

    for item in stored_embeddings:
        emb = item.get("embedding")
        if emb is None:
            continue

        emb_type = _embedding_type(emb)

        if emb_type == "arcface":
            if arcface_embedding is None:
                continue
            sim = cosine_similarity(arcface_embedding, emb)
            method = "arcface"
            method_threshold = threshold
        elif emb_type == "histogram":
            if histogram_embedding is None:
                histogram_embedding = extract_histogram_embedding(face["crop"])
            sim = cosine_similarity(histogram_embedding, emb)
            method = "histogram"
            method_threshold = histogram_threshold
        else:
            continue

        if sim > best_sim:
            best_sim = sim
            best_angle = item.get("angle")
            best_method = method
            best_threshold = method_threshold

    result["best_similarity"] = float(best_sim)
    result["best_angle"] = best_angle
    result["method"] = best_method
    if best_method == "histogram":
        result["threshold"] = best_threshold

    if best_sim < 0:
        result["errors"] = "No valid embeddings to compare"
        return False, result

    result["verified"] = best_sim >= best_threshold
    return result["verified"], result


def verify_face_from_pil(
    image_pil: Image.Image,
    stored_embeddings: List[Dict],
    threshold: float = DEFAULT_ARCFACE_THRESHOLD,
    histogram_threshold: float = DEFAULT_HISTOGRAM_THRESHOLD,
    model_path: str = MODEL_PATH,
) -> Tuple[bool, Dict]:
    """Helper for Streamlit camera input (PIL)."""

    image_bgr = pil_to_bgr(image_pil)
    return verify_face_image(
        image_bgr,
        stored_embeddings,
        threshold=threshold,
        histogram_threshold=histogram_threshold,
        model_path=model_path,
    )
