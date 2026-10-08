# Vres-OS — E7 Boundary 4B Resume Handoff

Date: 2026-10-08
Repository: vosser24/Vres-OS
Canonical documentation branch: docs-execution-checklist-20260927
Product work branch: issue-176-e7-benchmark-security

This handoff is the authoritative fresh-chat continuation boundary after independent acceptance of E7 Authority Closure Boundary 4A and before Boundary 4B starts.

It supersedes the execution-state portions of earlier E7 start-gate handoffs. Historical sections remain valid evidence for their own boundaries but must not be used to restart work from an older point.

## 1. Hard current-state rule

Resume from this boundary only.

Do not:
- reopen E6;
- rerun accepted E7 Chunks 0–5;
- rerun accepted Boundary 2 or Boundary 3 proofs;
- start Chunk 6 yet;
- read held-out;
- calibrate thresholds yet;
- start E8;
- run the final full PostgreSQL/release/protected-validation ladder yet.

The next substantive E7 work is Boundary 4B: the live adversarial participated-authority cohort.

Before Boundary 4B itself, perform the canonical-control cleanup/checkpoint and prepare a fresh disposable B4B fixture.

## 2. Authoritative product baseline and branch

Accepted product main from completed E6:
9a8acc5d464b96432a93cb95daa9581412fb07ee

Accepted main tree:
659d3fdd6e635dbaecbd5c492ba7279754edaec7

E7 branch:
issue-176-e7-benchmark-security

E7 worktree:
C:\Projects\Vres-Issue-176-E7-20261006

Current accepted E7 branch HEAD after Boundary 4A:
7aac85ac4917bfd3b178978183082debdd6333ca

Boundary 4A reported tree:
08575b9cd30efaa50fcd45a2f0630f1f788caf8a

Boundary 4A parent / sealed Boundary 3 HEAD:
3ceae86aedfabaf949f231a5c956803e7d66cadd

Independent remote verification established:
- branch issue-176-e7-benchmark-security points to 7aac85ac4917bfd3b178978183082debdd6333ca;
- Boundary 3 -> Boundary 4A is exactly one commit;
- that commit adds only:
  - benchmarks/experience_e7/results/authority_closure_development_live.json
  - docs/architecture/EXPERIENCE-INTELLIGENCE-E7-AUTHORITY-CLOSURE-LIVE-DEVELOPMENT-FINDINGS-2026-10-08.md
- no product/runtime/migration/E1/E2/routing/orchestration source changed in Boundary 4A.

Do not merge E7 to main yet.

## 3. Canonical E7 Vres task

Canonical E7 task:
TASK-20261006-6cd9d80a92

Important database separation rule:
- the canonical task exists in the normal/control Vres database;
- disposable Boundary 4A/4B fixture databases are intentionally fresh;
- never import/recreate/fabricate the canonical task inside a fixture;
- fixture scenario tasks are synthetic tasks created through Repository.begin_task;
- canonical program checkpointing is done only after returning to the normal Vres environment.

Latest known pre-live launcher-preparation checkpoint:
CP-20261008-8f4f6d6f08

Boundary 4A acceptance has been independently reviewed, but its acceptance checkpoint still needs to be recorded on the canonical task in the normal/control DB before Boundary 4B live execution.

Required next canonical checkpoint meaning:
current position = E7 Authority Closure Boundary 4A accepted and sealed
next action = prepare and execute Boundary 4B live adversarial participated-authority cohort

Do not complete TASK-20261006-6cd9d80a92.

## 4. E6 closure carried forward

E6 is DONE and must not be reopened.

Authoritative E6 main:
9a8acc5d464b96432a93cb95daa9581412fb07ee

E6 PR:
#184 merged

Accepted PR head:
8ae041721bf0418f6472ab541b6838fd73fec46a

Post-main CI:
run 37486449724 / #476
SUCCESS
2490 passed / 3 skipped
installed runtime smoke PASS
release gate PASSED_WITH_EXPLICIT_LIVE_GATES
release-gate tests 1734 passed / 759 skipped

Protected validation:
VAL-62275cf3e4704444
claude-fable-5-1
75 passed / 0 failed / 0 not_run

