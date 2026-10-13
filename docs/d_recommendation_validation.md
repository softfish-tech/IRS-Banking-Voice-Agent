# D validation record — 2026-10-14

## Inputs and scope

- Main ZIP SHA-256: e3d09b01125b83248e07bb7b47511887b25964c76dd5e55d2ed14e67cb0b5499.
- E integration ZIP SHA-256: b4b9125ad928fb10199fd327bb651cb808b862eb87d4dbdf06d8273941de7240.
- Python 3.12.14 / Pydantic 2.13.5, Windows. Project requires Python >=3.11.
- ZIP snapshots contain no Git history. Remote commit IDs, authors, branch merge status and GitHub CI results are not verified.

## Results

| Snapshot | Verification | Passed |
| --- | --- | ---: |
| Original main | Unit schema baseline | 4 |
| Original E | 12 unit + 18 integration + 1 E2E method | 31 |
| Main + D | 45 unit + 3 shared-state integration | 48 |
| E + D | 53 unit + 21 integration + 1 E2E method | 75 |
| E + real D | Explicit adapter/orchestrator replacement checks | 7 |

E's E2E method executes eight S01-S08 subtests; it is not counted as eight separate methods. The real-D replacement method also covers those eight scenarios using scripted A/B/C. No tests are disabled or skipped. Source compilation passes (26 Python files on main+D, 49 on E+D).

The eight async-adapter tests were written before its implementation; the initial focused run failed on the missing adapter. A subsequent fixture-subtype validation issue was corrected while keeping strict validation. The integration checks also verified the canonical consent-patch restriction rather than widening that schema.

## Practical limits

- No code coverage percentage, model accuracy, Recall@5, full mutation score or performance SLA is claimed.
- This run uses Python 3.12; E's checked-in GitHub CI targets Python 3.11 and has not been executed here.
- HTTP tests exercise E's local server; no manual browser visual QA or real voice pipeline was performed.
- D uses a synthetic static catalog and session/profile map. Runtime profile association and the final bank catalog require team review.
- E's default browser mode continues to replay fixtures. Passing replacement tests does not change application composition.
- C/E retain risk and recommendation permission; no shared field/enum or other module implementation changed.

Clean patch application and packaged file integrity are checked during delivery. Machine-specific logs and delivery manifests are supplied separately from repository source.
