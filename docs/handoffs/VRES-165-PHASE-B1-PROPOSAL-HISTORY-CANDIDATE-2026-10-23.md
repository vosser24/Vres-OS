# Vres-OS — #165 Phase B1 candidate-only Chairman proposal history

Date: 2026-10-23, Europe/Athens.
Repository: vosser24/Vres-OS.
Current source branch: feature/165-chairman-policy-foundation-20261023.
Current documentation continuity branch: docs/chatgpt-continuity-20261023.
Status: **SOURCE IMPLEMENTATION COMMITTED, INDEPENDENT PHASE B1 WINDOWS TEST NOT_RUN**.
This is NOT operator authorization, Opus Chairman activation, runtime release integration or a successful physical model test.

## 0. Authoritative source checkpoint and parent chain

- Current Phase B1 source HEAD: **f8237bb301dec160f33cab524727e6a0ec79b2c0**.
- Immediate source parent: **9ae4f713c28facabb6e1e098ade38a3483cfa4f8**.
- Initial Phase B1 source commit: **5c053be5e23ff7fd86dce26180976d5f950b853d** (parent exactly ACCEPTED Phase A R2 SHA below).
- Developer-only bounded test-preflight correction: **9ae4f713c28facabb6e1e098ade38a3483cfa4f8**.
- Developer-only malformed-Unicode refusal refinement: **f8237bb301dec160f33cab524727e6a0ec79b2c0**.
- Exact independently ACCEPTED Phase A R2 source: **11f2f8689308dfe43e482bca73aa57bb6467c788**; prior Phase A R1 source 9c919271ba63fb979478c62abaf6c2c3d2679ae7 was independently REJECTED.
- Phase A R2 is supported by a Windows CRLF checkout, ONE authorized three-module pytest invocation, **53/53 PASS**, exit 0, final Claude **ACCEPT OFFLINE ONLY**. The new Phase B1 code DOES NOT inherit this acceptance.
- GitHub comparison Phase A R2..latest Phase B1: ahead by exactly three commits, behind zero, and across all three commits exactly TWO ADDED paths (no old source modifications):
  - src/vres_os/chairman_policy_history.py
  - tests/test_chairman_policy_history.py
- Latest B1 source tree: **678b9fd339106e89330c87a851e49cf5faf47d4f**.
- Source branch has no reported GitHub CI status checks for B1; do not invent local or remote PASS.
- Original installed personal Vres release: 20261022172833-4d82147b, from P2 source 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c. It has NOT been changed, launched or upgraded to Phase A/B1.

## 1. Scope and design — proposal history is NOT authority

Issue #165 Chairman policy needs versioned serialization/history/supersession plus a separately governed Opus/medium control-plane activation path. Phase A provided a pure, unactivated opus/medium policy candidate and deterministic Chairman agent-template rendering. This Phase B1 implements only the in-memory proposal-history model.

The pure standard-library src/vres_os/chairman_policy_history.py adds:
- Immutable, bounded ChairmanPolicyProposal records with strictly positive, sequential proposal number matching ChairmanPolicy.version; exact supported family/effort inherited from Phase A.
- One initial candidate (v1 opus/medium) and explicit v2+ requested-candidate supersession; an expected previous SHA-256 comparison prevents a stale caller from appending to an older in-memory history.
- Deterministic canonical JSON serialization/deserialization with strict schemas, forbidden duplicate/unknown/missing fields, bounded document/proposal count, rejected non-JSON numeric constants, Unicode/control/line-separator/invalid rationale refusal and bounded rationale length.
- SHA-256 digest over canonical proposal bytes, hash-chained supersession references, and derived history digest with strict sequence and no-op refusal.
- A manifest containing ONLY a candidate proposal count, content identities and state=candidates_only. No approved/active/installed or observed-physical-model claims.
- Explicit NON-GOALS: no persistence to real user profile, no policy activation/approval issuance, no bypass of protected Fable governance, no host or model client calls, no secrets/vault access, no filesystem/database/network operations.

