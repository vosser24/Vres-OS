# Vres-OS #165 PERSONAL C2-D1B — pinned read-only Chairman doctrine audit and coordinated two-way policy-body/test DESIGN v0

**Authored:** 2026-10-27, Europe/Athens.
**Repository:** vosser24/Vres-OS.
**Product:** one current-user PERSONAL Windows installation, not enterprise IAM.
**STATUS:** **AUTHOR READ-ONLY SOURCE AUDIT + NEW DESIGN DRAFT ONLY** / INDEPENDENT_CLAUDE_DESIGN_REVIEW_NOT_RUN / D1B_SOURCE_NOT_EDITED / D1B_PYTEST_NOT_RUN / D1B_OFFLINE_ACCEPT_NOT_GRANTED / NO_RELEASE / NO_INSTALL / NO_MODEL_ACTIVATION.
**Preceding accepted source gate:** C2-D1 pure offline refusal/diagnostic planner independently OFFLINE_ACCEPT only at feature SHA **358b3554075f87f5b8287fbb37d66fa95ad68b7c**.
**Safety:** **LIVE_SCHEMA_048_INCIDENT=OPEN — absolutely NO PostgreSQL contact, including SELECT.** Do not attempt Vres task/CLI/bootstrap/doctor/health/hook/recovery/persistence probes; VRES_REPLY_GUARD_WARNING and VRES_PERSISTENCE_WARNING remain unresolved.

## 0. Scope and epistemic limitations

This is a **targeted GitHub READ-ONLY audit** of immutable feature source, original P2 source, selected normative current test contracts, protected worker/validator agents, accepted Phase A materializer, model-routing skill, release-artifact schema and the V-07 roadmap entry. ChatGPT read these files through the GitHub connector. No Windows process, Python, pytest, database, provider, installer, user/global Claude file, credentials or physical model inspection occurred.

The Git tree was enumerated successfully at feature tree af1d7349f1e7028145567b6330a5b25bdc0f5920 (**492 paths, not truncated**). Relevant likely surfaces were identified. This audit **DOES NOT CLAIM every textual source/test/roadmap file was read in full**: an additional bounded source/doctrine cross-reference pass remains mandatory before any future D1B SOURCE commit. Historical documents should be classified as historical observations, not rewritten as live normative agent doctrine.

Independent design verdict has not been requested, nor inferred from preceding C2 V1 DESIGN_ACCEPT, C2-D1 STATIC_PASS or C2-D1 OFFLINE_ACCEPT. The design V0 may receive DESIGN_REVISE; preserve that SHA and correct in a new docs-only review revision, never self-certify.

Read authoritative docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md FIRST. Then the C2-D1 independently accepted handoff docs/handoffs/VRES-165-PERSONAL-C2-D1-INDEPENDENT-OFFLINE-ACCEPT-AND-D1B-DESIGN-NEXT-2026-10-27.md, blob **bf8d81bb64c14d89d55e00caeb30b6b5f6b7d51b**, and C2 corrected V1 accepted concept, docs/architecture/VRES-165-PERSONAL-C2-REVERSIBLE-CHAIRMAN-MODEL-CHANGE-DESIGN-V1-2026-10-26.md blob **407e36528c5cda925517ae0a9db6ba826069aac9**. Original V0 DESIGN_REVISE, seven V1 informational items, eight D1 informational items and the complete V-01..V-42 roadmap must not be erased or broadened by this proposal.

## 1. GitHub source identity anchored to the exact accepted feature commit

**Review baseline branch:** feature/165-chairman-policy-foundation-20261023.
**Review baseline HEAD:** 358b3554075f87f5b8287fbb37d66fa95ad68b7c.
**Review baseline TREE:** af1d7349f1e7028145567b6330a5b25bdc0f5920.
**Direct parent (C1 R1 independently accepted):** 7ac041018d4ec5a06be07318ecce5e140faccd91.