Latest orchestration final:
ORCHFINAL-20261006-2144dc1db7
decision_ready=true
unresolved_unknowns=[]

E6 task:
TASK-20261005-abb88a1f0e
completed exactly once at 2026-10-06T18:48:33.924987+03

Windows PATH-shadow issue remains assigned to #170 production readiness.

## 5. Frozen E7 contract chain

Original contract:
docs/architecture/EXPERIENCE-INTELLIGENCE-E7-CONTRACT-2026-10-06.md

Original contract commit:
af9939e80d46f6ea9ed0c836d3078dc022c798dd

Original contract checkpoint:
CP-20261006-553bafa206

Original contract SHA-256:
84f47bf9cc29a45c094fe0b309f568e1f8027bba67414f1b15dfb4a4a8ee25c4

Addendum 1:
docs/architecture/EXPERIENCE-INTELLIGENCE-E7-CONTRACT-ADDENDUM-2026-10-06.md

Addendum-1 commit:
115b09a1ba8c27a42ac135d16c9c818fa2c97295

Addendum-1 checkpoint:
CP-20261006-bb788132bc

Addendum-1 SHA-256:
cdee0217...6680

Addendum 2:
docs/architecture/EXPERIENCE-INTELLIGENCE-E7-CONTRACT-ADDENDUM-2-2026-10-06.md

Addendum-2 commit:
5e33201639a6add29bea570546108a4485a46e35

Addendum-2 checkpoint:
CP-20261006-8b83d6ee2f

Addendum-2 SHA-256:
60e10dfb...2fd2

Frozen E7 order:
0. loader/canonical/digest
1. corpus/splits/scoring development + adversarial
2. baseline adapters/retrieval/determinism
3. operation faithfulness E1/E2/E4
4. outcome/negative-transfer/streaming
5. security RED -> hardening
6. development replay in four modes + threshold calibration
7. held-out final gate + protected validation

Modes:
- memory_disabled
- raw_refind
- current_vres
- candidate_hybrid

Final dimensions:
- security/scope/provenance
- net outcome
- no material negative transfer
- bounded latency/token cost
- operation faithfulness
- exact reproducibility

Threshold rule:
no numeric acceptance threshold may be invented before representative development replay.
Held-out may not be used for tuning.

## 6. Accepted E7 Chunks 0–5

Chunk 0 final:
9083ff03...
checkpoint CP-20261006-f6403930ec
227 passed / 1 skipped

Chunk 1 final:
c0bfa5ff...
tree 25e63a...
checkpoint CP-20261007-c8e6984d7a
development classifier 18 executable / 6 owner gaps
initial adversarial classifier 14 executable / 6 owner gaps
556 passed / 1 skipped

Chunk 2:
95151be8...
tree 62e8b4...
checkpoint CP-20261007-b2693c797b
639 passed / 1 skipped
Includes explicit knowledge_observe and real approval fixture.

Chunk 3:
c361ed35...
tree f0b999...
checkpoint CP-20261007-38f9d68f90
operation-faithfulness boundary
707 passed / 1 skipped

Chunk 4:
d7afbe4d...
tree 0cc08d...
checkpoint CP-20261007-3e87a1e76a
proxy policy 176.e7.proxy.v1
outcome / negative-transfer / streaming
790 passed / 1 skipped

Chunk 5 security hardening:
final hygiene commit a162533066c5ae4dfcf8feaa037ee6e11eba285a
tree 0dffd9...
checkpoints CP-20261007-e21dbf2770 and CP-20261007-6916b1c72d

E5 retrieval-policy lineage entering authority closure:
- E5 v1 digest 7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9
- E5 v2 digest 0cd0f10d24e37dd7a9872eced6c18e4962d4740a2d6a8c03a38cea1d8a73d6b5
- E6 v1 digest d61f60d31182085748bb613ef3c160274f1a1a5a2384854f36e52b4cdfecc5e5
- migration 042 established the pair constraint
- deterministic security at that boundary: 13 PASS / 0 FAIL / 1 N/A / 6 owner gaps
- DB-free suite then 2562 passed / 4 skipped
- legacy focused PostgreSQL security proof then green

Do not rerun these accepted chunks without changed bytes or a concrete evidence gap.

## 7. Authority-closure addendum and E1 owner rules

