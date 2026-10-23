# Vres-OS — #165 Chairman policy Phase A development and exact resume

Date: 2026-10-23 (Europe/Athens).
Classification: SOURCE FEATURE CANDIDATE PUBLISHED; INDEPENDENT WINDOWS TESTING NOT RUN.
Repository: vosser24/Vres-OS.
Roles: ChatGPT primary developer, Claude independent evaluator, user Windows operator/approval authority.
This document is NOT release permission, a successful test report, or an instruction to start Vres against the schema-048 database.

## 0. Current source and documentation boundary

- New source branch: feature/165-chairman-policy-foundation-20261023.
- New source SHA: 9c919271ba63fb979478c62abaf6c2c3d2679ae7.
- Source parent: 3ba41d5ae6b8f2c2abd93d27f82cce0755878237 (independently R4 ACCEPT for offline database-target-guard scope).
- Source tree: 1da8726b5fa3caa2e56d102cb68fa1e3e2f25989.
- Source changes: ADDED src/vres_os/chairman_policy.py; ADDED tests/test_chairman_policy_materialization.py; MODIFIED plugins/vres-os/agents/chairman.md (one model-routing explanation, not its pinned frontmatter).
- New #165 tests: NOT_RUN. No model/client evidence, installation, worker routing or PostgreSQL behavior has been tested at this source SHA.
- Prior docs HEAD: e8f9229449e356fb22718a1d94115ddfd69fff73 on docs/chatgpt-continuity-20261023; the SHA of THIS new docs commit must be read back from GitHub.
- GitHub main last checked: 9a8acc5d464b96432a93cb95daa9581412fb07ee, unchanged by this source tranche.
- Published original personal P2 source: 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c on personal/p2f-postinstall-hardening-20261022.
- Windows installed release remains 20261022172833-4d82147b from 82c8243 (last reported); not updated, run or inspected by this GitHub code change.

## 1. #165 product contract, state and boundaries

Issue #165 is OPEN. It requires a control-plane Chairman model policy separate from worker-phase model policies, default initial Opus family with medium effort, generation-tolerant aliases (not a dated claude-opus-5-5 ID), deterministic installed agent materialization with source/policy provenance, governed policy history, bounded host-observed model/cost/token/time evidence, no automatic model promotion and explicit unavailable-family behavior without downshift. Protected routing and validation must remain Fable/high; routine workers Sonnet and deep workers Opus. Physical proof belongs to #169, not an offline unit test.

Pre-tranche preview: the shipped Chairman template frontmatter is still Sonnet/high. The current src/vres_os/model_policy.py is the DB-backed worker/phase recommendation path; it is not the Chairman control plane. User explicitly restored all full-scope V-01..V-42 functionality to ACTIVE DEVELOPMENT backlog on 2026-10-22, but held runtime actions remain disabled.

This tranche is ONLY Phase A: a pure standard-library module representing an immutable versioned requested policy snapshot, deterministic canonical JSON, strict rejection of invalid/unknown/duplicate data, and an in-memory renderer of a verified Chairman template whose only modified frontmatter fields are model and effort. Initial requested snapshot is opus/medium. It returns reviewable SHA-256 digests for template, policy, and rendered-candidate bytes. It does NOT write files, persist history, authorize transitions, alter installed agent files, contact a provider, read a vault or DB, or produce host-observed model identity. The source template continues to advertise Sonnet/high until separate approved release integration.

No new model route, deployment, cost measurement, policy promotion or experimental activation is claimed. Worker/validator frontmatter is unchanged: sonnet-expert Sonnet/medium; opus-expert Opus/high; routing-arbiter and validator Fable/high. Source-only text clarification in Chairman instructions separates policy from routed worker pins.

## 2. Frozen offline independent evaluation contract

Windows new detached review worktree: C:\Projects\Vres-ChatGPT-Review-165A-20261023.
Expected HEAD 9c919271ba63fb979478c62abaf6c2c3d2679ae7; expected single parent 3ba41d5ae6b8f2c2abd93d27f82cce0755878237.
Changed file allowlist: precisely the three paths named in Section 0. Worktree must be clean; git diff --check must return 0.
Read tests/conftest.py before executing. Do not run the Vres plugin, PostgreSQL, migrations, setup, installed runtime, real model provider, credential vault or global Claude modification. If Python or Claude attempts database hooks, stop with BLOCKED. No broad or integration tests, installs, test fixture rewriting or source edits.

ONE authorized offline command after isolation preflight:

    py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_policy_materialization.py tests/test_chairman_continuity_contract.py tests/test_plugin_contract.py

Independent Claude review:
1. Verify exact source SHA, parent, branch history, changed-path allowlist and clean Git diff.
2. Confirm default requested policy is version 1 / opus / medium, family alias without a dated physical model, canonical deterministic serialization, rejected duplicate/unknown/type errors and immutable policy snapshots.
3. Confirm byte-deterministic Chairman candidate rendering; original template body, description, name, and unrelated fields intact; only model/effort updated in candidate. Source template Sonnet/high remains unchanged in its frontmatter.
4. Confirm provenance manifest template/policy/rendered SHA-256 correctness, never a claim of installed or observed model evidence.
5. Confirm protected Fable/high and governed Sonnet/Opus worker agents are untouched and ModelPolicyService worker policy has not been silently altered.
6. Check code/test reliability, unexpected file side effects and unsupported input. Do not infer physical host acceptance or #165 completion from a green unit suite.
7. Report exact command, exit code, selected/passed/failed/skipped/deselected where available, and ACCEPT / REJECT / BLOCKED with minimal reproducible code findings. Do NOT edit.
After the report ChatGPT owns any corrections, bounded review re-run and source commit.

