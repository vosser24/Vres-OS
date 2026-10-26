# Vres-OS #165 — PERSONAL C2 reversible Chairman model-selection design v0 (DESIGN ONLY)

**Design date:** 2026-10-26, Europe/Athens.
**Repository:** vosser24/Vres-OS.
**Canonical design branch:** docs/chatgpt-continuity-20261023.
**Current authoritative status:** C2_DESIGN_V0_DRAFT / INDEPENDENT_C2_DESIGN_REVIEW_NOT_RUN / TESTS_NOT_RUN / NO_AUTHORITY_ISSUED / NO_MODEL_ACTIVATION / NO_INSTALLER_RUN / NO_NEW_SOURCE_COMMIT.
**Owner of design and GitHub documentation commit:** ChatGPT. **Independent reviewer:** Claude Code, read-only. **Operator:** current Windows user, explicit fresh permission for any future material actions. This document does NOT itself request or constitute such permission.

## 0. Executive decision and decision boundary

**Proposed outcome, NOT performed:** offer a clear personal current-user choice to change the Vres Chairman's requested model/effort from Sonnet/high to Opus/medium, with byte-exact source provenance, an independently authorized and recoverable release transition, and an explicitly separately authorized way to return to the prior policy.

**Architecture decision v0:** use a **new independently verified immutable personal release candidate and a controlled active-release transition**, rather than directly patching the existing managed Chairman file in place. The current installer ties its managed plugin to pinned source release objects and a release manifest; silently changing one managed file would make the active pointer and recorded release identity untruthful. The current installer is NOT a validated model-switch API and must not be executed while the schema-048 incident is held.

**Two distinct meanings of approval:**
- Practical USER EXPERIENCE: show the operator the target, requested model/effort, old/new digests, revert plan, and ask for a clear affirmative choice in an independently rendered UI. A ChatGPT/Claude prompt, ordinary PowerShell confirmation or same-user JSON is NOT currently a trusted F1 authority event.
- Protected #165 F1 AUTHORITY: old completed policy/history G and latest ledger L must come from an independently trusted anchor; a real T2-resistant consent/anchor provider, independently governed protected validator, protected CAS and a distinct new install warrant W must exist. **None exists or has been authorized now.** This is the normative B2B R3 contract (DESIGN_ACCEPT strictly for B2B-1 DENY-ONLY) and mandatory R3 erratum; do not bypass it by relabeling a local yes/no question as verified user presence.

C2 DESIGN_ACCEPT, if later issued by Claude, will mean design review acceptance ONLY, not installed permission, source tests, F1 completion or a mandate to use a provider. The user specifically requested progress on design, not immediate switch. Continue PERSONAL single-user pragmatism without falsely relaxing already adopted protected boundaries.

## 1. Grounded factual baseline and sources

| Evidence | Exact supported value | Meaning and limit |
| --- | --- | --- |
| **Installed current-user Vres product** | Vres-OS, release **20261022172833-4d82147b** | Operator's constrained read of active-install.json pointer, not independently observed live session |
| Original installed release source | commit **82c82430b38f93bd6b9d5c3af3b5de9c1368af9c**, plugin Chairman Git blob **6f2239c4dd0d52090d31415c17f763505f93b900** | Public immutable repository source, not itself an independently trusted T2-resistant publisher root |
| Actual current-user managed agent | **Sonnet/high**, UTF-8 **24208 bytes**, uniform LF, **SHA-256 a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73** | Operator's bounded managed-file read; current runtime model NOT checked |
| Corresponding release distribution agent | Sonnet/high, 24208 bytes, LF, exact same SHA-256 **a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73** | File-level equality to selected release copy, not live physical identity |
| Independent source reconciliation | ChatGPT independently recomputed original P2 git Chairman UTF-8 LF SHA-256 **a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73** | Actual installed files are byte-consistent with P2 release bytes at observation time |
| **ONLY a hypothetical P2-derived candidate** | Requested Opus/medium, 24208 bytes LF, SHA-256 **b73e7497454a464f6b6bc1df00f42422696da786a07eb2936ae73ad73abedf54** | Pure frontmatter-only computation, **not created, installed or approved** |
| Separate newer accepted C1 preview source | feature HEAD **7ac041018d4ec5a06be07318ecce5e140faccd91**, source plugin blob **64cba93d6f69960350a0006b594734288f087ccc** | Different body/release source; NOT installed. The C1 CRLF candidate SHA **d0cd8821fcddb6ef76344d513e0f33595ab6fc2954db800c5960c1198d64550f** MUST NOT be treated as the installed-release candidate |
| Newer C1 source/test acceptance | independent STATIC_PASS, Windows selected 29 individual PASS/exit0, report-only **OFFLINE_ACCEPT**, successful one manual read-only source preview | Source-checkout CLI read-only, not registered/installed and not user or F1 consent |
| Protected source/authority scope | accepted Phase A policy materializer blob **36e62d6a2712ac305fd4070bac658b94d61d155e**; B2B R3 design blob **110ccffcbc1c1f00f5b674b4836fed432708f4ea**; post-review erratum blob **e7536be90246ad3894befb8a2f5e158d3088028d** | Phase A may calculate pure bytes. R3 positive trust/installer/runtime steps are DEFERRED, not delivered |