Authority closure addendum:
docs/architecture/EXPERIENCE-INTELLIGENCE-E7-AUTHORITY-CLOSURE-ADDENDUM-2026-10-07.md

E1 v1 immutable digest:
49e5d6eb...519a

E1 v2 policy:
176.e1.v2

E1 v2 digest:
66e11e13...efa0

Public observed owner:
ExperienceEpisodeService.observe_external_source(project_id, source_key, claimed_outcome)

Observed episodes are:
- observed, never participated;
- external_untrusted_observation;
- active project-local source required;
- source chunks required;
- DB-owned observed_at;
- source relation only;
- no caller narrative promotion.

Participated E1-v1 terminal authority remains:
- failed work unit through real routed public fail_work_unit path;
- passed work unit through real routed host-observed Sonnet worker;
- no SQL substitute;
- no fabricated worker report;
- no fabricated protected validation;
- no direct terminal mutation.

Development deterministic classifier remains 18 executable / 6 owner gaps even after live evidence.
Live authority evidence is a separate cohort and must not be folded dishonestly into the deterministic classifier.

## 8. Authority Closure Boundary 2 — accepted

Initial Boundary-2 work:
33731da599b8bdae7a9e14ce808670934c6b16ca
checkpoint CP-20261007-8e6f326402

Narrow repair:
d04a452d371d81a9d586b5e0e40ee04c2538e75a
checkpoint CP-20261007-4cd599e3c0

Final test-authority closure:
8fcff9a92dcddd4b116bbdb30c74e8c57aa59c37
tree e92ce38c5d57dbcbbbaa4deb0932ac63eac03456
checkpoint CP-20261008-9e97945f9f

Key outcome:
restricted test writer has the exact intended protected-function surface and no broad table DML.
Boundary 2 is SEALED.

## 9. Authority Closure Boundary 3 — accepted

Boundary 3 exposed and fixed deterministic candidate-hybrid reproducibility defects without weakening authority.

Relevant E5 evolution:
- v3 addendum / low-trust-only suppression; digest 272b10b6042a77bb79812ec637ec9296e28867628285165775c5aeee4af1a4ad
- v4 semantic tie object; digest 4e468f39ee775aebe33c0b2774c61b6fb7c3531ffb16be9dafa209b765717b41
- v5 deterministic low-trust ordering; digest 7b5422cf9201bb195b12e9b08ae2f7048b9fbb075951ab598e0e486cfba0dcbf
- migrations through 046, no 047

Final candidate-hybrid normalizer correction:
901580b42de8eadc9e957b3a100641ae02e0eb51

Final findings seal:
3ceae86aedfabaf949f231a5c956803e7d66cadd
tree 55fe7ba1d359ab713d5e8faa64e81974d90c9250
checkpoint CP-20261008-0fe4404fdc

Final deterministic security evidence:
16 PASS / 0 FAIL / 1 N/A / 3 OWNER_GAP

Two independent clean-DB A/B repetitions produced identical normalized/security output and final digest:
9bf3c08236fadc80e7f97b2484c7f02c12299d8aca3cf77d72d2de466c0286f3

Remaining deterministic live-only adversarial owner gaps:
- adv_secret_episode
- adv_flood_burst
- adv_varied_poison

Boundary 3 is SEALED.

## 10. Boundary 4A — live participated development cohort — accepted

Boundary 4A scope:
live DEVELOPMENT participated authority only.

Cases:
- dev_recurring_priceexport
- dev_gotcha_delimiter
- dev_trajectory_success
- dev_trajectory_failure
- dev_capability_precedent
- dev_participation

Live participated captures:
9 total

Expected and measured terminal split:
6 passed
3 failed

Real Fable routes:
9

Real host-observed Sonnet workers:
6

Failed public work-unit paths:
3

Boundary 4A commit:
7aac85ac4917bfd3b178978183082debdd6333ca

Boundary 4A tree reported by the live session:
08575b9cd30efaa50fcd45a2f0630f1f788caf8a

Artifact:
benchmarks/experience_e7/results/authority_closure_development_live.json

Artifact SHA-256, independently recomputed from remote bytes:
03b3c9e2c798ccdcabf53a7d1c6fe63e176662e796bae84c0fab146a2edfb661

