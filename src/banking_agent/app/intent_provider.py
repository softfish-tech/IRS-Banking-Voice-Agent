"""E-owned selection of A's public intent adapter implementation."""

from __future__ import annotations

import os
from pathlib import Path

from banking_agent.app.orchestrator.interfaces import IntentModule
from banking_agent.app.llm_agent_support import FusedIntentModule, build_llm_understanding_from_environment, understanding_mode_from_environment
from banking_agent.modules.intent import (
    EncoderIntentClassifier,
    IntentModuleAdapter,
    TrainedIntentClassifier,
)


def build_intent_module(
    provider: str | None = None,
    model_path: str | Path | None = None,
    *,
    local_files_only: bool = False,
) -> IntentModule:
    """Return A's rules adapter or a supplied trained artifact adapter.

    A missing trained artifact is configuration failure, never a silent switch
    to a different implementation.  Callers that want a fallback must select
    ``rules`` explicitly.  ``minilm_encoder`` loads A's checked-in classifier
    artifact and the manifest-pinned Hugging Face encoder revision.
    """

    selected = (provider or os.environ.get("BANKING_AGENT_INTENT_PROVIDER", "rules")).strip().lower()
    if selected == "rules":
        adapter: IntentModule = IntentModuleAdapter()
    elif selected == "minilm_encoder":
        classifier = EncoderIntentClassifier.from_pretrained(local_files_only=local_files_only)
        adapter = IntentModuleAdapter(classifier=classifier.classify)
    elif selected != "trained":
        raise ValueError("intent_provider_must_be_rules_trained_or_minilm_encoder")
    else:
        configured_path = model_path or os.environ.get("BANKING_AGENT_INTENT_MODEL_PATH")
        if not configured_path:
            raise ValueError("trained_intent_model_path_required")
        artifact = Path(configured_path)
        if not artifact.is_file():
            raise ValueError("trained_intent_model_not_found")
        classifier = TrainedIntentClassifier.load(artifact)
        adapter = IntentModuleAdapter(classifier=classifier.classify)
    llm = build_llm_understanding_from_environment()
    return FusedIntentModule(adapter, llm, mode=understanding_mode_from_environment()) if llm else adapter
