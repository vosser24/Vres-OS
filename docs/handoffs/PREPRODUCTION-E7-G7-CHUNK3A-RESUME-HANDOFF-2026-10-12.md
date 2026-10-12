# Vres-OS — E7 / G7 Chunk 3A durable new-chat handoff

**Handoff date:** 2026-10-12 (Europe/Athens)
**Repository:** vosser24/Vres-OS
**Current execution boundary:** G7 Chunk 3A — failed initial DESIGN review; no Chunk 3A code written or accepted
**Intended use:** New-chat read-only rehydration, followed by a separate user-provided Chunk 3A execution prompt
**Status:** Documentation handoff, NOT validation, product implementation, an authority grant, or approval to begin the next development phase

> THIS HANDOFF SUPERSEDES ALL EARLIER RESUME/NEXT-ACTION POINTERS FOR THE CURRENT E7/G7 WORK. Preserve earlier history; do not execute older October 6/8 Boundary-4B instructions as though they were the current next step. The product and benchmark acceptance criteria from those files still apply.

## 1. Exact stop point — DO NOT ADVANCE ON RESUME ALONE

The previous Claude Code session completed G7 Chunks 1, 1A and 2 on separate product feature branches and started planning Chunk 3A. Chunk 3A was stopped AFTER a host-observed independent design-review failure and BEFORE product implementation.

- Chunk 3A design task: **TASK-20261012-3201f6f610**.
- First Chunk 3A protected design review: **VAL-397fb4037e9546df**, host-recorded **FAILED / REQUIRES_CHANGES**.
- Independent reviewer: **claude-fable-5-1**, agent **ab05765462f038c80**. Reported 9/11 checks passed, two blocking areas; no overall PASS.
- Chunk 3A worktree exists locally at **C:\Projects\Vres-G7-Chunk3-20261012**; local branch **issue-176-e7-g7-chunk3**.
- Remote branch **issue-176-e7-g7-chunk3** did not exist when independently checked on 2026-10-12. This is expected. Do not invent a remote commit.
- The original proposed contract is an ignored/local review artifact in **C:\Projects\Vres-Issue-176-E7-20261006\.vres\local-tools\g7-chunk3a-contract-review-20261012\CONTRACT.md**, together with its README, source snapshots and SHA256SUMS.txt. Its precise full-file content and SHA must be reread locally. The attachment/transcript excerpts are NOT a substitute for a byte-identical review artifact.
- No Chunk 3A Python service, MCP implementation, migration, commit or push was performed. Do not assert otherwise.
- This handoff is a docs-only checkpoint. It does not freeze or approve a revised Chunk 3A contract.

**New chat FIRST ACTION:** read this document and check the explicit branch/task/validator state against the actual current repository and Vres control tools. Report discrepancies. Do not create a replacement design, dispatch a validator, run PostgreSQL tests or edit code until the user supplies the next Chunk 3A prompt.

## 2. Durable Git source of truth (verified public GitHub state immediately before this handoff)

**Product main after accepted E6:** 9a8acc5d464b96432a93cb95daa9581412fb07ee.
**Original E7 security branch:** issue-176-e7-benchmark-security
- HEAD: **0b4d5cdd79ec1e14366f9edce06575fbb8429294**.
- Tree: **49068e09a8a90e80dcffaf44980b5f3348d83c84**.
- This original product branch has not advanced during G7 feature-branch work; do not fast-forward it implicitly.

**G7 Chunk 1 + Chunk 1A feature branch:** issue-176-e7-g7-chunk1
- Base: 0b4d5cdd79ec1e14366f9edce06575fbb8429294.
- Chunk 1 commit: **03a989759b5fde4d8d2a8d2dcadd739586c73b0c**, tree **831d1d777c30fd680dfca50e0f454f5a909d0959**; 9 files.
- Chunk 1A safety follow-up: **99c730082469222de8162248ff8fe9d695fd52c6**, tree **a835b91ee2ac27c2414c4258b521e824eec2caaf**; 3 files; parent 03a9897.
- Remote feature-branch HEAD verified at 99c7300.

**Accepted G7 Chunk 2 feature branch:** issue-176-e7-g7-chunk2
- HEAD: **ac45967f63690b76d41b7303ad43248afed8751f**.
- Tree: **7a95990fb4413ddf387e90e9cfad5266f266c643**.
- Parent: 99c730082469222de8162248ff8fe9d695fd52c6.
- Exact 10 committed paths:
  1. src/vres_os/database_boundary.py
  2. src/vres_os/migrations/048_source_effective_trust.sql (new)
  3. tests/integration/test_e6_observability_schema.py
  4. tests/integration/test_g7_source_effective_trust.py (new)
  5. tests/integration/test_g7_source_trust_ledger.py
  6. tests/integration/test_migrator_resume_journey.py
  7. tests/integration/test_pg_fixture_safety.py
  8. tests/test_embedding_lifecycle_unit.py
  9. tests/test_migration_contract.py
  10. tests/test_session_contamination.py
