"""Inference for the published MiniLM + logistic-regression artifact (Part A).

The exported model is a frozen ``sentence-transformers/all-MiniLM-L6-v2``
encoder followed by a NumPy implementation of multinomial logistic regression.
No scikit-learn, torch, or sentence-transformers import happens at module import
time: they are loaded only when :meth:`EncoderIntentClassifier.from_pretrained`
is called, so the default rule-based intent module keeps its light dependency
footprint.

The artifact directory is ``model_artifacts`` next to this module. Loading
verifies the SHA-256 of every parameter/config file and checks that the 77
labels and route mapping agree with ``banking77.py``.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from banking_agent.schemas.state import UnderstandingResult

from .banking77 import (
    BANKING77_LABELS,
    DEFAULT_OPERATIONAL_INTENT,
    operational_intent_for,
)
from .mock import detect_risk, extract_entities
from .taxonomy import OPERATIONAL_INTENTS

DEFAULT_ARTIFACT_DIR = Path(__file__).with_name("model_artifacts")
_REQUIRED_ARTIFACTS = (
    "logreg_params.npz",
    "label_order.json",
    "route_mapping.json",
    "preprocessing.json",
)


class EncoderArtifactError(RuntimeError):
    """Raised when the published artifact is missing, corrupt, or inconsistent."""


def _artifact_bytes(path: Path) -> bytes:
    """Return canonical artifact bytes, independent of checkout line endings."""
    data = path.read_bytes()
    if path.suffix in {".json", ".txt", ".md"}:
        data = data.replace(b"\r\n", b"\n")
    return data


def _sha256_artifact(path: Path) -> str:
    return hashlib.sha256(_artifact_bytes(path)).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EncoderArtifactError(f"cannot read {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise EncoderArtifactError(f"{path} must contain a JSON object")
    return payload


def _verify_checksums(artifact_dir: Path, manifest: dict[str, Any]) -> None:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise EncoderArtifactError("manifest is missing artifact checksums")
    for name in _REQUIRED_ARTIFACTS:
        expected = artifacts.get(name)
        path = artifact_dir / name
        if not isinstance(expected, dict):
            raise EncoderArtifactError(f"manifest has no checksum for {name}")
        if not path.is_file():
            raise EncoderArtifactError(f"missing artifact: {path}")
        actual_size = len(_artifact_bytes(path))
        if actual_size != expected.get("bytes"):
            raise EncoderArtifactError(
                f"{name} byte size mismatch: {actual_size} != {expected.get('bytes')}"
            )
        actual_hash = _sha256_artifact(path)
        if actual_hash != expected.get("sha256"):
            raise EncoderArtifactError(f"{name} SHA-256 mismatch")


def _validate_label_and_route_files(
    artifact_dir: Path,
) -> tuple[list[str], dict[str, str], str]:
    labels_payload = _load_json(artifact_dir / "label_order.json")
    labels = labels_payload.get("labels")
    if labels != list(BANKING77_LABELS):
        raise EncoderArtifactError(
            "label_order.json does not match BANKING77 published order"
        )
    if labels_payload.get("count") != len(BANKING77_LABELS):
        raise EncoderArtifactError("label_order.json count is not 77")

    routes_payload = _load_json(artifact_dir / "route_mapping.json")
    label_to_route = routes_payload.get("label_to_route")
    default_route = routes_payload.get("default_route")
    if not isinstance(label_to_route, dict) or not isinstance(default_route, str):
        raise EncoderArtifactError("route_mapping.json has an invalid shape")
    expected_routes = {
        label: operational_intent_for(label) for label in BANKING77_LABELS
    }
    if label_to_route != expected_routes:
        raise EncoderArtifactError(
            "route_mapping.json does not match the canonical route mapping"
        )
    if default_route != DEFAULT_OPERATIONAL_INTENT:
        raise EncoderArtifactError("route_mapping.json default route is wrong")
    return labels, dict(label_to_route), default_route


def _as_text_list(texts: Sequence[str]) -> list[str]:
    values = list(texts)
    if any(not isinstance(value, str) for value in values):
        raise TypeError("texts must contain only strings")
    return values


class EncoderIntentClassifier:
    """Frozen-encoder intent classifier behind the Part A result contract.

    The fine-grained BANKING77 label is retained for traces, while the emitted
    intent is the operational route. Confidence is the probability mass of the
    predicted route, which is more stable than a 77-way arg-max probability and
    matches :class:`TrainedIntentClassifier`.
    """

    def __init__(
        self,
        *,
        encoder: object,
        coefficients: Any,
        intercepts: Any,
        classes: Any,
        label_order: Sequence[str],
        label_to_route: dict[str, str],
        default_route: str,
        preprocessing: dict[str, Any],
        manifest: dict[str, Any],
    ) -> None:
        self._encoder = encoder
        self._coefficients = coefficients
        self._intercepts = intercepts
        self._classes = classes
        self._class_names = [str(label) for label in classes]
        self._label_order = tuple(label_order)
        self._label_to_route = dict(label_to_route)
        self._default_route = default_route
        self.manifest = manifest
        self._preprocessing = preprocessing
        self._batch_size = int(preprocessing["embedding"]["batch_size"])
        self._embedding_dimension = int(
            preprocessing["embedding"]["embedding_dimension"]
        )
        self._route_order = sorted(
            set(OPERATIONAL_INTENTS) | set(self._label_to_route.values())
        )
        self._route_indices = self._build_route_indices()

    def _build_route_indices(self) -> dict[str, Any]:
        np = _numpy()
        indices: dict[str, Any] = {}
        for route in self._route_order:
            positions = [
                index
                for index, label in enumerate(self._class_names)
                if self._label_to_route[label] == route
            ]
            indices[route] = np.asarray(positions, dtype=np.int64)
        return indices

    @classmethod
    def from_pretrained(
        cls,
        artifact_dir: str | Path | None = None,
        *,
        encoder: object | None = None,
        device: str | None = None,
        verify_checksums: bool = True,
    ) -> "EncoderIntentClassifier":
        """Load and validate the exported artifact.

        ``encoder`` is injectable so unit and integration tests can exercise the
        wrapper without downloading model weights or importing torch.
        """
        directory = (
            Path(artifact_dir) if artifact_dir is not None else DEFAULT_ARTIFACT_DIR
        )
        manifest = _load_json(directory / "manifest.json")
        if verify_checksums:
            _verify_checksums(directory, manifest)

        labels, label_to_route, default_route = _validate_label_and_route_files(
            directory
        )
        preprocessing = _load_json(directory / "preprocessing.json")
        text_config = preprocessing.get("text", {})
        embedding_config = preprocessing.get("embedding", {})
        if text_config.get("normalization") != "none":
            raise EncoderArtifactError("unsupported text normalization")
        if text_config.get("steps") != []:
            raise EncoderArtifactError("unsupported preprocessing steps")
        if embedding_config.get("normalize_embeddings") is not True:
            raise EncoderArtifactError("artifact requires L2-normalized embeddings")

        np = _numpy()
        params_path = directory / "logreg_params.npz"
        try:
            with np.load(params_path, allow_pickle=False) as params:
                coefficients = np.asarray(params["coef"], dtype=np.float64)
                intercepts = np.asarray(params["intercept"], dtype=np.float64)
                classes = np.asarray(params["classes"], dtype=str)
        except (OSError, KeyError, ValueError) as exc:
            raise EncoderArtifactError(f"cannot read {params_path}: {exc}") from exc

        expected_dimension = int(embedding_config.get("embedding_dimension", 0))
        if expected_dimension <= 0:
            raise EncoderArtifactError("preprocessing.json has no embedding dimension")
        if coefficients.shape != (77, expected_dimension):
            raise EncoderArtifactError(
                f"coefficient shape is {coefficients.shape}, expected "
                f"(77, {expected_dimension})"
            )
        if intercepts.shape != (77,):
            raise EncoderArtifactError(
                f"intercept shape is {intercepts.shape}, expected (77,)"
            )
        if classes.shape != (77,) or len(set(classes.tolist())) != 77:
            raise EncoderArtifactError("classifier classes are not 77 unique labels")
        if set(classes.tolist()) != set(labels):
            raise EncoderArtifactError("classifier classes do not match label_order")
        if not np.isfinite(coefficients).all() or not np.isfinite(intercepts).all():
            raise EncoderArtifactError("classifier parameters contain non-finite values")

        if encoder is None:
            from sentence_transformers import SentenceTransformer

            encoder_config = manifest.get("encoder", {})
            model_id = encoder_config.get("model_id")
            revision = encoder_config.get("revision")
            if not isinstance(model_id, str) or not isinstance(revision, str):
                raise EncoderArtifactError("manifest encoder id/revision is missing")
            kwargs: dict[str, Any] = {"revision": revision}
            if device is not None:
                kwargs["device"] = device
            encoder = SentenceTransformer(model_id, **kwargs)

        return cls(
            encoder=encoder,
            coefficients=coefficients,
            intercepts=intercepts,
            classes=classes,
            label_order=labels,
            label_to_route=label_to_route,
            default_route=default_route,
            preprocessing=preprocessing,
            manifest=manifest,
        )

    def _embed(self, texts: list[str]) -> Any:
        np = _numpy()
        if not texts:
            return np.empty((0, self._embedding_dimension), dtype=np.float32)
        values = self._encoder.encode(
            texts,
            batch_size=self._batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        embeddings = np.asarray(values, dtype=np.float32)
        if embeddings.ndim != 2 or embeddings.shape[1] != self._embedding_dimension:
            raise EncoderArtifactError(
                f"encoder returned shape {embeddings.shape}, expected "
                f"(n, {self._embedding_dimension})"
            )
        return embeddings

    def _decide(self, texts: Sequence[str]) -> tuple[list[str], Any]:
        np = _numpy()
        values = _as_text_list(texts)
        embeddings = self._embed(values)
        logits = embeddings.astype(np.float64) @ self._coefficients.T + self._intercepts
        if len(values):
            logits -= logits.max(axis=1, keepdims=True)
            probabilities = np.exp(logits)
            probabilities /= probabilities.sum(axis=1, keepdims=True)
            labels = [self._class_names[index] for index in probabilities.argmax(axis=1)]
        else:
            probabilities = np.empty((0, len(self._class_names)), dtype=np.float64)
            labels = []
        return labels, probabilities

    @property
    def classes(self) -> tuple[str, ...]:
        """Classifier class order, which is the column order of ``predict_proba``."""
        return tuple(self._class_names)

    @property
    def label_order(self) -> tuple[str, ...]:
        """The 77 BANKING77 labels in published label-id order."""
        return self._label_order

    @property
    def label_to_route(self) -> dict[str, str]:
        return dict(self._label_to_route)

    def predict_labels(self, texts: Sequence[str]) -> list[str]:
        """Return fine-grained BANKING77 labels for traces and error analysis."""
        labels, _ = self._decide(texts)
        return labels

    def predict_proba(self, texts: Sequence[str]) -> list[dict[str, float]]:
        """Return softmax class probabilities in ``classes`` order."""
        _, probabilities = self._decide(texts)
        return [
            {
                label: float(value)
                for label, value in zip(self._class_names, row.tolist())
            }
            for row in probabilities
        ]

    def predict_route_proba(self, texts: Sequence[str]) -> list[dict[str, float]]:
        """Aggregate class probabilities into the operational route space."""
        _, probabilities = self._decide(texts)
        rows: list[dict[str, float]] = []
        for row in probabilities:
            rows.append(
                {
                    route: float(row[self._route_indices[route]].sum())
                    for route in self._route_order
                }
            )
        return rows

    def classify(self, text: str) -> UnderstandingResult:
        """Classify one turn and return the shared Part A result shape."""
        labels, probabilities = self._decide([text])
        label = labels[0]
        route = self._label_to_route.get(label, self._default_route)
        confidence = float(probabilities[0, self._route_indices[route]].sum())
        confidence = min(max(confidence, 0.0), 1.0)
        return UnderstandingResult(
            intent=route,
            confidence=confidence,
            risk_level=detect_risk(text, route),
            entities=extract_entities(text),
        )

    def classify_many(self, texts: Sequence[str]) -> list[UnderstandingResult]:
        """Batch variant of :meth:`classify` with one encoder call."""
        values = _as_text_list(texts)
        labels, probabilities = self._decide(values)
        results = []
        for text, label, row in zip(values, labels, probabilities):
            route = self._label_to_route.get(label, self._default_route)
            confidence = float(row[self._route_indices[route]].sum())
            confidence = min(max(confidence, 0.0), 1.0)
            results.append(
                UnderstandingResult(
                    intent=route,
                    confidence=confidence,
                    risk_level=detect_risk(text, route),
                    entities=extract_entities(text),
                )
            )
        return results


def _numpy():
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise EncoderArtifactError(
            "encoder inference requires numpy; install "
            "model_artifacts/requirements-inference.txt"
        ) from exc
    return np


__all__ = [
    "DEFAULT_ARTIFACT_DIR",
    "EncoderArtifactError",
    "EncoderIntentClassifier",
]
