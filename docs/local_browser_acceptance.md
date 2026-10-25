# Local browser acceptance checklist

This is a local-development acceptance checklist for the authenticated
SafeBank browser surface. Use only the synthetic profiles and synthetic text
provided by the app. It is intentionally separate from the frozen evaluation:
checking a UI build must not overwrite or reinterpret a frozen artifact.

## Preconditions

1. Start the local service in production mode.
2. Create or sign in to a synthetic account bound to `session-001`.
3. For tests involving LLM wording or contextual resolution, ensure the
   configured LLM provider responds before judging the product behaviour.

## Conversation paths

| ID | Browser steps | Expected public result |
| --- | --- | --- |
| B-01 | Ask `Which currencies are supported for card transactions?` | A grounded `ANSWER`; expanding **View evidence** shows readable excerpts, not internal document IDs. |
| B-02 | Ask `How much does it cost to replace my card?`, then `Because it is damaged.` | First turn is a focused `CLARIFY` for the replacement reason; second turn answers the damaged-card fee with grounded evidence. |
| B-03 | Ask the same first question, then `What about my transfer?` | The agent does not carry the card-fee subject into the new topic; it asks only for the missing transfer detail. |
| B-04 | Ask `My debit card was lost or stolen.`; then ask a fee or delivery follow-up. | The initial turn is an escalation/handoff and later turns do not weaken that route into a policy answer. |
| B-05 | Ask `I do not recognise this card fee.`; then ask for a savings-product recommendation. | Complaint handling remains active and the recommendation is safely blocked. |
| B-06 | With a fresh `session-001` conversation, ask `Which savings product would you recommend for me?` | A recommendation is shown without a redundant consent question; recommendations come from the bound synthetic profile. |
| B-07 | After B-06, ask `Please show the recommendation again.` | The same conversation retains its bound profile and produces a recommendation again. |
| B-08 | Start a new conversation after B-04 or B-05, then ask B-06. | The old handoff/complaint state does not leak to the new conversation; the profile remains bound to the signed-in account. |

## UI and session paths

| ID | Browser steps | Expected public result |
| --- | --- | --- |
| U-01 | Send any synthetic question. | The user bubble appears immediately, then a visible thinking state, followed by a single assistant bubble. |
| U-02 | Reload after a completed turn, select the saved conversation, and continue it. | The message history, versioned conversation, and relevant state are restored; no duplicate turn is created. |
| U-03 | Restart the local service, open the same page. | The UI starts on sign-in; an old browser session is not silently retained. |
| U-04 | Try an invalid username/password or invalid registration input. | The UI shows a specific validation/authentication message rather than a raw API error. |
| U-05 | When voice is not configured, inspect the voice control. | The UI clearly reports that local voice input is unavailable and does not create an empty chat turn. |

## Interpretation

- B-02, B-03, B-04, B-05, and B-08 are the state/context safety checks.
- B-06 and B-07 are the positive recommendation checks missing from the
  frozen multi-turn semantic fixture.
- A provider timeout, malformed LLM output, or unavailable local model is a
  runtime observation. Record it separately from a decision-policy failure;
  do not claim that a timed-out turn passed its behavioural check.
