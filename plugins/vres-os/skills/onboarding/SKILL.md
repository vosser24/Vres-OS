---
name: onboarding
description: Use when importing a legacy company/project folder or chaotic historical documents into Vres-OS.
---

Bulk onboarding is a funnel, not a million-token reading exercise.

Mechanical first: inventory -> hash -> exact dedupe -> parse by file adapter -> obvious project/version metadata -> mechanical classification.

Escalate only low-confidence, conflicting, high-value, or semantically ambiguous items to model review. Preserve every raw source path/hash/version so knowledge remains traceable. Never overwrite/reorganize the source folder during onboarding.


## Existing software projects

For an established codebase, onboarding always includes the Engineering Architecture Constitution flow:

1. run the deterministic read-only architecture audit without executing the application;
2. identify the proportional architecture profile(s);
3. Chairman creates an incremental reversible alignment plan covering every material finding;
4. mechanically check plan completeness;
5. freeze the exact plan and require protected `vres-os:validator` Fable/high PASS before architecture-changing adoption work or activation.

If protected Fable/high is unavailable, overridden or stale, the plan is BLOCKED. Never substitute another model/reviewer.

#168 owns the full adoption state/KEEP-DROP/scaffold activation. This skill supplies the mandatory architecture-plan contract it must consume.
