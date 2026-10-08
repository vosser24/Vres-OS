# Vres-OS — E7 Resume Handoff

Date: 2026-10-06
Repository: `vosser24/Vres-OS`
Documentation branch: `docs-execution-checklist-20260927`

This file is the durable fresh-session handoff from completed E6 repository acceptance into the E7 start gate. It supplements the historical canonical checklist/handoff and is authoritative for the E6→E7 boundary described here.

## 1. Hard sequencing rule

Do not start E7 implementation until E6 is fully closed at the Vres task layer.

E6 repository acceptance is complete:
- protected validation passed;
- PR merged;
- exact post-main CI passed.

Still required before E7:
- verify temporary validator-test cleanup;
- complete `TASK-20261005-abb88a1f0e` exactly once;
- read back completed status after the latest protected PASS.

Do not rerun E6 tests, release gate or protected validation unless accepted bytes change or a concrete evidence gap is discovered.

## 2. Authoritative product state

Authoritative `main`:
`9a8acc5d464b96432a93cb95daa9581412fb07ee`

Authoritative tree:
`659d3fdd6e635dbaecbd5c492ba7279754edaec7`

E6 accepted PR head:
`8ae041721bf0418f6472ab541b6838fd73fec46a`

E6 base:
`6af7bddf246e0f628c3e52add9528742e85189ca`

PR:
`#184` — merged

Merge commit:
`9a8acc5d464b96432a93cb95daa9581412fb07ee`

Merge parents:
- `6af7bddf246e0f628c3e52add9528742e85189ca`
- `8ae041721bf0418f6472ab541b6838fd73fec46a`

## 3. E6 task / contract / policy

E6 task:
`TASK-20261005-abb88a1f0e`

Frozen contract commit:
`fe6cfcfe0d87cd6920303242a1d647975aa3bf22`

Frozen contract tree:
`49b017914948eb76fc27c9cbdd550f1d80c12009`

Contract:
`docs/architecture/EXPERIENCE-INTELLIGENCE-E6-CONTRACT-2026-10-05.md`

Contract blob:
`e2cc483f262a71c04227fdbc380827c0cf215ec5`

E6 policy:
`176.e6.v1`

E6 policy digest:
`d61f60d31182085748bb613ef3c160274f1a1a5a2384854f36e52b4cdfecc5e5`

Frozen E5 retrieval-policy digest:
`7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9`

Migration:
`041_experience_retrieval_observability.sql`

No migration 042 was added.

## 4. E6 accepted implementation history

Chunk 1 final hardening:
`f93813086735e21b418539ab3ef8e07826fe8458`

Chunk 2:
- report `ORCHREP-20261006-4b7fd8cada`
- commit `623ee7300395c0b2efa303c7f331a93397b4a89b`
- checkpoint `CP-20261006-418c7da860`

Chunk 3:
- plan `ORCHPLAN-20261006-18992fa21a`
- work `ORCHWORK-20261006-2a601e6c3f`
- report `ORCHREP-20261006-766c1fc5f0`
- feature commit `9e2590c46242aa4229d0d47fd39fcf34fb85df91`
- feature tree `340f9f8e838154b4d2fddb21c419fd9750550726`
- checkpoint `CP-20261006-bb839fc92e`

Full-suite guard-test repair:
`bcf693a2e35d3636fd396ac7256f4aeec1b03b8a`

Final PR-CI portability repair:
`8ae041721bf0418f6472ab541b6838fd73fec46a`

That last change was test-only and accepted equivalent PostgreSQL FK-protection exception subclasses without weakening the constraint/message proof.

Latest repair governance:
- plan `ORCHPLAN-20261006-2b13935075`
- work unit `ORCHWORK-20261006-dfbfa83b1a`
- initial report `ORCHREP-20261006-279f25a2ba`
- retry report `ORCHREP-20261006-fac4d07523`
- final `ORCHFINAL-20261006-2144dc1db7`
- `decision_ready=true`
- `unresolved_unknowns=[]`

If older plan IDs appear in task-summary prose, use the durable orchestration event chain. The latest authoritative finalized plan is `ORCHPLAN-20261006-2b13935075`.

## 5. E6 local and CI evidence

Final local acceptance:
- 2489 passed
- 0 failed
- 0 errors
- 4 skipped
- 41 migrations, latest 041
- isolated `VRES_DATA_DIR`
- disposable DB dropped
- release gate `PASSED_WITH_EXPLICIT_LIVE_GATES`
- release-gate tests 1733 passed / 760 skipped
- wheel `vres_os-0.2.0a1-py3-none-any.whl`
- wheel SHA-256 `caab46cbf9d909fa5304f95fb0a3892e5af2b9aa31037d5066a9ab9e9d49f8bc`
- wheel bytes 413225
- checkpoint `CP-20261006-78dd265cf4`

