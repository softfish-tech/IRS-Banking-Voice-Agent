"""Optional Phase-two entry point: a trained pipeline behind ``classify``.

The deterministic rule implementation in :mod:`banking_agent.modules.intent.mock`
stays the default so Phase-one integration is reproducible and dependency-free.
This module wraps the fitted scikit-learn pipeline produced by
``scripts/train_intent_baseline.py`` and exposes the same
``classify(text) -> UnderstandingResult`` shape, so E can switch to it without
touching the contract.

``scikit-learn``/``joblib`` are imported lazily inside :meth:`load`, so importing
the module never pulls them in.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from pathlib import Path

from banking_agent.schemas.state import UnderstandingResult

from .banking77 import operational_intent_for
from .mock import detect_risk, extract_entities


class TrainedIntentClassifier:
    """Route a fitted 77-class BANKING77 pipeline into the shared contract.

    The fine-grained label never leaves the module: it is mapped to an
    operational route with :func:`operational_intent_for`, which is what C and E
    branch on. :meth:`predict_labels` exposes the raw label for the decision
    trace, which must stay diagnostic rather than contractual.
    """

    def __init__(
        self,
        pipeline: object,
        route_map: Callable[[str], str] = operational_intent_for,
    ) -> None:
        self._pipeline = pipeline
        self._route_map = route_map

    @classmethod
    def load(cls, path: str | Path) -> "TrainedIntentClassifier":
        """Load a joblib-serialised pipeline saved by the training script."""
        import joblib

        return cls(joblib.load(path))

    def predict_labels(self, texts: Sequence[str]) -> list[str]:
        """Return the raw fine-grained labels, for traces and error analysis."""
        return [str(label) for label in self._pipeline.predict(list(texts))]

    def _route_mass(
        self, classes: list[str], row: Sequence[float], chosen_label: str
    ) -> float:
        """Probability mass sitting on the route of the predicted label.

        The returned ``intent`` is the route, so the honest confidence is the
        total probability of every fine-grained label that maps to it. On
        BANKING77 a well-calibrated 77-way arg-max is frequently below 0.4 even
        when the route is right, which would make C clarify almost everything.
        """
        chosen_route = self._route_map(chosen_label)
        return sum(
            float(value)
            for label, value in zip(classes, row)
            if self._route_map(label) == chosen_route
        )

    def _confidence(
        self, texts: Sequence[str], labels: Sequence[str]
    ) -> list[float | None]:
        proba = getattr(self._pipeline, "predict_proba", None)
        if callable(proba):
            rows = proba(list(texts))
            classes = getattr(self._pipeline, "classes_", None)
            if classes is None:
                return [float(max(row)) for row in rows]
            class_list = [str(label) for label in classes]
            return [
                self._route_mass(class_list, row, label)
                for row, label in zip(rows, labels)
            ]

        scores = getattr(self._pipeline, "decision_function", None)
        if callable(scores):
            result: list[float | None] = []
            for row in scores(list(texts)):
                top = max(float(value) for value in row)
                # One-vs-rest margins are not probabilities: turn the winning
                # margin into a confidence with the logistic function, so a
                # margin of 0 reads as "unsure" (0.5) rather than near-zero.
                result.append(1.0 / (1.0 + math.exp(-top)))
            return result

        return [None] * len(texts)

    def classify(self, text: str) -> UnderstandingResult:
        label = self.predict_labels([text])[0]
        intent = self._route_map(label)
        confidence = self._confidence([text], [label])[0]
        return UnderstandingResult(
            intent=intent,
            confidence=confidence,
            risk_level=detect_risk(text, intent),
            entities=extract_entities(text),
        )

    def classify_many(self, texts: Sequence[str]) -> list[UnderstandingResult]:
        labels = self.predict_labels(texts)
        confidences = self._confidence(texts, labels)
        return [
            UnderstandingResult(
                intent=self._route_map(label),
                confidence=confidence,
                risk_level=detect_risk(text, self._route_map(label)),
                entities=extract_entities(text),
            )
            for text, label, confidence in zip(texts, labels, confidences)
        ]


__all__ = ["TrainedIntentClassifier"]