## 3. Prior accepted P2-A1 baseline and unresolved release risks

R4 P2-A1 security correction commit 3ba41d5ae6b8f2c2abd93d27f82cce0755878237 was independently ACCEPTED only for 183/183 selected OFFLINE tests. Prior R1 at 5e578e2 (42), R2 at 27f3588 (117), R3 at 2101c67 (153) were REJECTED despite green selected tests. No merge, physical DB test, install or runtime startup followed.

Carry forward R4-1 conditional IPv6 translated destination risk; R4-2 invalid config status availability; R4-3 held-entry terminal control output; R4-4 missing invalid-config test; R4-5 stale help/docstrings. Preserve the detailed R4 handoff, original failures and exact source SHA. Do not rerun R4 solely because docs were committed.

## 4. Absolute safety holds — unchanged

LIVE_SCHEMA_048_INCIDENT=OPEN
D2=OPEN
F2=QUARANTINED
R0_DB_READ=NOT_RUN
NATIVE_TRUST_APPROVAL=NOT_GRANTED
K0_T1=BLOCKED
L-04=OPEN
POSITIVE_PRODUCTION_TRUST_ISSUANCE=DISABLED
POSTGRESQL_SERVICE=STOPPED at last reported operator observation
CURRENT_INSTALLED_RELEASE_RUNTIME_ACTIVATION=NOT_RUN
PA_01..PA_08=NOT_COMPLETE
ISSUE_165=OPEN
SOURCE_165A_TEST_RESULT=NOT_RUN
CHARTER_ONLINE_MODEL_OBSERVED=NO
INSTALLER_POLICY_MATERIALIZATION=NOT_IMPLEMENTED

Do not start/contact the held cluster (even SELECT), run migrations, expose credentials, change Windows global Claude governance, install a new release, issue native trust, sign, merge to main or force push without distinct operator approval.

## 5. Next development sequence and continuity method

1. Operator safely synchronizes GitHub source 9c919271 into a NEW detached Windows review worktree and starts Claude in safe mode with built-in read/search/Bash only, no Vres hooks/MCP. One review of the exact three changed paths plus selected offline tests.
2. User returns Claude's entire sanitized report. If rejected, ChatGPT implements minimal corrections on SAME #165 branch; no modification by Claude. If accepted, annotate **Phase A OFFLINE ONLY**, not #165 fully complete.
3. Then Phase B: governed versioned policy authority/history/supersession and EXACT staged Windows release materialization with hash/policy identity and safe rollback; explicit unavailable-model refusal; never silently activate through a docs change. Separate host-observed physical policy/worker/validator behavior deferred to later #169 when DB safety is independently resolved.
4. Continue other full-scope items from the 42-row register without losing V-36/P2-A1 safeguards or K0 history.
5. Per operator's 2026-10-23 instruction, every substantive Vres development/evaluation response MUST end with a docs-only Git handoff commit on docs/chatgpt-continuity-20261023 and an updated docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md; verify and report both exact source and docs SHAs. Do not edit prior rejected evidence or claim unobserved PASS.

## 6. Copy-ready next-session prompt

RESUME Vres-OS from the CURRENT HEAD of GitHub docs/chatgpt-continuity-20261023, first reading docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md and this #165 Phase A handoff, then the P2-A1 R4 accepted handoff and full 42-item Vres register. ChatGPT owns code and commits; Claude reviews exact Git commits on isolated Windows worktrees; user approves consequential actions. New #165 source SHA is 9c919271ba63fb979478c62abaf6c2c3d2679ae7, parent accepted R4 source 3ba41d5ae6b8f2c2abd93d27f82cce0755878237, feature branch feature/165-chairman-policy-foundation-20261023. Only pure offline Chairman policy materialization has been coded, static template still Sonnet/high; Windows independent evaluation NOT_RUN. The next action is ONE safe operator fetch/worktree and ONE targeted Claude offline evaluation. Preserve all P2-A1 R1-R3 REJECT and R4 ACCEPT evidence, schema-048 no-contact rule, PA holds, installed release 20261022172833-4d82147b and open #165 runtime integration. After each substantive reply commit docs and update continuity index. No repeated source publication, Vres startup, policy activation, PR/merge or background claims.

## 7. 2026-10-23 IMPORTANT OPERATOR SCRIPT ERRATUM (append-only)

The first Windows PowerShell review-worktree instructions emitted by ChatGPT after this handoff used the INVALID 38-character source SHA 9c919271ba63fb979478c62ab6c2c3d2679ae7, missing "af". The GitHub HEAD recorded earlier in this document, **9c919271ba63fb979478c62abaf6c2c3d2679ae7**, is correct and verified. The operator's remote check rightfully STOPPED, a subsequent git fetch succeeded, and an invalid-reference worktree-add FAILED. Because PowerShell continued through individually executed statements, a false final READY marker was printed with no review directory created. No #165 evaluation ran. For the exact preserved failure, strict single-scriptblock remedy, and next operator action, read [the SHA/transcription recovery handoff](VRES-165-PHASE-A-OPERATOR-SHA-ERRATUM-2026-10-23.md). This erratum supersedes the bad SHA in the earlier CHAT RESPONSE; it does not alter the authored source commit.
