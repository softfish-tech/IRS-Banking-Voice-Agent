"""BANKING77 intent-classification baselines (Part A Macro-F1 experiment).

Reads the gitignored CSVs in ``data/raw/banking77/`` and writes machine-readable
metrics to ``data/processed/`` plus a report table to
``docs/results_intent_baseline.md``.

Protocol: BANKING77 ships only train/test. A stratified holdout of the train
split is the dev set used to select the model and its hyper-parameters; the
test split is scored once, with the model refitted on the full train split.
The split that wins on dev is the one reported, never the one that wins on test.

Usage:
    .venv/Scripts/python.exe scripts/train_intent_baseline.py
    .venv/Scripts/python.exe scripts/train_intent_baseline.py --limit 2000
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

import numpy as np  # noqa: E402
import sklearn  # noqa: E402
from sklearn.calibration import CalibratedClassifierCV  # noqa: E402
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.naive_bayes import ComplementNB  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.svm import LinearSVC  # noqa: E402

from banking_agent.modules.intent.banking77 import (  # noqa: E402
    BANKING77_LABELS,
    operational_intent_for,
)

MODEL_NAMES = (
    "tfidf_complement_nb",
    "tfidf_linear_svc",
    "tfidf_linear_svc_calibrated",
    "tfidf_logreg",
)


def load_split(path: Path) -> tuple[list[str], list[str]]:
    texts: list[str] = []
    labels: list[str] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            texts.append(row["text"])
            labels.append(row["category"])
    return texts, labels


def macro_f1(labels_true: list[str], labels_pred: list[str]) -> float:
    return float(f1_score(labels_true, labels_pred, average="macro", zero_division=0))


def build_model(name: str, seed: int, c: float | None = None) -> Pipeline:
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2), sublinear_tf=True, lowercase=True, min_df=1
    )
    if name == "tfidf_linear_svc":
        classifier = LinearSVC(C=1.0 if c is None else c, random_state=seed, tol=1e-3)
    elif name == "tfidf_linear_svc_calibrated":
        classifier = CalibratedClassifierCV(
            LinearSVC(C=1.0 if c is None else c, random_state=seed, tol=1e-3),
            method="sigmoid",
            cv=3,
        )
    elif name == "tfidf_logreg":
        classifier = LogisticRegression(
            C=1.0 if c is None else c,
            class_weight="balanced",
            max_iter=1000,
            random_state=seed,
        )
    elif name == "tfidf_complement_nb":
        classifier = ComplementNB()
    else:  # pragma: no cover - guarded by argparse choices
        raise ValueError(f"unknown model: {name}")
    return Pipeline([("tfidf", vectorizer), ("clf", classifier)])


class EncoderClassifier:
    """Frozen sentence embeddings plus a logistic-regression probe.

    Imported lazily so the default TF-IDF run keeps working without torch.
    """

    def __init__(self, model_name: str, seed: int, c: float = 10.0) -> None:
        self.model_name = model_name
        self.seed = seed
        self.c = c
        self._encoder = None
        self._classifier: LogisticRegression | None = None

    def _embed(self, texts: list[str]):
        return self._encoder.encode(
            list(texts),
            batch_size=64,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

    def fit(self, texts: list[str], labels: list[str]) -> "EncoderClassifier":
        from sentence_transformers import SentenceTransformer

        self._encoder = SentenceTransformer(self.model_name)
        self._classifier = LogisticRegression(
            C=self.c, class_weight="balanced", max_iter=2000, random_state=self.seed
        )
        self._classifier.fit(self._embed(texts), labels)
        return self

    def predict(self, texts: list[str]) -> list[str]:
        return list(self._classifier.predict(self._embed(texts)))


def top_confusions(
    labels_true: list[str], labels_pred: list[str], limit: int = 15
) -> list[dict[str, object]]:
    matrix = confusion_matrix(labels_true, labels_pred, labels=list(BANKING77_LABELS))
    pairs = []
    for gold_index, gold in enumerate(BANKING77_LABELS):
        for pred_index, pred in enumerate(BANKING77_LABELS):
            if gold_index == pred_index:
                continue
            count = int(matrix[gold_index][pred_index])
            if count:
                pairs.append({"gold": gold, "predicted": pred, "count": count})
    pairs.sort(key=lambda item: (-int(item["count"]), str(item["gold"])))
    return pairs[:limit]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir", default=str(REPO_ROOT / "data" / "raw" / "banking77")
    )
    parser.add_argument("--out-dir", default=str(REPO_ROOT / "data" / "processed"))
    parser.add_argument(
        "--report", default=str(REPO_ROOT / "docs" / "results_intent_baseline.md")
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dev-frac", type=float, default=0.12)
    parser.add_argument("--svc-grid", default="0.1,0.5,1.0,2.0,5.0")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="cap training rows with a stratified sample (smoke runs)",
    )
    parser.add_argument(
        "--encoder",
        action="store_true",
        help="also run the frozen sentence-embedding + logistic-regression rung",
    )
    parser.add_argument(
        "--encoder-model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="sentence-transformers model used by --encoder",
    )
    parser.add_argument(
        "--save-model",
        default=None,
        help="joblib path for the dev-selected pipeline, e.g. "
        "models/intent_tfidf_linear_svc_calibrated.joblib",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    np.random.seed(args.seed)
    data_dir = Path(args.data_dir)

    train_texts, train_labels = load_split(data_dir / "train.csv")
    test_texts, test_labels = load_split(data_dir / "test.csv")

    if args.limit is not None and args.limit < len(train_texts):
        # train.csv is ordered by intent, so a head-truncation would train on a
        # handful of classes; cap with a stratified sample instead.
        train_texts, _, train_labels, _ = train_test_split(
            train_texts,
            train_labels,
            train_size=args.limit,
            random_state=args.seed,
            stratify=train_labels,
        )

    unknown = sorted(set(train_labels + test_labels) - set(BANKING77_LABELS))
    if unknown:
        print(f"FAIL: dataset contains labels outside the published space: {unknown}")
        return 1
    print(f"train {len(train_texts)} | test {len(test_texts)}")

    fit_texts, dev_texts, fit_labels, dev_labels = train_test_split(
        train_texts,
        train_labels,
        test_size=args.dev_frac,
        random_state=args.seed,
        stratify=train_labels,
    )
    print(f"fit {len(fit_texts)} | dev {len(dev_texts)} | test {len(test_texts)}")

    outcomes: dict[str, dict[str, object]] = {}
    predictions: dict[str, list[str]] = {}

    majority_class = Counter(fit_labels).most_common(1)[0][0]
    outcomes["majority"] = {
        "params": {"strategy": "most_frequent", "class": majority_class},
        "dev_macro_f1": macro_f1(dev_labels, [majority_class] * len(dev_labels)),
        "test_macro_f1": macro_f1(test_labels, [majority_class] * len(test_labels)),
        "test_accuracy": float(
            accuracy_score(test_labels, [majority_class] * len(test_labels))
        ),
        "fit_seconds": 0.0,
    }
    predictions["majority"] = [majority_class] * len(test_labels)
    print(f"majority: dev macro-F1 {outcomes['majority']['dev_macro_f1']:.4f}")

    svc_grid: tuple[float | None, ...] = tuple(
        float(value) for value in args.svc_grid.split(",")
    )
    for name in MODEL_NAMES:
        grid: tuple[float | None, ...] = (
            svc_grid
            if name in ("tfidf_linear_svc", "tfidf_linear_svc_calibrated")
            else (None,)
        )
        best: tuple[float, float | None, float] | None = None
        for c in grid:
            started = time.perf_counter()
            model = build_model(name, args.seed, c)
            model.fit(fit_texts, fit_labels)
            score = macro_f1(dev_labels, list(model.predict(dev_texts)))
            seconds = time.perf_counter() - started
            print(f"  {name} C={c}: dev macro-F1 {score:.4f} ({seconds:.1f}s)")
            if best is None or score > best[0]:
                best = (score, c, seconds)
        assert best is not None
        dev_score, best_c, fit_seconds = best

        final = build_model(name, args.seed, best_c)
        final.fit(train_texts, train_labels)
        test_pred = list(final.predict(test_texts))
        outcomes[name] = {
            "params": {"C": best_c},
            "dev_macro_f1": dev_score,
            "test_macro_f1": macro_f1(test_labels, test_pred),
            "test_accuracy": float(accuracy_score(test_labels, test_pred)),
            "fit_seconds": round(fit_seconds, 1),
        }
        predictions[name] = test_pred
        print(
            f"{name}: dev {dev_score:.4f} -> test macro-F1 "
            f"{outcomes[name]['test_macro_f1']:.4f}"
        )

    if args.encoder:
        started = time.perf_counter()
        probe = EncoderClassifier(args.encoder_model, args.seed)
        probe.fit(fit_texts, fit_labels)
        dev_score = macro_f1(dev_labels, probe.predict(dev_texts))
        seconds = time.perf_counter() - started

        final_probe = EncoderClassifier(args.encoder_model, args.seed)
        final_probe.fit(train_texts, train_labels)
        test_pred = final_probe.predict(test_texts)
        outcomes["encoder_logreg"] = {
            "params": {"model": args.encoder_model, "C": 10.0},
            "dev_macro_f1": dev_score,
            "test_macro_f1": macro_f1(test_labels, test_pred),
            "test_accuracy": float(accuracy_score(test_labels, test_pred)),
            "fit_seconds": round(seconds, 1),
        }
        predictions["encoder_logreg"] = test_pred
        print(
            f"encoder_logreg: dev {dev_score:.4f} -> test macro-F1 "
            f"{outcomes['encoder_logreg']['test_macro_f1']:.4f}"
        )

    # Selection uses dev only; the test score is reported, never used to choose.
    best_name = max(outcomes, key=lambda key: outcomes[key]["dev_macro_f1"])
    per_class = f1_score(
        test_labels,
        predictions[best_name],
        labels=list(BANKING77_LABELS),
        average=None,
        zero_division=0,
    )
    support = Counter(test_labels)
    per_class_rows = [
        {
            "intent": label,
            "f1": round(float(score), 4),
            "support": int(support.get(label, 0)),
        }
        for label, score in zip(BANKING77_LABELS, per_class)
    ]
    confusions = top_confusions(test_labels, predictions[best_name])

    # Second view: the same predictions mapped to the operational routes that
    # C/E actually branch on. product_recommendation cannot appear here because
    # BANKING77 has no recommendation intent.
    gold_routes = [operational_intent_for(label) for label in test_labels]
    predicted_routes = [
        operational_intent_for(label) for label in predictions[best_name]
    ]
    routes = sorted(set(gold_routes))
    route_rows = [
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
                4,
            ),
            "support": gold_routes.count(route),
        }
        for route in routes
    ]
    route_metrics = {
        "routes_scored": routes,
        "macro_f1": round(
            float(
                f1_score(
                    gold_routes,
                    predicted_routes,
                    labels=routes,
                    average="macro",
                    zero_division=0,
                )
            ),
            4,
        ),
        "accuracy": round(float(accuracy_score(gold_routes, predicted_routes)), 4),
        "per_route": route_rows,
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics = {
        "command": " ".join(sys.argv),
        "dataset": "PolyAI/banking77",
        "seed": args.seed,
        "dev_fraction": args.dev_frac,
        "counts": {
            "train": len(train_texts),
            "dev": len(dev_texts),
            "fit": len(fit_texts),
            "test": len(test_texts),
            "intents": len(BANKING77_LABELS),
        },
        "environment": {
            "python": sys.version.split()[0],
            "scikit_learn": sklearn.__version__,
            "numpy": np.__version__,
        },
        "models": outcomes,
        "selected_on_dev": best_name,
        "per_class_f1": per_class_rows,
        "top_confusions": confusions,
        "route_evaluation": route_metrics,
    }
    (out_dir / "intent_baseline_metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    with (out_dir / "intent_baseline_per_class_f1.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=["intent", "f1", "support"])
        writer.writeheader()
        writer.writerows(per_class_rows)

    weakest = sorted(per_class_rows, key=lambda row: row["f1"])[:10]
    lines = [
        "# Intent classification baseline results (Part A)",
        "",
        "Generated by `scripts/train_intent_baseline.py`; do not edit by hand.",
        "",
        f"- Dataset: BANKING77 (CC-BY-4.0), train {len(train_texts)} / "
        f"test {len(test_texts)}, {len(BANKING77_LABELS)} intents.",
        f"- Dev: stratified {args.dev_frac:.0%} holdout of train, seed {args.seed} "
        f"({len(dev_texts)} examples); used for model and `C` selection.",
        "- Test is scored once, after refitting on the full train split.",
        f"- Command: `{sys.argv[0]} {' '.join(sys.argv[1:])}`",
        f"- Environment: Python {sys.version.split()[0]}, "
        f"scikit-learn {sklearn.__version__}, numpy {np.__version__}.",
        "",
        "## Model comparison",
        "",
        "| model | dev Macro-F1 | test Macro-F1 | test accuracy | fit (s) |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name in outcomes:  # insertion order: majority, TF-IDF ladder, encoder
        row = outcomes[name]
        lines.append(
            f"| `{name}` | {row['dev_macro_f1']:.4f} | {row['test_macro_f1']:.4f} | "
            f"{row['test_accuracy']:.4f} | {row['fit_seconds']} |"
        )
    lines += [
        "",
        f"Headline: **`{best_name}`** was selected on dev Macro-F1, giving a test "
        f"Macro-F1 of **{outcomes[best_name]['test_macro_f1']:.4f}** "
        f"(accuracy {outcomes[best_name]['test_accuracy']:.4f}).",
        "",
        "## Weakest intents (test, lowest F1)",
        "",
        "| intent | F1 | support |",
        "| --- | --- | --- |",
    ]
    lines += [
        f"| `{row['intent']}` | {row['f1']:.4f} | {row['support']} |" for row in weakest
    ]
    lines += [
        "",
        "## Most frequent confusions (test)",
        "",
        "| gold | predicted | count |",
        "| --- | --- | --- |",
    ]
    lines += [
        f"| `{row['gold']}` | `{row['predicted']}` | {row['count']} |"
        for row in confusions
    ]
    lines += [
        "",
        "## Route-level (mapped) results on test",
        "",
        "Fine-grained predictions mapped through `operational_intent_for`.",
        "",
        "| route | F1 | support |",
        "| --- | --- | --- |",
    ]
    lines += [
        f"| `{row['route']}` | {row['f1']:.4f} | {row['support']} |"
        for row in route_rows
    ]
    lines += [
        "",
        f"Route Macro-F1 **{route_metrics['macro_f1']:.4f}**, accuracy "
        f"{route_metrics['accuracy']:.4f}, over the {len(routes)} routes "
        "present in the test gold labels. `product_recommendation` is not "
        "scored: BANKING77 has no recommendation intent, so that route is "
        "reached by rules and scenario text only.",
        "",
        "## Notes",
        "",
        "- Macro-F1 is the metric required by the proposal: it weights all 77 "
        "intents equally, which matters because the train split is uneven "
        "(35-187 examples per class).",
        "- `majority` is the trivial lower bound; the TF-IDF models are the "
        "working baselines. `encoder_logreg`, when present, is a frozen "
        "sentence encoder with a logistic-regression probe (`--encoder`).",
        "- The route-level section above is a mapped view of the same "
        "predictions. It is still a BANKING77 score: `fraud_suspicion`, "
        "`fee_complaint`, and `product_recommendation` are only partly or not "
        "at all represented in the dataset, so they are covered by the rule "
        "layer and the scenario tests instead.",
        "- Reproducing the encoder rung needs `sentence-transformers`; the default run "
        "reproduces the TF-IDF ladder alone in about 20 seconds.",
    ]
    Path(args.report).write_text("\n".join(lines) + "\n", encoding="utf-8")

    if args.save_model:
        import joblib

        # The encoder rung is not a joblib pipeline and needs torch at load
        # time, so fall back to the best dev-ranked pipeline that is one.
        pipelines = [name for name in outcomes if name in MODEL_NAMES]
        target = best_name
        if target not in MODEL_NAMES:
            target = max(pipelines, key=lambda name: outcomes[name]["dev_macro_f1"])
            print(
                f"--save-model: selected model `{best_name}` is not a joblib pipeline; "
                f"saving `{target}` instead"
            )
        artifact = build_model(target, args.seed, outcomes[target]["params"].get("C"))
        artifact.fit(train_texts, train_labels)
        model_path = Path(args.save_model)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(artifact, model_path)
        print(f"wrote {model_path} ({target})")

    print()
    print(f"selected on dev: {best_name}")
    print(f"test macro-F1: {outcomes[best_name]['test_macro_f1']:.4f}")
    print(f"wrote {out_dir / 'intent_baseline_metrics.json'}")
    print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