Exact-head PR CI:
- run `37446906094`
- run number 475
- SUCCESS
- synthetic merge `78a2a417d5c24621c27807183a6c24a9a591f54e`
- 2490 passed / 3 skipped
- installed import smoke PASS
- release gate PASS
- release-gate tests 1734 passed / 759 skipped
- artifact id `11403772860`
- artifact ZIP SHA-256 `996f19e0103f8c5eb4caff312542ba9594eecf8781b27bdcab33742675969f26`

Post-main CI:
- run `37486449724`
- run number 476
- event `push`
- branch `main`
- exact SHA `9a8acc5d464b96432a93cb95daa9581412fb07ee`
- SUCCESS
- full suite 2490 passed / 3 skipped
- installed runtime import smoke PASS
- release gate `PASSED_WITH_EXPLICIT_LIVE_GATES`
- release-gate tests 1734 passed / 759 skipped
- completed 2026-10-06T15:24:21Z

## 6. Installed Windows/live E6 proof

Installed managed release:
`20261006135316-d311a4f8`

Managed install contained all 41 migrations.

Explicit managed start upgraded the installed DB from 38 to 41 by applying 039, 040 and 041.

Then:
- managed doctor: 41 migrations
- managed selftest: PASS
- repeated managed start: READY with no migrations pending
- fresh Claude Code 2.1.291: `start vres` READY

One real native `experience_retrieve`:
- public response remained E5 schema `176.e5.v1`
- abstained with `no_eligible_experience`
- zero returned items
- no E6 internal observation identifiers leaked

Exactly one E6 host observation:
- observation `ERO-773599b1778e4cc8a0bc4452520f6e4f`
- tool use `toolu_01VQWARkGyZm2sgYmjDEc2b7`
- Vres session/project `181 / 18002`
- attribution `main_thread`
- E5/E6 policy digests matched
- provider-session digest matched the live host session without exposing the raw provider id
- persisted item count / abstention / reason matched the returned pack

Installed privilege topology:
- runtime SELECT-only on all four E6 ledgers
- runtime no direct mutation
- runtime no protected E6 writer-function EXECUTE
- writer no direct table mutation
- writer EXECUTE only on the three protected E6 functions
- PUBLIC no mutation / protected EXECUTE
- schema, E6 tables and E6 writer functions owned by `vres_os_migrator`
- `user_event_writer` bound to `vres_os_writer`
- 12 active immutability trigger bindings
- no new `experience-observe hook-launch-failed`

Live plugin path:
`C:\Users\User\.claude\skills\vres-os`

Source == release distribution == live plugin for:
- `hooks\hooks.json` SHA-256 `700BF6AD711212C3A3A22419E42E0E5D62A491A7454C55C07AFED8409F0C34F7`
- `bin\vres-experience-observe.ps1` SHA-256 `68B869912C1EE9D94F539752E057577C1B40A8E2AFED46B6BF66C07D2804EAD8`

Non-empty item live proof and duplicate host redelivery were intentionally not manufactured. PostgreSQL integration evidence is authoritative for those deterministic paths.

## 7. PATH-shadow defect carried to #170

On the tested Windows machine, plain `vres` resolves the old global Python entry point before the managed launcher.

Old global:
`C:\Users\User\AppData\Local\Programs\Python\Python312\Scripts\vres.exe`

Managed:
`C:\Users\User\AppData\Local\VresOS\bin\vres.cmd`

This caused stale-package diagnostics before the managed launcher was invoked explicitly.

This is not an E6 retrieval defect. It is tracked under #170 production-readiness/install acceptance.

Do not hide the evidence by simply deleting the stale executable. Production readiness should ensure the managed launcher wins deterministically or detects/reports the conflict.

## 8. Protected validation history

First request:
`VAL-5b77b813435d42e5`
- observed model `claude-fable-5-1`
- failed because DB-backed criteria could not obtain authorized disposable DB evidence
- no contract criterion failed

Second request:
`VAL-7276379055e540c9`
- observed model `claude-fable-5-1`
- disposable DSN route worked
- test child inherited installed split-role Vres config
- this rebound provenance-writer authority and polluted expected disposable-test ACLs
- environment problem, not E6 source defect