- GitHub compare verified precisely one commit on the branch beyond the accepted Chunk 1A parent; GitHub commit, parent, tree, and ten files matched.
- GitHub showed NO associated workflow runs or check-runs at the last check. CI is unverified, not passed.

**Canonical documentation branch:** docs-execution-checklist-20260927
- Immediate predecessor HEAD before this handoff commit: **e1ba18e07572037271002472d148564fc97626fa**.
- This new handoff and the append-only pointer in the historical handoff advance that docs branch; retrieve the new SHA from the branch rather than expecting e1ba18e after this documentation-only commit.
- Do not merge docs branch into product main as part of preparing for Chunk 3A.
- Do not alter accepted contracts, historical reports, scorer, corpus, policy digests or frozen artifacts merely to update the handoff.

**File-level boundary:** local worktrees and ignored review bundles are Windows host assets. This GitHub docs commit does not upload or certify their bytes. Reverify them on the actual host. A new chat must not invent or reconstruct hashes it cannot read.

## 3. Local Windows worktrees and what each is for

- **C:\Projects\Vres-Issue-176-E7-20261006** — original E7 product worktree AND the registered/control Vres project context used for normal Vres task tools and local ignored review bundles. Original product branch issue-176-e7-benchmark-security, HEAD 0b4d5cd.
- **C:\Projects\Vres-G7-Chunk1-20261009** — accepted G7 foundation/safety worktree; branch issue-176-e7-g7-chunk1 at 99c7300.
- **C:\Projects\Vres-G7-Chunk2-20261009** — accepted G7 effective-trust reader worktree; branch issue-176-e7-g7-chunk2 at ac45967.
- **C:\Projects\Vres-G7-Chunk3-20261012** — next implementation worktree; branch issue-176-e7-g7-chunk3 based exactly on ac45967; at current stop there were no product code changes.
- **C:\Projects\Vres-E7-B4B-Docs-20261009** — durable canonical documentation worktree; local branch historically named docs-e7-b4b-v2-20261009 while remote canonical branch is docs-execution-checklist-20260927.

**Session rule:** Vres tasks are recorded in the normal/control Vres database, not in the disposable PostgreSQL fixture. The old provider session ID from the prior chat MUST NOT be reused. In a new Claude Code session, use VRES_CURRENT_SESSION_ID supplied by the newest lifecycle hook and explicitly invoke task_resume with task_key=TASK-20261012-3201f6f610. Read the returned active task and read-only session/task binding. Never call no-key task_resume when multiple unfinished tasks exist.

**State protection rule:** Checkpoint material task state BEFORE validation_prepare. Once protected validation is PASSED, do not checkpoint/invalidate merely to improve prose. A rejected/failed review must remain in history. A fresh independent review uses a new request key; never replay or rewrite an old report. No manual host-origin fabrication.

## 4. Source-of-truth docs and precedence

Start from this handoff, then consult:

1. docs/handoffs/PREPRODUCTION-RESUME-HANDOFF-2026-09-27.md — full older chronology; its newest appended pointer directs here.
2. docs/handoffs/PREPRODUCTION-E7-B4B-RESUME-HANDOFF-2026-10-08.md — frozen B4A/B4B boundaries and live proof methodology, HISTORICAL instructions only.
3. docs/handoffs/PREPRODUCTION-E7-RESUME-HANDOFF-2026-10-06.md — full E6/E7 opening evidence and final validation ladder, HISTORICAL instructions only.
4. docs/PREPRODUCTION-EXECUTION-CHECKLIST-2026-09-27.md — governing sequential checklist. Do not leap to E8 or later issues before E7 is DONE.
5. docs/architecture/EXPERIENCE-INTELLIGENCE-E7-B4B-V1-OWNER-GAP-DECISION-2026-10-09.md — original frozen B4B-v1 security disposition.
6. docs/architecture/EXPERIENCE-INTELLIGENCE-E7-B4B-V2-PROVENANCE-DESIGN-2026-10-09.md — future prospective B4B-v2 protocol; DRAFT, not acceptance.
7. docs/architecture/EXPERIENCE-INTELLIGENCE-E7-G7-SOURCE-TRUST-ATTESTATION-CONTRACT-2026-10-09.md — G7 design rev 5, accepted after previous failed revisions, original text remains byte-identical.
8. docs/architecture/EXPERIENCE-INTELLIGENCE-E7-G7-DESIGN-FREEZE-ERRATA-2026-10-09.md — additive frozen G7 policy 176.g7.v1; overrides earlier incompatible draft statements.
9. docs/architecture/EXPERIENCE-INTELLIGENCE-E7-G7-DERIVED-STALENESS-CLARIFICATION-2026-10-09.md — accepted current-digest semantics; document's original PROPOSED heading deliberately not rewritten.
10. docs/architecture/EXPERIENCE-INTELLIGENCE-E7-G7-DESCRIPTOR-BINDING-SECURITY-ERRATUM-2026-10-12.md — accepted CR/LF fail-closed reader correction and normalized NULL/empty semantics; original PROPOSED heading deliberately not rewritten.

