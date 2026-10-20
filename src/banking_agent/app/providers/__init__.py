"""E-owned, provider-neutral LLM transport infrastructure.

This package deliberately has no dependency on A/C domain decisions.  Owners
may use it to obtain validated structured data, then validate and return their
own public module contracts.
"""

from .client import OpenAICompatibleClient, create_llm_client
from .interfaces import LLMClient, LLMMessage, LLMRequest, LLMResult
from .mock import MockLLMClient
from .privacy import SensitiveDataGuard
from .settings import LLMSettings

__all__ = [
    "LLMClient", "LLMMessage", "LLMRequest", "LLMResult", "LLMSettings",
    "MockLLMClient", "OpenAICompatibleClient", "SensitiveDataGuard", "create_llm_client",
]
