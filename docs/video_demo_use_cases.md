# NovaGuide video demo use cases

This is a recording script for the local NovaGuide prototype. It is a product
demonstration, not a rerun of the frozen evaluation. Use only the synthetic
local account and data supplied by the app.

## Before recording

1. Start the local server and sign in with a synthetic account bound to a
   savings profile (for example `session-001`).
2. Use **New conversation** before each numbered demo. Complaint and handoff
   state intentionally persist within one conversation, so they must not carry
   into an independent demo.
3. Keep the evidence panel collapsed until Demo 1, then expand it briefly to
   show readable policy excerpts rather than internal IDs.
4. If demonstrating voice, use the first turn of Demo 1: record it, review the
   transcript, select **Use text**, then send it. The remaining turns can be
   typed to keep the recording short and reliable.

## Recommended four-demo set

### 1. Clarification closes into a grounded answer

**Purpose:** Show voice/text input, targeted clarification, recent-turn context
resolution, RAG grounding, and a concise final answer.

| Turn | Say or type | Expected visible behaviour |
| --- | --- | --- |
| 1 | `How much does it cost to replace my card?` | NovaGuide asks why the card needs replacing; it must not guess a fee. |
| 2 | `It was damaged.` | It resolves the short reply against the prior clarification and answers the damaged-card replacement question. |
| 3 | `What should I do now?` | It keeps the damaged-card context and explains the next safe policy step. |

**Narration:** “The assistant does not infer a reason-specific policy from an
ambiguous question. After the customer provides the missing reason, it retrieves
and presents only evidence relevant to that branch.”

**Show:** The question bubble appears immediately, the thinking state, final
answer, then **View evidence**. Do not present the exact wording as fixed—the
grounded facts and safe route are the acceptance point.

### 2. Complaint state prevents inappropriate recommendation

**Purpose:** Show complaint handling, multi-turn state persistence, and the
recommendation safety gate.

| Turn | Say or type | Expected visible behaviour |
| --- | --- | --- |
| 1 | `I do not recognise this card fee.` | A support-request/complaint response confirms a simulated case is open. |
| 2 | `Can I challenge that?` | The case remains open; NovaGuide does not invent a waiver or outcome. |
| 3 | `Can you recommend a savings product?` | Recommendation is unavailable while the complaint is unresolved. No products are shown. |

**Narration:** “The complaint state is an explicit rule-controlled state, not
an LLM guess. It prevents a marketing recommendation while the customer’s case
is still unresolved.”

### 3. A current fraud report overrides an earlier benign topic

**Purpose:** Show that high-risk safety signals take priority over conversation
history and that escalation persists.

| Turn | Say or type | Expected visible behaviour |
| --- | --- | --- |
| 1 | `What is the replacement-card fee?` | A focused clarification asks for the replacement reason. |
| 2 | `Someone used my card without permission.` | The prior card-fee flow is interrupted; NovaGuide records a simulated human-assistance handoff. |
| 3 | `Can I freeze it now?` | The handoff remains active; it does not fall back into a normal policy or product route. |

**Narration:** “A current unauthorised-use report has priority over ordinary
policy context. The system escalates and retains that safety route across later
turns.”

### 4. Profile-backed recommendation in a clean conversation

**Purpose:** Show the positive recommendation route, profile binding, and
recommendation continuity without exposing fixture eligibility details.

| Turn | Say or type | Expected visible behaviour |
| --- | --- | --- |
| 1 | `Which savings product would you recommend for me?` | A recommendation card and a ranked list of product names appear. The browser must not expose synthetic goal, age, residency, or deposit-rule text. |
| 2 | `Please show the recommendation again.` | The same conversation produces the permitted recommendation again. |

**Narration:** “The product profile was bound when this synthetic account was
created. C permits the route, D ranks eligible products, and the UI presents
only customer-facing product names—not internal fixture reasoning.”

## Optional fifth demo: unsupported-service boundary

Use this only if there is time to show a fifth route.

| Turn | Say or type | Expected visible behaviour |
| --- | --- | --- |
| 1 | `What is the bank policy for crypto wallet recovery?` | A grounded answer explains that cryptocurrency wallet recovery is unsupported. |
| 2 | `Can you recover the crypto for me?` | It retains the unsupported-service boundary and does not invent recovery steps. |

**Narration:** “The system can answer a boundary question from reviewed policy
evidence, while refusing to fabricate a process for an unsupported service.”

## Suggested recording order

Record Demos **1 → 2 → 3 → 4**. This order progresses from helpful assistance,
to complaint protection, to urgent safety escalation, and finishes with a
positive recommendation. It covers `CLARIFY`, `ANSWER`, `HANDLE_COMPLAINT`,
`BLOCK`, `ESCALATE`, RAG evidence, stateful context, profile-backed D output,
and the browser voice-to-text handoff in roughly 4–6 minutes.

If a configured LLM provider times out during a recording, restart that demo in
a new conversation and describe it as a runtime issue, not as a safety-policy
result. Do not use a failed provider call as evidence that a route passed.