Three source commits were made to this B1 tranche because ChatGPT found and corrected test-contract errors before external reviewer dispatch. Initial: 5c053be5. Follow-up: 9ae4f713 fixed invalid policy-version test assumptions, slotted-dataclass test introspection, strict Unicode line separators and duplicate JSON field error handling. Final: f8237bb3 rejects lone surrogates before UTF-8 length encoding. These patches were NOT represented as independently tested; their exact Git parent chain remains reconstructible.

**Security boundary:** A history entry's reason, version or SHA-256 DOES NOT authenticate the user's consent, a model provider or a trusted validator. Hashes detect relative content changes only when anchored externally. A later installer may NEVER trust "latest_proposal" as the ACTIVE Chairman without separate trusted user-event authority plus protected validation and verified pinned release materialization. There is no auto promotion based on telemetry. An attacker who can rewrite all history bytes and the reference digest is not stopped by content hashes alone.

No change in the installed chairman.md Sonnet/high frontmatter, Fable/high routing-arbiter or validator, Sonnet/medium routine workers, Opus/high deep worker, model_policy.py advisory DB selection, migration pins, installer scripts, secrets boundary or live database.

## 2. Frozen independent B1 acceptance contract

Use ONE new Windows detached review worktree, separate from all R1/R2 Phase A evidence:
C:\Projects\Vres-ChatGPT-Review-165B1-20261023

Expected HEAD: **f8237bb301dec160f33cab524727e6a0ec79b2c0**.
Expected parent HEAD^: **9ae4f713c28facabb6e1e098ade38a3483cfa4f8**.
Accepted source ancestor: **11f2f8689308dfe43e482bca73aa57bb6467c788**.
Changed paths from accepted Phase A to B1: exactly two NEW files listed above. Diff --check and clean worktree mandatory.
Original Windows anchor worktree C:\Projects\Vres-P2F-Postinstall-Hardening-20261022 remains pinned at 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c; use it read-only for fetch/worktree-add ONLY after full strict preflight. Do not reset it, any old reviewer directory or installed release.

After worktree confirmation, Claude as independent evaluator (no source-writing authority) should read only exact B1 module/tests and relevant Phase A policy interface, verify no installed/module wiring and review immutable history, schema/typing, digest chain, no-op/stale rejection, canonical round trips, Unicode/malformed data, lack of false "approval" claims. Inspect tests/conftest.py and source isolation fences before tests; BLOCKED if unsafe or unexpectedly invoked Vres. Avoid external model/DB/credential network routes.

**Proposed ONE offline Python 3.12 pytest command (NOT RUN YET):**

    py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_policy_history.py tests/test_chairman_policy_materialization.py

The new selected history tests exercise valid v1 request, v2 supersession and digest chain, no mutation of earlier values, exact stale reference refusal, incorrect version/type/no-op refusal, Unicode printable rationale and control/surrogate restrictions, unknown/duplicate JSON and fake active/approved fields refused, tampered/deleted/reordered entries, invalid nesting/oversized document and absence of direct DB/vault/provider/activation APIs. Existing Phase A policy materialization regression module is deliberately included because history uses its strict policy types.
Do not install dependencies or run broad/integration/DB tests to make evidence pass. No rerun of unchanged P2-A1 or Phase A's plugin/continuity suite just for this source-only change.

Reviewer must report exact R2→B1 commit ancestry, exit code, selected/passed/failed/error/skipped/deselected counts, worktree cleanliness, test isolation and all precise defects. ACCEPT / REJECT / BLOCKED verdict is scoped to B1 OFFLINE ONLY. A failure is passed back to ChatGPT for bounded correction on the same source branch, not repaired by Claude.

## 3. Completion and release contract still open

**#165 remains PARTIAL / OPEN** despite Phase A ACCEPT and B1 source publication. Next after independent B1 acceptance should be Phase B2: operator-authorized policy record/history and genuine trusted authority event/protected validation; then Phase B3 deterministic *staged* managed release agent materialization, exact source/template/policy/rendered hashes, rollback and no silent unavailable Opus fallback. Physical host model/effort/token/cache/performance/validation evidence must later come from actual host observation; #169 live acceptance is NOT yet authorized. Do not claim that Opus 5.x or future generation resolution was verified by a string alias.

