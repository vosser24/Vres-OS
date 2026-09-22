# Vres-OS Finalization — Technical Handoff (2026-09-22)

## Purpose

Authoritative continuation handoff after F-14 onboarding investigation, issue #132 implementation, issue #133 validator-ingestion remediation, #133 merge/install, and migration 035 application.

This supersedes the resume state in `docs/FINALIZATION-HANDOFF-2026-09-21.md` without deleting that historical evidence.

Repository: `vosser24/Vres-OS`

Blocking suite: `docs/FINAL-VERIFICATION.md`
Historical matrix: `docs/LIVE-VERIFICATION.md`

## 1. Executive resume state

- F-00 through F-13: **physically PASS**. Do not rerun unless an owning surface later changes.
- F-14: **in progress**.
- F-15: held until F-14 is formally PASS/REUSED.
- Issue #103: closed/completed.
- Issue #133: closed/completed after PR #134 and green post-merge CI.
- Issue #132: open; BOM fix checkpoint is committed on `issue-132-json-bom`; fresh protected validation of the exact checkpoint is next.
- No new feature work before finalization completes.

## 2. Repository / runtime identity

Authoritative GitHub main:

`59f82e9cb1cedd08eb426e4a83752e21ed9f156b`

This is PR #134 merge: `#133 Prevent interim validator stop from consuming validation`.

PR #134 head:

`4ce5439516b3ea3f301fa044c3fef4707888e705`

CI:
- PR run #329: SUCCESS
- post-merge main run #330: SUCCESS
- full PostgreSQL suite: SUCCESS
- import smoke: SUCCESS
- release gate: SUCCESS

Active installed release:

`20260922134224-aa3f4ebb`

Runtime Python:

`C:\Users\User\AppData\Local\VresOS\releases\20260922134224-aa3f4ebb\venv\Scripts\python.exe`

Verified installed #133 surfaces:
- imported `vres_os.hooks`
- imported `vres_os.validation_audit`
- packaged migration `035_validation_ingestion_deferred_disposition.sql`

Installed verification:
- `INSTALLED_133_HOOK=PASS`
- `INSTALLED_133_AUDIT=PASS`
- `INSTALLED_035_RESOURCE=PASS`

Migration 035 was physically applied with `vres start`.
`vres doctor` then showed PostgreSQL connected with **35 migrations recorded**.

## 3. F-14 reuse audit

Whole-case F-14 reuse was **not eligible** because no complete exact prior LV23–LV27 physical PASS/evidence set was available for review.

Partial reuse remains valid for post-#126 cross-project onboarding path safety because the owning surfaces were unchanged from behavior commit:

`59010df5577e2457c673f74a29e093fbeae9d930`

Relevant audited surfaces:
- `src/vres_os/onboarding.py`
- `src/vres_os/parse_worker.py`
- `src/vres_os/sources.py`
- `src/vres_os/knowledge.py`
- `src/vres_os/embeddings.py`
- `src/vres_os/mcp_server.py`
- `docs/architecture/ONBOARDING.md`
- `plugins/vres-os/skills/onboarding/SKILL.md`

Retained post-#126 evidence:
- A job `MIG-20260921-92b1485d`, source `SRC-d9af2fa52f97`
- B job `MIG-20260921-447da70a`, source `SRC-1d8a4974dbdb`
- same content hash, separate project ownership/provenance

Never use pre-#126 evidence to prove the #125 path boundary.

## 4. F-14 primary fixture

Project:
`C:\Projects\Vres-F14-Onboarding-20260922`

Project id: `8454`

Project key:
`project:af096b7cbdccc820c615f37c`

Embeddings: `embeddings_enabled=false`

Fixture:
`C:\Projects\Vres-F14-Onboarding-20260922\f14_input`

Files:
- `f14_process.txt`
- duplicate `f14_process_copy.txt`
- `f14_analysis.md`
- `f14_table.csv`
- `f14_valid.json`
- malformed `f14_bad.json`
- unsupported `f14_unsupported.rtf`

Created with Windows PowerShell `Set-Content -Encoding utf8`, which produced UTF-8 BOM in this environment.

Pre-hash manifest:
`f14_before_hashes.json`

Do not regenerate, rewrite, normalize, clean, or reset the original fixture.

After-hash comparison is still pending formal F-14 closure.

## 5. F-14 first onboarding result

Job:
`MIG-20260922-c10e90e7`

Observed:
- files_seen 7
- unique_files 4
- duplicates 1
- knowledge_candidates 2
- review_required 3
- chunks_created 2
- embedding_jobs_queued 0
- unsupported_catalogued 0
- no embedding worker

Interpretation:
- duplicate accounting PASS
- malformed input surfaced visibly PASS
- embeddings-disabled behavior PASS
- `.rtf` review is expected; `unsupported_catalogued=0` is not a defect
- counts reconcile: 4 unique + 1 duplicate + 2 parser-error files = 7
- actual defect: valid Windows UTF-8 BOM JSON rejected

## 6. Issue #132

Issue:
**#132 — F-14: Windows UTF-8 BOM JSON is rejected during onboarding**

