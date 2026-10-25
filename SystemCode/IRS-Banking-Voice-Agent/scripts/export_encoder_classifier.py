"""Export the published BANKING77 encoder/classifier artifact (Part A).

The experiment in ``train_intent_baseline.py`` selects a frozen
``sentence-transformers/all-MiniLM-L6-v2`` encoder plus a multinomial logistic
regression probe. This script reproduces that exact protocol and writes a small,
reviewable inference artifact:

* ``logreg_params.npz`` - coefficients, intercepts, and class order;
* ``label_order.json`` - all 77 BANKING77 labels in published order;
* ``route_mapping.json`` - the complete label-to-operational-route bridge;
* ``preprocessing.json`` - the exact text/embedding configuration;
* ``manifest.json`` - pinned encoder revision, checksums, metrics, and runtime.

The 90 MB encoder weights are deliberately not committed. The manifest pins the
Hugging Face revision and records a SHA-256 for every file in that snapshot, so
the encoder can be downloaded and verified without bloating Git.

Usage:
    .venv/Scripts/python.exe scripts/export_encoder_classifier.py
    .venv/Scripts/python.exe scripts/export_encoder_classifier.py --device cpu
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

import numpy as np  # noqa: E402
import sklearn  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import accuracy_score, f1_score  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402

from banking_agent.modules.intent.banking77 import (  # noqa: E402
    BANKING77_LABELS,
    BANKING77_TO_OPERATIONAL_INTENT,
    DEFAULT_OPERATIONAL_INTENT,
    operational_intent_for,
)
from banking_agent.modules.intent.taxonomy import OPERATIONAL_INTENTS  # noqa: E402

DEFAULT_OUT_DIR = (
    REPO_ROOT / "src" / "banking_agent" / "modules" / "intent" / "model_artifacts"
)
DEFAULT_ENCODER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_ENCODER_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir", default=str(REPO_ROOT / "data" / "raw" / "banking77")
    )
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--encoder-model", default=DEFAULT_ENCODER_MODEL)
    parser.add_argument("--encoder-revision", default=DEFAULT_ENCODER_REVISION)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dev-frac", type=float, default=0.12)
    parser.add_argument("--classifier-c", type=float, default=10.0)
    parser.add_argument(
        "--allow-download",
        action="store_true",
        help="download the pinned encoder snapshot if it is not already cached",
    )
    return parser.parse_args()


def load_split(path: Path) -> tuple[list[str], list[str]]:
    texts: list[str] = []
    labels: list[str] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            texts.append(row["text"])
            labels.append(row["category"])
    return texts, labels


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_artifact(path: Path) -> str:
    """Hash an artifact independently of the checkout's line endings."""
    data = path.read_bytes()
    if path.suffix in {".json", ".txt", ".md"}:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, payload: object) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    path.write_bytes(text.encode("utf-8"))


def macro_f1(gold: list[str], predicted: list[str]) -> float:
    return float(f1_score(gold, predicted, average="macro", zero_division=0))


def snapshot_manifest(model_id: str, revision: str, allow_download: bool):
    from huggingface_hub import snapshot_download

    try:
        snapshot_dir = snapshot_download(
            repo_id=model_id,
            revision=revision,
            local_files_only=True,
        )
    except Exception:
        if not allow_download:
            raise RuntimeError(
                "the pinned encoder snapshot is not cached; rerun with "
                "--allow-download to fetch it"
            ) from None
        snapshot_dir = snapshot_download(repo_id=model_id, revision=revision)

    root = Path(snapshot_dir)
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return root, files