Read-first durable factual handoff:
- docs/handoffs/VRES-165-PERSONAL-C2-INSTALLED-CHAIRMAN-MANAGED-RELEASE-BYTES-READONLY-PASS-AND-REVERSIBLE-C2-DESIGN-NEXT-2026-10-26.md (current installed file observations and independent P2 SHA).
- docs/handoffs/VRES-165-PERSONAL-C1-R1-INDEPENDENT-OFFLINE-ACCEPT-AND-READONLY-MANUAL-PREVIEW-NEXT-2026-10-26.md.
- docs/architecture/VRES-165-B2B-TRUSTED-CHAIRMAN-AUTHORITY-CONTRACT-R3-2026-10-26.md and docs/architecture/VRES-165-B2B-R3-POSTREVIEW-ERRATUM-2026-10-26.md (normative prior R3 DENY-ONLY acceptance and deferred B2B-2/B2C/B2D gates).
- Original P2 installer install.ps1 Git blob **29a5f0da235021cc8c5607eb92218e5ea98145fa**, src/vres_os/release_artifact.py blob **ddfc1beacad98199b489dc6f56456baf4d519c6a**, src/vres_os/install_recovery.py blob **1c0d585645280678af4875f2842a3350f9805e0a**, all at P2 source commit 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c.

## 2. Terminology and strict separation of observation, configuration and authority

- **SOURCE_TEMPLATE_PREVIEW:** pure developer/source checkout bytes, reported baseline caller-supplied, proposed render not installed (already accepted C0/C1). Never an installation warrant.
- **MANAGED_FILE_OBSERVED:** current-user managed Chairman on disk, read-only header and digest. Now observed for P2 on 2026-10-26. Could differ from what Claude actually loads.
- **RELEASE_DISTRIBUTION_OBSERVED:** bytes and manifest-released counterpart under selected release. Matches observed managed file, but does not prove release trust root or host execution.
- **EFFECTIVE_HOST_SELECTION / PHYSICAL_MODEL_OBSERVED:** host-native selected/resolved provider family, effort and fallback under real session/project/managed overrides. Currently NOT verified; separate #169/B2D physical trial with appropriate independent provenance. Do not claim active Opus from bytes alone.
- **REQUESTED_POLICY:** alias family "opus" and effort "medium", with policy version and canonical digest. The requested alias may resolve to future physical Opus generations subject to pre-state approved family rules; no hard-coded dated model ID and no silent fallback.
- **L / G / Q:** protected latest proposal history / last independently COMPLETED governing installed policy-pins / currently pending policy intent. L is not necessarily G; Q=RECOVERY remains blocked and does not clear itself. These are protected concepts in R3, NOT current trusted store contents.
- **E / V / W:** a verified proposal consent event / independent protected validation / distinct fresh installation consent warrant, produced by different trusted services under R3. Ordinary chat or operator script output cannot instantiate these.
- **READONLY_DIAGNOSTIC:** can list paths, compare hashes, show preview only. Read-only support is not a new positive trust API.