Physical source:
- project id 8454
- job `MIG-20260922-c10e90e7`

Root cause:
`src/vres_os/ingestion.py::_json()` used `encoding="utf-8"`; Windows PowerShell 5.1 commonly writes a UTF-8 BOM with `Set-Content -Encoding utf8`.

Required behavior:
- ordinary UTF-8 JSON parses
- UTF-8 BOM JSON parses
- malformed BOM JSON still rejects
- size bound unchanged
- source bytes never rewritten
- one decoded text value is used for both `json.loads` and returned document text
- no #132 migration

Checkpoint branch:
`issue-132-json-bom`

Checkpoint base:
`59f82e9cb1cedd08eb426e4a83752e21ed9f156b`

Tracked implementation surface:
- `src/vres_os/ingestion.py`
- `tests/test_ingestion.py`

Implementation:
- decode once via `utf-8-sig`
- parse decoded `text`
- return same `text`
- no source write

Regressions:
- `test_json_without_bom_still_parses`
- `test_json_with_utf8_bom_parses`
- `test_malformed_json_with_utf8_bom_still_errors`

Earlier focused execution:
- 4 passed
- `git diff --check` clean

Local `.venv-issue132/` is local test infrastructure and must never be committed.

## 7. #132 Vres task / rejected historical validation

Worktree:
`C:\Users\User\AppData\Local\Temp\claude\C--Projects-Vres-F14-Onboarding-20260922\42219ec5-907c-445b-a357-04349deebd5f\scratchpad\vres-os-issue-132`

Project id: `1732`

Project key:
`project:397197c0675b7aedb985f945`

Task:
`TASK-20260922-7356ddbefe`

Acceptance decision:
`DEC-20260922-797cf5c4c9`

Route:
`ROUTE-616f4038fd034e2e`

Prior orchestration:
- `ORCHPLAN-20260922-4c1e8f060a`
- `ORCHFINAL-20260922-1c29525adf`

Historical rejected validation:
`VAL-83f5f6b11f0d40a0`

Do not reuse that request. It was rejected due to the #133 platform race, not due to #132 code.

## 8. Issue #133 discovered during #132 validation

First attempt:
`VATT-b9d68540e2264da4` -> rejected because report not yet observable.

Later true-final attempt:
`VATT-9f1d61db30504222` -> `request already consumed`.

Root cause:
an interim SubagentStop consumed/rejected the pending request before the real terminal validator report arrived.

Issue:
**#133 — Protected validator interim SubagentStop can consume pending validation before final report**

An initial `background_tasks` liveness design was rejected before commit because that field is parent-session-scoped, not validator-specific.

Final design:
- one bounded defer gated by `stop_hook_active`
- first generic missing-report stop may become durable `deferred` while request stays pending
- continuation stop with `stop_hook_active=true` cannot defer again
- valid report uses full existing fail-closed checks
- still missing -> reject
- malformed present report -> reject
- stale task/artifact -> stale
- `background_tasks` is not validator-specific authority

Migration 035 adds `deferred` audit disposition only.

## 9. #133 evidence / publication

Branch:
`issue-133-validator-interim-stop`

Commit:
`4ce5439516b3ea3f301fa044c3fef4707888e705`

Focused unit/audit:
**11 passed**

Real PostgreSQL targeted journey:
**7 passed**

Protected-validation PostgreSQL slice:
**8 passed**

Protected A3 validation:
`VAL-af2308c602eb4de8`

Observed model:
`claude-fable-5-1`

Agent:
`ac4b86f90ab51ba93`

Session:
`b98bd3d1-9f9a-4c1e-b064-0caa25b85de4`

Accepted ingestion:
`VATT-46c09f93cd7b4a40`

PR:
`#134`

PR CI #329 SUCCESS.

Merge:
`59f82e9cb1cedd08eb426e4a83752e21ed9f156b`

Post-merge CI #330 SUCCESS.

Issue #133 CLOSED/completed.

## 10. Exact next gate

Do not begin by editing code.

Next session:
1. inspect the committed `issue-132-json-bom` checkpoint
2. resume `TASK-20260922-7356ddbefe`
3. run focused deterministic JSON tests
4. create a **fresh** protected validation request for exactly:
   - `src/vres_os/ingestion.py`
   - `tests/test_ingestion.py`
5. canonical `vres-os:validator`, protected Fable/high
6. inspect authoritative `validation_evidence` plus durable ingestion attempts

Required PASS:
- new `VAL-*`
- request status `passed`
- protected Fable observed_model
- agent_id/session_id persisted
- report persisted
- task validation_status `passed`
- no rejected/stale/unobserved terminal attempt
- if deferred appears, it may only be non-consuming and followed by accepted terminal PASS

If not authoritative PASS:
**STOP. Do not automatically redispatch.**

If PASS:
- no new code edits
- open #132 PR from checkpoint branch
- require exact-head CI SUCCESS
- merge
- require post-merge main CI SUCCESS
- then run only the smallest physical F-14 JSON retest

## 11. Remaining F-14 closure after #132 merge