def route_metrics(
    gold_labels: list[str], predicted_labels: list[str]
) -> dict[str, Any]:
    gold_routes = [operational_intent_for(label) for label in gold_labels]
    predicted_routes = [operational_intent_for(label) for label in predicted_labels]
    routes = sorted(set(gold_routes))
    per_route = []
    for route in routes:
        per_route.append(
            {
                "route": route,
                "f1": round(
                    float(
                        f1_score(
                            gold_routes,
                            predicted_routes,
                            labels=[route],
                            average=None,
                            zero_division=0,
                        )[0]
                    ),
                    6,
                ),
                "support": gold_routes.count(route),
            }
        )
    return {
        "routes_scored": routes,
        "macro_f1": round(macro_f1(gold_routes, predicted_routes), 6),
        "accuracy": round(float(accuracy_score(gold_routes, predicted_routes)), 6),
        "per_route": per_route,
    }


def build_route_mapping() -> dict[str, Any]:
    label_to_route = {
        label: operational_intent_for(label) for label in BANKING77_LABELS
    }
    route_to_labels = {
        route: sorted(label for label, value in label_to_route.items() if value == route)
        for route in sorted(OPERATIONAL_INTENTS)
    }
    explicit = {
        label: route
        for label, route in BANKING77_TO_OPERATIONAL_INTENT.items()
        if label in label_to_route
    }
    return {
        "schema_version": 1,
        "source": "BANKING77 published label space mapped to Part A operational intents",
        "default_route": DEFAULT_OPERATIONAL_INTENT,
        "routes": sorted(OPERATIONAL_INTENTS),
        "explicit_mappings": len(explicit),
        "default_mappings": len(BANKING77_LABELS) - len(explicit),
        "label_to_route": label_to_route,
        "route_to_labels": route_to_labels,
    }