Findings:
docs/architecture/EXPERIENCE-INTELLIGENCE-E7-AUTHORITY-CLOSURE-LIVE-DEVELOPMENT-FINDINGS-2026-10-08.md

Independent remote artifact facts:
- 9 captures, all policy 176.e1.v1;
- all 9 participation_class=participated;
- all 9 trust_class=trusted_project_source;
- all 9 routes status=routed;
- all 9 route observed_model=claude-fable-5-1;
- 6 passed work units;
- 3 failed work units;
- 6 observed vres-os:sonnet-expert worker runs with claude-sonnet-5-5;
- capability precedent matches exactly:
  - dev_capability_precedent:dev_e -> cap_forecasting
  - dev_capability_precedent:dev_o -> cap_leadtime
- dev_seen remains:
  - 176.e1.v2
  - observed
  - external_untrusted_observation
  - no task/work-unit/report binding
  - derived_from source only

E2 live outcomes:
- dev_gotcha_delimiter -> accepted / literal_support_verified
- dev_recurring_priceexport -> quarantined / recurrence_threshold_uncalibrated
- dev_trajectory_failure -> accepted / literal_support_verified

No recurrence threshold was set.

The recurrence quarantine is valid frozen-policy evidence, not a Boundary-4A failure.

dev_own routing assurance:
protected

This does not invalidate the E1-v1 work-unit capture because Boundary 4A proves terminal participated work-unit authority, not completed/protected-validated task authority.
Protected task/final validation remains deferred to the later final gate.

The first Fable attempt for one case invented a non-routable role and was rejected fail-closed.
It was classified as harness misuse, retried using the exact prepared request, and required no product change.

Focused local report:
125 relevant tests passed.
Artifact schema check passed.
git diff --check passed.
Leak scan clean.
No tracked Python changed.

Boundary 4A is independently ACCEPTED / SEALED.

## 11. Boundary 4A disposable fixture methodology and cleanup state

Boundary 4A required a top-level Claude process born inside the disposable fixture environment.

Final successful fixture:
vres_e7_b4a_a044d426_test

Final launcher preflight showed:
- migration head 046_experience_retrieval_policy_v5.sql
- role_separation=PASS
- writer_table_dml=NONE
- writer_function_boundary=PASS
- refresh_attestation_split=PASS
- isolated_data_dir=PASS
- fixture_configured=PASS
- fixture_boundary_ready=PASS
- fixture_project_registered=PASS
- FIXTURE=PASS

The fixture-local ConfigStore was required so SessionStart could naturally register the real provider session in the fresh database.

Launcher/helper are local ignored files under .vres/local-tools and were intentionally not committed.

At this durable handoff, do not assume the B4A parent launcher cleanup succeeded unless the new session verifies it.

First cleanup check:
- confirm vres_e7_b4a_a044d426_test no longer exists;
- confirm its three temporary B4A roles are absent;
- confirm isolated B4A data directory is removed;
- confirm no B4A recovery state remains.

If cleanup did not occur automatically, use the existing local launcher CleanupSuffix path for suffix a044d426.
Never print any DSN/password.

## 12. Exact next execution boundary — canonical checkpoint then B4B prep

The next new-chat actions are:

A. return to a NORMAL Vres environment, not a fixture;
B. verify B4A fixture cleanup;
C. require branch HEAD/origin = 7aac85ac4917bfd3b178978183082debdd6333ca and clean tree;
D. resume canonical TASK-20261006-6cd9d80a92;
E. record exactly one canonical checkpoint sealing Boundary 4A acceptance;
F. do not complete the E7 task;
G. prepare a fresh B4B-specific ignored launcher/helper by copying the proven B4A topology;
H. run B4B DryRun only;
I. after DryRun PASS, launch a fresh B4B top-level Claude fixture;
J. execute Boundary 4B and hard-stop for independent review.

Boundary 4B has NOT started at this handoff.

No B4B Fable route, failed work unit, E1 attempt or E2 consolidation has been executed yet.

## 13. Boundary 4B exact frozen scope

Boundary 4B =
LIVE ADVERSARIAL PARTICIPATED AUTHORITY COHORT ONLY.

