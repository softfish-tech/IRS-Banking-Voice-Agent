import unittest
import asyncio

from pydantic import BaseModel, Field

from banking_agent.app.providers.client import OpenAICompatibleClient
from banking_agent.app.providers.errors import ProviderErrorCode, ProviderTransportError
from banking_agent.app.providers.interfaces import LLMMessage, LLMRequest
from banking_agent.app.providers.mock import MockLLMClient
from banking_agent.app.providers.settings import LLMSettings


class Payload(BaseModel):
    label: str = Field(min_length=1)


def request(*, idempotency_key: str | None = None, content: str = "synthetic prompt") -> LLMRequest:
    return LLMRequest(model="synthetic-model", messages=(LLMMessage(role="user", content=content),), idempotency_key=idempotency_key)


class FailingThenValidTransport:
    def __init__(self): self.calls = 0
    async def complete(self, *_):
        self.calls += 1
        if self.calls == 1: raise ProviderTransportError(ProviderErrorCode.UNAVAILABLE)
        return {"choices": [{"message": {"content": '{"label":"valid"}'}}]}


class ValidTransport:
    def __init__(self): self.calls, self.headers, self.payloads = 0, [], []
    async def complete(self, _, headers, payload, *__):
        self.calls += 1
        self.headers.append(dict(headers))
        self.payloads.append(dict(payload))
        await asyncio.sleep(0)
        return {"choices": [{"message": {"content": '{"label":"valid"}'}}]}


class LLMProviderGatewayTests(unittest.IsolatedAsyncioTestCase):
    async def test_mock_validates_structured_output_without_network(self):
        client = MockLLMClient([{"label": "valid"}])
        result = await client.generate(request(), Payload)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.data, {"label": "valid"})

    async def test_mock_rejects_invalid_structured_output(self):
        result = await MockLLMClient([{"label": ""}]).generate(request(), Payload)
        self.assertEqual(result.error_code, ProviderErrorCode.INVALID_RESPONSE)

    async def test_retries_sanitized_transport_failure_and_emits_no_prompt(self):
        events = []
        transport = FailingThenValidTransport()
        settings = LLMSettings(provider="openai_compatible", base_url="https://example.test", api_key="server-only", max_retries=1)
        result = await OpenAICompatibleClient(settings, transport=transport, telemetry=events.append).generate(request(), Payload)
        self.assertEqual(result.status, "ok")
        self.assertEqual(transport.calls, 2)
        self.assertEqual(events[0]["outcome"], "ok")
        self.assertNotIn("prompt", events[0])
        self.assertNotIn("server-only", str(events[0]))

    def test_production_settings_require_https_and_server_key(self):
        with self.assertRaises(ValueError):
            LLMSettings(provider="openai_compatible", base_url="http://localhost", api_key="x").validate()
        with self.assertRaises(ValueError):
            LLMSettings(provider="openai_compatible", base_url="https://example.test").validate()

    async def test_idempotency_coalesces_duplicates_caches_success_and_reuses_provider_key(self):
        transport = ValidTransport()
        settings = LLMSettings(provider="openai_compatible", base_url="https://example.test", api_key="server-only")
        client = OpenAICompatibleClient(settings, transport=transport)
        first, duplicate = await asyncio.gather(
            client.generate(request(idempotency_key="opaque-operation-1"), Payload),
            client.generate(request(idempotency_key="opaque-operation-1"), Payload),
        )
        cached = await client.generate(request(idempotency_key="opaque-operation-1"), Payload)
        self.assertEqual(transport.calls, 1)
        self.assertEqual(first, duplicate)
        self.assertEqual(first, cached)
        self.assertEqual(transport.headers, [{"Authorization": "Bearer server-only", "Content-Type": "application/json", "Idempotency-Key": "opaque-operation-1"}])

    async def test_rejects_reuse_of_a_key_for_different_logical_request(self):
        transport = ValidTransport()
        settings = LLMSettings(provider="openai_compatible", base_url="https://example.test", api_key="server-only")
        client = OpenAICompatibleClient(settings, transport=transport)
        await client.generate(request(idempotency_key="opaque-operation-1"), Payload)
        conflict = await client.generate(request(idempotency_key="opaque-operation-1", content="different synthetic prompt"), Payload)
        self.assertEqual(conflict.status, "error")
        self.assertEqual(conflict.error_code, ProviderErrorCode.IDEMPOTENCY_CONFLICT)
        self.assertEqual(transport.calls, 1)

    async def test_blocks_credentials_before_mock_or_provider_transport(self):
        mock = MockLLMClient([{"label": "valid"}])
        result = await mock.generate(request(content="My OTP is 123456"), Payload)
        self.assertEqual(result.error_code, ProviderErrorCode.SENSITIVE_DATA_BLOCKED)
        self.assertEqual(mock.requests, [])

        transport = ValidTransport()
        client = OpenAICompatibleClient(
            LLMSettings(provider="openai_compatible", base_url="https://example.test", api_key="server-only"),
            transport=transport,
        )
        result = await client.generate(request(content="CVV: 123"), Payload)
        self.assertEqual(result.error_code, ProviderErrorCode.SENSITIVE_DATA_BLOCKED)
        self.assertEqual(transport.calls, 0)

    async def test_pseudonymizes_identifiers_before_provider_call_and_cache_key(self):
        transport = ValidTransport()
        client = OpenAICompatibleClient(
            LLMSettings(provider="openai_compatible", base_url="https://example.test", api_key="server-only"),
            transport=transport,
        )
        result = await client.generate(
            request(idempotency_key="opaque-operation-privacy", content="Email jane@example.com, call +65 8123 4567; card 4111 1111 1111 1111."),
            Payload,
        )
        self.assertEqual(result.status, "ok")
        sent = str(transport.payloads[0])
        self.assertNotIn("jane@example.com", sent)
        self.assertNotIn("8123 4567", sent)
        self.assertNotIn("4111 1111 1111 1111", sent)
        self.assertIn("[EMAIL_1]", sent)
        self.assertIn("[PHONE_1]", sent)
        self.assertIn("[CARD_REF_1]", sent)