Corrected validator PostgreSQL methodology:
- fresh disposable DB ending exactly `_test`
- secret value remains behind a local handle
- parent resolves the handle only for a bounded child process
- fresh empty `VRES_DATA_DIR` in the pytest child only
- `VRES_ALLOW_TEST_DB=1` in child only
- injected `VRES_TEST_DATABASE_URL` only
- clear `VRES_DATABASE_URL`
- clear `VRES_PROVENANCE_WRITER_DATABASE_URL`
- clear `VRES_MIGRATION_DATABASE_URL`
- never put test DB variables in the parent Claude/Vres process

Corrected topology preflight:
`ISOLATED_CONFIG configured=False writer='' migrator='' boundary=0`

Sentinel tests:
3 passed in 3.10s

Final protected request:
`VAL-62275cf3e4704444`

Observed model:
`claude-fable-5-1`

Outcome:
PASSED

Frozen E6 contract:
- 75 passed
- 0 failed
- 0 not_run

Independent focused PostgreSQL validation:
- 244 passed
- 0 failed
- 0 skipped

Focused non-DB validation:
- 492 passed

Freeze checkpoint:
`CP-20261006-bd92a14857`

Do not invalidate or rerun this PASS unless accepted bytes change or a concrete evidence gap is found.

## 9. Exact remaining E6 closure

Before E7, verify validator-test cleanup because cleanup output has not been durably captured here.

Expected cleanup:
- temporary validator secret handle is absent
- its disposable `*_test` DB is dropped
- temporary validator helper is removed
- temporary isolated test-data directory is removed
- temporary validator-reset evidence file is removed

If already clean, do nothing.
If not, remove only the temporary validator resources. Never touch the canonical installed Vres database and never print the secret value.

Then resume:
`TASK-20261005-abb88a1f0e`

Require:
- latest protected validation `VAL-62275cf3e4704444` = passed
- task `validation_status=passed`
- latest orchestration final `ORCHFINAL-20261006-2144dc1db7`
- `decision_ready=true`
- no post-freeze mutation invalidated the review

Complete the task exactly once through the governed completion path.

Read back:
- task status = completed
- completion timestamp after final protected PASS
- completion-after-latest-passed-validation = true
- final protected PASS preserved

Only then is E6 fully DONE and E7 authorized.

## 10. E7 scope

E7 is `benchmark + security ladder`.

E7 is not E8 automatic Chairman memory injection.

E7 must cover the #176 evaluation program.

### Experienced-colleague benchmark

Build a sanitized deterministic Vres corpus with:
- static project/environment state
- dynamic state changes
- recurring workflows
- project/environment gotchas
- false premises
- successful trajectories
- failed trajectories
- user corrections and decisions
- procedure reuse
- cross-project scope traps
- noisy/distractor history
- exact expected evidence keys

Version and hash:
- corpus
- development/held-out/adversarial split definitions
- expected evidence keys
- scoring rules

### Memory-operation faithfulness

Measure:
- source-support precision
- omission
- unsupported additions/hallucinations
- corruption of prior memory
- deduplication
- conflict recognition
- temporal update correctness
- secret/injection persistence rate

Operation-level checks are mandatory. Final-answer quality alone is insufficient.

### Retrieval quality

Measure:
- Recall@k
- Precision@k
- relevant evidence coverage
- irrelevant-memory rate
- duplicate-memory rate
- stale-memory suppression
- contradiction retrieval
- premise-awareness accuracy
- abstention
- retrieval latency
- context-token cost

### Outcome comparison

On the same held-out task set compare:
1. memory disabled
2. raw archive/refinding only
3. current Vres knowledge/procedure baseline
4. candidate hybrid experience memory

Measure:
- task/criterion success
- retries/rework
- tool/API calls
- token/runtime cost
- validation failures
- harmful/negative transfer
- unnecessary reuse

### Streaming learning

Sequentially evaluate:
- forward transfer
- retained competence
- new gotcha acquisition
- stale-knowledge update
- selective forgetting
- negative transfer
- learning curve over time

### Security/red-team

At minimum:
- malicious project document attempts durable instruction
- successful-looking poisoned trajectory
- memory prompt injection after context reset
- cross-project memory exfiltration
- external observation attempting company-rule authority
- poisoned procedure candidate
- secret-bearing episode
- revoked source still influencing later retrieval
- embedding/lexical poisoning
- trusted/untrusted conflict
- second-Windows-user isolation where relevant

Also cover:
- memory flooding/amplification
- semantically varied repeated poison
- source-diversity-aware retrieval
- recurrence cannot increase authority without independent evidence
- participated vs observed experience
- retrieval-triggered challenge/reverification
- retrieval must not silently rewrite the memory it just consumed

### Held-out discipline

