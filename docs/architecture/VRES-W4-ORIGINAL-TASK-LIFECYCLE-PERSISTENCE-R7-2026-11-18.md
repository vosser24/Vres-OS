# 2026-11-18 — Original task lifecycle direct persistence boundary R-7

**SOURCE-ONLY author remediation. Python/AST/compile/pytest NOT_RUN. Security review #185 OPEN. Nothing authorizes PostgreSQL, native Claude/FastMCP/hooks, Windows execution, installation or release.**

## Static R-6 finding

In the ORIGINAL `src/vres_os/task_lifecycle.py`, `transition_task_status` persisted `reason` within `TASK_STATUS_CHANGED` event JSON using `redact()` (display-only redaction), instead of `redact_for_persistence()`. For example, `password=abc,def` may be display-masked as `password=[REDACTED],def`, leaving a credential-like tail in the persisted event. This conclusion follows from source redaction rules, **not** from PostgreSQL observation or a runtime test. A direct lifecycle writer does not automatically inherit Repository method-level redaction.

The same transition previously sent user-supplied structural `task_key` and `provider_session_id` into direct SQL without invoking the Repository's existing tainted-identity guard. These are authority/join identifiers and must not be silently masked.

## Minimal R-7 change

1. Reuse the original Repository `_persist_identity_unmodified` validation BEFORE cancellation instruction handling or database connections; reject tainted task/session identities without echoing their raw values.
2. Apply the existing canonical `redact_for_persistence` to the COMPLETE status-transition reason before constructing event JSON or the result, suppressing entire unsafe fields rather than partially displaying/masking them.
3. Preserve original lifecycle transition rules, validation invalidation, explicit current-user cancellation provenance, session locking/unbinding, focus selection, returned status fields, SQL schema and original CLI/FastMCP owners.
4. Author synthetic fake-connection tests for partial-mask tail suppression, session/task identity pre-connect rejection and clean transition behavior. **Tests AUTHORED NOT_RUN.**

**Limitations:** this is preventive source remediation; real transaction behavior, existing DB rows, other direct writers (including session lifecycle), exception/log/outbound pathways and original Claude session integration remain unverified. No independent attributable THREAT_MODEL / RELEASE_DESIGN / OPERATIONS verdict has been received.

**ABSOLUTE HOLDS:** `LIVE_SCHEMA_048_INCIDENT=OPEN` — no PostgreSQL even SELECT; `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN` — no installed native Claude Code/FastMCP/hooks. F1/Fable positive authority not granted. No P3, Windows Git L2, R13/main merge, stage/release/install/update/UAT, installed P2, credential/profile, real legacy/PRISM or TASK-DAY-01 actions. Historical 732/732 guarded PASS belongs only to old source `9e2b538b`, never R-7.

**Owner design:** one original PERSONAL Windows companion to Claude CLI with original FastMCP, Chairman, Repository, tasks/sessions/results/history and original installation/update/recovery; no new GUI, task store, installer or enterprise IAM.