**Important:** An accepted review recorded by Vres can supersede a frozen document's old status line via an additive reviewed record. Do not silently revise protected historical bytes for cosmetic reasons.

## 5. Immutable G7 policy and trust-boundary invariants

- Policy version: **176.g7.v1**.
- Policy digest SHA-256: **f20b037b00d0a5711666fd6c1d98538101708d99e7f6f32cf5a490ff6b96cf03**.
- Migration 047: **047_source_trust_ledger.sql**, append-only vres.source_trust_events; UPDATE/DELETE/TRUNCATE denied, owner-guarded INSERT, protected record_source_trust_decision; no ordinary runtime/writer EXECUTE on issuance function. Migrator/owner role is deployment authority and is NOT an MCP workaround.
- The only grant/revoke issuance authority is a source/project/content/descriptor-bound, immutable USER_INSTRUCTION event, from typed user_prompt, actor user, latest user-authority event by task_events.id, whose complete trimmed payload.text equals I authorize <exact source_trust subject>. Merely mentioning the subject, negating it, quoting it, or using an AskUserQuestion answer is NOT approval. approval_events is not a G7 authority source.
- Exact subject form: source_trust:<grant|revoke>:<project_id>:<source_key>:<content_digest>:<descriptor_digest>. The issuer derives expected identity inside the database. Requests/caller values alone cannot establish authorization.
- G8 host-ingress remains OPEN: a same-user shell-capable process can potentially forge unsigned prompt-hook ingress to the provenance writer. A correctly stored USER_INSTRUCTION is NOT independently authenticated proof that a human entered it. Production positive trust issuance remains DISABLED.
- Migration 048: **048_source_effective_trust.sql**, one STABLE SECURITY DEFINER read-only function, vres.source_effective_trust(source_id), returning ONLY verified_trusted or unverified; runtime EXECUTE allowed on the reader only; definer owns digest access.
- Reader requires source active, project-scoped, newest ledger event by id is valid unrevoked grant, current G7 policy/digest, matching current DB-computed chunk and descriptor digests, chunk_count > 0, correct source/project/user-event binding, and no restrictive external_untrusted_observation label.
- CR or LF in source_type, origin or version results in unverified even if a grant row was issued. This closes non-injective newline-separated descriptor serialization collisions. Migration 047 itself is unchanged and may record an inert, never-effective grant for a CR/LF descriptor.
- origin/version NULL and empty string are intentionally equivalent normalized absence under 176.g7.v1, not a promise of exact raw SQL-field identity.
- Digest-bound derived staleness: modifying bound source content/descriptor makes it unverified; restoring precisely the previously authorized digests may re-verify the same still-unrevoked grant when all other gates hold; revocation is never undone by restoration.
- Authorizations never transfer to a different project/source key or differing digests. Labels, content_hash, metadata, title, paths, similarity/rank/frequency do not grant trust.
- No new policy, mutable authority record, general grant setter, auto-grandfathering, or relaxed security rule may be introduced in Chunk 3A.

## 6. Accepted G7 engineering and validation history — classify evidence honestly

**G7 design history:**
- Early G7 revisions rejected for writable approval authority, forged/text-only checks, AskUserQuestion provenance, latest-event ordering and G8 ingress gaps. Review IDs: VAL-ea1520bbb051493f; VAL-ada05e213965497f; VAL-168d073866974f8d; VAL-b3ea906804df4cce.
- Revision 5 PASSED: **VAL-ca09c908c83247e2**; frozen baseline document SHA-256 **b4fc3a84f3fac9017fe9e0da2b1bfc9e5ddc4c50ce2826c1e59456940b5d53a1**.
- R3 provenance split-role test: 55/55 reported passed; latest anchor MUST order by task_events.id, not host-supplied created_at.
- Additive G7 freeze docs commit ff1280a37a04177d838b64cf575171de2c06269b; protected review **VAL-4364e4279c8f4123**, passed.

**G7 Chunk 1:**
- Commit 03a9897; protected review **VAL-1b1af80955f84d42** PASSED, host-recorded Fable according to local transcript.
- Reported 107 focused unit PASS; 12 isolated PostgreSQL ledger PASS; migration 047 and privilege isolation; no G8 solve, no production issuer.
- e6 observability schema and user-event-writer integration journeys deferred due to production-shaped/shared-role fixture needs; both remain MERGE blockers.