The output vocabulary must never merge these layers: "candidate rendered" != "policy authorized" != "installed SHA matches" != "running model observed". Avoid a single unqualified "CURRENT MODEL" field.

## 3. Why immutable new-release activation is recommended, and what is REJECTED

### Option A — modify managed plugin chairman.md directly: REJECT for governed C2

An ordinary same-user editor could replace only model/effort fields while leaving body intact, but this would break equality with the selected release distribution and manifest. The active-install.json pointer would continue to name a Sonnet/high release even though a file no longer matches. The next Vres installer update/recovery might overwrite or reject the patch. Atomic replacement of one file also does not make the full installed plugin/pointer/loader transition atomic. A same-user backup is useful for troubleshooting but not F1 independent authority or trustworthy rollback.

**Hard STOP:** no in-place mutation of the existing 20261022172833-4d82147b plugin; no "temporary quick model patch" as an approved #165 installation. Do not edit release manifest to fake provenance, do not change release ID without a genuine fully verified release transition.

### Option B — use a separate user/project Claude model override: NOT #165 install path

May be considered later for a **separately labeled session-local model experiment** only after actual host precedence and effective-loader behavior have been reviewed. It may not affect the Chairman agent frontmatter, could override unrelated user/project state and is not equivalent to installed Chairman policy. It cannot close F1/#165 or be promoted as a rollback of installed governance. No host CLI/flag/settings probing is requested now.

### Option C — new pinned immutable policy-bearing release: RECOMMENDED architecture, NOT implemented

A future reviewed release publisher must produce a **new immutable full personal release candidate**, with a distinct release ID and explicit policy binding to an ORIGINAL trusted template. The user chooses Sonnet/high -> Opus/medium for the Chairman only. Existing Sonnet routine workers, Opus deep workers, protected Fable/high validator and other plugin material must remain byte/pin-stable unless independently separately approved.

**Important current implementation limitation:** P2 release_artifact.py stages from exact approved Git source blobs and the current manifest schema records only each Git file blob/path/SHA-256. It does NOT yet carry a legitimate derived-policy mapping that allows installing a rendered agent differing from the staged Git plugin blob. Therefore future code must choose AND independently review one of the following before building or activating anything:
1. **Minimal pinned pilot:** a future exact candidate Git source commit includes the deterministic rendered Chairman content **as a new pinned Git plugin blob**, with separate externally reviewed provenance of original trusted template/policy/rendering and a corresponding new release. This preserves the current manifest's ordinary blob equality but alone does not establish runtime-configurable active policy or F1 positive authority. Never mislabel it as a complete #165 implementation.
2. **Preferred governed policy-aware release:** a new versioned, explicitly reviewed artifact/manifest format binds source Git commit/tree, original template Git blob and SHA, renderer identity, canonical requested policy/version/digest, rendered exact agent SHA, immutable output release ID, old protected worker/validator pins, and installed target. Staging renders deterministically and verifies the result independently before creating a new immutable release. The manifest must distinguish source Git bytes from derived rendered bytes; DO NOT silently reuse existing manifest version or pretend transformed content still equals its original Git blob. New release_artifact verifier and installer tests required.

Both candidate packaging methods are **future implementations** and do not authorize a release publisher or protected trust root merely by being checked into GitHub. The existing P2 installer also touches the managed plugin, launchers and global Claude contract/settings during updates. Such side effects must be either explicitly approved and byte-scoped or eliminated by a separately designed dedicated supported update path. No existing installer execution is permitted now; the schema-048 incident remains OPEN and its preflight imports/side effects are not independently cleared for this use case.

## 4. Proposed read-only C2 plan record (inert until trusted provider exists)