| Surface | Exact Git blob | Audited role / boundary |
| --- | --- | --- |
| Current feature Chairman agent | 64cba93d6f69960350a0006b594734288f087ccc | plugins/vres-os/agents/chairman.md, 112 numbered lines; frontmatter Sonnet/high, doctrine line 74 |
| Original installed-basis P2 agent source | 6f2239c4dd0d52090d31415c17f763505f93b900 | Same path at P2 commit 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c; fixed Sonnet-default body line74 |
| Chairman orchestration source test | e50c4bfa3a7920b91bdfefbc2bd14f1e9a14fee8 | tests/test_aigo_orchestration_contract.py, Sonnet SOURCE pins lines109/182 and protected worker pins183–185 |
| Phase A renderer | 36e62d6a2712ac305fd4070bac658b94d61d155e | src/vres_os/chairman_policy.py; only model/effort header fields change; body bytes preserved, LF/CRLF kept |
| Phase A renderer test | 4a9e2ea4540bd074351179fb0a68a677acd113f8 | tests/test_chairman_policy_materialization.py; body-preservation tests, source Sonnet/high baseline and DEFAULT candidate Opus/medium |
| Accepted D1 refusal planner | 9cde474f7f9a5450c9faf7cbcbe4a608d317c1fd | Pure deny-only, DO NOT promote to release permit |
| Accepted D1 planner tests | 975ed8f4a5a38c307be48a99f401c1edcbeba67f | 74 observed Windows cases and independent OFFLINE_ACCEPT at exact reviewed prior SHA |
| Fable arbiter agent | 6fde89db42201f7421b1d8bb34fef3947e81e687 | routing-arbiter.md remains model:fable / effort:high |
| Protected validator agent | a8c7bdfeac398401a4640632a1e106ab9bf34dab | validator.md remains model:fable / effort:high |
| Sonnet worker agent | 4ab962742dfe125e7d726ad57ea3adf3e13009f5 | sonnet-expert.md remains model:sonnet / effort:medium |
| Deep Opus worker agent | f1cd42ca4ac7db1daeacb166d4a9ef683076b5c8 | opus-expert.md remains model:opus / effort:high |
| Model routing skill | 9e1a1ba4ae3e6cd3d12aad036f20b88e657777ae | plugins/vres-os/skills/model-routing/SKILL.md, advisory routing and pinned worker/validator controls |
| Protected model policy | b437ee63c65618a4153da9131743a46c6b34b5ca | docs/architecture/MODEL-POLICY.md: Fable/high reviewer non-downshiftable; model_recommend is not installation |
| Current personal release artifact | ddfc1beacad98199b489dc6f56456baf4d519c6a | src/vres_os/release_artifact.py, VERSION=2, Git-object/source-blob pinned |
| Source release input policy | a0cdf3195f0cf0f2a61ce32521a74f78260832f7 | src/vres_os/release_inputs.py, pinned release inputs, not a Chairman model switch |
| Current canonical roadmap V-07 | c6c8c24e4a38efb2e7589017e98b43b2015821df | docs/roadmap/VRES-FULL-SCOPE-FUNCTIONALITY-REGISTER-2026-10-22.md line30: configurable Chairman Opus/medium STILL full-policy UNBUILT |

**Key source comparison:** The original P2 agent and the current feature source agent both contain 112 numbered lines, and a line-by-line read comparison shows their ONLY differing line is line **74**. P2 states "The Chairman itself runs on Sonnet as the default control plane". Current feature line74 already says the Chairman control-plane model/effort follow its own pinned frontmatter, independent from worker routing, BUT still asserts "Opus is reserved for work where deeper reasoning materially improves execution; it is never the default shell or a routine routing model." That latter unqualified sentence is incompatible with an intentionally authorized Opus Chairman as the user-facing shell, even if the worker role should never become the default routine tier. This is a **source doctrine contradiction**, not a permission to modify installed P2.