**G7 Chunk 1A fixture safety:**
- Commit 99c7300; protected **VAL-716368e0a41f4d75** PASSED per local host record.
- Reported 38 tests passed, zero skipped; fixture now checks approved isolated cluster identifier before any privileged DDL, database *_test suffix, explicit VRES_ALLOW_TEST_DB=1 and created-resource cleanup inventory.

**G7 Chunk 2 and correction chain:**
- Early attempted Chunk 2 review **VAL-7af7ef84a950484c** REJECTED because outcome=passed included two not_run checks; it did NOT pass the Vres parser.
- Original digest-bound Chunk 2 review **VAL-0c47a21a33be462f** PASSED for its earlier tested scope; afterward a descriptor serialization collision was reproduced; protected validation was explicitly invalidated for genuine post-review security changes while preserving the old review as history.
- Derived-staleness review **VAL-c08e1ab8b7ca4ef8** PASSED; docs commit cf9008b384de946f932222211b7b3658e32a2ffa.
- Descriptor security design attempts: **VAL-e9fb387e3cce48e4** FAILED on incomplete design/regressions; **VAL-3017ca2614ef44ed** REJECTED because a passed report included not_run; **VAL-33498ab977c247f4** PASSED, accepting Option A CR/LF fail-closed under frozen 176.g7.v1; docs commit e1ba18e07572037271002472d148564fc97626fa.
- Corrected Chunk 2 attempt **VAL-ecd30ab4144a4f3b** REJECTED because Validator session is not bound to this task. The fix was explicit task_resume with exact Chunk 2 key, NOT weakening validation or fabricating host evidence.
- Final corrected Chunk 2 protected **VAL-b3d1bf2428fc4b0f** PASSED (host observed model claude-fable-5-1, agent a059518f054dc8c18; 13 checks; canonical report persisted per local Vres transcript).
- Independently repeated focused PostgreSQL results reported: 115 PASS, 0 FAIL/skip (71 effective-trust, 12 ledger, 32 fixture-safety); 107 directly affected unit PASS; original uncorrected reader RED had 12 security-denial failures; exact resource cleanup verified.
- Commit ac45967, no E1/E2/E5/scorer/corpus changes; original migration 047 and 176.g7.v1 policy digest unchanged.
- No exact-head CI workflow/check run was observed for ac45967 at last GitHub check; do not call it green.

**Evidence qualification:** GitHub branch SHAs/commits/paths were independently checked via connected GitHub. Protected validation/test results above are drawn from the supplied Claude Code host transcripts and must be re-read from Vres validation_evidence before relied on for a later release gate. Do not claim a chat or a relayed report independently reran local PostgreSQL.

## 7. Chunk 3A proposed design and failed first review — exact current boundary

**Local proposed contract (not accepted):**
C:\Projects\Vres-Issue-176-E7-20261006\.vres\local-tools\g7-chunk3a-contract-review-20261012\CONTRACT.md
- Wrote approximately 66 lines as PROPOSED design, with README and SHA256SUMS in the same ignored bundle.
- New Vres task TASK-20261012-3201f6f610 was created and session-bound in the prior Claude Code session.
- VAL-397fb4037e9546df was delegated ONCE to vres-os:validator; host recorded **FAILED**, verdict **REQUIRES_CHANGES**; Fable model claude-fable-5-1, agent ab05765462f038c80; 9/11 checks passed, two blockers. Do not promote favorable partial findings to design acceptance.
- Reviewer reran four existing role-boundary tests, which passed; this does NOT establish new Chunk 3A integration acceptance.
- No implementation RED tests or service/MCP code were written, no product commit, no remote Chunk 3 branch.

**Reviewer-endorsed design choices (ENDORSED IN PART, NOT ACCEPTED):**
- Exactly two read-only project-scoped MCP tools: **source_trust_status** and **source_trust_inspect**.
- **source_trust_grant** and **source_trust_revoke** are NOT REGISTERED while G8 remains open. No placeholder operational-looking path that can secretly invoke the owner recorder.
- Authorization-subject preview DEFERRED (no second authority implementation in Python).
- Every public result discloses G8 limitation; no claim that database user_prompt proves human-origin authentication.
- Project ID bound from trusted current Vres project, never from MCP caller.
- Runtime role remains read-only on ledger and can EXECUTE reader only. Do not give migrator/owner credentials to MCP.
- No migration, change to 047/048, new policy/digest, E5 v6, or B4B in Chunk 3A.