A future read-only C2 planner MAY:
1. Select an explicitly nominated current-user Vres installation root and resolve all ancestors without following symlinks, junctions or reparse points. Do not recursively walk unrelated Claude/global directories. Refuse a custom CLAUDE_CONFIG_DIR until independently scoped; never infer location from source workspace.
2. Read the bounded active-install.json pointer and current release distribution manifest under its existing validated release, verify release source/template provenance from independently rooted release evidence (NOT just self-reported fields), and check last completed G and L/Q if a REAL trusted provider exists. Without provider, label these as UNVERIFIED CLAIMS.
3. Re-read EXACT managed target and release-distribution bytes with bounded UTF-8, required frontmatter fields, LF/CRLF check, body unchanged, full SHA-256. Refuse release mismatch, unexpected overrides, wrong owner/SID/root/release instance, unknown source, non-file/reparse substitutions, malformed/missing manifest or any active pending install journal.
4. For current installed P2 specifically, require baseline SHA **a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73**, release **20261022172833-4d82147b**, Sonnet/high LF **24208** bytes, as a documented historical preview identity, but NEVER as an indefinitely trusted authorization: compare actual bytes again just before any real action.
5. Build a pure memory candidate using Phase A renderer with actual verified P2 baseline bytes, only model=opus and effort=medium. Expected **P2-only** candidate SHA **b73e7497454a464f6b6bc1df00f42422696da786a07eb2936ae73ad73abedf54**, 24208 LF bytes. Abort/RECOMPUTE if actual source baseline, release, renderer or schema changed. Preserve all other agent/worker/validator files; never silently copy the newer C1 source-template body or its CRLF digest.
6. Display human-readable old vs new and hash labels **SOURCE OBSERVED**, **CANDIDATE NOT INSTALLED**. Explicitly state "No authority, installation, or active host model check happened." Do not read credentials or auto-run provider calls.

This inert PLAN is not consent, permit, install-prepared state or trusted release identity. Any future programmatic read-only planning is a new separately source-reviewed/tested tranche after this design review. The current C1 manual output already works and does not need repeated tests.

## 5. Required positive authority sequence BEFORE any installed mutation (B2B R3 is normative)

The minimum future policy change contract, once real providers are independently selected and expressly authorized:

**A. Trusted enrollment/current governing state.** A reviewed trusted release publisher and authenticated genesis H_0 or existing protected H_n must independently identify machine, Windows SID, install instance and canonical target, current completed G, immutable proposal ledger L, pending Q and validator pins. Currently absent: **BLOCKED**. Local P2 files and a matching SHA demonstrate bytes, not T2-resistant trusted genesis.

**B. Immutable new proposal C.** Exactly one linked new B1 proposal appended to trusted current L (initial-genesis special case if approved); no history rewind, made-up intermediate transitions, adjacent fake hops or self-derived expected history authority. Proposal canonical history bytes, policy, template/renderer/release/target/old pins are bound by distinct domain-separated digests. If pending Q is not NONE, STOP.

**C. Independent E provider-rendered proposal consent.** A real provider (not Claude/chat/PowerShell) renders verifiable facts including last COMPLETED Sonnet/high governing G AND latest proposed L/disposition, old -> requested policy/version, template/release changes, existing protected validator pins, machine/current SID/target, exact bytes/release, alias family rule, and expected runtime uncertainty. Positive user presence and nonce/challenge must be protected from ordinary same-user T2 code. Operator cancellation/refusal writes no permit. Missing provider = INDETERMINATE/BLOCKED; an ordinary "yes" is NOT E.

**D. Independent protected V and atomic proposal CAS.** A separately reviewed validator uses pre-state protected pins and independently fetched bytes/E/H_n/C, not agent-provided validation text or candidate-chosen Fable identity. A genuine protected service atomically checks current epoch/head/L/G/Q, E nonce and revocation, V outcome, target/release/source/renderer, schema/family rules; consumes E once and advances a pending-intent anchor H_(n+1). E may be used only for this proposal CAS, not for installation. R3 NF-05/NF-07/NF-08/NF-10 remain OPEN until actual trusted services are tested.

