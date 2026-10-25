"""Deterministic, network-free structured LLM client for CI and owner tests."""

from collections import deque
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ValidationError

from .errors import ProviderErrorCode
from .interfaces import LLMRequest, LLMResult, ResponseModel
from .privacy import SensitiveDataBlocked, SensitiveDataGuard


class MockLLMClient:
    def __init__(self, responses: Sequence[Mapping[str, Any]] = (), *, privacy_guard: SensitiveDataGuard | None = None) -> None:
        self._responses = deque(dict(item) for item in responses)
        self._privacy_guard = privacy_guard or SensitiveDataGuard()
        self.requests: list[LLMRequest] = []

    async def generate(self, request: LLMRequest, response_model: type[ResponseModel]) -> LLMResult:
        request_id = str(uuid4())
        try:
            request = self._privacy_guard.sanitize(request)
        except SensitiveDataBlocked:
            return LLMResult(request_id=request_id, status="error", error_code=ProviderErrorCode.SENSITIVE_DATA_BLOCKED)
        self.requests.append(request)
        if not self._responses:
            return LLMResult(request_id=request_id, status="error", error_code=ProviderErrorCode.UNAVAILABLE)
        try:
            validated = response_model.model_validate(self._responses.popleft())
        except (ValidationError, TypeError, ValueError):
            return LLMResult(request_id=request_id, status="error", error_code=ProviderErrorCode.INVALID_RESPONSE)
        return LLMResult(request_id=request_id, status="ok", data=validated.model_dump(mode="json"), attempts=1)
