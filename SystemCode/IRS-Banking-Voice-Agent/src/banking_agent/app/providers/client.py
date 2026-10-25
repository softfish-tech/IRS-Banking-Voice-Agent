"""OpenAI-compatible structured-output transport with safe operational limits."""

import asyncio
import hashlib
import json
from collections.abc import Awaitable, Callable, Mapping
from time import monotonic
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from pydantic import ValidationError

from .errors import ProviderErrorCode, ProviderTransportError
from .interfaces import LLMRequest, LLMResult, ResponseModel
from .mock import MockLLMClient
from .privacy import SensitiveDataBlocked, SensitiveDataGuard
from .settings import LLMSettings

TelemetrySink = Callable[[Mapping[str, object]], None]


class UrlLibJsonTransport:
    """Minimal server-side HTTPS transport; no browser code or persistence."""

    async def complete(self, url: str, headers: Mapping[str, str], payload: Mapping[str, Any], timeout: float) -> Mapping[str, Any]:
        def send() -> Mapping[str, Any]:
            request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=dict(headers), method="POST")
            try:
                with urlopen(request, timeout=timeout) as response:  # noqa: S310 - URL is validated in settings.
                    body = json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                if exc.code == 429:
                    raise ProviderTransportError(ProviderErrorCode.RATE_LIMITED) from None
                if 500 <= exc.code <= 599:
                    raise ProviderTransportError(ProviderErrorCode.UNAVAILABLE) from None
                raise ProviderTransportError(ProviderErrorCode.INVALID_RESPONSE) from None
            except (URLError, OSError, ValueError, json.JSONDecodeError):
                raise ProviderTransportError(ProviderErrorCode.UNAVAILABLE) from None
            if not isinstance(body, dict):
                raise ProviderTransportError(ProviderErrorCode.INVALID_RESPONSE)
            return body

        return await asyncio.to_thread(send)