**E. Distinct W installation consent and enforcement.** A fresh trusted UI shows pending H_(n+1), currently installed baseline, exact proposed immutable release and rendered bytes, target, rollback/recovery consequence, current revocation status, and a different purpose/nonce. W is bound to exact pending epoch and candidate, and cannot be created or accepted by a same-user agent. It must be separately time/freshness checked; suggested provider-owned E and W windows are at most 300 seconds each, not proven timers. No W => NEVER write installed files. A revoked/expired/stale/withdrawn release, alias mismatch, missing protected V or unknown consent source => REFUSED.

**F. Trusted B2C install/load verification.** Separately review who can actually write and WHO/WHAT Claude loads. A T2-resistant anchor alone is insufficient when the installed Vres plugin remains same-user writable; either protected load-path enforcement or independent per-load/per-use verification is required before claiming protected model policy. New release candidate and old release preserve manifest identity. B2C rechecks independent pre-state/target/bytes/release/current journal, stages exact approved new release, applies under its own independently trusted execution boundary, reads back complete managed plugin/active pointer and actual loader identity, and ONLY THEN may a protected service perform exact bound COMPLETE_INSTALL with current Q/E/V/W references, not mutable file bytes alone. The runtime physical resolved Opus identity and worker/validator pins still need separate honest #169/B2D observation. If that cannot be verified, declare INSTALLED_FILE_ONLY or BLOCKED as appropriate, NEVER "Opus active".

**At design v0 every A–F trusted positive service is unavailable, or not independently accepted. Real INSTALLATION MUST STOP.** This is a testable protected boundary, not a plan to invoke or simulate authority with mocked same-user signatures.

## 6. Reversibility / recovery — precise contract, not an unproven rollback promise

A future implementation should offer a simple USER-facing "Revert to Sonnet/high" with the same positive authority level as an original switch. Historical P2 release bytes SHA and independently retained immutable old release can be the desired governing CONTENT, but **an old trusted consent event cannot be reused** to authorize a rollback. Proposal-history L never rewinds; return to old model content is a NEW linked B1 proposal / separately approved forward epoch under accepted B1 adjacency constraints, with fresh E/V and new W when changing installed release.

**Incident and crash matrix, normative intended behavior:**

| Point of interruption | What may be asserted | Required safe behavior |
| --- | --- | --- |
| Pure preview or temporary offline candidate staging before E/H CAS | OLD installed release remains, no positive approval | Discard inert staging; no installed mutation, no trust state |
| E refused, validator refused or proposal CAS failed | No permitted installation | Preserve old installation and protected H_n, do not silently retry |
| Pending H_(n+1) exists but no valid W | Intent-only, G still old Sonnet/high | No writes, no new proposal while Q pending, explicit cancellation/recovery gate |
| W accepted, but before any installed bytes change | Candidate authorized for specific intended attempt ONLY | Abort attempt on expiry/revoke/mismatch; no automatic reuse of E/W |
| Any part of managed plugin / release pointer updated, but completion not proven | **BLOCKED / RECOVERY**; neither Opus active nor old governing assumed | Preserve journal and old release, prevent duplicate attempts; separately warranted RESTORE_GOVERNING or verified completion; NEVER clear Q merely because "rollback worked" |
| New bytes read back but protected COMPLETE_INSTALL missing | Still PENDING/BLOCKED | Reconcile independent W/journal/load evidence, forward CAS completion or separately authorized recovery, no automatic promotion to G |
| Protected COMPLETE_INSTALL claimed but runtime loaded bytes/alias/validator provenance unverified | Installed file may be observed, physical mode NOT proven | Don't assert physical Opus; refuse protected active-model claim, escalate separately to #169/B2D |
| Future explicit revert request after completed installation | New intended successor policy, NOT history rewind | Independent new C/E/V/CAS/W for Sonnet/high and byte-exact staged prior content; confirm old SHA and new observed load, no silent demotion |

R3 reviewer erratum **R3-N01** specifically forbids clearing Q after a partial write while actual installed/loaded bytes differ from last completed governing G. R3-N02 requires protected COMPLETE_INSTALL to bind exact proposed Q/E/V/W/release/render evidence. These must remain explicit blockers in any C2 code. A same-user pending-install.json or backup digest may assist operator diagnosis but is **NOT** an authoritative protected journal or proof of consent. Because Windows plugin directory and active pointer updates are not one atomic transaction, do NOT advertise "atomic rollback" without a new validated mechanism.

