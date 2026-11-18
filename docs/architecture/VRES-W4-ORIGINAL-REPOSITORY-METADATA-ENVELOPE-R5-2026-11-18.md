# 2026-11-18 — Original Repository R-5 project metadata and task/session envelope boundary

**GITHUB SOURCE-ONLY AUTHOR CANDIDATE / ALL TESTS AUTHORED NOT_RUN / NO INDEPENDENT SECURITY ACCEPTANCE / NO OPERATIONAL RELEASE AUTHORITY.**

## Exact source-specific gap

Static review of R-4 source `32c9cd13b4bb54cbe361d6c78ea9c6aa6dcb9a6b` found the original `Repository.ensure_project` writing `name`, `root_path`, `remote_url` and `current_branch` directly, despite new strict task/event/checkpoint payload sanitization. Other original Repository writes accepted unsanitized task classification/lead role, event type/actor/session ID, checkpoint reason/creator and close-session reason. A synthetic credential-bearing string in such a field could be inserted without traversing `redact_for_persistence`. **This is a source-observed possibility, not a verified live database leak.**

## Minimal R-5 original-owner correction

- Reuse the existing R-4 `redact_for_persistence` helper in `src/vres_os/repository.py`; no schema, migrations, new storage owner, app, Chairman, runtime, GUI, installer or dependency.
- For project `name`/`remote_url`/`branch` and text reasons in checkpoint/session closure, suppress tainted strings before the original SQL parameters are assembled. Identity-preserving project key and root path are **rejected** if unsafe rather than silently replaced, avoiding accidental project identity aliasing.
- Treat task family/lead role, event type/actor/session ID, Claude provider/session binding keys and historical previous task key as structural join/authority identifiers. Reject tainted values instead of substituting `[REDACTED_UNSAFE_FIELD]` as a shared identifier, preserving exact safe Claude session IDs and explicit task bindings.
- Validate relevant inputs before calling `connect` where possible; any historical task key returned from the DB is checked before binding transition events are inserted.
- Add synthetic fake-connection-only regression candidates for project metadata, identity refusal, event envelopes, task role/family, session-close reason, checkpoint reason and invalid session binding. **Tests have NOT_RUN.**

## Limitations, review and unchanged gates

Strict key/string heuristics are incomplete and may suppress legitimate metadata; unusual valid paths containing credential-shaped text are intentionally rejected. This source candidate does not inspect or repair historical rows; does not certify non-Repository SQL writers, logging/exceptions/returns, direct native host routes, arbitrary unknown secret encodings, real session compatibility or actual runtime. It is not proof of first-FULL V-01..V-42 readiness.

Review must assess identifier false positives, caller behavior on rejected project/session metadata, consistency with original `Repository`, task_resume continuity, R-2/R-3/R-4 and full GitHub issue #185. Genuinely distinct attributable three-part review (`THREAT_MODEL`, `RELEASE_DESIGN`, `OPERATIONS`) remains **NOT_OBTAINED**. Owner-side author analysis is not independent security acceptance.

`LIVE_SCHEMA_048_INCIDENT=OPEN`: NO PostgreSQL even SELECT. `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`: no native Claude/FastMCP installed host/hooks. F1/Fable positive authority NOT_GRANTED; P3, Windows Git L2, R13 stage, main/R13 merge, installed P2, credentials/profile, real project, install/update/recovery and Windows UAT held. No source Python/AST/compile/pytest, PowerShell, DB or host execution performed.

Preserve ONE practical PERSONAL Windows Claude Code CLI-primary + original FastMCP companion with original Chairman/tasks/session/results/history, project/data-source/credentials, experience/governed learning and original consent-based install.ps1/update.ps1/recovery.