**BLOCKER 1 — proposed CONTRACT Section 5 recovery model was incorrect:**
- A source can have MULTIPLE unrevoked grants at once, each with its own recorded content/descriptor digests. Calling a grant "active" is not synonymous with "effective".
- The 048 reader considers the single NEWEST ledger event by id, not whichever unrevoked grant matches current bytes.
- If newest event is a revoke, effective trust returns unverified, even while other grants remain unrevoked.
- 047 deduplicates a re-grant of an already-unrevoked digest pair: it returns the existing grant row without appending a newer event. A naive instruction "re-grant current state" may achieve NOTHING.
- Positive GRANT for a source not status=active is refused with source_not_active. Guidance cannot assume a grant can follow a source lifecycle revoke.
- The proposed state label older_grant_revoked_while_newer_grant_active is misleading: reversing which grant was revoked gives different histories with similarly named states.
- Required replacement: evidence-derived, BOUNDED display of every relevant ledger event and each unrevoked grant, with recorded digests, newest-event identity, revocation link, current source match, project and source status, effective reader result, and incomplete/truncated marker where necessary. Explain rules, NOT a universal repair sequence.
- Required separate deterministic scenarios:
  A. Grant A -> Grant B -> Revoke A; B unrevoked yet latest event revoke, so reader unverified.
  B. Grant A -> Grant B -> Revoke B; A may remain unrevoked yet reader unverified.
  C. Grant A -> Grant B -> restore source A bytes; latest grant B can prevent A's old grant from being effective.
  D. Grant A -> Grant B -> Revoke A -> attempt re-grant B; 047 can replay/dedup B with no new row, hence still unverified.
  E. Several distinct unrevoked grants plus a latest revoke; no single "current active grant" assumption.
  F. Inactive/revoked SOURCE while ledger grants remain unrevoked; reader unverified and 047 GRANT refused; do not conflate source revoke with trust-grant revoke.
- For each, the new contract must pin actual ledger order, active/unrevoked identities, newest event, current source digests, expected 048 result, dedup behavior and truthful descriptive guidance.
- supersedes_event_key, if exposed publicly, is DERIVED by a project/source-scoped join of source_trust_events.supersedes_event_id to referenced event_key. It is NOT a physical column. Fail closed on inconsistent/cross-source references.

**BLOCKER 2 — proposed CONTRACT Section 8 test matrix was insufficient:**
- tests/test_runtime_surfaces.py currently asserts 52 registered MCP tools. With exactly two read-only tools it should assert 54, presence of status/inspect, and explicit ABSENCE of source_trust_grant/source_trust_revoke. Preserve all prior prohibited setter assertions.
- PURE request-shape validation must reject BEFORE a DB connection or application SQL: non-object, missing/wrong source_key, unknown fields, caller-provided project_id, invalid limits, mutation requests. New tests must instrument connection factories and assert zero SQL.
- Unknown and foreign-project sources must be indistinguishable after correctly scoped lookup; project_id and foreign contents must not be echoed. No source title/path/metadata/credentials in status.
- Require PostgreSQL test explicitly proving transaction_read_only=on, with a REAL restricted runtime login and zero writes. If multiple queries form one status snapshot, define/test true READ ONLY / appropriate consistent snapshot; never claim atomicity without establishing it.
- Add multi-active-grant Cases A–F including restore-to-older-digests and inactive branch; bounded/truncated event inventory must NEVER imply complete recovery guidance.
- Resolve supersedes_event_key from physical supersedes_event_id with correctness and isolation tests.
- Add positive controls for actual ledger grant vs no grant, stale content, exact restore, descriptor CR/LF exclusion, normalized origin/version NULL/empty, source/ledger revoke, company scope, role restriction, zero chunks and conflicting evidence.
- Assert disabled issuer cannot be reached through an MCP alias, internal shortcut, owner credentials, user_event_id parameter or unlisted route.
- source_revoke is an existing E4 source lifecycle operation. Chunk 3A cannot invoke it, confuse it with ledger revoke, or silently cascade.
- Test service and MCP bounded outputs, deterministic ordering and incompleteness markers.
- Read-only results must not turn stale labels into positive trust; vres.source_effective_trust is the only positive-trust truth owner.

**Reviewer non-blocking notes:** explicit validation-before-SQL wording; no project_id echoed in ANY response. Both should be incorporated in the revised design, not left implicit.

## 8. Safe next Chunk 3A design/review methodology — NOT EXECUTED BY THIS HANDOFF

This is the approved next design direction but not a command to run it on mere resume:

