"""Public chat DTOs remain stable and hide internal agent implementation data."""

import unittest

from banking_agent.app.api.dto import to_chat_turn_response_v1
from banking_agent.schemas import Action, AgentState, Decision, RetrievedDocument
from banking_agent.schemas.response import AgentResponse, TechnicalError


class PublicApiDtoTests(unittest.TestCase):
    def test_success_hides_state_reason_code_and_document_identifier(self) -> None:
        state = AgentState(
            session_id="session-1", user_text="test",
            decision=Decision(action=Action.ANSWER, reason_code="INTERNAL_REASON"),
        )
        response = AgentResponse(
            request_id="request-1", session_id="session-1", status="ok",
            decision=state.decision, text="Synthetic answer",
            citations=[RetrievedDocument(document_id="internal-doc-id", title="Policy", source="Synthetic", score=.9, excerpt="Private excerpt")],
            state=state,
        )

        payload = to_chat_turn_response_v1(response).model_dump(mode="json")
        self.assertEqual(payload["api_version"], "v1")
        self.assertEqual(payload["message"], {"kind": "answer", "text": "Synthetic answer"})
        self.assertEqual(payload["decision"], {"action": "ANSWER"})
        self.assertEqual(payload["citations"], [{"title": "Policy", "source": "Synthetic", "excerpt": "Private excerpt"}])
        self.assertNotIn("state", str(payload))
        self.assertNotIn("INTERNAL_REASON", str(payload))
        self.assertNotIn("internal-doc-id", str(payload))

    def test_error_uses_a_generic_public_code(self) -> None:
        state = AgentState(session_id="session-1", user_text="test")
        response = AgentResponse(
            request_id="request-1", session_id="session-1", status="error",
            text="The request could not be completed because a module failed. Please try again.",
            error=TechnicalError(module="B", code="timeout"), state=state,
        )

        payload = to_chat_turn_response_v1(response).model_dump(mode="json")
        self.assertEqual(payload["message"]["kind"], "technical_error")
        self.assertEqual(payload["error"], {"code": "agent_unavailable"})
        self.assertNotIn("timeout", str(payload))
        self.assertNotIn("'B'", str(payload))
