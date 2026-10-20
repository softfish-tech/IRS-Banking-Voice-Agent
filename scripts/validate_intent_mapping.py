"""Validate the BANKING77 -> operational intent mapping (Part A).

Usage:

    python scripts/validate_intent_mapping.py --check   # CI / pre-experiment
    python scripts/validate_intent_mapping.py           # print the 77-row table

The printed table is the source for the report's label-mapping appendix.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from banking_agent.modules.intent.banking77 import (  # noqa: E402
    BANKING77_LABELS,
    BANKING77_TO_OPERATIONAL_INTENT,
    DEFAULT_OPERATIONAL_INTENT,
    operational_intent_for,
    unresolved_intents,
)
from banking_agent.modules.intent.taxonomy import OPERATIONAL_INTENTS  # noqa: E402

RAG_LABEL_REGISTRY = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "banking_agent"
    / "modules"
    / "rag"
    / "banking77_mapping.json"
)


def rag_registry_labels() -> set[str] | None:
    """Return B's label keys when the RAG registry is present."""
    if not RAG_LABEL_REGISTRY.exists():
        return None
    payload = json.loads(RAG_LABEL_REGISTRY.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("RAG banking77_mapping.json must be a JSON object")
    return set(payload)


def problems() -> list[str]:
    """Return every reason the mapping is not safe to train or report on."""
    found: list[str] = []
    if len(BANKING77_LABELS) != 77:
        found.append(f"expected 77 labels, found {len(BANKING77_LABELS)}")
    if len(set(BANKING77_LABELS)) != len(BANKING77_LABELS):
        found.append("BANKING77_LABELS contains duplicates")
    for label in unresolved_intents():
        found.append(f"mapping references a label that does not exist: {label}")
    if DEFAULT_OPERATIONAL_INTENT not in OPERATIONAL_INTENTS:
        found.append("DEFAULT_OPERATIONAL_INTENT is not an operational intent")
    for label in BANKING77_LABELS:
        route = operational_intent_for(label)
        if route not in OPERATIONAL_INTENTS:
            found.append(f"{label}: route {route!r} is not an operational intent")
    try:
        rag_labels = rag_registry_labels()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        found.append(f"cannot read the RAG label registry: {exc}")
        rag_labels = None
    if rag_labels is not None:
        missing = sorted(set(BANKING77_LABELS) - rag_labels)
        extra = sorted(rag_labels - set(BANKING77_LABELS))
        if missing:
            found.append(f"RAG registry is missing labels: {missing}")
        if extra:
            found.append(f"RAG registry has unknown labels: {extra}")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the BANKING77 intent mapping."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero when the mapping is incomplete or inconsistent",
    )
    args = parser.parse_args()

    found = problems()

    if not args.check:
        print(f"{'id':>2}  {'banking77 label':<45} operational intent")
        for index, label in enumerate(BANKING77_LABELS):
            print(f"{index:>2}  {label:<45} {operational_intent_for(label)}")
        print()

    if found:
        for item in found:
            print(f"FAIL {item}")
        return 1

    print(
        f"OK: {len(BANKING77_LABELS)} labels, "
        f"{len(BANKING77_TO_OPERATIONAL_INTENT)} explicit routes, "
        f"{len(BANKING77_LABELS) - len(BANKING77_TO_OPERATIONAL_INTENT)} defaulted to "
        f"{DEFAULT_OPERATIONAL_INTENT}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
