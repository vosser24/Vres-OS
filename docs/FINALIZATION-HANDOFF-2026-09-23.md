# Vres-OS Finalization — Technical Handoff (2026-09-23, F-15 final acceptance)

This file supersedes `docs/FINALIZATION-HANDOFF-2026-09-22.md` as the authoritative continuation state. The 2026-09-22 file is not deleted or edited; it remains as history and is linked below.

Predecessor: [`docs/FINALIZATION-HANDOFF-2026-09-22.md`](./FINALIZATION-HANDOFF-2026-09-22.md)

## Purpose

Resume Vres-OS final physical acceptance from the exact state reached on 2026-09-23 (after F-15) without re-running already-proven fixtures, losing evidence, rediscovering historical defects, or implementing unrelated features.

Repository:

`vosser24/Vres-OS`

This file is the authoritative continuation state for the next chat/session.

Blocking suite:

`docs/FINAL-VERIFICATION.md`

Historical detailed matrix:

`docs/LIVE-VERIFICATION.md`

At this handoff:

- **F-00 through F-15 are PASS.** F-15 is a fresh physical PASS (see "F-15 accepted physical evidence" below).
- Repository HEAD is `9f52e521ba4be6a9ebb5b096e3aa6ef80060b515` (merge of PR #140, issue #139).
- Issue **#103** remains CLOSED as completed (unchanged since prior handoffs).
- Issue **#132** and **#136** remain CLOSED as completed (unchanged since prior handoffs).
- Issue **#139** is CLOSED as completed via PR #140 (see F-15 evidence section below).
- GitHub issue **#141** is open as a non-blocking, non-critical post-finalization follow-up.
- Final release wording (use this wording, not stronger claims): F-00 through F-15 PASS; eligible for wider controlled live evaluation on the tested environment; NOT production-ready by implication; no measured token-savings claim; Smart Returns production verdict remains HOLD.
- No new feature work should begin before explicit user direction on the post-finalization roadmap (section 14, held).

---

# 1. Exact repository / installation identity

## GitHub

Current `main` at this handoff:

`9f52e521ba4be6a9ebb5b096e3aa6ef80060b515`

That commit is the merge of PR #140 (issue #139).

## Installed runtime used for F-15

Active installed release:

`20260923100129-18e49bb3`

Observed: installed `routing.py` hash matched main; installed `routing_completion.py` hash matched main. Migration 036 packaged and physically applied; `MIGRATION_COUNT=36`; latest migration `036_protected_pass_supersedes_routine_route.sql`.

Do not hardcode an older release path. Read `%LOCALAPPDATA%\VresOS\active-install.json` when a managed Python path is needed.

---

# 2. Finalization operating policy

Unchanged from prior handoffs. Reproduced for continuity:

Do not add features while F-00..F-15 is incomplete.

For a physical defect:

1. stop the affected F-case;
2. preserve evidence;
3. create a GitHub issue;
4. make the smallest correct fix;
5. review the exact diff;
6. require CI SUCCESS on the exact PR head;
7. merge;
8. require post-merge main CI SUCCESS;
9. physically rerun only the failed subcase unless the change invalidates broader evidence.

Do not rerun passed F-cases without a concrete reason.

Stop immediately on:

- credential leak;
- wrong-task continuation;
- cross-project leakage;
- unauthorized model downgrade;
- false validation PASS;
- stale-plan execution;
- write outside declared scope;
- fabricated telemetry;
- unexpected deletion/corruption of user-owned Claude settings.

Use isolated synthetic fixtures. Never run destructive credential cleanup against the real Windows Credential Manager namespace without true isolation.

User working preferences:

- exact commands;
- minimal repeated explanation;
- evidence-driven verdicts;
- no repeated questions already answered;
- smallest fixes only;
- no speculative rewrites;
- safe isolated testing;
- direct interpretation of pasted output.

---

# 3. Finalization matrix

| Case | Status | Notes |
|---|---|---|
| F-00 | PASS | update/migrations/statusline identity |
| F-01 | PASS | fresh install / Claude ownership boundaries |
| F-02 | PASS | rollback / uninstall / recovery ownership |
| F-03 | PASS | stranded cancellation repair |
| F-04 | PASS | bounded protected model/assurance lifecycle |
| F-05 | PASS | checkpoint / compact / clear / restart continuity |
| F-06 | PASS | concurrent sessions + cross-project isolation |
| F-07 | PASS | anti-overengineering / bounded context / noisy output |
| F-08 | PASS | project-agent authority + governor-confirmed gap acquisition |
| F-09 | PASS | real parallel fan-out + provenance + dependency join |
| F-10 | PASS | retry isolation + latest-plan + write-scope safety |
| F-11 | PASS | SEO/ecommerce multi-domain synthesis (corrected rerun; see the 2026-09-21 handoff, section 11) |
| F-12 | PASS | independent judgmental product acceptance: PASS -> FAIL/block -> fresh remediation -> PASS |
| F-13 | PASS | procedure + durable knowledge reuse with provenance/scope (fresh physical PASS, NOT REUSED) |
| F-14 | PASS | onboarding + retrieval baseline; #132/#136 fixes physically proven; see predecessor section 9 |
| F-15 | PASS | realistic-day integrated final verdict; #139 protected-completion repair physically proven; see "F-15 accepted physical evidence" below |

**Finalization is now complete: F-00 through F-15 are PASS.** Do not rerun F-00 through F-15 unless a later change touches an owning surface (see the surface-triggered regression table in `docs/FINAL-VERIFICATION.md`). Do not claim production readiness or measured token savings.

---

# 4. F-00 through F-05 — retained PASS evidence (condensed; unchanged history)

## F-00 — PASS

Windows status-line executable path defect: issue #117 / PR #118, behavior commit `f35bf19416083369aa87347a891d429081428cf5`. Forward-slash Windows runtime path fixed Claude `statusLine.command`; physical rerun rendered correctly.

## F-01 — PASS

Isolated current-user fixture (`C:\Vres F01 Isolated Δοκιμή`, source `C:\Vres F01 Δοκιμή\Vres-OS`) proved: user global sentinel survived; only Vres managed global block added; custom settings/statusLine preserved; shipped `vres-rules.md` hash matched; missing project `CLAUDE.md` received minimal scaffold; existing project `CLAUDE.md` stayed byte-identical; spaces/non-ASCII paths worked. PowerShell 5.1 display mojibake was decode/display only; persisted UTF-8 was correct.

## F-02 — PASS

Proved: interrupted journal blocks blind retry and preserves recovery evidence; caught late update failure restores active release/plugin/bin/global Claude rules/settings; uninstall removes only Vres-owned surfaces; replacement custom statusLine survives; explicit cleanup stays inside owned paths. Real defect: issue #119 / PR #120 (PowerShell local `$home` collided with readonly `$HOME`, renamed to `$ClaudeHome`), behavior stage `4b68889f1217eabf6fcf5bd52b8547917f08d016`, PR CI #308 SUCCESS, post-merge CI #309 SUCCESS. Safety lesson: the F-02 isolated filesystem harness did not isolate Windows Credential Manager; `uninstall.ps1 -RemoveLocalData` removed the real current-user `postgres.default` credential, which was repaired securely. Never repeat destructive credential cleanup under the same Windows account without credential-store isolation.

## F-03 — PASS

Historical task `TASK-20260918-865791f345`, project `C:\Projects\Vres-60-Final-20260918-152340`. Exact same-session prompt `cancel this task` succeeded. Durable evidence: task cancelled; session unbound; cancellation event 1207; `TASK_STATUS_CHANGED` 1208; `SESSION_UNBOUND` 1209; no artifact/expert/repair/orchestration/validation activity after cancellation. Issue #60 evidence updated.

## F-04 — PASS

Project `C:\Projects\Vres-F04-Protected-20260921`, task `TASK-20260921-e0000dedf2`. Protected pricing fixture: deterministic route; commercial-director / `cap.pricing`; one `vres-os:sonnet-expert`; observed model `claude-sonnet-5`; `ORCHESTRATION_FINAL` decision_ready=true before validation; exactly one validator (`VAL-6ce6d5c89ed04a7a`, observed `claude-fable-5-1`, PASS); direct completion; no second validator/repair/reroute/post-PASS orchestration mutation. A premature completion call was correctly rejected fail-closed and made no durable mutation. Issue #60 closed.

## F-05 — PASS

Project `C:\Projects\Vres-F05-Continuity-20260921`, task `TASK-20260921-00f8c9eb71`. Probe `f05_probe.py` -> `F05 TEST PASS`. Proved durable recovery of objective, decision, changed surface, exact executed evidence, blocker/current state, next action through native `/compact`, native `/clear`, and real process exit/restart. Clear defect: issue #121 / PR #122 (durable end reason normalized to `provider_session_replaced`), behavior commit `19ec313b1d81a2ddd245ac3f12b18269e15c96aa`, CI #310 / #311 SUCCESS. Latest checkpoint from that fixture: `CP-20260921-d6c6a6695e`. Task remains open intentionally.

---

# 5. F-06 through F-11 — retained PASS evidence (condensed; unchanged history)

## F-06 — PASS

Historical same-project concurrency (`C:\Projects\Vres-F06-Concurrency-A-20260921`, tasks `TASK-20260921-8e51bf0c7f` / `TASK-20260921-b58b9c0e79`) exposed issue #123, fixed by PR #124 (replacement provider session inherits still-active same-host predecessor task before project-focus fallback; behavior commit `dc9f29207f786af3518f7ad6b36a3e89e1bf2999`; CI #312/#313 SUCCESS). Physical rerun proved A1 remained A1, A2 remained open, predecessor ended `provider_session_replaced`, no live-session false closure.

Historical cross-project onboarding defect (issue #125 / PR #126, `onboard_folder` accepting another registered project's path) fixed at behavior commit `59010df5577e2457c673f74a29e093fbeae9d930` (PR CI #316 SUCCESS; post-merge #317 SUCCESS). Fresh post-fix projects: `C:\Projects\Vres-F06-XProject-A-20260921` (project id 6897) and `C:\Projects\Vres-F06-XProject-B-20260921` (project id 6909), both containing byte-identical `f06_scope_fixture\scope.txt` (SHA256 `bfde2805e9a78ef0b17321d17b4ede7f4eab8b600a9ba77fda2a162303dafc1b`). Cross-project onboarding rejection, own-project provenance separation, A-only knowledge isolation, company-wide publication hold, completion/ambiguity handling, and final native `/clear` lineage all proved PASS. Read-only proof ended `F06 SOURCE PROVENANCE: PASS` and `F06 CLEAR LINEAGE: PASS`. Therefore F-06 = PASS.

## F-07 — PASS

Project `C:\Projects\Vres-F07-Simple-20260921` (project id 7044). Direct one-line edit only, large file narrowed by marker/search, noisy command redirected to temp, output bounded, true exit `EXIT=0`, decisive line `F07 ACCEPTANCE PASS`; no worker/validator/persistent task/routing/work graph. Durable DB proof: TASKS=[], ROUTING REQUESTS=0, WORKER RUNS=0, WORK UNITS=0, VALIDATION REQUESTS=0. Ended `F07 GOVERNANCE MINIMALITY: PASS`. Therefore F-07 = PASS.

## F-08 — PASS

Project `C:\Projects\Vres-F08-Agents-20260921` (project id 7055, task id 96, `TASK-20260921-22d3decd4c`). Governor-confirmed acquisition for synthetic need `xenolithic kiln resonance calibration`: pre-block acquisition rejected, discovery `ORCHDISC-20260921-721a7ea445`, blocked route `ROUTE-4ae2e49aab8f4db5` (arbiter `claude-fable-5-1`), wrong-gap rejection, valid acquired capability `cap.project.f08.xenolithic-kiln` (owner `specialist-f08-xenolithic-kiln`), duplicate-acquisition rejection, rediscovery `ORCHDISC-20260921-712322da29`. Project-agent authority: forbidden `model`/`effort` frontmatter rejected; registered agent `agent.project.f08.xenolithic-kiln` (`write_policy=report_only`); source-drift re-registration required and performed (digest `066dba6d...` -> `2c1a7caa...`). Durable DB proof confirmed project-scoped capability/agent, `proven_count=0`, exactly one acquisition event, zero company-wide rows. Ended `F08 DURABLE AUTHORITY: PASS`. Therefore F-08 = PASS.

## F-09 — PASS

Same project id 7055, task id 97 (`TASK-20260921-806307a54e`). Discovery `ORCHDISC-20260921-701f203ef6` (no gaps). Stale route `ROUTE-24ba269271ac414e` correctly rejected (`task_changed_during_routing`), preserved as evidence. Fresh route `ROUTE-308686808d634543` (arbiter `claude-fable-5-1`): cto lead, routine assurance, three exact Sonnet experts. Plan `ORCHPLAN-20260921-ba6e77eeb7`; work units A (kiln) `ORCHWORK-20260921-52037b0787`, B (data) `ORCHWORK-20260921-9ea685ded0`, C (dependent CTO) `ORCHWORK-20260921-0c4b9bb0cf`. A/B DB intervals overlapped (True); C started only after latest prerequisite completion. Final `ORCHFINAL-20260921-869f78c259`, decision_ready=true, synthesis contained `F09_KILN_LIMIT=73`, `F09_KILN_MODE=phase-locked`, `F09_DB_ENGINE=PostgreSQL`, `F09_DB_ISOLATION=serializable`. Read-only proof ended `F09 PARALLEL DAG: PASS`. Therefore F-09 = PASS.

## F-10 — PASS

Project `C:\Projects\Vres-F10-Safety-20260921` (project id 7236, task id 98, `TASK-20260921-2594d63453`). Route `ROUTE-d09ed25e6fdd4905` (cto + data-director, both Sonnet, `hard_protected=false` but assurance **protected** — valid governor consequence reasoning). PLAN 1 (`ORCHPLAN-20260921-664a4bac38`) proved retry isolation: replan-while-running rejected, B's intentional failure led to host-stop rejection and a fresh retry host, successful sibling A was never rerun. PLAN 2 (`ORCHPLAN-20260921-c0505c4606`) proved latest-plan enforcement (old PLAN 1 execution rejected), write-scope overlap rejection, and out-of-scope native write rejection with in-scope write succeeding (`F10_PLAN2_A=PASS`). PLAN 3 (`ORCHPLAN-20260921-74a72ca094`) proved disjoint concurrent write scopes with real time overlap (`F10_CTO_WRITE=PASS`, `F10_DATA_WRITE=PASS`). Durable assertion ended `F10 RETRY / PLAN / WRITE SCOPE: PASS`. Therefore F-10 = PASS.

## F-11 — PASS

Corrected acceptance rerun task `TASK-20260921-1e0eea9c54` (remains ACTIVE), project id 7429, `C:\Projects\Vres-F11-SEO-20260921`. The earlier `TASK-20260921-dd8b1517a7` run is preserved as non-clean history, not part of the acceptance. Route `ROUTE-aee2c09255e34ca5` (protected, lead cto): SEO Sonnet via `agent.project.f11.seo`, data-director Sonnet, digital-director Sonnet, CTO Opus. Plan `ORCHPLAN-20260921-6f37e91013`; reports SEO `ORCHREP-20260921-79210106f8`, Digital/CRO `ORCHREP-20260921-46ed990f23`, Data `ORCHREP-20260921-d3b98caafe`; arbitration `ORCHARB-20260921-9ecbbd2ce0` (topic "F11 faceted-navigation indexation policy") recorded after SEO/Digital reports and before CTO execution; CTO report `ORCHREP-20260921-c05632b528`; final `ORCHFINAL-20260921-9662c9b003`, decision_ready=true. Arbitration resolved the SEO/CRO facet-indexation disagreement explicitly (category + exactly one controlled facet indexable; everything else excluded) rather than averaging it. Final evidence seal confirmed `transaction_read_only=on`, task remained active, no unauthorized company-wide authority, `f11_simple.txt` logical value `F11_SIMPLE_DIRECT_READ=PASS`. Full contract, fixture script, and assumptions caveat are retained verbatim in the 09-21 handoff (section 11) and are not repeated here. Therefore F-11 = PASS.

---

# 6. Observations intentionally preserved, not defects

Do not "clean" or rewrite these away (carried forward unchanged from prior handoffs):

1. F-06 A2 reply-gate warning `state_changed_after_reply_gate`, immediately resolved with a non-material gate and no state corruption.
2. F-06 PRIMARY protected validator correctly refused to treat relayed cross-project evidence as independently verified.
3. F-08 first acquisition call omitted `task_key`; schema error was harness noise, followed by the real governed rejection.
4. F-08 one company-wide hold call supplied literal `"null"` for `path_or_uri`; the scope guard executes first and no write occurred.
5. F-09 stale route `ROUTE-24ba269271ac414e` was correctly rejected after a mid-route checkpoint.
6. F-09 Worker B read a read-only fixture before claiming its work unit.
7. F-10 governor chose protected assurance despite `hard_protected=false`; this is valid governor consequence reasoning, not a failure.
8. F-10 early `orchestration_plan_record` attempts had schema/exclusion-field mistakes before the successful plan; no incorrect plan persisted.
9. PowerShell LF/CRLF Git warnings in disposable agent fixture repos are non-blocking; registered source digests were verified after commits.
10. F-15 procedural deviation: after successful #139 physical completion retest, Claude attempted `task_checkpoint` twice despite the explicit no-post-completion-write instruction; both attempts were rejected mechanically; no state mutation resulted. Recorded as a deviation, not a hidden success (see F-15 evidence section below).

---

# 7. F-12 accepted physical evidence (2026-09-21) — retained near-verbatim

Project: `C:\Projects\Vres-F12-Acceptance-20260921`

Task: `TASK-20260921-3f4d89508a` — ACTIVE, not completed.

Frozen test SHA256: `56ECEAB561EC4D65707F9DD85EA99CCABE1A796FA2868C3A0C8F16F30DFB65DA`.

Plan A PASS: `ORCHPLAN-20260921-11ae92c8aa`; implementation `ORCHREP-20260921-439767260c`; verifier `ORCHREP-20260921-411db6ba56`; final `ORCHFINAL-20260921-d1fbff091d`, decision_ready=true. Accepted artifact commit: `0b9866dbbe2d3fb751d995d6261be8986f9a551c`.

Plan B required FAIL: `ORCHPLAN-20260921-522482004e`; deterministic implementation report `ORCHREP-20260921-3f3ea1c9c0` PASS; independent verifier `ORCHREP-20260921-9f0e5b7f18` FAIL; no successful final. Finalization was rejected because J1 had not passed independent verification. Failed artifact commit: `bee552142149c07f9871ec9bd1953c436734adf0`.

Plan C remediation PASS: `ORCHPLAN-20260921-9ac3120cd9`; implementation `ORCHREP-20260921-fac8b9ef12`; verifier `ORCHREP-20260921-adc783baea`; final `ORCHFINAL-20260921-7a2c3de0f6`, decision_ready=true.

Durable proof: every work graph preceded its implementation start; implementers reported deterministic criteria only; verifiers were dependent/report-only and ran only after implementation PASS; J1 sequence was PASS / FAIL / PASS; Plan-B failure remained durable after Plan C; all routes used routine assurance; no protected validator was required; read-only PostgreSQL proof used transaction_read_only=on. Final accepted conclusion: `F12 INDEPENDENT PRODUCT ACCEPTANCE: PASS`.

F-12 evidence project must not be cleaned. Current preserved state at handoff: HEAD `bee552142149c07f9871ec9bd1953c436734adf0`; only `refund_notice.py` contains the uncommitted Plan-C remediation. Do not reset or commit it merely for tidiness.

---

# 8. F-13 accepted physical evidence (2026-09-21) — retained near-verbatim

Status: fresh physical PASS, NOT REUSED. Formally reviewed PASS against source/main `9ade2489f1b26c7f91a62e3eb62cd14788d621f9`. All data is synthetic acceptance-test data; none is production or customer data.

Primary project:

- path: `C:\Projects\Vres-F13-Reuse-20260921`
- project id: `8123`
- task: `TASK-20260921-f379c19fb6` — ACTIVE, not completed.

Candidate/source commit: `9ade2489f1b26c7f91a62e3eb62cd14788d621f9`.

### Procedure acceptance and changed-content rejection

- procedure: `proc.f13.net-sales-ranking-v1`
- preferred version: `1`
- approval: `APPROVAL-6196f1675ee2`
- a changed Units-ranking contract submitted with the same approval was rejected: `Approval retry changes the accepted contract; new approval required`

### Reuse after native /clear

- native `/clear` was performed before Day-2;
- initial diagnostic matcher miss (intent-only `procedure_match` returned `[]`) checkpoint: `CP-20260921-90fea81e4e`;
- successful reuse checkpoint: `CP-20260921-3b50cd1bbd`;
- exact accepted contract was retrieved with `procedure_get` before processing Day-2;
- Day-2 result: `001002 Beta 80`, `000007 Gamma 50`, `001001 Alpha 40`;
- preferred version and approval remained unchanged after the run.

### Preference provenance

- `pref.f13.net-sales-ranking` -> source event `1832`
- `pref.f13.net-sales-ranking-clean` -> source event `1840`
- project id `8123`
- negation `do not use Units` preserved;
- altered positive statement (`For this F-13 workflow, use Units for ranking.`) rejected with `Preference must quote the actual latest user instruction, not an inferred preference`;
- negative probe keys `pref.f13.negation-probe` and `pref.f13.negation-probe-clean` are absent.

### Limited observation

- source: `SRC-baf072d280d5`
- knowledge: `KNOW-ccc9c72d6702`
- type `observation`, status `observed`
- synthetic seven-day / association-only / no-causation / no-policy limitations retained;
- unapproved canonical causal rule rejected: `Canonical rule requires a recorded user approval event`

### Knowledge supersession

- old: `KNOW-cf2b025e78a6`
- new: `KNOW-e052afd17823`
- old status `superseded`; old points to new via `superseded_by`;
- current search (`F13THRESHOLD`) returns only threshold 12;
- old threshold 10 remains directly retrievable as history.

### Procedure promotion negative

- candidate v2 exists only as `candidate`;
- `accepted_by` null; `approval_key` null;
- decision `requires_user`;
- `validation_passed` false;
- reason `candidate has not passed independent validation`;
- preferred version remains `1`.

### Model-policy negative

- one synthetic run stored with `measurement_source=reported`;
- provider `claude`, model `sonnet`, effort `medium`;
- runtime 10 ms; input/output tokens 10/10;
- task-family-specific active model-policy count = 0;
- recommendation remained `claude/default/medium`, source `fallback`.

### Isolation project

- path: `C:\Projects\Vres-F13-Isolation-20260921`
- project id `8328`
- task `TASK-20260921-518b6f81d3`
- primary procedure not matched/read/mutated;
- primary knowledge not searched/read/promoted;
- primary preferences absent;
- reuse of the primary preference key rejected: `Preference key belongs to another scope`

### Final checkpoint

`CP-20260921-f78361d168`

### Formal behavioral verdict

1. exact accepted contract reused rather than prior output — PASS
2. changed approved content requires new approval — PASS
3. negation/source provenance preserved — PASS
4. observations/preferences remain limited and project-scoped — PASS
5. observation not promoted into causation/policy — PASS
6. superseded knowledge historical, not current truth — PASS
7. project scope enforced — PASS
8. no automatic procedure promotion from self-reported claims — PASS
9. no automatic model-policy promotion from self-reported telemetry — PASS

### F-13 observations retained (non-blocking, not defects)

- intent-only `procedure_match` missed; the intended "same again" + `task_family` retrieval succeeded;
- the Claude host `<pasted_content>` wrapper is preserved verbatim in preference provenance (the negation and semantic statement remained intact);
- the generic cross-project object-scope error mentions "writes" on some read attempts.

Do not open defects for these observations during finalization unless later evidence makes them blocking.

F-13 evidence projects must not be cleaned.

---

# 9. F-14 accepted physical evidence (2026-09-22) — retained near-verbatim

Status: fresh physical PASS, NOT REUSED. F-14 physically proves the #132 and #136 fixes and re-confirms post-#126 cross-project provenance behavior against current main (as of the 09-22 handoff).

## CURRENT MAIN (at F-14 acceptance)

- main SHA: 34b466e4270b99070f6cba7a0cc87ddbc0fcbbd1
- PR #137 merged
- post-merge CI #335 SUCCESS
- active installed release: 20260922163125-0a726330
- installed ingestion.py SHA matched current repo
- installed classifier: plain.json -> document 0.5; example.js -> code 1.0; process.json -> process 0.5700000000000001

## PRIMARY F-14 PROJECT

- path: C:\Projects\Vres-F14-Onboarding-20260922
- project id: 8454
- project key: project:af096b7cbdccc820c615f37c
- embeddings_enabled=false
- original onboarding job: MIG-20260922-c10e90e7

Original mixed fixture: f14_process.txt, f14_process_copy.txt, f14_analysis.md, f14_table.csv, f14_valid.json, f14_bad.json, f14_unsupported.rtf

Original onboarding evidence: files_seen=7, unique_files=4, duplicates=1, knowledge_candidates=2, review_required=3, chunks_created=2, embedding_jobs_queued=0, unsupported_catalogued=0, duplicate accounting PASS, malformed input visibility PASS, unsupported .rtf review behavior PASS, embeddings disabled / no embedding worker

## ORIGINAL FIXTURE INTEGRITY

- pre-hash manifest: C:\Projects\Vres-F14-Onboarding-20260922\f14_before_hashes.json
- all 7 current file hashes and lengths matched the original manifest
- EXTRA_FILES=NONE
- ORIGINAL_FIXTURE_INTEGRITY=PASS

## LEXICAL RETRIEVAL ON ORIGINAL PROJECT

- F14LEXICAL-ALPHA: PASS, chunk CHUNK-b4df4832c325, source SRC-d42d8a4822fb, source file f14_process.txt
- F14LEXICAL-BETA: PASS, chunk CHUNK-2e30b12dd6ee, source SRC-c3ddc237430f, source file f14_analysis.md
- embeddings_enabled=false; LEXICAL_WITHOUT_EMBEDDINGS=PASS

## ISSUE #132 — Windows UTF-8 BOM JSON parser defect

- PR #135; merged main bebc9480aec7ea821b8ad9b61a008f4793cdef87; post-merge CI #333 SUCCESS
- valid BOM JSON accepted; malformed BOM JSON rejected for JSON syntax instead of BOM decoding; source bytes unchanged; no embedding jobs

## ISSUE #136 — .json misclassified as code because ".js" substring matched ".json"

- protected validation: VAL-82cf5f82e6fa41d3, terminal accepted/passed
- validated commit: 8a4bd18fc3d3ae8602c7ea0dfe1f110e03343460
- PR #137; merge commit/current main 34b466e4270b99070f6cba7a0cc87ddbc0fcbbd1
- PR CI #334 SUCCESS; post-merge CI #335 SUCCESS
- issue #136 closed/completed

## FINAL POST-#136 JSON RETEST

- fresh project: C:\Projects\Vres-F14-JSON-Retest2-20260922, project id 9405, project key project:923fcbfa04035ee43b6d64ea, job MIG-20260922-3475edc2
- result: files_seen=2, unique_files=1, duplicates=0, knowledge_candidates=1, review_required=2, chunks_created=1, embedding_jobs_queued=0, unsupported_catalogued=0
- valid JSON: source SRC-d77bc7edaf71, chunk CHUNK-de0ede31b36b, lexical marker F14LEXICAL-GAMMA retrieved, F14LEXICAL_GAMMA=PASS
- malformed JSON: review queue id 10, ParserInputError "Expecting property name enclosed in double quotes: line 4 column 1 (char 49)", not a BOM decoding error
- second review item: expected heuristic review for valid document classification at score 0.50 — explicitly note this is not a parse failure
- final JSON verdicts: VALID_JSON_BOM_PARSE=PASS, VALID_JSON_KNOWLEDGE_BEARING=PASS, VALID_JSON_CHUNK_CREATED=PASS, MALFORMED_JSON_SYNTAX_REJECTION=PASS, MALFORMED_ERROR_IS_NOT_BOM=PASS, F14LEXICAL_GAMMA=PASS, LEXICAL_WITHOUT_EMBEDDINGS=PASS, EMBEDDING_JOBS_ZERO=PASS, SOURCE_BYTES_UNCHANGED=PASS, F14_POST136_JSON_RETEST=PASS

## POST-#126 CROSS-PROJECT PROVENANCE REUSE

- reuse baseline behavior commit: 59010df5577e2457c673f74a29e093fbeae9d930; owning surfaces audited unchanged through current main
- Project A: job MIG-20260921-92b1485d, source SRC-d9af2fa52f97, project id 6897, project key project:168c4bca3077f71388733f50
- Project B: job MIG-20260921-447da70a, source SRC-1d8a4974dbdb, project id 6909, project key project:69f8723407a5dd9d3efee65e
- both: same content hash bfde2805e9a78ef0b17321d17b4ede7f4eab8b600a9ba77fda2a162303dafc1b, separate project ownership, extracted as document, one chunk each, embedding_jobs_queued=0
- POST126_CROSS_PROJECT_PROVENANCE_REUSE=PASS

## FORMAL F-14 VERDICT

F-14 — PASS. Reason: raw sources unchanged; extraction/dedupe/provenance visible; malformed and unsupported cases surfaced visibly; lexical retrieval ALPHA/BETA/GAMMA works with embeddings disabled; embeddings correctly NOT RUN/zero jobs; valid Windows BOM JSON physically proven after #132; valid JSON physically proven knowledge-bearing/chunked after #136; post-#126 cross-project provenance evidence remains valid and explicitly reused.

---

# 10. F-15 accepted physical evidence (2026-09-23)

Status: fresh physical PASS. F-15 exercised a realistic-day integrated Chairman scenario: a simple deterministic task, an authoritative Smart Returns multi-domain final verdict, a physical protected-validation repair for issue #139, native continuity (`/compact`, `/clear`), a physical #139 completion retest, and descriptive usage observations. Final release wording is recorded exactly as supplied and is not strengthened anywhere in this file.

## Simple deterministic phase

- Project: `C:\Projects\Vres-F15-Realistic-Day-20260922`
- Project id: `9569`
- Project key: `project:3ec032f95c7586c00e6a8fa7`
- Task: `TASK-20260922-e67a4e17f0`
- Final task status: `completed`
- `completed_at`: `2026-09-23T10:56:45.535040+03:00`
- `daily-summary.txt` completed and verified
- checkpoint `CP-20260922-4d8884fc1f`

## Smart Returns authoritative final

- `ORCHFINAL-20260922-256389d642`
- `decision_ready=true`
- PLAN verdict: DECISION-READY
- PRODUCTION verdict: HOLD
- Production HOLD remains pending two named-but-unmeasured evidence gates. The two gates were named as part of the supplied requester evidence but no further identifying detail was supplied to this documentation task beyond "two named unmeasured evidence gates"; this file does not fabricate their names.

## Preserved initial failed protected validation (not reinterpreted or erased)

- `VAL-57a53294e37546f4` — FAILED

## Authoritative protected validation

- `VAL-2a1bff9f46574ad4`
- `vres-os:validator`
- observed model `claude-fable-5-1`
- agent `af0055613d5a3cd02`
- session `52688e2a-7dca-4017-bf55-c4595a67036a`
- PASSED, 15/15
- `latest_passed_validation_at` `2026-09-22T18:35:54Z`

## Issue #139

- issue #139, PR #140
- repaired PR head `c45c48d73df5423d478824b998556cadffe6089f`
- PR CI #339 SUCCESS
- merge/main `9f52e521ba4be6a9ebb5b096e3aa6ef80060b515`
- post-merge CI #340 SUCCESS
- issue #139 CLOSED / completed

## Installed runtime

- release `20260923100129-18e49bb3`
- `routing.py` installed hash matched main
- `routing_completion.py` installed hash matched main
- migration 036 packaged and physically applied
- `MIGRATION_COUNT=36`
- latest migration `036_protected_pass_supersedes_routine_route.sql`

## Post-#139 rehydration

- original F-15 task resumed without supplying a replacement task key
- `validation_status` remained passed
- protected PASS remained current
- historical failed validation remained preserved
- artifact bytes matched the protected validation evidence

## Native continuity

- `/compact` PASS
- automatic PreCompact checkpoint `CP-20260923-2225c42519`
- `/clear` PASS
- both recovered the correct task and recognized that the old free-text instruction to dispatch validation was stale
- neither repeated validation nor mutated the reviewed artifact

## #139 physical completion retest

- `task_complete_routed` returned `completed=true`
- `assurance="protected"`
- `routing_request_key=ROUTE-211932206974438a`
- final `validation_status` remained passed
- no second validation
- no fabricated protected routing claim
- task became completed
- project focus cleared

## Procedural deviation (recorded as a deviation, not a hidden success)

- after successful completion, Claude attempted `task_checkpoint` twice despite the explicit no-post-completion-write instruction
- both attempts were rejected mechanically
- no state mutation resulted

## Usage/status observations (descriptive only, no policy claims)

- Observation A: Sonnet 5 · high | ctx 13% | 5h 16% | 7d 23%
- Observation B after a tiny no-tool probe: Sonnet 5 · high | ctx 13% | 5h 16% | 7d 23%
- Interpretation: no visible change at displayed precision; descriptive observation only; no measured token-savings claim; no routing/model policy change based on this observation

## Optional features (recorded as NOT RUN, not PASS)

- embeddings disabled: NOT RUN
- Codex not on PATH / optional: NOT RUN

## Non-blocking follow-up

- GitHub issue #141 — "Post-validation resume can retain stale validation next_action"
- structured validation state was correct and native compact/clear behaved safely
- tracked as a non-critical post-finalization follow-up, not an F-15 blocker

## Final release wording (use this wording, not stronger claims)

- F-00 through F-15 PASS
- eligible for wider controlled live evaluation on the tested environment
- NOT production-ready by implication
- no measured token-savings claim
- Smart Returns production verdict remains HOLD

## FORMAL F-15 VERDICT

F-15 — PASS. Reason: the realistic-day scenario exercised durable-state resume, a simple deterministic task through completion, an authoritative multi-domain Smart Returns final (decision-ready plan, production HOLD pending named-but-unmeasured gates), preservation of an initial failed protected validation alongside a later authoritative PASSED protected validation (15/15), physical repair and closure of issue #139 with green PR and post-merge CI, an installed-runtime match to main including migration 036, correct post-#139 rehydration without validation state loss, safe native `/compact` and `/clear` continuity that did not repeat validation or mutate the reviewed artifact, a clean physical completion retest with protected assurance and no second validation, a faithfully preserved procedural deviation (rejected post-completion checkpoint attempts) that caused no state mutation, and descriptive-only usage observations. No production-readiness or measured token-savings claim is made anywhere in this evidence.

---

# 11. Issue #103 — CLOSED (completed)

Unchanged from prior handoffs. Issue **#103 — Add first-class project agents and governed parallel execution DAG** was closed as completed after F-08 through F-12 physical acceptance, PR #129 merge (`94f864e2315ba5060e8f2a8c71b56cf7543cd0a6`), and green PR CI #323 / post-merge main CI #324. No further #103 action or rerun is pending.

---

# 12. Closed defect chronology

- #117 / PR #118 — Windows statusLine executable backslash normalization
  - `f35bf19416083369aa87347a891d429081428cf5`
- #119 / PR #120 — PowerShell `$HOME` collision in uninstall
  - stage `4b68889f1217eabf6fcf5bd52b8547917f08d016`
- #121 / PR #122 — native `/clear` durable end reason
  - `19ec313b1d81a2ddd245ac3f12b18269e15c96aa`
- #123 / PR #124 — concurrent replacement session could bind wrong task
  - `dc9f29207f786af3518f7ad6b36a3e89e1bf2999`
- #125 / PR #126 — `onboard_folder` accepted another registered project's path
  - `59010df5577e2457c673f74a29e093fbeae9d930`
- #132 / PR #135 — Windows UTF-8 BOM JSON parser defect
  - merged main `bebc9480aec7ea821b8ad9b61a008f4793cdef87`; post-merge CI #333 SUCCESS
- #136 / PR #137 — `.json` misclassified as code because `.js` substring matched `.json`
  - merge commit / current main `34b466e4270b99070f6cba7a0cc87ddbc0fcbbd1`; PR CI #334 SUCCESS; post-merge CI #335 SUCCESS
- #139 / PR #140 — protected-completion repair (migration resume expectation for migration 036; honor later protected PASS at routed completion)
  - repaired PR head `c45c48d73df5423d478824b998556cadffe6089f`; PR CI #339 SUCCESS; merge/main `9f52e521ba4be6a9ebb5b096e3aa6ef80060b515`; post-merge CI #340 SUCCESS

---

# 13. Projects/evidence that must not be cleaned

Carried forward unchanged from the 2026-09-22 handoff, plus the new F-15 evidence project.

Historical defect evidence:

- `C:\Projects\Vres-F06-Concurrency-A-20260921`
- `C:\Projects\Vres-F06-Isolation-B-20260921`

Fresh F-06 final evidence:

- `C:\Projects\Vres-F06-XProject-A-20260921`
- `C:\Projects\Vres-F06-XProject-B-20260921`

F-07:

- `C:\Projects\Vres-F07-Simple-20260921`

F-08/F-09:

- `C:\Projects\Vres-F08-Agents-20260921`

F-10:

- `C:\Projects\Vres-F10-Safety-20260921`

F-11 (failed attempt `TASK-20260921-dd8b1517a7` and corrected rerun `TASK-20260921-1e0eea9c54`, both in one project):

- `C:\Projects\Vres-F11-SEO-20260921`

F-12 (task `TASK-20260921-3f4d89508a`):

- `C:\Projects\Vres-F12-Acceptance-20260921`
- preserved Plan-A artifact commit `0b9866dbbe2d3fb751d995d6261be8986f9a551c`
- preserved Plan-B failed artifact commit `bee552142149c07f9871ec9bd1953c436734adf0`
- current evidence state: HEAD remains the Plan-B commit and only `refund_notice.py` contains the uncommitted Plan-C remediation; do not reset, clean, or commit it merely for tidiness.

F-13 (task `TASK-20260921-f379c19fb6`, project id `8123`):

- `C:\Projects\Vres-F13-Reuse-20260921`

F-13 isolation probe (task `TASK-20260921-518b6f81d3`, project id `8328`):

- `C:\Projects\Vres-F13-Isolation-20260921`

F-14 (project id `8454`) and post-#136 JSON retest (project id `9405`):

- `C:\Projects\Vres-F14-Onboarding-20260922` (task/project id 8454)
- `C:\Projects\Vres-F14-JSON-Retest2-20260922` (project id 9405)

F-15 (project id `9569`, task `TASK-20260922-e67a4e17f0`):

- `C:\Projects\Vres-F15-Realistic-Day-20260922`

These disposable repos contain physical evidence and should remain untouched now that finalization is complete.

---

# 14. Post-finalization roadmap — retain, DO NOT IMPLEMENT YET

Unchanged from prior handoffs. Held pending explicit user direction; it was never authorized to start.

## Claude -> Codex execution handoff

Desired direction:

`vres handoff codex`

Principles:

- Vres owns task;
- hand off task state, not transcript/protocol translation;
- governed executor;
- prefer `codex exec --json`;
- trust postconditions, not exit code alone;
- temporary worktree + changed-path verification after real workspace-write preflight;
- never danger-full-access fallback.

## External Capability Discovery & Audit

Inventory installed MCP/plugins/skills/agents and classify:

- USE
- USE WITH GUARDS
- DEVELOPMENT REQUIRED
- DECLINE

Installation != adoption. Vres retains model/effort authority.

## JEV Browser Control

First browser-control fixture, likely USE WITH GUARDS.

Do not let a model-pinned external agent become a governed Vres agent.

## E-11 UX/UI Browser Audit Capstone

Audit account-creation flow with durable screenshots/journey findings/remediation/redesign/diagram/presentation-ready evidence.

## Superpowers plugin

Optional external development methodology only. Never a Vres runtime dependency.

---

# 15. New-session resume instructions

When opening a fresh session:

1. Treat this handoff as authoritative (it supersedes the 2026-09-22 and 2026-09-21 handoffs).
2. **Do not rerun F-00 through F-15** unless a later change touches an owning surface.
3. Do not clean, reset, rewrite, or tidy retained evidence projects, especially F-11/F-12/F-13/F-14/F-15.
4. Verify GitHub main only if needed; do not replay old history.
5. Confirm the installed runtime only if there is evidence it changed from `20260923100129-18e49bb3`.
6. Finalization F-00 through F-15 is complete. There is no next F-case.
7. Use the exact final release wording in section 10 ("Final release wording") for any external summary. Do not claim production readiness or measured token savings.
8. #103, #132, #136, and #139 are closed as completed; no further physical or administrative action is pending on any of them.
9. GitHub issue #141 remains open as a non-blocking, non-critical post-finalization follow-up.
10. Keep the post-finalization roadmap in section 14 held until the user explicitly authorizes it to start; it was never authorized to start.
11. No new feature work before explicit user direction on next steps.

Immediate next action in a new session: none required by finalization; await explicit user direction on the post-finalization roadmap or any new objective.

---

# 16. One-line resume state

**Current blocker:** none.

**Last completed case:** F-15 PASS. Finalization F-00 through F-15 is complete.

**Next action:** await explicit user direction; post-finalization roadmap (section 14) remains held, not authorized to start.

**Do not redo:** F-00..F-15.