**Source test contradictions:** tests/test_aigo_orchestration_contract.py line109 requires literal "model: sonnet" in current source Chairman agent; line182 requires the same. Lines183–185 assert router Fable/high, routine worker Sonnet and deep worker Opus/high. Those latter pins are **PROTECTED** and MUST NOT change merely because the Chairman parent policy changes. Source agent line74 and lines40–46/56–59/107 govern routing, assurance and worker dispatch. Model-routing skill likewise says routed expert tier is independent from Chairman parent. Keep all protected checks and mechanical no-agent-model-override rules.

**Phase A distinction:** DEFAULT_CHAIRMAN_POLICY in accepted src/vres_os/chairman_policy.py is intentionally version1 Opus/medium as an inert requested policy, while SOURCE template remains Sonnet/high. tests/test_chairman_policy_materialization.py lines ~137–145 assert source Sonnet baseline and that materialization changes only frontmatter, never BODY; current source body policy neutrality is therefore a prerequisite. A default or claimed rendered SHA is diagnostic, NEVER a live-installed model or consent.

**Release distinction:** Original P2 active managed+distribution Chairman last READ-ONLY observed Sonnet/high, LF 24208 bytes SHA256 a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73, matching original P2 Git source. Current feature SOURCE body is a DIFFERENT Git blob, not the installed P2 bytes. Strict personal release_artifact VERSION=2 ties published files to their original Git blob identity; a policy-rendered candidate with altered model/effort cannot silently masquerade as original source blob. No D1B v3 release schema, publisher, signing, plugin-only updater or installer is designed/implemented in this source-stage proposal.

## 2. Proposed minimal D1B source correction contract — no writes yet

**Goal:** A newly reviewed, versioned SOURCE Chairman body semantically compatible with either policy-pinned **Sonnet/high** OR **Opus/medium**, including a future genuine transition back to Sonnet, while keeping worker/validator and the accepted Phase A materializer unchanged.

**Proposed source baseline handling:** Keep source agent frontmatter **Sonnet/high** as a fixed, reviewable baseline template. Explicitly label it as a *source template default*, NOT an unconditionally required installed Chairman model. Pure materialization of that same template with policy (sonnet,high) must be byte-identical. Materialization with canonical policy (opus,medium) must change EXACTLY model/effort frontmatter fields, preserving whole policy-neutral body and line-ending convention; reverse rendering from reviewed source to Sonnet/high must not require rewriting the body or inventing new policy/history consent. This is source-only evidence, no physical install.

**Required line74 doctrine correction, proposed semantics not yet final prose:**
- Chairman is user-facing parent/control plane; its own model/effort follow separately pinned, independently approved *installed policy* when one exists.
- Shipped SOURCE template Sonnet/high is a baseline, not a proof of installed or loaded family.
- Governed ordinary deterministic workers remain Sonnet; the routed **Opus expert worker** is conditional deep-reasoning escalation, **not default routine WORKER**. Do NOT say unqualified "Opus is never the default SHELL"; that is false when Opus is approved for Chairman parent.
- Only pinned Fable/high can arbitrate genuinely ambiguous routes and serve as protected independent validation; an Opus Chairman does not become an alternative Fable validator, does not turn Opus execution routine, does not bypass protected validation, and does not grant model override authority.
- A refusal from missing independent user event E, validator V, CAS, install warrant W, publisher or loader is not solved by making agent prose neutral.

**Source/doctrine full-scan obligation before implementation:** In addition to inspected agent/test/policy contracts, check all relevant CURRENT normative source/test/docs for fixed Chairman-Sonnet claims, including tests/test_aigo_orchestration_contract.py and roadmap V-07, architecture model-policy docs, release documentation and operational templates. Record exact file/line/sha, classify as (a) runtime enforceable, (b) current test contract, (c) current normative docs, or (d) immutable historical handoff. DO NOT edit history solely to match new source. This initial audit is TARGETED and does NOT assert exhaustive negative results elsewhere.