Maintain separately:
- frozen development/replay corpus
- held-out acceptance corpus
- adversarial security corpus
- temporal/update cases that appear only in held-out evaluation

Do not tune on held-out acceptance.

Any model judge:
- must be calibrated against deterministic/human-labelled samples
- cannot be the sole authority for protected acceptance

## 11. E7 threshold rule

Do not invent numeric pass/fail thresholds from intuition.

First establish:
1. memoryless baseline
2. raw-archive/refinding baseline
3. current Vres knowledge/procedure baseline
4. candidate hybrid-memory result

Only after representative replay may thresholds be frozen.

Final E7 acceptance must require:
- no security/scope/provenance regression
- measurable net outcome benefit on relevant tasks
- no material negative-transfer increase
- bounded latency/token overhead
- improved or non-inferior memory-operation faithfulness
- exact reproducible evidence

Threshold selection must not use the held-out acceptance corpus.

## 12. E7 opening sequence

After E6 local task completion:

1. fetch `origin/main`
2. require exact main `9a8acc5d464b96432a93cb95daa9581412fb07ee`
3. create a new isolated E7 branch/worktree from that exact main
4. create/bind a new E7 Vres task
5. perform discovery before implementation
6. inspect E1-E6 truth owners and benchmark/replay/test primitives
7. read all E7/evaluation/security requirements in issue #176
8. identify reusable lifecycle/revocation/replay/procedure/capability/observability fixtures
9. define corpus, splits, expected evidence and scoring model
10. default to no new durable runtime truth owner unless discovery proves a gap
11. draft a bounded E7 contract
12. encode anti-leakage and held-out discipline
13. encode security/red-team methodology
14. encode performance/token/latency measurement
15. define threshold calibration procedure without choosing threshold numbers
16. freeze/checkpoint the E7 contract
17. only then implement bounded red-first chunks

Suggested branch:
`issue-176-e7-benchmark-security`

Suggested contract:
`docs/architecture/EXPERIENCE-INTELLIGENCE-E7-CONTRACT-2026-10-06.md`

These names are suggestions only. Discover first; if E7 state already exists, never duplicate it.

## 13. Testing methodology to preserve

- Python 3.12
- fresh unique disposable PostgreSQL DB ending exactly `_test`
- never use/repair the historical drifted DB
- isolated empty `VRES_DATA_DIR`
- no inherited installed split-role config in ordinary single-role integration tests
- credentials through local handles only
- never print DSNs/passwords
- protected validator DB evidence through child-process-only secret injection
- targeted red tests before implementation
- smallest viable change
- affected unit/static after each chunk
- fresh PostgreSQL integration for durable-state changes
- concurrency/idempotency/rollback where writes exist
- malformed/corrupt corpus/candidate inputs fail closed
- project/scope isolation
- provenance/source-digest checks
- secret/injection negative proofs
- deterministic replay/scoring reproducibility where promised
- exact corpus/split/expected-key/scoring digests
- explicit no-hidden-chain-of-thought persistence
- no duplicate expensive full suite/release gate/protected validation without changed bytes or concrete evidence gap
- one coherent final fresh PostgreSQL suite
- release gate once
- installed-runtime smoke only if E7 changes MCP/plugin/packaging
- exact-head PR CI
- protected Fable/high final review
- guarded expected-head merge
- exact post-main CI
- task completion exactly once

## 14. Remaining program

After E7:
- E8: Chairman automatic smallest relevant experience-pack integration + protected acceptance
- E9/#169: physical Windows/Visual Studio integrated learning acceptance
- continue #165-#169 according to the canonical preproduction sequence
- #170: separate production-readiness/go-live gate, including the Windows PATH-shadow defect

Do not call Vres production-ready before #170 is fully evidenced.

## 15. Fresh-chat resume prompt