1. Verify original branch and docs SHA and source files. Verify original failed review through validation_evidence; task remains unfinished.
2. Read full ignored original CONTRACT.md and its SHA256SUMS.txt from the host. Keep original bundle EXACTLY frozen. If it is absent, disclose loss and reconstruct a NEW PROPOSED contract from THIS handoff and source reading; never claim restored identity.
3. Create separate **g7-chunk3a-contract-review-r2-20261012** ignored bundle (or date-appropriate unique r2 path); fix Sections 5 and 8, add Cases A–F, add design source snapshots and acceptance matrix; do not edit original failed bundle.
4. Purely validate contract against 047, 048, MCP registry and public request/schema; no code or PostgreSQL implementation before design acceptance.
5. Scan bundle for DSNs/passwords/secrets and raw fixture traces. Record full SHA-256 of every accepted input; never include password-bearing diag.out from old security proof.
6. Bind CURRENT host session to TASK-20261012-3201f6f610 with exact task_resume key. Do not reuse historical provider session ID, switch tasks mid-review or guess by recency.
7. Checkpoint material revised design BEFORE validation_prepare. Prepare exactly ONE new independent Fable/high design review of frozen r2 manifest; include returned request key.
8. PASS requires host-observed model/agent/session, canonical persisted report, all required checks completed/passed, no not_run on a passed report, accepted exact file hashes. A prose PASS or SubagentHandback without persisted report is NOT accepted.
9. On FAILED/REJECTED review STOP, preserve rejection. No automatic retry or weakening of validator ingestion.
10. Only if design accepted, record the approved contract durably via a reviewed additive docs record. A passed Vres task state freezes itself; use validation_invalidate ONLY for genuine post-review implementation changes if lifecycle requires, preserving design PASS historically.
11. Then RED-first tests and smallest Python/MCP read-only implementation, focused isolated PostgreSQL and unit tests, one separate implementation protected validation. STOP before product commit/push. Product commit requires separate user approval in a later boundary.

These steps are recorded for continuity; the NEW CHAT SHOULD WAIT FOR THE USER'S SEPARATE 3A PROMPT before starting them.

## 9. Frozen resource safety and Windows shell lessons — do not repeat known mistakes

**PostgreSQL:**
- Use an explicitly approved, physically isolated PostgreSQL 18.6 disposable cluster. Last observed isolated cluster: 127.0.0.1:55432; system_identifier **7694553000872930884**. Verify the ACTUAL target identity before any CREATE/DROP; never rely on port or DSN name alone.
- Known shared/control cluster system identifier **7685334034094099024** is NEVER a disposable target. Do not run destructive or privilege-changing fixture operations there.
- Project-local protected secret handle previously used: **pg_e7_b4b_isolated_dsn**. Resolve via local Vres secret runner; never print raw DSNs, passwords, secret-store values or credentials. Do not store secrets in handoffs or CLI arguments.
- Disposable database name MUST end exactly with **_test**, VRES_ALLOW_TEST_DB=1 must be explicitly opt-in only in test context, and VRES_TEST_CLUSTER_SYSTEM_ID must match independently read pg_control_system().system_identifier.
- Verify entire created-resource inventory before ANY DROP. Never perform destructive pre-cleanup of arbitrary names. On failure retain safe, value-free evidence; then use approved exact-resource cleanup with identity recheck. Require zero remaining fixture databases and roles.
- Never create vres_os/control roles in the isolated fixture merely to make shared/control-topology journeys pass.
- Real runtime/writer/migrator role separation matters. The migrator in isolated PG may exercise protected functions for TEST PROOF only, never as production MCP bridge.
- Some historical tests rely on a production-shaped shared database role and stay DEFERRED: tests/integration/test_e6_observability_schema.py and tests/integration/test_user_event_writer_boundary_journey.py. They are mandatory MERGE GATES; do not mark as PASS without an actual appropriate execution.

**Windows/Claude Code:**
- Claude Bash cwd often resets to C:\Projects\Vres-Issue-176-E7-20261006 after commands. Always specify the intended worktree in each command and verify branch/HEAD before writes.
- Do not assume Unix heredocs or /tmp paths work inside PowerShell; do not mix shell dialects blindly. Confirm CLI syntax with --help on the actual installed tool. GitHub gh CLI was previously absent; use git fetch, git ls-remote and GitHub connector/API rather than assuming gh exists.
- CRLF vs LF can cause sed/grep and artifact hash surprises. Inspect Git-staged blobs, full SHA-256 and actual diff; LF-normalized equivalence is NOT raw-byte equality. Do not rewrite entire accepted files merely to normalize line endings.
- Test runners: use Python 3.12 and actual executable exit code; preserve junit counts/skips; never let a shell pipeline hide pytest failure. No unnecessary 240-second sleeps/background polling loops. Stop only identified orphan jobs. Do not trigger work while validation is in flight.
- A prior PostgreSQL expiry test deadlocked because it staged a second user event while holding ALTER TABLE's exclusive lock; stage user events BEFORE the locking DDL transaction. Exact cleanup after interruption is mandatory.
- A disposable-role password once leaked into a raw diagnostic traceback. It was confined to a dropped fixture role and subsequently sanitized for review; NEVER copy raw diagnostic outputs or runtime credentials into Git, docs, artifact bundles or user messages.
- Avoid invented migration names/paths, guessed SQL function signatures, tests and hardcoded migration counts. Read migrations and call signatures before scripting. Migrations 047/048 exist; any future migration requires reviewed necessity.
- Reviewer may return a canonical report via assistant-authored SubagentHandback, which Vres parses. Do NOT count tool_result or user-authored text as review. outcome=passed with any not_run check is invalid. Ingestion audit stores exact reasons, and binding mismatch requires exact task_resume before validation_prepare, not manual SQL repairs.
- Rerun affected tests only when bytes change or a real evidence gap is found; no repeated full suite/release gate/protected validator until the appropriately scoped final phase.