Future recovery tests must simulate interruption at each step, T2 changed file/load-path, stale warrants, pending Q recovery and race/revocation, preserving old release provenance and no automatic state promotion. Actual recovery may be STOP/BLOCKED rather than automatic.

## 7. Narrow data/permissions policy and user experience

**Exactly allowed future C2 model-policy data for human report:**
- Current-user install identity and **authenticated** Windows SID/install instance only when a real approved provider exists.
- Release ID and committed source/template/policy/render SHA, current managed file bytes/sha/newline, proposed model alias/effort and digest, whether broader agent/worker/validator pins differ.
- Installed versus intended versus host-observed status, explicit warnings for missing host proof and unavailable alias.
- Read-only preview digest/hash and a descriptive refusal code, NEVER credentials, logs, stored secrets or long agent instruction bodies.

**Prohibited current operations and implicit side effects:**
- Running Vres CLI, bootstrap, setup, doctor, migration, task hooks or any command that might connect to incident PostgreSQL, including SELECT. Existing installer check/doctor/imports are NOT approved substitutes; LIVE_SCHEMA_048_INCIDENT remains OPEN.
- Reading or writing Windows Credential Locker, keyring, vault, passwords, Claude tokens, user-global settings/hooks/plugins, provider/Fable or unrelated project files for convenience.
- Automatically updating model based on performance telemetry or generating an approval from Claude text, a fake signed JSON, ordinary per-user DPAPI, provider-claimed user identity or a single Windows Hello API result.
- Mutating the historical installed 20261022172833-4d82147b release files, release manifest, active-install.json, managed Chairman or launchers in the current design/review session.
- Creating installation scripts, source changes, credential services or opening PR/main merely because this document has been committed.

**Future supported operator flow after all gates are proven:**
1. Preview changes, including current file lineage vs requested release, intelligible old/new policy, and whether host's current model is actually verified.
2. Confirm proposal intent via independent E provider; protected V+CAS pending.
3. Independently confirm installation via separate W with rollback and exact target summary.
4. Controlled new release transition, readback, independent loader proof, separately trusted COMPLETE_INSTALL; physical model evidence separately.
5. Distinct later new consent to revert; no hidden auto-demotion, no silent Opus-family substitution.

For PERSONAL usability, the visible steps may be concise grouped screens; this does NOT allow combining E/W silently or substituting a text response for a protected consent boundary. Two separate screens are acceptable when one is a real proposed policy authority event and the second is a real installed-release write; ordinary read-only preview needs neither.

## 8. Delivery slices, validation methodology and hard STOPs

### C2-D0 — THIS DESIGN ONLY

- This new Markdown document and canonical docs index modification are the ONLY intended GitHub changes; feature branch HEAD **7ac041018d4ec5a06be07318ecce5e140faccd91** unchanged.
- Claude Code independently evaluates this exact authored design using Read/Glob/Grep only from a newly guarded detached docs worktree; no Python/pytest/PowerShell/Git/MCP/DB/source edits/installer. Review outcome **DESIGN_ACCEPT / DESIGN_REVISE / DESIGN_BLOCKED**. **DESIGN_ACCEPT means ONLY conceptual design acceptable for further separately scoped work**, NOT privilege or F1 authorization. Preserve exact reviewed design blob and all unresolved findings.
- No Windows host commands/test runs are needed for a pure documentation design.

### C2-D1 — permitted future small inert, pure/offline programmatic planning (PROPOSAL, not approved)

- If independently accepted, ChatGPT may propose a distinct **pure** renderer/descriptor/preview contract using already accepted C0 and Phase A. All input bytes explicitly caller-supplied; old and new SHA computed from actual bytes; only REFUSED/INDETERMINATE for any claimed authority. No FILE SYSTEM / process / provider / registry / Vres CLI / installed-target write/read in this D1 pure tranche. Clearly mark trust evidence UNVERIFIED. Do not duplicate accepted C0 tests just to repeat.
- A separate exact source SHA, focused independent STATIC review, ONE selected disposable Windows pytest using protected conftest and process-level PG tripwire, then independent OFFLINE_ACCEPT/REJECT before treating code as accepted.
- Does not authorize installation, R3 positive CAS or protected model validation.