## 3. Proposed future SOURCE commit allowlist (CONDITIONAL, not approved yet)

If the independent design reviewer accepts the plan, a future separately bounded source commit MAY change precisely:
1. **MODIFY** plugins/vres-os/agents/chairman.md — policy-neutral body, source Sonnet/high header retained, routing/governance meaning unchanged except disambiguation of Chairman-vs-Opus-worker roles.
2. **MODIFY** tests/test_aigo_orchestration_contract.py — explicitly make lines109/182 tests of reviewed Sonnet/high SOURCE BASELINE only, preserve protected Fable-high arbiter and validator + Sonnet worker + Opus/high expert pins; test required doctrine/role separation.
3. **ADD** tests/test_chairman_policy_aware_body.py — narrow pure in-memory acceptance tests of **BOTH Sonnet/high and Opus/medium**, reversibility, exact policy materialization/body bytes under LF and CRLF, fixed role pins, malformed and contradictory doctrine, no installed/protected authority and no positive API.

**ALL other source files protected unchanged** unless independent design reviewer provides a concrete blocking reason to revise this plan first, including:
- src/vres_os/chairman_policy.py, tests/test_chairman_policy_materialization.py;
- src/vres_os/chairman_c2_offline_planner.py and its accepted tests;
- C0 preview, C1 CLI, B2B denial, routing/validator/worker agents, test conftest, pyproject;
- installer/release_artifact.py/install_recovery.py/install.ps1/active pointer/release files, global Claude configuration, and any PostgreSQL-backed state.

This allowlist is a **proposed** minimal source-change surface. The independent reviewer must assess whether leaving current Sonnet SOURCE assertions but merely clarifying them is sufficient; otherwise DESIGN_REVISE, not silent code changes. No SHA or test acceptance is inherited by new source code: new commit -> new review -> one scoped Windows pytest -> independent report-only OFFLINE_ACCEPT.

## 4. New D1B source TEST matrix — gate criteria proposed, nothing executed

A future additional test file should cover these observable pure source properties:
1. **Sonnet baseline** (LF): explicit source family=sonnet, effort=high, exact policy-neutral body; Phase A render with Sonnet/high policy equals source bytes.
2. **Opus requested candidate** (LF): render Opus/medium with current reviewed new source body unchanged byte-for-byte, header model/effort only, verify content SHA actual bytes; output strictly DIAGNOSTIC_ONLY / NOT_INSTALLED / NOT_AUTHORIZED when shown, no install-ready.
3. **CRLF parity:** both above cases from uniform CRLF template, no mixed-newline normalization; body preservation.
4. **Return to Sonnet**: render reviewed SOURCE template with Sonnet/high after considering previous Opus diagnostic context, no request to invent a fake B1 history hop; pure byte output only, not a replayed consent.
5. **Routing role invariants**: Sonnet deterministic worker default, Fable/high arbiter and validator, Opus/high routed expert only when allowed, no Agent.model override; no "Opus is never default shell" contradictory source body.
6. **Negative original P2 doctrine**: original P2 fixed Sonnet body is NOT a suitable source for a frontmatter-only Opus install; preserve its diagnostic-only rejected history, do not relabel old original digest as releasable.
7. **Negative missing release/provider**: even perfect source grammar and tests do not create trusted publisher, independently authenticated H0/E/V/CAS/W, installed/loaded state or F1 permit.
8. **No side effects**: no new runtime/DB/installer/protected Claude interaction in the authored pure tests. The existing conftest AppData fence is process-level, not host proof.
9. **History**: keep accepted B1 adjacent no-repeat and protected G/L/Q semantics untouched; no fabricated Sonnet hop to retry failed Opus proposal.
10. **Scope**: treat source-body review as NOT equivalent to running Claude's effective model; no actual provider family selection occurs in these source-only tests.

Static review MUST examine test assertions to prevent accidental tautological fixtures, fabricated positive checks or an overly broad string-only assertion. Preserve all eight D1 informational findings; none is automatically resolved by D1B.