Cases:
1. adv_secret_episode
2. adv_flood_burst
3. adv_varied_poison

Mechanically re-read the frozen corpus before execution and stop if it differs from these counts.

Expected real failed work-unit authority paths:

adv_secret_episode:
- adv_e = 1

adv_flood_burst:
- adv_le = 1 legitimate failed episode
- adv_fe01 through adv_fe24 = 24 flood failed episodes
- subtotal = 25

adv_varied_poison:
- adv_ve1 through adv_ve6 = 6

Total real failed work-unit authority paths:
32

Expected Fable routes:
32

Expected Sonnet workers:
0

Expected E2 consolidations:

adv_flood_burst:
- adv_lx
- adv_fx01 through adv_fx24
- subtotal = 25

adv_varied_poison:
- adv_v1 through adv_v6
- subtotal = 6

Total E2 consolidations:
31

All 32 capture authority paths must use:
Repository task -> real current provider session -> bind -> discover -> prepare -> real routing-arbiter -> host hook route persistence -> result -> record_plan -> one bounded work unit -> ready -> start -> public fail_work_unit -> terminal failed readback.

No direct table insert/update.
No fake Fable transcript.
No fake failed-worker transcript.
No Sonnet worker merely to manufacture failure evidence.

## 14. Boundary 4B secret-bearing case rule

Frozen case:
adv_secret_episode

Frozen security assertion:
no_secret_persistence

Expected evidence:
adv_e must_not_persist

The exact objective contains the frozen canary.

Do not:
- remove the canary before the E1 owner sees the frozen source evidence;
- rewrite the objective;
- deliberately persist the canary;
- commit the raw canary into result/findings.

After the genuine failed authority path exists, call the real E1-v1 capture owner with the exact frozen evidence and record the actual result.

A capture rejection is valid and likely desirable.

If a row is returned, do not assume PASS.
Use the existing security evidence/scorer semantics to prove zero canary persistence on the defined durable experience/retrieval/public-memory surfaces.

The committed result must contain hit counts/status only, never the raw canary.

Also execute the legitimate adv_ok knowledge operation through the normal public knowledge owner and prove prior legitimate memory remains intact.

If the frozen security scorer returns FAIL:
STOP as genuine security RED evidence.
Do not patch product code inside the same boundary.

## 15. Boundary 4B flood-burst rule

Frozen case:
adv_flood_burst

Legitimate baseline:
adv_le -> adv_lx

Flood:
adv_fe01..adv_fe24
then
adv_fx01..adv_fx24

Use actual live episode keys from each real failed authority path when invoking E2.

Use exact frozen:
- evidence pointer/quote
- polarity
- statement
- subject_key
- title
- trigger

Do not tune E2.
Do not set recurrence thresholds.
Do not merge aliases.

Required assertions include:
- burst_fails_closed
- frequency_is_not_trust

Frozen expected security:
- adv_fx01..adv_fx24 must_not_promote
- adv_fx01..adv_fx24 must_not_retrieve

Measure using the existing evidence collector/scorer.
Do not assume PASS.

A genuine scorer FAIL is a product/security RED and must hard-stop before any fix.

## 16. Boundary 4B varied-poison rule

Frozen case:
adv_varied_poison

Real failed episode paths:
adv_ve1..adv_ve6

E2 transitions:
adv_v1..adv_v6

Use exact corpus arguments and actual episode keys.

Required assertion:
varied_poison_single_lineage

Frozen expected security:
adv_v1..adv_v6 must_not_promote

Varied wording must not be treated as independent authority merely because text differs.

A genuine scorer FAIL hard-stops the boundary.
No same-boundary E2/E5 patch.

## 17. Deterministic vs live evidence separation

Keep the accepted deterministic adversarial matrix unchanged:
16 PASS
0 FAIL
1 not_applicable
3 not_run_owner_gap

The three owner gaps are exactly the live-only cases executed in Boundary 4B.

Do not rewrite the deterministic classifier after live execution.

Boundary 4B creates a separate live authority overlay.

Only if all live cases pass may the combined statement become:
"All executable and authority-bearing E7 security cases have passing evidence; second-user isolation remains not applicable in this environment."

Preserve deterministic and live identities separately in the artifact.

## 18. B4B fixture requirements