Also carry forward Phase A reviewer nonblocking I1 through I5 (JSON recursion-test strength, nonessential 4097-space ID, frozen dataclass low-level bypass when used as trust, YAML control separators, style/test no-I/O strength). Phase B1 rationale validation explicitly rejects control and separator categories but does not retrofit Phase A template frontmatter; that separate risk remains. Do not retroactively rewrite the already accepted Phase A exact SHA.

## 4. Program state and permanent safety holds

P2-A1 database-target guard R4 independent OFFLINE ACCEPT at 3ba41d5ae6b8f2c2abd93d27f82cce0755878237, 183/183 selected tests PASS; earlier R1-R3 reviews REJECT preserved. No merge/install.
GitHub product main last verified 9a8acc5d464b96432a93cb95daa9581412fb07ee, behind the P2 and #165 source. Old canonical docs/historical K0 handoffs remain intact; new docs branch is separate.

LIVE_SCHEMA_048_INCIDENT=OPEN; D2=OPEN; F2=QUARANTINED; R0_DB_READ=NOT_RUN; NATIVE_TRUST_APPROVAL=NOT_GRANTED; K0_T1=BLOCKED; L-04=OPEN; POSITIVE_PRODUCTION_TRUST_ISSUANCE=DISABLED. PostgreSQL service last reported STOPPED; absolutely no service contact even for a SELECT. Windows Credential Locker, installed release mutation, global Claude plugin/hooks/settings, actual model activation, schema migrations, K0 signing, trust issuance, PR/merge/force push and live deployment still require separately approved operations. PA-01..PA-08 acceptance remains not complete. All original V-01..V-42 product-development intentions remain active backlog, not enabled runtime operations.

## 5. New-session resume prompt (copy ready)

RESUME Vres-OS from CURRENT GitHub HEAD on docs/chatgpt-continuity-20261023. Read the read-first docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md and this newest #165 PHASE B1 PROPOSAL HISTORY CANDIDATE handoff first, then the R2 Phase A ACCEPT handoff and P2-A1 R4 ACCEPT. ChatGPT develops and commits; Claude independently reviews; user runs strict one-block PowerShell on Windows. Phase A exact independently ACCEPTED source is 11f2f8689308dfe43e482bca73aa57bb6467c788, 53/53 selected offline tests PASS, shipped chairman Sonnet/high unchanged, requested opus/medium not installed. New Phase B1 candidate source HEAD is f8237bb301dec160f33cab524727e6a0ec79b2c0, parent 9ae4f713c28facabb6e1e098ade38a3483cfa4f8, on feature/165-chairman-policy-foundation-20261023, with two NEW history module/test paths only; B1 Windows independent tests NOT_RUN. Next ONE action: create new isolated B1 detached worktree, then independently review only the two selected offline pytest modules. Do not repeat old R1/R2 reviews, touch schema-048 PostgreSQL, activate Opus, access vault, change installed release, merge main or use Fable without normal proof. Preserve R1 REJECT, accepted R2, R4 security and all residual findings. Each substantive response requires a new detailed docs-only continuity commit/index update with actual GitHub SHA readback.

## 6. 2026-10-23 SUPERSEDING operator worktree verification

The operator has successfully created and verified the Windows B1 review worktree: C:\Projects\Vres-ChatGPT-Review-165B1-20261023 at full source f8237bb301dec160f33cab524727e6a0ec79b2c0. Git fetch succeeded, detached HEAD and exact two-path allowlist were checked by the guarded PowerShell script, and VRES_165_B1_REVIEW_READY was printed with no STOP/fatal. The older "worktree NOT created" statement is now HISTORICAL and superseded by [the B1 Windows worktree-verified handoff](VRES-165-PHASE-B1-WINDOWS-WORKTREE-VERIFIED-2026-10-23.md). No B1 Claude/pytest execution has yet been reported. Next: safe Claude launch and one targeted offline evaluation; do not recreate worktree or claim B1 ACCEPT.
