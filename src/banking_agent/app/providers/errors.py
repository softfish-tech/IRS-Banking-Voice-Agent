"""Sanitized provider failures. Never expose vendor payloads or credentials."""

from enum import StrEnum


class ProviderErrorCode(StrEnum):
    CONFIGURATION = "configuration"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"
    INVALID_RESPONSE = "invalid_response"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    SENSITIVE_DATA_BLOCKED = "sensitive_data_blocked"


class ProviderTransportError(Exception):
    """Internal transport error with a safe, provider-neutral classification."""

    def __init__(self, code: ProviderErrorCode) -> None:
        self.code = code
        super().__init__(code.value)