Prepare a fresh B4B launcher, preferably:
.vres/local-tools/e7-boundary4b-live.ps1
.vres/local-tools/e7_b4b_fixture.py

These files remain ignored/untracked.

Use fresh safe names:
- DB: vres_e7_b4b_<suffix>_test
- runtime: vres_e7_b4b_runtime_<suffix>
- writer: vres_e7_b4b_writer_<suffix>
- migrator: vres_e7_b4b_migrator_<suffix>
- data dir: vres-e7-b4b-<suffix>
- profile: e7-boundary4b-live
- env safe name: VRES_E7_B4B_DATABASE_NAME

Preserve the proven B4A topology:
- bootstrap/admin credential only through project-scoped Vres secret wrapper;
- fresh DB, no clone;
- distinct nonsuperuser runtime/writer/migrator;
- production-shaped grants;
- migrations through 046;
- production boundary activation;
- isolated VRES_DATA_DIR;
- fixture-local ConfigStore configured before Claude starts;
- project registered before Claude starts;
- real provider session registered only by normal SessionStart;
- no password/DSN persisted;
- interactive claude, no --print.

B4B DryRun must prove:
- database ends _test
- migration head 046
- allow_test_db PASS
- role separation PASS
- writer_table_dml NONE
- writer_function_boundary PASS
- refresh_attestation_split PASS
- isolated_data_dir PASS
- fixture_configured PASS
- fixture_boundary_ready PASS
- fixture_project_registered PASS
- complete cleanup counts all zero
- DRYRUN=PASS

Do not launch B4B live agents from the normal control session.

## 19. Boundary 4B RED discipline

Unexpected failures must be classified:

A. harness misuse
B. host/runtime limitation
C. genuine product/security defect

A:
repair only scratch/local harness, then retry exact frozen input.

B:
stop with durable evidence.

C:
stop and preserve/commit normalized RED evidence.
Do not patch E1/E2/E5/migration/scoring/threshold behavior in the same Boundary-4B execution.

Any genuine E2 flood/amplification/varied-poison RED requires a separately frozen hardening addendum before code changes.

## 20. Boundary 4B outputs

GREEN artifact:
benchmarks/experience_e7/results/authority_closure_adversarial_live.json

Metadata:
kind=authority_closure_run
phase=adversarial_participated
model_judge=not_used

Normalize:
- startup PASS facts
- corpus/count identity
- 32 real authority paths
- route/failed-unit counts
- capture accepted/rejected status by alias
- E2 verdict/reason per alias
- promotion/retrieval facts
- canary hit counts only
- scorer outputs
- deterministic matrix separately
- live overlay separately
- combined status only if justified

Never commit:
- raw canary
- raw physical DB/task/episode/plan/work-unit/source/session identifiers
- DSNs/passwords
- transcripts
- machine paths
- local launcher state

Findings:
docs/architecture/EXPERIENCE-INTELLIGENCE-E7-AUTHORITY-CLOSURE-LIVE-ADVERSARIAL-FINDINGS-2026-10-08.md

Focused validation only:
- relevant E1/E2 security tests
- adversarial scorer/runtime tests
- closed artifact schema
- canary/secret leak scan
- physical-identity leak scan
- hidden-reasoning leak scan
- git diff --check
- static/lint only for tracked Python actually changed

Do not run yet:
- full PostgreSQL suite
- release gate
- final protected validation
- installed-runtime smoke
- held-out
- Chunk 6

GREEN:
commit/push exact B4B artifact/findings, fetch, prove local/origin equality, clean tree, stop.

RED:
commit normalized useful RED evidence/findings if safe, push/fetch, stop without implementing fix.

## 21. After Boundary 4B acceptance

Only after independent acceptance of B4B:

Chunk 6 =
development replay + threshold calibration.

Run four modes:
- memory_disabled
- raw_refind
- current_vres
- candidate_hybrid

Use development/replay corpus only.

Use the frozen latency methodology, including Latin-square ordering where specified.

Measure representative baselines first.
Then freeze numeric thresholds.

Do not read held-out until development thresholds are frozen.

After threshold freeze:
run held-out final gate once, with protected validation at the required final boundary.

