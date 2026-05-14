"""ArcFace embedding extraction utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

import numpy as np


class ArcFaceEmbeddingError(RuntimeError):
	"""Raised when the ArcFace model cannot be loaded or used."""


def _l2_normalize(vector: np.ndarray, eps: float = 1e-10) -> np.ndarray:
	norm = np.linalg.norm(vector)
	if norm < eps:
		return vector
	return vector / norm


def _prepare_input(face_rgb: np.ndarray, layout: str = "NCHW") -> np.ndarray:
	if face_rgb is None or not isinstance(face_rgb, np.ndarray):
		raise ArcFaceEmbeddingError("face_rgb must be a NumPy array.")

	if face_rgb.ndim != 3 or face_rgb.shape[2] != 3:
		raise ArcFaceEmbeddingError("face_rgb must be an RGB image (H, W, 3).")

	if face_rgb.dtype != np.float32:
		face_rgb = face_rgb.astype(np.float32)

	if layout.upper() == "NHWC":
		return np.expand_dims(face_rgb, axis=0)

	# Default to NCHW
	face_chw = np.transpose(face_rgb, (2, 0, 1))
	return np.expand_dims(face_chw, axis=0)


@dataclass
class ArcFaceEmbedder:
	"""ArcFace embedding extractor supporting ONNX Runtime or PyTorch."""

	model_path: str
	backend: str = "onnx"
	providers: Optional[Iterable[str]] = None

	_session: object | None = None
	_input_name: str | None = None
	_input_layout: str | None = None

	def _load_onnx(self) -> None:
		try:
			import onnxruntime as ort
		except Exception as exc:
			raise ArcFaceEmbeddingError(
				"onnxruntime is not available. Install it or switch to PyTorch."
			) from exc

		providers = list(self.providers) if self.providers else None
		if providers is None:
			available = ort.get_available_providers()
			providers = [
				provider
				for provider in ("CUDAExecutionProvider", "CPUExecutionProvider")
				if provider in available
			]

		try:
			session = ort.InferenceSession(self.model_path, providers=providers)
		except Exception as exc:
			raise ArcFaceEmbeddingError(
				f"Failed to load ONNX ArcFace model: {self.model_path}"
			) from exc

		inputs = session.get_inputs()
		if not inputs:
			raise ArcFaceEmbeddingError("ONNX model has no inputs.")

		self._session = session
		self._input_name = inputs[0].name
		input_shape = inputs[0].shape
		if isinstance(input_shape, (list, tuple)) and len(input_shape) == 4:
			# Infer layout: [N, H, W, C] or [N, C, H, W]
			if input_shape[1] == 3 and input_shape[2] in (112, None):
				self._input_layout = "NCHW"
			elif input_shape[3] == 3 and input_shape[1] in (112, None):
				self._input_layout = "NHWC"

	def _load_torch(self) -> None:
		try:
			import torch
		except Exception as exc:
			raise ArcFaceEmbeddingError(
				"PyTorch is not available. Install it or switch to ONNX."
			) from exc

		try:
			model = torch.jit.load(self.model_path, map_location="cpu")
			model.eval()
		except Exception as exc:
			raise ArcFaceEmbeddingError(
				f"Failed to load Torch ArcFace model: {self.model_path}"
			) from exc

		self._session = model

	def _ensure_loaded(self) -> None:
		if self._session is not None:
			return

		backend = self.backend.lower()
		if backend == "onnx":
			self._load_onnx()
		elif backend == "torch":
			self._load_torch()
		else:
			raise ArcFaceEmbeddingError(
				"Unsupported backend. Use 'onnx' or 'torch'."
			)

	def extract(self, face_rgb: np.ndarray) -> np.ndarray:
		"""Generate a 512D L2-normalized embedding."""

		self._ensure_loaded()
		layout = self._input_layout or "NCHW"
		input_blob = _prepare_input(face_rgb, layout=layout)

		if self.backend.lower() == "onnx":
			session = self._session
			if session is None or self._input_name is None:
				raise ArcFaceEmbeddingError("ONNX session is not initialized.")
			outputs = session.run(None, {self._input_name: input_blob})
			if not outputs:
				raise ArcFaceEmbeddingError("ONNX model returned no outputs.")
			embedding = outputs[0][0]
		else:
			import torch

			model = self._session
			if model is None:
				raise ArcFaceEmbeddingError("Torch model is not initialized.")
			tensor = torch.from_numpy(input_blob)
			with torch.no_grad():
				output = model(tensor)
				if isinstance(output, (tuple, list)):
					output = output[0]
				embedding = output.cpu().numpy()[0]

		embedding = np.asarray(embedding, dtype=np.float32)
		return _l2_normalize(embedding)


def extract_arcface_embedding(
	face_rgb: np.ndarray,
	model_path: str,
	backend: str = "onnx",
	providers: Optional[Iterable[str]] = None,
) -> np.ndarray:
	"""
	Convenience wrapper for single-call embedding extraction.
	"""

	embedder = ArcFaceEmbedder(
		model_path=model_path,
		backend=backend,
		providers=providers,
	)
	return embedder.extract(face_rgb)

