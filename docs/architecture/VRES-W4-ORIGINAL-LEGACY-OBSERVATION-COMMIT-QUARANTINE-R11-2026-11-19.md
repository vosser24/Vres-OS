# Vres-OS W4 R-11 original historical observation quarantine

STATUS: SOURCE ONLY; TESTS NOT_RUN, migration 043 NOT_APPLIED. One original Claude Code CLI/FastMCP/Chairman/Repository, no Tk GUI or second store/runtime/installer. Preserve V-01..V-42 and full original roadmaps.

## Concrete original findings

- P1: applied migration 023 may propagate raw historical obs.text/question/tool_use_id into task events, latest task state, SQL return and committed metadata. R8 redaction is not retroactive; no real leakage incident is asserted.
- P1: migration 042's new function is omitted from original activate_boundary writer grants. R11 conditionally grants it solely to the trusted writer, retaining PUBLIC/runtime revocation.

## Prospective original-schema-safe correction

Migration 043 adds nullable strict_persistence_stage_version to the ORIGINAL user_input_observations ledger. All historical observations remain unverified (NULL). New versioned original SQL stage delegates to original 029 stage under its active session lock, then marks the just-created row under the same transaction; Python only uses this route after redact_for_persistence. The marker is a trusted-writer route assertion, not a secret or independently verified sanitization certificate.

The same original vres.commit_user_inputs signature/body is prospectively replaced to propagate only version-1 strict observations verbatim. For unverified pending observations, new task events and function return contain the fixed [UNVERIFIED_LEGACY_USER_INPUT_HELD] marker; their question/tool IDs are not copied, task_state latest instruction uses that fixed marker for an unverified instruction, and derived committed tool IDs exclude unverified rows. Existing applied migrations 023/029/032 remain untouched. Old callers continue to stage but cannot certify history. Full normal strict new task continuity remains.

## Residual risk and holds

Historical raw observations, previous task events/state and past session metadata are NOT cleaned or verified; no destructive operation permitted. Compromised trusted writer, unknown secret formats, missing/misordered host turns and cancellation writer-to-status split transaction remain unresolved P0/P1. Legacy pending user intent is deliberately held; after all approvals the operator can reassert it in a new trusted turn. #185 current R11 independent attributable 3-part review absent; migration ownership/grants/concurrency/source and original installer/update compatibility require independent review. New Python AST/compile/pytest, SQL, Windows, native Claude/FastMCP/hooks, UAT all NOT_RUN. Historical 732/732 PASS only old 9e2b538b.

Absolute holds unchanged: LIVE_SCHEMA_048_INCIDENT=OPEN (NO PostgreSQL even SELECT); HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN (NO native Claude/installed FastMCP/hooks); F1/Fable NOT_GRANTED; P3/Windows Git L2/R13/main merges, profiles/credentials, protected installed P2, PRISM/legacy/TASK-DAY-01, installer/update/recovery/real UAT/rollback held. No host access or migration application.