## 10. E7/B4B and release obligations still open — DO NOT DELETE

**Program sequencing:** #163, #174 and #164 finished; #176 E1–E6 accepted in earlier work; #176 E7 ACTIVE. E8 and later checklist implementation remain held. Product main is still E6-accepted main at 9a8acc5; G7 feature branches have not been merged into main.

**Frozen E7 B4B-v1:** 
- Original B4B expected 32 genuinely host-routed failed work-unit authority paths: 1 adv_secret_episode, 25 adv_flood_burst, 6 adv_varied_poison; 31 corresponding E2 consolidation calls (25+6). No expected Sonnet workers.
- The historical live **adv_secret_episode** security RED artifact, SHA-256 **aea04d4e3a7b67d19a8b7aea092b18f53c3300afc805d350b29f517e60480693**, in benchmarks/experience_e7/results/authority_closure_adversarial_live.json at historical commit c3a7f23, is preserved. E1 hardening commit 0b4d5cd passed **VAL-6764e6430153434f**, but NO live post-hardening rerun of this historical case is claimed.
- Deterministic adversarial matrix preserved: **16 PASS / 0 FAIL / 1 NOT_APPLICABLE / 3 OWNER_GAP**. This is NOT the required live 32-path overlay and cannot be substituted for it.
- Frozen v1 flood and varied-poison: **BLOCKED_OWNER_EVIDENCE**, not green. A synthetic isolated PG rehearsal observed 20 proposed lessons before a shared MAX_OPEN_PROPOSED=20 cap, with legitimate learning potentially starved by ordering; the v1 scorer overcounted proposed rows as promotion, and verified common lineage was unavailable. No higher-authority escalation was observed in that rehearsal. Do not call it a live exploit or a passed live test.
- Prospective B4B-v2 provenance design remains DRAFT/unfrozen, not a retroactive fix for B4B-v1. Family F/P1 honestly labeled observed-source containment does NOT establish unforgeable origin. G7 source trust is one prerequisite only.
- **G1**: participated failed episode citing an untrusted source must not retain inappropriately trusted origin; needs separately reviewed owner-derived downgrade.
- **G2**: verifiable common lineage across sources, not caller-declared labels, is unresolved.
- **G8**: authenticate host/human origin of user_prompt ingress; separate security architecture/review before enabling positive source-trust issuance. G7 migration ledger protections alone do not solve it.
- Never use content lexicons, benchmark aliases, arbitrary frequency thresholds, fake human approval, fabricated Fable routes, or retrospective alteration of frozen E1/E2/E5 policy/scorer/corpus to manufacture a pass.

**After Chunk 3A:**
- Full G7 Chunk 3 grant/revoke execution remains BLOCKED on an independently secured G8 path; read-only Chunk 3A is a useful partial, not full issuance.
- G7 Chunk 4: introduce prospective E5 v6 source raw-evidence eligibility via ledger-verified trust, preserve v2–v5 byte-identical replay, and prove SAME-SNAPSHOT trust/content consistency. The 048 reader itself is atomic only within its own statement; cross-statement retrieval can race, including modify-restore oscillation.
- G7 Chunk 5: read-only legacy source audit and documentation, report rows currently admitted by caller label without grandfathering them; do not infer user approval.
- Retest both deferred integration journeys before MERGE on production-shaped safe database/CI.
- Then G1/G2 and B4B-v2 prospective harness development as separately designed/accepted, and original B4B-v1 obligations stay honest.
- E7 Chunk 6: development-only benchmark replay (memory_disabled, raw_refind, current_vres, candidate_hybrid), representative latency/token baselines, THEN freeze thresholds; held-out acceptance only AFTER freeze without tuning. No unobserved benchmark routes/counts.
- Final E7 ladder, only at a coherent ready state: full fresh PostgreSQL suite once; release gate; installed Windows/plugin runtime smoke if packaging or MCP changed; exact-head CI; independent Fable/high validation; guarded merge; exact post-main CI; complete canonical E7 task once.
- E8: smallest relevant automatic Chairman experience-pack integration, AFTER E7 acceptance.
- E9/#169 physical Windows/Visual Studio integrated learning acceptance, remaining checklist issues, and #170 independent go-live/readiness including Windows PATH-shadow defect. Do not call Vres production-ready prematurely.