def main() -> int:
    args = parse_args()
    np.random.seed(args.seed)
    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_texts, train_labels = load_split(data_dir / "train.csv")
    test_texts, test_labels = load_split(data_dir / "test.csv")
    unknown = sorted(set(train_labels + test_labels) - set(BANKING77_LABELS))
    if unknown:
        print(f"FAIL: labels outside BANKING77: {unknown}")
        return 1
    if len(BANKING77_LABELS) != 77 or len(set(BANKING77_LABELS)) != 77:
        print("FAIL: BANKING77 label space is not 77 unique labels")
        return 1

    fit_texts, dev_texts, fit_labels, dev_labels = train_test_split(
        train_texts,
        train_labels,
        test_size=args.dev_frac,
        random_state=args.seed,
        stratify=train_labels,
    )

    from sentence_transformers import SentenceTransformer

    encoder = SentenceTransformer(
        args.encoder_model,
        revision=args.encoder_revision,
        device=args.device,
    )
    dimension_getter = getattr(encoder, "get_embedding_dimension", None)
    if dimension_getter is None:  # sentence-transformers < 6.1
        dimension_getter = encoder.get_sentence_embedding_dimension
    embedding_dimension = int(dimension_getter())
    max_seq_length = int(encoder.max_seq_length)

    def embed(texts: list[str]) -> np.ndarray:
        values = encoder.encode(
            texts,
            batch_size=args.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return np.asarray(values, dtype=np.float32)

    print(f"train {len(train_texts)} | dev {len(dev_texts)} | test {len(test_texts)}")
    print(f"encoder {args.encoder_model}@{args.encoder_revision}")

    def fit_probe(texts: list[str], labels: list[str]) -> LogisticRegression:
        probe = LogisticRegression(
            C=args.classifier_c,
            class_weight="balanced",
            max_iter=2000,
            random_state=args.seed,
        )
        probe.fit(embed(texts), labels)
        return probe

    dev_probe = fit_probe(fit_texts, fit_labels)
    dev_predictions = list(dev_probe.predict(embed(dev_texts)))
    dev_score = macro_f1(dev_labels, dev_predictions)

    final_probe = fit_probe(train_texts, train_labels)
    test_embedding = embed(test_texts)
    sklearn_predictions = [str(value) for value in final_probe.predict(test_embedding)]
    test_score = macro_f1(test_labels, sklearn_predictions)
    test_accuracy = float(accuracy_score(test_labels, sklearn_predictions))
    routes = route_metrics(test_labels, sklearn_predictions)

    classes = np.asarray(final_probe.classes_, dtype=str)
    coefficients = np.asarray(final_probe.coef_, dtype=np.float64)
    intercepts = np.asarray(final_probe.intercept_, dtype=np.float64)
    classifier_params = {
        key: value
        for key, value in final_probe.get_params().items()
        if value is None or isinstance(value, (bool, int, float, str))
    }

    logits = test_embedding.astype(np.float64) @ coefficients.T + intercepts
    logits -= logits.max(axis=1, keepdims=True)
    probabilities = np.exp(logits)
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    numpy_predictions = classes[np.argmax(probabilities, axis=1)].tolist()
    sklearn_probabilities = final_probe.predict_proba(test_embedding)
    max_probability_difference = float(
        np.max(np.abs(probabilities - sklearn_probabilities))
    )
    prediction_mismatches = sum(
        gold != sklearn_prediction
        for gold, sklearn_prediction in zip(numpy_predictions, sklearn_predictions)
    )

    if prediction_mismatches:
        print(f"FAIL: numpy/sklearn prediction mismatches: {prediction_mismatches}")
        return 1
    if len(set(classes)) != 77 or set(classes) != set(BANKING77_LABELS):
        print("FAIL: classifier classes do not cover the 77 BANKING77 labels")
        return 1
    if coefficients.shape != (77, embedding_dimension):
        print(f"FAIL: unexpected coefficient shape {coefficients.shape}")
        return 1
    if intercepts.shape != (77,):
        print(f"FAIL: unexpected intercept shape {intercepts.shape}")
        return 1

    snapshot_dir, encoder_files = snapshot_manifest(
        args.encoder_model,
        args.encoder_revision,
        args.allow_download,
    )

    npz_path = out_dir / "logreg_params.npz"
    np.savez_compressed(
        npz_path,
        coef=coefficients,
        intercept=intercepts,
        classes=classes,
    )

    label_order = {
        "schema_version": 1,
        "dataset": "PolyAI/banking77",
        "count": len(BANKING77_LABELS),
        "order": "BANKING77 published label-id order",
        "labels": list(BANKING77_LABELS),
        "label_ids": {
            label: index for index, label in enumerate(BANKING77_LABELS)
        },
    }
    write_json(out_dir / "label_order.json", label_order)

    route_mapping = build_route_mapping()
    write_json(out_dir / "route_mapping.json", route_mapping)

    preprocessing = {
        "schema_version": 1,
        "text": {
            "normalization": "none",
            "lowercase": False,
            "strip": False,
            "steps": [],
            "note": "Raw user text is passed to the frozen sentence encoder.",
        },
        "tokenizer": {
            "class": type(encoder.tokenizer).__name__,
            "do_lower_case": bool(getattr(encoder.tokenizer, "do_lower_case", False)),
            "model_max_length": int(encoder.tokenizer.model_max_length),
            "padding_side": str(encoder.tokenizer.padding_side),
            "truncation_side": str(encoder.tokenizer.truncation_side),
        },
        "embedding": {
            "method": "SentenceTransformer.encode",
            "batch_size": args.batch_size,
            "show_progress_bar": False,
            "convert_to_numpy": True,
            "normalize_embeddings": True,
            "output_value": "sentence_embedding",
            "precision": "float32",
            "device": args.device,
            "max_seq_length": max_seq_length,
            "embedding_dimension": embedding_dimension,
        },
    }
    write_json(out_dir / "preprocessing.json", preprocessing)

    (out_dir / "requirements-inference.txt").write_text(
        "numpy==2.5.4\n"
        "sentence-transformers==6.1.0\n"
        "transformers==5.19.0\n"
        "torch==2.14.1\n"
        "huggingface-hub==1.33.0\n",
        encoding="utf-8",
    )
    (out_dir / "requirements-export.txt").write_text(
        "-r requirements-inference.txt\nscikit-learn==1.9.1\n",
        encoding="utf-8",
    )

    artifact_names = (
        "logreg_params.npz",
        "label_order.json",
        "route_mapping.json",
        "preprocessing.json",
    )
    artifacts = {
        name: {
            "bytes": (out_dir / name).stat().st_size,
            "sha256": sha256_artifact(out_dir / name),
        }
        for name in artifact_names
    }

    import huggingface_hub
    import sentence_transformers
    import torch
    import transformers

    manifest = {
        "schema_version": 1,
        "artifact_name": "banking77-all-MiniLM-L6-v2-logreg",
        "part": "A",
        "task": "BANKING77 77-class intent classification",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "id": "PolyAI/banking77",
            "license": "CC-BY-4.0",
            "train_examples": len(train_texts),
            "test_examples": len(test_texts),
            "intents": len(BANKING77_LABELS),
        },
        "training_protocol": {
            "seed": args.seed,
            "dev_fraction": args.dev_frac,
            "fit_examples": len(fit_texts),
            "dev_examples": len(dev_texts),
            "selection": "dev Macro-F1; refit on full train; test scored once",
            "dev_macro_f1": round(dev_score, 6),
        },
        "metrics": {
            "test_macro_f1": round(test_score, 6),
            "test_accuracy": round(test_accuracy, 6),
            "route_macro_f1": routes["macro_f1"],
            "route_accuracy": routes["accuracy"],
            "per_route": routes["per_route"],
        },
        "encoder": {
            "provider": "Hugging Face",
            "model_id": args.encoder_model,
            "revision": args.encoder_revision,
            "license": "Apache-2.0",
            "embedding_dimension": embedding_dimension,
            "max_seq_length": max_seq_length,
            "snapshot_bytes": sum(item["bytes"] for item in encoder_files),
            "snapshot_files": encoder_files,
        },
        "classifier": {
            "type": "sklearn.linear_model.LogisticRegression",
            "params_source": "LogisticRegression.get_params()",
            "params": classifier_params,
            "parameters_file": "logreg_params.npz",
            "coefficient_shape": list(coefficients.shape),
            "intercept_shape": list(intercepts.shape),
            "classes_order": "sklearn sorted class order stored in classes",
            "decision_rule": "argmax(softmax(embedding @ coef.T + intercept))",
        },
        "labels": {
            "file": "label_order.json",
            "count": len(BANKING77_LABELS),
            "prediction_column": "classes (sklearn order)",
            "published_order_file": "labels (BANKING77 order)",
        },
        "routes": {
            "file": "route_mapping.json",
            "default_route": DEFAULT_OPERATIONAL_INTENT,
            "explicit_mappings": route_mapping["explicit_mappings"],
            "default_mappings": route_mapping["default_mappings"],
            "route_values": route_mapping["routes"],
        },
        "preprocessing": {
            "file": "preprocessing.json",
            "text_normalization": "none",
            "embedding_normalization": "L2",
            "batch_size": args.batch_size,
        },
        "verification": {
            "numpy_sklearn_prediction_mismatches": prediction_mismatches,
            "softmax_max_abs_difference": max_probability_difference,
            "all_labels_covered": True,
            "all_routes_valid": all(
                route in OPERATIONAL_INTENTS
                for route in route_mapping["label_to_route"].values()
            ),
            "artifact_checksums_required_at_load": True,
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "sentence_transformers": sentence_transformers.__version__,
            "transformers": transformers.__version__,
            "torch": torch.__version__,
            "huggingface_hub": huggingface_hub.__version__,
        },
        "artifacts": artifacts,
        "inference": {
            "entry_point": (
                "banking_agent.modules.intent.encoder_classifier:"
                "EncoderIntentClassifier"
            ),
            "factory": "EncoderIntentClassifier.from_pretrained()",
            "requirements": "requirements-inference.txt",
            "encoder_download": (
                "SentenceTransformer(model_id, revision=revision); weights are "
                "not vendored in this repository"
            ),
        },
    }
    write_json(out_dir / "manifest.json", manifest)

    readme = f"""# BANKING77 encoder classifier

Part A deliverable for the banking voice agent: a frozen
`{args.encoder_model}` sentence encoder followed by a multinomial logistic
regression probe.

## Results

| Metric | Value |
| --- | ---: |
| BANKING77 test Macro-F1 | **{test_score:.4f}** |
| BANKING77 test accuracy | {test_accuracy:.4f} |
| Route Macro-F1 | {routes['macro_f1']:.4f} |
| Route accuracy | {routes['accuracy']:.4f} |

The test split is scored once after refitting on all {len(train_texts):,} train
examples. Model selection used a stratified {args.dev_frac:.0%} dev holdout of
train (seed {args.seed}).

## Files

| File | Purpose |
| --- | --- |
| `logreg_params.npz` | `coef` (77 x {embedding_dimension}), `intercept` (77), and sklearn class order |
| `label_order.json` | 77 BANKING77 labels in published label-id order |
| `route_mapping.json` | Complete label-to-operational-route mapping |
| `preprocessing.json` | Raw-text, tokenizer, embedding, batch, and normalization config |
| `manifest.json` | Pinned encoder revision, per-file SHA-256, metrics, versions, entry point |
| `requirements-inference.txt` | Exact Python runtime used for inference |
| `requirements-export.txt` | Additional dependency for re-exporting the artifact |

## Frozen encoder

- Model: `{args.encoder_model}`
- Revision: `{args.encoder_revision}`
- License: Apache-2.0
- Embedding dimension: {embedding_dimension}
- Maximum sequence length: {max_seq_length}

The encoder weights are **not** stored in Git. The revision is immutable and
`manifest.json` records the byte size and SHA-256 of every file in the snapshot.
This avoids a ~90 MB binary in the repository while keeping the model pinned.

## Inference

```bash
python -m pip install -e .
python -m pip install -r src/banking_agent/modules/intent/model_artifacts/requirements-inference.txt
```

```python
from banking_agent.modules.intent import EncoderIntentClassifier

classifier = EncoderIntentClassifier.from_pretrained()
result = classifier.classify("Why was I charged this fee?")
print(result.intent, result.confidence, result.risk_level, result.entities)
```

`classify()` returns `UnderstandingResult`: operational intent, route-probability
confidence, risk level, and entities. It never returns an action, reason code, or
final response. To plug it into E's adapter:

```python
from banking_agent.modules.intent import IntentModuleAdapter

adapter = IntentModuleAdapter(classifier=classifier.classify)
```

## Verification and limits

- Loading verifies SHA-256 for all four parameter/config artifacts.
- The exported NumPy softmax path has zero prediction mismatches against
  `LogisticRegression.predict`; maximum probability difference is
  {max_probability_difference:.3e}.
- Fine-grained mistakes should be interpreted through operational routes. Three
  routes (`fraud_suspicion`, `fee_complaint`, `product_recommendation`) are only
  partly or not represented in BANKING77 and still depend on the rule layer.
- The model always predicts one of 77 labels; abstention remains C's decision.

## Attribution

- BANKING77: Casanueva et al. (2020), `PolyAI/banking77`, CC-BY-4.0.
- `sentence-transformers/all-MiniLM-L6-v2`: Apache-2.0.

Reproduce with:

```bash
python scripts/export_encoder_classifier.py
```
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")

    print(f"dev Macro-F1: {dev_score:.6f}")
    print(f"test Macro-F1: {test_score:.6f}")
    print(f"test accuracy: {test_accuracy:.6f}")
    print(f"route Macro-F1: {routes['macro_f1']:.6f}")
    print(f"numpy/sklearn mismatches: {prediction_mismatches}")
    print(f"softmax max abs difference: {max_probability_difference:.3e}")
    print(f"wrote artifact to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
