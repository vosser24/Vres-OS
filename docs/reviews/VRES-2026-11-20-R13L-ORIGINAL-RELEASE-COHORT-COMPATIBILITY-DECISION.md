# Vres-OS — R13L original Claude strict-stage/release-cohort compatibility hold

2026-11-20 | AUTHOR-SIDE SOURCE ONLY | NOT_RUN | NOT_APPLIED | NO INDEPENDENT RELEASE APPROVAL

## Why this integrated source gate is needed

The R13D–R13K original Claude Code CLI + original FastMCP companion uses the original `hooks.user_prompt` and `session_prompts.stage_user_instruction`. That stage calls `vres.stage_strict_user_input` in migration 043; later observed host turn and compatible signature/body semantics were revised by migration 047. Original migration 042 adds latest-observation/control precedence; 044-046 alter the same writer/cancellation/session-binding sequence. The original `src/vres_os/release_inputs.py` still accepts ONLY the previously released 001–041 hash-pinned SQL files and refuses anything newer. Therefore current source and packaged release cohort are structurally incompatible. This is a static mismatch, not a real DB outcome.

R13L adds an explicit **negative release-cohort prerequisite** inside the ORIGINAL `release_input_problems` validator (after its existing P0 source interlock, before source scan). It names the COMPLETE prospective SQL 042–047 cohort and required minimum 047 rather than silently permitting an intermediate partial release; it reports the missing accepted pins in an actionable source-level diagnostic. It intentionally **does not add or approve any SQL pin, remove 048, change live schema, run diagnostics, bypass the original release owner or lift holds**. The original release path still refuses the 048 file. The exact live migration ledger remains unknown under Schema-048 NO PostgreSQL EVEN SELECT.

## Exact source observations for independent reviewer

- `src/vres_os/session_prompts.py`: `_stage_entry` invokes `vres.stage_strict_user_input` with `STRICT_STAGE_CONTRACT`.
- `src/vres_os/hooks.py`: `user_prompt` first establishes `begin_reply_turn`, then blocks when strict staging is unavailable; a current 041 database cannot supply the 043/047 contract.
- `src/vres_os/migrations/042_latest_observed_user_input_control_precedence.sql`: original observation precedence.
- `043_legacy_observation_commit_quarantine.sql`: strict writer stage and quarantine.
- `044_original_current_turn_atomic_cancellation.sql`, `045_original_bound_task_cancellation_r13a.sql`, `046_original_observation_rebind_quarantine_r13b.sql`, `047_original_cancel_observed_turn_and_validation_r13c.sql`: integrated source history; no retroactive rewriting of immutable historical SQL.
- `048_original_task_terminal_hold_r13f.sql`: source-only prospective denial; number/ledger collision unverified, no rename/apply authority.
- `src/vres_os/release_inputs.py`: release 001–041 pins unchanged; new explicit held-cohort diagnostic.
- `src/vres_os/release_artifact.py`, original `install.ps1`, `update.ps1` and `w4-operations-holds.json`: original release, staging, Git and Windows holds unchanged.

## Required next decision, NOT YET GRANTED

A genuinely distinct, attributable GitHub reviewer must assess whether to publish an independently trusted exact release that:
1. Preserves immutable 001–041 migration hashes and obtains verifiable evidence for any live 042–048 ledger or collision **without currently contacting PostgreSQL**.
2. Resolves whether historical prospective 048 is compatible with the REAL database ledger, and whether new numbered SQL is needed (only after incident clearance); do not just rename or bypass it.
3. Audits writer/runtime permission closure across 042–048, existing Chairman/model tool cancellation authority, fail-closed Claude hooks and actual compatible host version; determines which repairs MUST be in the approved source and SQL pin set.
4. Separately validates original offline source/wheels/publisher/NTFS/installer/update.ps1 and rollback, and confirms ONE same October managed Windows installation remains the only installed application.
5. Explicitly scopes first isolated offline Python AST/compile/pytest approval, then separately PostgreSQL/host/Windows/UAT clearance. The source gate itself does not perform any of those operations.

## Status / safeguards / provenance

GitHub source-only R13L changes include only original `release_inputs.py`, authored static test and this detailed review. No execution, AST, compile, pytest, SQL, PostgreSQL (even SELECT), native Claude Code/FastMCP/hooks, Windows git/preflight/update, installed release, credentials/profile or real PRISM/legacy/UAT has been performed. Prior historical 732/732 pytest and 407/407 compile evidence belongs to older 9e2b538b only. R13D–R13L all NOT_RUN.

Issue #185 currently OPEN with 14 owner-authored comments and no independently attributable positive THREAT_MODEL / RELEASE_DESIGN / OPERATIONS verdict; Claude Fable 5.2's unsigned REVISE/DESIGN_REVISE/BLOCKED advisory is only advisory. No PR: .github/workflows/ci.yml has pull_request PostgreSQL and tests. No protected main/R13 merge. Preserve original V-01..V-42/M0..M8/W0..W3/W4, personal one-user CLI + MCP Chairman, real task resume/results/experience, original release/recovery architecture. P0 Schema-048 and host-hook incidents both OPEN; F1/Fable positive NOT_GRANTED.

Next practical milestone is **real attributable review and incident evidence**, not automatic source migration pin promotion, local Windows updates or an invented PASS. No asynchronous handoff is claimed.