## 5. Independent Claude DESIGN_ONLY review gate — NOT YET RUN

This docs-only D1B design v0 needs its own guarded detached Windows DOCUMENT review checkout. Reviewer should read:
- This design file IN FULL.
- Latest accepted C2-D1 final handoff and corrected C2 V1 R1 design/acceptance and B2B R3 erratum as relevant.
- Actual current accepted SOURCE D1 checkout at **C:\Projects\Vres-ChatGPT-Review-165C2-D1-20261027** (existing unchanged detached source SHA 358b355...): FULL latest plugins/vres-os/agents/chairman.md, FULL tests/test_aigo_orchestration_contract.py, selected actual Phase A policy+tests, model-routing skill and ALL four protected worker/arbiter/validator agent fronts/bodies, original P2 doctrine quote as provenance.
- The docs-only checkout may contain a DIFFERENT OLDER SOURCE snapshot; do NOT confuse that with the accepted CURRENT FEATURE source. Claude can use exact ABSOLUTE read-only paths for the separate D1 worktree, disclose any permission/read barriers, and must not claim SHA hashing without Git.

**Claude permitted tools:** Read, Glob, Grep ONLY, scoped to those two explicit worktrees. No Bash, Git, PowerShell, Python, pytest, MCP/Vres tasks, database even SELECT, provider, subagents, installed current-user files, hidden source writes or runtime activation.

**Expected independent decision:** exactly one **DESIGN_ACCEPT**, **DESIGN_REVISE**, **EVIDENCE_BLOCKED**, with full vs partial file coverage and itemized BLOCKING vs INFORMATIONAL findings. Evaluate two-way policy-neutral source doctrine, Sonnet worker vs Opus worker vs Chairman family, all protected Fable pins, source-header baseline test semantics, exact future allowed changed paths, diagnostic-only outputs, no real F1 positive grant, Phase A body invariant, release v2 incompatibility and source/doctrine scan completeness. Explain any additional source/test files required before approving future implementation. Final marker:

\`VRES_165_PERSONAL_C2_D1B_DESIGN_REVIEW_COMPLETE\`

Even DESIGN_ACCEPT authorizes considering a future bounded SOURCE candidate, **NOT** a Git source change without a separately verified new feature SHA/test gate and **NOT** an installed model switch.

## 6. Roadmap, safety and next execution boundary

The existing PERSONAL backlog remains the full V-01..V-42 roadmap. This plan is only the V-07 (#165) Chairman selection body/test compatibility prerequisite; separate Visual Studio/legacy-project onboarding, personal continuity, secure reusable current-user credential handles and production work remain in backlog. Avoid disproportionate enterprise rollout machinery while preserving actual protected F1 stop-contract.

LIVE_SCHEMA_048_INCIDENT=OPEN, NO PostgreSQL contact even SELECT; current-user installed P2 Chairman last observed Sonnet/high, LF 24208 bytes and SHA a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73; effective running Claude session not verified, Opus/medium UNINSTALLED. H0/Hn/E/V/CAS/W, publisher, independent loader/host #169 and B2C release actor remain OPEN. VRES_PERSISTENCE_WARNING and VRES_REPLY_GUARD_WARNING MUST NOT be investigated via Vres task/DB. No credential/vault/keyring, global Claude config, native provider/Fable, signing, main merge or installer action.

**ONLY NEXT operator gate** (after THIS documentation draft is committed and exact GitHub SHA/tree/blob read back): guarded detached Windows DOCS worktree checkout, then independent Claude DESIGN_ONLY report. No fresh source checkout, no D1 Python tests, no source edit, no installer or model activation. If DESIGN_REVISE/EVIDENCE_BLOCKED, preserve this draft and create a bounded review correction/new docs SHA. If DESIGN_ACCEPT, stage a separately authorized source-scope implementation and static-first test ladder.