```text
Resume the Vres-OS preproduction program from the E7 durable handoff.

Repository:
vosser24/Vres-OS

Documentation branch:
docs-execution-checklist-20260927

Read first:
docs/handoffs/PREPRODUCTION-E7-RESUME-HANDOFF-2026-10-06.md

Also consult:
docs/PREPRODUCTION-EXECUTION-CHECKLIST-2026-09-27.md
docs/handoffs/PREPRODUCTION-RESUME-HANDOFF-2026-09-27.md

AUTHORITATIVE PRODUCT MAIN:
9a8acc5d464b96432a93cb95daa9581412fb07ee

AUTHORITATIVE PRODUCT TREE:
659d3fdd6e635dbaecbd5c492ba7279754edaec7

E6 PR:
#184 MERGED

E6 POST-MAIN CI:
run 37486449724 / #476
SUCCESS
2490 passed / 3 skipped
release gate PASSED_WITH_EXPLICIT_LIVE_GATES

E6 PROTECTED PASS:
VAL-62275cf3e4704444
claude-fable-5-1
75 passed / 0 failed / 0 not_run

E6 ORCHESTRATION FINAL:
ORCHFINAL-20261006-2144dc1db7
decision_ready=true
unresolved_unknowns=[]

E6 TASK:
TASK-20261005-abb88a1f0e

START GATE:
Do not begin E7 until the E6 task is read back as completed exactly once.

First:
- verify/remove leftover temporary validator test resources without printing credentials
- resume the exact E6 task with the current host session
- verify latest protected PASS and orchestration final
- complete E6 exactly once
- read back completion after the latest protected PASS

Do not rerun E6 tests/release gate/validation.
Do not modify accepted E6 bytes.

Then start E7:
benchmark + security ladder.

E7 must cover:
- versioned/hashed experienced-colleague benchmark
- operation-level memory faithfulness/hallucination
- retrieval quality metrics
- memoryless/raw-refinding/current-Vres/hybrid baselines
- streaming forward transfer/retention/stale update/forgetting/negative transfer
- memory poisoning/red-team and flooding
- participated vs observed
- retrieval-triggered reverification without silent rewrite
- latency/token/scale
- separate development, held-out acceptance and adversarial corpora

Do not invent numeric acceptance thresholds before representative baseline/replay measurement.
Do not tune on held-out acceptance.
Do not let a model judge be the sole protected authority.

E7 opening:
- branch/worktree from exact main 9a8acc5d...
- create/bind a new E7 task
- discovery first
- reuse E1-E6 truth owners
- default to no new durable truth owner unless discovery proves a gap
- draft/freeze the complete E7 contract before implementation
- bounded red-first chunks
- fresh isolated PostgreSQL
- exact evidence/digests
- final protected Fable/high
- guarded merge + exact post-main CI

Do not start E8 Chairman auto-injection during E7.
Preserve the #170 Windows PATH-shadow finding for production readiness.
```


---

## 16. 2026-10-08 superseding execution boundary — Boundary 4A accepted / Boundary 4B next

This section supersedes the E7 opening-state instructions above for current execution.

Newest detailed handoff:
docs/handoffs/PREPRODUCTION-E7-B4B-RESUME-HANDOFF-2026-10-08.md

Authoritative E7 branch:
issue-176-e7-benchmark-security

Accepted E7 HEAD:
7aac85ac4917bfd3b178978183082debdd6333ca

Accepted predecessor:
Boundary 3 = 3ceae86aedfabaf949f231a5c956803e7d66cadd

Boundary 4A:
ACCEPTED / SEALED

Boundary 4A artifact:
benchmarks/experience_e7/results/authority_closure_development_live.json

Boundary 4A artifact SHA-256:
03b3c9e2c798ccdcabf53a7d1c6fe63e176662e796bae84c0fab146a2edfb661

Boundary 4A measured live authority:
- 9 E1-v1 participated trusted captures
- 9 real host-observed Fable routes
- 6 real host-observed Sonnet workers
- 6 passed work units
- 3 failed work units
- correct dev_seen E1-v2 observed/external-untrusted distinction
- exact cap_forecasting / cap_leadtime capability precedent
- recurrence quarantine preserved because threshold calibration has not started

Current canonical E7 task:
TASK-20261006-6cd9d80a92

The canonical task lives only in the normal/control Vres database.
Do not import/recreate it in disposable live fixtures.

Exact next sequence:
1. verify/finish B4A fixture cleanup;
2. return to the normal Vres environment;
3. checkpoint Boundary 4A acceptance on TASK-20261006-6cd9d80a92;
4. prepare and DryRun a fresh B4B disposable launcher;
5. execute Boundary 4B only after the fresh fixture/session startup gate passes.

Boundary 4B has NOT started.

Boundary 4B exact live scope:
- adv_secret_episode: 1 failed authority path
- adv_flood_burst: 25 failed authority paths
- adv_varied_poison: 6 failed authority paths
- total 32 real Fable-routed failed work-unit authority paths
- expected Sonnet workers: 0
- total frozen E2 consolidations: 31

Do not start Chunk 6, threshold calibration, held-out, final E7 protected/release gates or E8 during Boundary 4B.

For all execution detail, authority rules, RED discipline, fixture methodology and the current fresh-chat resume prompt, use:
docs/handoffs/PREPRODUCTION-E7-B4B-RESUME-HANDOFF-2026-10-08.md