### C2-D2 — protected real B2B-2 authority/provider and release publisher (FUTURE, BLOCKED now)

- Must resolve named independent T2-resistant release publisher, authenticated genesis/anchor, consent service E, independently protected V provenance, atomic CAS/revoke/nonce system, distinct W issuance, and loader/search-path enforcement with real T2 adversary testing. R3 NF-05..NF-10 and erratum requirements remain mandatory.
- This will require explicit new user consent and separate independent design/security review. A personal same-user Windows file, ordinary CLI Yes/No, user-own DPAPI or GitHub token alone is NOT sufficient. PostgreSQL incident NO CONTACT blocks any reliance on that database.
- If operator elects a differently scoped non-governed personal experiment instead, it must be honestly labeled out of F1/#165 protected acceptance and require a distinct consent/risk decision; this C2 design does not implement such an exception.

### C2-D3 — B2C installed new-release commit/recovery (FUTURE, BLOCKED now)

- Extend or version release manifest truthfully for policy-derived output, OR use a reviewed pinned pre-rendered Git blob; choose one explicit path and prove exact source/policy/renderer/target digest binding, previous-release backup, guarded managed plugin and active pointer transition, interruption recovery and protected loaded-byte check.
- Future installed Windows test must be done from a disposable/snapshotted current-user profile, not the existing personal live installation, until explicitly authorized. Test identical worker/validator pins, no hidden changes in global Claude rules/settings, no attacker replace/reparse, no F2/DB contact. A successful old installer smoke test is not adequate if the release artifact policy path changed.
- Source code and installer changes require new SHA, static-first review, offline selected tests then physical testing under a separate gate. Do not use the current P2 install.ps1 as a no-DB safe mutation path without a new audited specification.

### C2-D4 — #169/B2D physical acceptance (FUTURE, BLOCKED now)

- Under separate operator-approved Windows/Visual Studio acceptance, observe actual native host Chairman resolved Opus/medium and routine Sonnet, deep Opus, protected Fable/high workers with independently qualified evidence; refusal if alias unavailable/fallback. Distinguish operator host observations from T2-resistant proof where applicable.
- Do not close #165/F1, claim installed Opus or claim production readiness until all relevant independent authority/release/host gates are genuinely satisfied.

## 9. Focused independent DESIGN reviewer checklist (use actual refs and provenance)

Claude should challenge, not simply rubber stamp:
- Is the recommended immutable new-release path consistent with the existing P2 install.ps1 and release_artifact.py pinned Git blob manifest semantics? Does the design clearly say future model-policy materialization cannot be silently installed under the existing manifest schema? Could a pinned-pilot option mislead users about #165 completion?
- Are source checkout preview hash and current installed P2 LF hash and hypothetical P2 candidate SHA correctly distinguished, with no implied current active runtime model?
- Do proposed E, V, protected CAS, W and COMPLETE_INSTALL order align with independently DESIGN_ACCEPTED *DENY-ONLY* B2B R3 and mandatory erratum, including L/G/Q, genesis H_0, old validator pins, exactly-one append, revival/revocation, nonce/freshness, anti-oracle and no positivity from B2B-1?
- Is a same-user PowerShell confirmation explicitly NON-AUTHORITATIVE under the already accepted threat model? Are real trusted publisher/provider, protected validator/loader and host alias observation acknowledged as missing and STOP?
- Are rollback and crash states safe: no clearing Q after partial write until proven last completed G or separately protected W-backed recovery, no reuse of old E/W, no history rewind, no auto-demotion, no fabricated intermediate B1 step?
- Does C2 avoid reading/changing credentials, global Claude settings, incident PG, Fable/provider or active release now; and does it avoid falsely treating the existing installer as a safe DB-free production switch under LIVE_SCHEMA_048?
- Does it fit PERSONAL single-user usability instead of demanding meaningless public signing ceremonies, while not claiming T2-resistance without an actual independent boundary?
- Are independent evidence limits clear: original installer source reads by ChatGPT versus future Claude design opinion, and no physical installed runtime model check?
- Are proposed future slices genuinely deferred (not source/test/installation claims)? Is the exact next user action only a static Claude design review?

