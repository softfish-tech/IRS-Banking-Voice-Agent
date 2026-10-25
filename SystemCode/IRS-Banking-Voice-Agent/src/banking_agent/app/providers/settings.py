"""Server-only, non-secret provider configuration parsing."""

import os
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class LLMSettings:
    provider: str = "mock"
    base_url: str | None = None
    api_key: str | None = None
    timeout_seconds: float = 15.0
    max_retries: int = 2
    max_concurrency: int = 4
    requests_per_minute: int = 60
    idempotency_ttl_seconds: int = 300

    @classmethod
    def from_environment(cls) -> "LLMSettings":
        provider = os.environ.get("BANKING_AGENT_LLM_PROVIDER", "mock").strip().lower()
        base_url = os.environ.get("BANKING_AGENT_LLM_BASE_URL")
        api_key = os.environ.get("BANKING_AGENT_LLM_API_KEY")
        settings = cls(
            provider=provider,
            base_url=base_url.strip().rstrip("/") if base_url else None,
            api_key=api_key,
            timeout_seconds=float(os.environ.get("BANKING_AGENT_LLM_TIMEOUT_SECONDS", "15")),
            max_retries=int(os.environ.get("BANKING_AGENT_LLM_MAX_RETRIES", "2")),
            max_concurrency=int(os.environ.get("BANKING_AGENT_LLM_MAX_CONCURRENCY", "4")),
            requests_per_minute=int(os.environ.get("BANKING_AGENT_LLM_REQUESTS_PER_MINUTE", "60")),
            idempotency_ttl_seconds=int(os.environ.get("BANKING_AGENT_LLM_IDEMPOTENCY_TTL_SECONDS", "300")),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.provider not in {"mock", "openai_compatible"}:
            raise ValueError("BANKING_AGENT_LLM_PROVIDER must be mock or openai_compatible")
        if self.timeout_seconds <= 0 or self.max_retries < 0 or self.max_retries > 3:
            raise ValueError("Invalid LLM timeout or retry configuration")
        if self.max_concurrency < 1 or self.requests_per_minute < 1 or not 1 <= self.idempotency_ttl_seconds <= 3600:
            raise ValueError("LLM concurrency and rate limits must be positive")
        if self.provider == "openai_compatible":
            if not self.base_url or not self.api_key:
                raise ValueError("OpenAI-compatible provider requires server-side base URL and API key")
            parsed = urlparse(self.base_url)
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValueError("LLM base URL must be an HTTPS URL")