Do not alter `f14_input`.

Preferred retest:
- fresh small retest project/folder
- `Copy-Item` original valid/malformed BOM JSON bytes
- prove valid BOM JSON parses/indexes
- prove malformed BOM JSON now fails for syntax, not BOM

Remaining checks:
- compare original hashes to `f14_before_hashes.json`
- lexical retrieval with embeddings disabled:
  - `F14LEXICAL-ALPHA`
  - `F14LEXICAL-BETA`
  - after JSON retest `F14LEXICAL-GAMMA`
- duplicate/dedupe provenance as needed
- retain original `.rtf` review PASS
- retain `embedding_jobs_queued=0`; no embedding worker
- explicitly reuse post-#126 F-06 cross-project evidence

F-14 PASS only after:
- #132 merged + post-merge CI green
- BOM JSON retest passes
- malformed BOM JSON remains rejected
- lexical retrieval passes with embeddings disabled
- dedupe/review/provenance reconciled
- original hashes unchanged
- cross-project reuse explicitly post-#126

Then update/commit acceptance docs.

## 12. F-15 hold

Do not start F-15 until formal F-14 PASS/REUSED.

F-15 is final realistic-day integrated verdict.

Do not claim production readiness or measured token savings without evidence.

## 13. Operating method to preserve

Continue exactly this cadence:

1. One bounded substep at a time.
2. User runs physical Windows/Claude operations and pastes raw output.
3. Interpret evidence, not self-report prose.
4. Give the next exact command/prompt with a stop point.
5. Preserve rejected/stale/failed evidence.
6. For a real defect:
   - stop affected case
   - preserve evidence
   - open issue
   - smallest fix
   - deterministic regressions
   - protected/independent validation as required
   - commit
   - push
   - PR
   - exact-head CI green
   - merge
   - exact-main post-merge CI green
   - rerun only failed physical subcase
7. Do not waive protected validation.
8. Do not downgrade assurance/model to bypass a blocker.
9. Do not clean/reset evidence projects for tidiness.
10. Never put credentials in chat/prompts/tool args/commits.
11. Use disposable `*_test` PostgreSQL databases.
12. Separate environment failures from regressions by base reproduction and CI.
13. Do not infer PASS from prose/exit code when Vres/PostgreSQL evidence exists.
14. Keep fixes separated from acceptance docs when practical.
15. Do not rerun passed F-cases unless owning surfaces changed.
16. If a harness command is wrong, fix the harness; do not call the noise a product defect.
17. Preserve exact SHAs, IDs, paths, validation keys, task keys, and job keys.
18. Before changing chats, checkpoint code + handoff.

User preference:
- exact commands
- minimal repeated explanation
- evidence-first decisions
- no repeated questions
- smallest fixes
- no speculative rewrites
- safe isolated testing
- direct interpretation of pasted logs
- comprehensive handoff before session switch

## 14. Evidence paths that must not be cleaned

All paths from the 2026-09-21 handoff remain retained.

Additionally:
- F-14: `C:\Projects\Vres-F14-Onboarding-20260922`
- #132 worktree: `C:\Users\User\AppData\Local\Temp\claude\C--Projects-Vres-F14-Onboarding-20260922\42219ec5-907c-445b-a357-04349deebd5f\scratchpad\vres-os-issue-132`
- #133 worktree: `C:\Projects\Vres-Issue133-Validator-20260922`
- installed-main update tree: `C:\Projects\Vres-Main-Update-20260922`

Do not delete test DBs just for tidiness before finalization evidence is secured.

## 15. Non-blocking observations

Do not reopen unless later material:
- some object-scope read errors say "writes"
- procedure intent-only match can miss when task-family retrieval succeeds
- pasted-content wrapper preserved in preference provenance
- PowerShell display mojibake can be display-only
- Windows symlink privilege local failure
- Node/libuv stdin-pipe local failure
- oversized Windows env can break Codex subprocess launch
- optional `psql`/Codex may be absent from PATH while managed Vres works

## 16. Fresh-chat startup

1. Treat this file as authoritative.
2. Do not rerun F-00..F-13.
3. Treat #133 as closed.
4. Main pre-#132 checkpoint is `59f82e9cb1cedd08eb426e4a83752e21ed9f156b`.
5. Inspect `issue-132-json-bom` checkpoint commit.
6. No #132 code changes before fresh protected validation.
7. Resume `TASK-20260922-7356ddbefe`.
8. Fresh `VAL-*`; never reuse `VAL-83f5f6b11f0d40a0`.
9. PASS -> #132 PR/CI/merge/post-merge CI.
10. Then bounded F-14 JSON/lexical/hash closure.
11. F-15 only after formal F-14 PASS.
12. Keep one-substep evidence cadence.

## 17. One-line resume state

**Blocker:** fresh protected validation of the committed #132 BOM fix.

**Last fully completed case:** F-13 PASS.

**Current case:** F-14 in progress.

**Next:** validate #132 on merged/installed #133 runtime, then PR/CI/merge if authoritative PASS.

**Do not redo:** F-00 through F-13.