class OpenAICompatibleClient:
    def __init__(self, settings: LLMSettings, *, transport: Any | None = None, telemetry: TelemetrySink | None = None, privacy_guard: SensitiveDataGuard | None = None) -> None:
        settings.validate()
        if settings.provider != "openai_compatible":
            raise ValueError("OpenAICompatibleClient requires openai_compatible settings")
        self._settings, self._transport, self._telemetry = settings, transport or UrlLibJsonTransport(), telemetry
        self._privacy_guard = privacy_guard or SensitiveDataGuard()
        self._semaphore = asyncio.Semaphore(settings.max_concurrency)
        self._rate_lock, self._next_request_at = asyncio.Lock(), 0.0
        self._idempotency_lock = asyncio.Lock()
        self._in_flight: dict[str, tuple[str, asyncio.Future[LLMResult]]] = {}
        self._completed: dict[str, tuple[float, str, LLMResult]] = {}

    async def _wait_for_rate_slot(self) -> None:
        async with self._rate_lock:
            now = monotonic()
            wait = max(0.0, self._next_request_at - now)
            self._next_request_at = max(now, self._next_request_at) + 60 / self._settings.requests_per_minute
        if wait:
            await asyncio.sleep(wait)

    def _emit(self, request_id: str, outcome: str, attempts: int, started: float) -> None:
        if self._telemetry is None:
            return
        try:
            self._telemetry({"request_id": request_id, "provider": self._settings.provider, "outcome": outcome, "attempts": attempts, "duration_ms": round((monotonic() - started) * 1000)})
        except Exception:
            pass

    @staticmethod
    def _usage(raw: Mapping[str, Any]) -> dict[str, int | None]:
        """Extract only numeric provider usage; malformed/missing usage is absent."""
        usage = raw.get("usage")
        if not isinstance(usage, Mapping):
            return {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}
        def value(name: str) -> int | None:
            item = usage.get(name)
            return item if type(item) is int and item >= 0 else None
        return {
            "prompt_tokens": value("prompt_tokens"),
            "completion_tokens": value("completion_tokens"),
            "total_tokens": value("total_tokens"),
        }

    @staticmethod
    def _fingerprint(request: LLMRequest, response_model: type[ResponseModel]) -> str:
        # Fingerprints are process-local comparison values only; never log or
        # persist them because they are derived from prompts.
        material = request.model_dump_json(exclude={"idempotency_key"}) + response_model.model_json_schema().__repr__()
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    async def _generate_once(
        self, request: LLMRequest, response_model: type[ResponseModel], request_id: str
    ) -> LLMResult:
        started = monotonic()
        payload = {"model": request.model, "messages": [message.model_dump() for message in request.messages], "max_tokens": request.max_output_tokens, "temperature": request.temperature, "response_format": {"type": "json_object"}}
        headers = {"Authorization": f"Bearer {self._settings.api_key}", "Content-Type": "application/json", "Idempotency-Key": request.idempotency_key or request_id}
        attempts = 0
        async with self._semaphore:
            while True:
                attempts += 1
                try:
                    await self._wait_for_rate_slot()
                    raw = await asyncio.wait_for(self._transport.complete(f"{self._settings.base_url}/chat/completions", headers, payload, self._settings.timeout_seconds), self._settings.timeout_seconds)
                    content = raw["choices"][0]["message"]["content"]
                    decoded = json.loads(content) if isinstance(content, str) else content
                    validated = response_model.model_validate(decoded)
                    self._emit(request_id, "ok", attempts, started)
                    return LLMResult(
                        request_id=request_id, status="ok", data=validated.model_dump(mode="json"),
                        attempts=attempts, **self._usage(raw),
                    )
                except TimeoutError:
                    code = ProviderErrorCode.TIMEOUT
                except ProviderTransportError as error:
                    code = error.code
                except (KeyError, IndexError, TypeError, ValueError, ValidationError, json.JSONDecodeError):
                    code = ProviderErrorCode.INVALID_RESPONSE
                if code in {ProviderErrorCode.TIMEOUT, ProviderErrorCode.UNAVAILABLE, ProviderErrorCode.RATE_LIMITED} and attempts <= self._settings.max_retries:
                    await asyncio.sleep(0.1 * attempts)
                    continue
                self._emit(request_id, "error", attempts, started)
                return LLMResult(request_id=request_id, status="error", error_code=code, attempts=attempts)

    async def generate(self, request: LLMRequest, response_model: type[ResponseModel]) -> LLMResult:
        try:
            request = self._privacy_guard.sanitize(request)
        except SensitiveDataBlocked:
            return LLMResult(request_id=str(uuid4()), status="error", error_code=ProviderErrorCode.SENSITIVE_DATA_BLOCKED)
        if request.idempotency_key is None:
            return await self._generate_once(request, response_model, str(uuid4()))

        key, fingerprint = request.idempotency_key, self._fingerprint(request, response_model)
        now = monotonic()
        async with self._idempotency_lock:
            self._completed = {
                cached_key: item for cached_key, item in self._completed.items() if item[0] > now
            }
            cached = self._completed.get(key)
            if cached is not None:
                _, cached_fingerprint, result = cached
                if cached_fingerprint != fingerprint:
                    return LLMResult(request_id=str(uuid4()), status="error", error_code=ProviderErrorCode.IDEMPOTENCY_CONFLICT)
                return result
            active = self._in_flight.get(key)
            if active is not None:
                active_fingerprint, future = active
                if active_fingerprint != fingerprint:
                    return LLMResult(request_id=str(uuid4()), status="error", error_code=ProviderErrorCode.IDEMPOTENCY_CONFLICT)
                return await asyncio.shield(future)
            future: asyncio.Future[LLMResult] = asyncio.get_running_loop().create_future()
            self._in_flight[key] = (fingerprint, future)

        try:
            result = await self._generate_once(request, response_model, str(uuid4()))
            if not future.done():
                future.set_result(result)
            if result.status == "ok":
                async with self._idempotency_lock:
                    self._completed[key] = (monotonic() + self._settings.idempotency_ttl_seconds, fingerprint, result)
            return result
        except asyncio.CancelledError:
            if not future.done():
                future.cancel()
            raise
        finally:
            async with self._idempotency_lock:
                active = self._in_flight.get(key)
                if active is not None and active[1] is future:
                    self._in_flight.pop(key, None)


def create_llm_client(settings: LLMSettings, *, telemetry: TelemetrySink | None = None):
    """Compose only E-owned provider infrastructure; callers own semantics."""
    settings.validate()
    if settings.provider == "mock":
        return MockLLMClient()
    return OpenAICompatibleClient(settings, telemetry=telemetry)
