"""Tests for the published MiniLM + logistic-regression artifact (Part A)."""

import hashlib
import json
import unittest
from pathlib import Path

from banking_agent.modules.intent import (
    EncoderArtifactError,
    EncoderIntentClassifier,
)
from banking_agent.modules.intent.banking77 import (
    BANKING77_LABELS,
    DEFAULT_OPERATIONAL_INTENT,
    operational_intent_for,
)
from banking_agent.modules.intent.taxonomy import OPERATIONAL_INTENTS
from banking_agent.schemas.state import UnderstandingResult

try:
    import numpy as np
except ImportError:  # pragma: no cover - CI installs only the base package
    np = None

ARTIFACT_DIR = (
    Path(__file__).parents[2]
    / "src"
    / "banking_agent"
    / "modules"
    / "intent"
    / "model_artifacts"
)


def _read_json(name: str) -> dict:
    return json.loads((ARTIFACT_DIR / name).read_text(encoding="utf-8"))


def _artifact_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    if path.suffix in {".json", ".txt", ".md"}:
        data = data.replace(b"\r\n", b"\n")
    return data


def _artifact_hash(path: Path) -> str:
    return hashlib.sha256(_artifact_bytes(path)).hexdigest()


class EncoderArtifactMetadataTests(unittest.TestCase):
    def test_manifest_pins_the_0_9307_model_combination(self) -> None:
        manifest = _read_json("manifest.json")
        self.assertEqual(
            manifest["encoder"]["model_id"],
            "sentence-transformers/all-MiniLM-L6-v2",
        )
        self.assertEqual(
            manifest["encoder"]["revision"],
            "1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
        )
        self.assertEqual(manifest["classifier"]["params"]["C"], 10.0)
        self.assertEqual(
            manifest["classifier"]["params"]["class_weight"], "balanced"
        )
        self.assertEqual(round(manifest["metrics"]["test_macro_f1"], 4), 0.9307)
        self.assertEqual(manifest["verification"]["numpy_sklearn_prediction_mismatches"], 0)
        self.assertTrue(manifest["verification"]["artifact_checksums_required_at_load"])

    def test_artifact_checksums_cover_every_inference_file(self) -> None:
        manifest = _read_json("manifest.json")
        expected_names = {
            "logreg_params.npz",
            "label_order.json",
            "route_mapping.json",
            "preprocessing.json",
        }
        self.assertEqual(set(manifest["artifacts"]), expected_names)
        for name, info in manifest["artifacts"].items():
            path = ARTIFACT_DIR / name
            self.assertEqual(len(_artifact_bytes(path)), info["bytes"])
            self.assertEqual(_artifact_hash(path), info["sha256"])

    def test_label_order_is_the_complete_published_space(self) -> None:
        payload = _read_json("label_order.json")
        self.assertEqual(payload["count"], 77)
        self.assertEqual(payload["labels"], list(BANKING77_LABELS))
        self.assertEqual(len(set(payload["labels"])), 77)

    def test_route_mapping_covers_all_labels_and_routes(self) -> None:
        payload = _read_json("route_mapping.json")
        self.assertEqual(payload["default_route"], DEFAULT_OPERATIONAL_INTENT)
        self.assertEqual(len(payload["label_to_route"]), 77)
        self.assertEqual(
            payload["label_to_route"],
            {label: operational_intent_for(label) for label in BANKING77_LABELS},
        )
        self.assertEqual(set(payload["routes"]), set(OPERATIONAL_INTENTS))
        self.assertEqual(payload["explicit_mappings"], 19)
        self.assertEqual(payload["default_mappings"], 58)

    def test_preprocessing_is_raw_text_plus_normalized_embeddings(self) -> None:
        payload = _read_json("preprocessing.json")
        self.assertEqual(payload["text"]["normalization"], "none")
        self.assertFalse(payload["text"]["lowercase"])
        self.assertEqual(payload["text"]["steps"], [])
        self.assertTrue(payload["embedding"]["normalize_embeddings"])
        self.assertEqual(payload["embedding"]["batch_size"], 64)
        self.assertEqual(payload["embedding"]["embedding_dimension"], 384)


class _FakeEncoder:
    """Small deterministic encoder so tests need no model download or torch."""

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def encode(self, texts, **kwargs):
        vectors = np.zeros((len(texts), self.dimension), dtype=np.float32)
        for row, text in enumerate(texts):
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            raw = (digest * ((self.dimension * 4 // len(digest)) + 1))[
                : self.dimension * 4
            ]
            values = np.frombuffer(raw, dtype=np.uint32).astype(np.float32)
            values -= values.mean()
            norm = float(np.linalg.norm(values))
            vectors[row] = values / norm if norm else 0.0
        return vectors


@unittest.skipUnless(np is not None, "encoder inference extra not installed")
class EncoderIntentClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.classifier = EncoderIntentClassifier.from_pretrained(
            encoder=_FakeEncoder()
        )

    def test_predict_labels_and_probabilities_cover_all_classes(self) -> None:
        texts = ["Why was I charged this fee?", "I lost my card."]
        labels = self.classifier.predict_labels(texts)
        self.assertEqual(len(labels), 2)
        self.assertTrue(set(labels) <= set(BANKING77_LABELS))

        rows = self.classifier.predict_proba(texts)
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(set(row), set(BANKING77_LABELS))
            self.assertAlmostEqual(sum(row.values()), 1.0, places=6)

    def test_route_probability_mass_sums_to_one(self) -> None:
        rows = self.classifier.predict_route_proba(["My card was declined."])
        self.assertEqual(set(rows[0]), set(OPERATIONAL_INTENTS))
        self.assertAlmostEqual(sum(rows[0].values()), 1.0, places=6)

    def test_classify_returns_the_part_a_contract_shape(self) -> None:
        result = self.classifier.classify(
            "Someone used my card without my permission."
        )
        self.assertIsInstance(result, UnderstandingResult)
        self.assertIn(result.intent, OPERATIONAL_INTENTS)
        self.assertIsNotNone(result.confidence)
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)
        self.assertEqual(result.risk_level.value, "HIGH")
        self.assertTrue(result.entities)

    def test_classify_many_matches_single_classification(self) -> None:
        texts = ["How do I change my PIN?", "I was charged twice."]
        batch = self.classifier.classify_many(texts)
        single = [self.classifier.classify(text) for text in texts]
        self.assertEqual([item.intent for item in batch], [item.intent for item in single])
        for left, right in zip(batch, single):
            self.assertAlmostEqual(left.confidence, right.confidence, places=12)

    def test_wrong_encoder_dimension_is_rejected(self) -> None:
        classifier = EncoderIntentClassifier.from_pretrained(
            encoder=_FakeEncoder(dimension=8)
        )
        with self.assertRaises(EncoderArtifactError):
            classifier.predict_labels(["hello"])


if __name__ == "__main__":
    unittest.main()
