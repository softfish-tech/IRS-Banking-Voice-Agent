"""Named, reproducible E-owned delivery configuration profiles.

Profiles change optional presentation/understanding helpers only.  They never
provide a model, endpoint, credential, or a C business decision.
"""

from __future__ import annotations

import os


FROZEN_20261023 = "frozen-20261023"
_FROZEN_20261023_DEFAULTS = {
    "BANKING_AGENT_CONTEXT_MEMORY": "enabled",
    "BANKING_AGENT_LLM_MIDDLE_LOOP": "enabled",
    "BANKING_AGENT_LLM_UNDERSTANDING": "llm",
    "BANKING_AGENT_LLM_UNDERSTANDING_MODE": "fuse",
    "BANKING_AGENT_LLM_QUERY_REWRITE": "llm",
    "BANKING_AGENT_LLM_CLARIFICATION": "llm",
    "BANKING_AGENT_RESPONSE_GENERATOR": "llm",
    "BANKING_AGENT_RECOMMENDATION_RESPONSE_GENERATOR": "llm",
}


def active_delivery_profile() -> str | None:
    """Return the requested profile, rejecting unknown production settings."""

    selected = os.environ.get("BANKING_AGENT_DELIVERY_PROFILE", "baseline").strip().lower()
    if selected in {"", "baseline"}:
        return None
    if selected == FROZEN_20261023:
        return selected
    raise ValueError("banking_agent_delivery_profile_must_be_baseline_or_frozen_20261023")


def delivery_setting(name: str, baseline_default: str) -> str:
    """Use an explicit environment value, then the selected profile, then baseline.

    This deliberately does not synthesize provider credentials or a model name.
    A frozen profile therefore fails closed at startup if its required external
    LLM configuration is missing rather than silently changing to mock output.
    """

    if name in os.environ:
        return os.environ[name]
    if active_delivery_profile() == FROZEN_20261023:
        return _FROZEN_20261023_DEFAULTS.get(name, baseline_default)
    return baseline_default