Required verdict exactly **DESIGN_ACCEPT / DESIGN_REVISE / DESIGN_BLOCKED**. Report BLOCKING and INFORMATIONAL findings with document section/lines; distinguish full/partial reads. Required statuses: DESIGN_ONLY, TESTS_NOT_RUN, SOURCE_MODIFICATION_NOT_RUN, NO_AUTHORITY_ISSUED, NO_MODEL_ACTIVATION, NO_POSTGRESQL_CONTACT_BY_REVIEWER. End marker: **VRES_165_PERSONAL_C2_REVERSIBLE_MODEL_SWITCH_DESIGN_REVIEW_COMPLETE**.

## 10. Canonical handoff, historical integrity and next session

**Immediate next operator task after this docs commit:** prepare a NEW clean detached Windows documentation-review worktree at exact new canonical docs HEAD from original clean P2 git repository; refuse wrong origin, unexpected docs SHA/tree, existing destination, dirty worktree, malformed Git branch, extra changed paths. Then start ONE fresh Claude Code session in that docs worktree for the independent C2 design-only review. **NO tests, source edits, Vres tasks, database commands, provider/model calls, installed release inspection, model activation or installer.**

**Canonical docs transaction:** ADD this design file and MODIFY only docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md. Old docs HEAD to confirm **baab8c59fa064fdec37dd3bbf443f529f8979002**, tree **f5786bc74894f4ef64b6d1a8d327f0da9108bfc4**, feature source HEAD **7ac041018d4ec5a06be07318ecce5e140faccd91**. Require recursive old/new tree EXACT these two docs paths, no deletes, one-parent unsigned commit, nonforce expected-SHA branch update, exact blob, commit/feature readback. No source branch change.

**NEW CHATGPT SESSION RESUME:** feature SHA 7ac041018d4ec5a06be07318ecce5e140faccd91, tree 0ef7af10335865231f4350e2dbb7ba561538ee00, independently OFFLINE_ACCEPTED C1 R1 pure source CLI/tests (29 individual Windows PASS/exit0; manual source preview PASS). User next independently read installed current-user original P2 release file identity at 20261022172833-4d82147b, Sonnet/high LF/24208 bytes SHA a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73, matching original P2 Git blob 6f2239c4dd0d52090d31415c17f763505f93b900. Pure P2 Opus/medium candidate digest b73e7497454a464f6b6bc1df00f42422696da786a07eb2936ae73ad73abedf54, NOT applied. New authored C2 reversible model-switch DESIGN v0, **independent review NOT_RUN**, explicitly recommends new pinned immutable release instead of in-place edit; old installer must be extended/reviewed to bind derived bytes, or reviewed pre-rendered candidate Git blob, and real F1 trusted E/V/CAS + distinct W provider and runtime loader enforcement remain UNAVAILABLE. No positive authority, global Claude changes, PostgreSQL, tests, source or installer writes. NEXT NEW guarded docs worktree for independent Claude static DESIGN-only review. The accepted B2B R3 SHA/blob 110ccffcbc1c1f00f5b674b4836fed432708f4ea is DESIGN_ACCEPT STRICTLY for DENY-ONLY B2B-1; mandatory erratum blob e7536be90246ad3894befb8a2f5e158d3088028d NF-05..NF-10 and R3-N01/N02/N06/N07 still OPEN. Original F1/#165 OPEN; LIVE_SCHEMA_048 INCIDENT prohibits PostgreSQL even SELECT, D2/F2/R0/K0-T1/L-04/PA-01..08 and two Vres task persistence warnings unresolved. No new installed model; last installed managed Chairman Sonnet/high, physical running Claude model unverified, Opus/medium UNINSTALLED. All previous per-SHA accept/reject/review statuses, V-01..V-42 PERSONAL roadmap and original P2 install release preserved.