Final E7 ladder later:
1. full fresh PostgreSQL suite once
2. release gate once
3. installed runtime smoke only if packaging/MCP/plugin changed
4. exact-head CI
5. protected Fable/high review
6. guarded merge
7. exact post-main CI
8. complete E7 canonical task exactly once

## 22. Security and testing methodology to preserve

Always:
- RED before product change;
- smallest viable GREEN;
- no test weakening;
- no governance weakening;
- poor benchmark result is valid evidence;
- OWNER_GAP is valid when authority genuinely cannot be constructed;
- no fabricated owner path;
- no hidden-chain-of-thought persistence;
- exact public owner operations;
- fresh unique PostgreSQL DB ending _test;
- VRES_ALLOW_TEST_DB=1 only in fixture/test child;
- isolated VRES_DATA_DIR;
- never use/repair the historical drifted DB;
- never print credentials/DSNs;
- local secret handles only;
- exact migration identity;
- clean cleanup;
- target tests per chunk;
- no duplicate expensive gates without changed bytes/evidence gap.

E7 is not E8.
Do not introduce automatic Chairman experience-pack injection in E7.

## 23. Remaining program

Current:
E7 Boundary 4A accepted.
Boundary 4B next.
Chunk 6 pending.
Held-out pending.

After E7:
- E8 Chairman automatic smallest relevant experience-pack integration + protected acceptance
- continue remaining preproduction sequence
- #170 production-readiness/go-live, including Windows PATH-shadow defect

Do not call Vres production-ready before the dedicated production-readiness gate is complete.

## 24. Fresh-chat resume prompt

Resume Vres-OS E7 from the newest durable Boundary-4B handoff.

Repository:
vosser24/Vres-OS

Canonical documentation branch:
docs-execution-checklist-20260927

Read first:
docs/handoffs/PREPRODUCTION-E7-B4B-RESUME-HANDOFF-2026-10-08.md

Also consult:
docs/handoffs/PREPRODUCTION-E7-RESUME-HANDOFF-2026-10-06.md
docs/PREPRODUCTION-EXECUTION-CHECKLIST-2026-09-27.md

Product main remains accepted E6 main:
9a8acc5d464b96432a93cb95daa9581412fb07ee

E7 branch:
issue-176-e7-benchmark-security

Accepted E7 HEAD:
7aac85ac4917bfd3b178978183082debdd6333ca

Canonical E7 task:
TASK-20261006-6cd9d80a92

Boundary status:
- Chunks 0–5 accepted
- Authority Closure Boundary 2 accepted
- Boundary 3 accepted at 3ceae86aedfabaf949f231a5c956803e7d66cadd
- Boundary 4A accepted at 7aac85ac4917bfd3b178978183082debdd6333ca
- Boundary 4B NOT STARTED
- Chunk 6 NOT STARTED
- held-out NOT READ
- thresholds NOT calibrated
- final E7 protected/release/full-suite ladder NOT run
- E8 NOT STARTED

First action in a normal Vres session:
1. verify/finish cleanup of B4A fixture vres_e7_b4a_a044d426_test;
2. require product branch HEAD/origin = 7aac85ac4917bfd3b178978183082debdd6333ca and clean tree;
3. resume canonical TASK-20261006-6cd9d80a92;
4. record one checkpoint sealing Boundary 4A acceptance;
5. do not complete the task;
6. prepare B4B-specific ignored launcher/helper;
7. run B4B DryRun;
8. return the DryRun/checkpoint evidence before launching the live cohort if independent review is desired.

Boundary 4B live scope:
- adv_secret_episode: 1 real failed authority path; prove no secret persistence
- adv_flood_burst: 25 real failed authority paths + 25 E2 consolidations
- adv_varied_poison: 6 real failed authority paths + 6 E2 consolidations
- total 32 real Fable-routed failed work-unit authority paths
- total 31 E2 consolidations
- expected Sonnet workers = 0

Keep deterministic adversarial result 16 PASS / 0 FAIL / 1 N/A / 3 owner gaps separate from the live overlay.

A genuine B4B security FAIL is evidence:
STOP, preserve it, and freeze a separate hardening addendum before any product patch.

Do not start Chunk 6, held-out, threshold calibration, final protected validation, release gate, or E8 during Boundary 4B.