## 11. Detailed resume checks for the NEXT CHAT (READ ONLY; do not begin Chunk 3A)

1. Fetch origin, verify remote docs branch includes THIS handoff and newest superseding pointer. Verify product feature branch ac45967 and documentation predecessor chain. No force pushes.
2. Inspect actual Windows worktrees; require Chunk 3 local branch based exactly on ac45967, no new code or unexpected changes. If local state differs, report before proceeding.
3. In the registered control Vres project, use the NEW host-supplied session ID, task_open_list, exact task_resume for TASK-20261012-3201f6f610, and validation_evidence. Read the host record of VAL-397fb4037e9546df; no current design PASS.
4. Read original ignored Chunk 3A bundle and its SHA256SUMS.txt. Check it remains frozen; note any missing assets. Do not publish raw secret-bearing diagnostics.
5. Source-read migrations 047/048, database_boundary, MCP registration and tests/test_runtime_surfaces.py (52 expected); compare with the reviewer's blocker list in §7.
6. Summarize discrepancies and record that the next intended controlled step will be r2 CONTRACT Sections 5 and 8 correction and one fresh design review — but WAIT for the user's next explicit 3A prompt.
7. Do not start review/implementation/tests/commit/merge merely because this handoff was loaded.

## 12. Suggested fresh-chat initialization text

Resume the Vres-OS program from the newest durable G7 Chunk 3A handoff on the canonical docs branch. Read docs/handoffs/PREPRODUCTION-E7-G7-CHUNK3A-RESUME-HANDOFF-2026-10-12.md FIRST. Reconcile its SHA and references against GitHub and the local Windows Vres worktrees. The accepted product base is ac45967f63690b76d41b7303ad43248afed8751f. The Chunk 3A task is TASK-20261012-3201f6f610. Its first design review VAL-397fb4037e9546df FAILED (9/11), and no Chunk 3A code, commit or push exists. Preserve the original ignored review bundle and its SHA. The blockers are multi-active-grant recovery and the missing Section 8 acceptance tests. Use the current host-supplied session ID, never the previous provider session. G8 remains open, positive production issuance disabled, E5 v6 not started, B4B/held-out/merge blocked. For this first message, perform only read-only preflight and return the exact state, discrepancies and ready-to-resume confirmation. Do NOT write a revised 3A prompt, change task state, dispatch a validator, run tests or start implementation until I supply my separate Chunk 3A instruction.

## 13. Completion truth and handoff integrity

**Completed:** G7 foundation, safety and effective-trust reader committed and remotely verified; corrected descriptor semantics and design reviews accepted; newest handoff is being committed on the canonical docs branch.

**Not completed:** Chunk 3A design acceptance, Chunk 3A implementation, full G7 grant/revoke integration, G8 authentication, E5 v6, legacy audit, both deferred integration journeys, G1/G2, B4B live acceptance, Chunk 6, held-out, E8, exact-head merge and production readiness.

**Scope of this docs commit:** the new durable handoff plus an append-only superseding pointer in the historical resume handoff. It DOES NOT commit the ignored/local 3A contract or review bundle, DOES NOT alter product code, and DOES NOT change any Vres task/validation state. The new session MUST read the original local artifacts to recover their exact bytes. The committed handoff records all known indispensable facts needed to reconstruct the proposed contract if those local artifacts are unavailable, but reconstruction would be new UNREVIEWED bytes.

## 14. Superseding pointer (appended 2026-10-12, after R3 acceptance)

The Chunk 3A R3 contract was independently accepted (`VAL-86c382ece1b34e02`, claude-fable-5-1, 15/15 passed, 0 not_run). Sections 1-13 above remain the chronological record up to the failed R2 review and are NOT edited. Authoritative current state: `docs/architecture/EXPERIENCE-INTELLIGENCE-E7-G7-CHUNK3A-R3-ACCEPTANCE-DECISION-2026-10-12.md` (decision) and `docs/architecture/EXPERIENCE-INTELLIGENCE-E7-G7-CHUNK3A-SOURCE-TRUST-INTERFACE-CONTRACT-R3-2026-10-12.md` (byte-identical reviewed contract, SHA-256 `ce6ef7c40f1263367c1202aa8e795ca41384810e62582899a3fca2adaf208c38`). The "next controlled step" wording in section 11 (R2 correction) is superseded: R3 is accepted; implementation is separately authorized and validated, and no product commit is implied.
