# Vres-OS — COMPLETE PERSONAL pending-development, integrated release, installation and real-Windows UAT plan

**Approved planning direction:** 2026-11-05, Europe/Athens. **Status:** PLANNING DECISION / NOT IMPLEMENTATION OR DEPLOYMENT AUTHORIZATION. **Product:** ONE Windows user's personal daily-operations Vres-OS; NOT enterprise IAM, multi-tenant, a second Chairman, or a collection of duplicate task stores.

**Authoritative companions:** 
- \`docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md\` (current READ FIRST, all historical evidence);
- \`docs/handoffs/VRES-2026-11-05-P1-DAILY-REVIEW-WINDOWS-AND-REAL-ADOPTION-PASS-CHECKPOINT.md\` (latest accepted real Personal Desk evidence);
- \`docs/roadmap/VRES-PERSONAL-LOCAL-WINDOWS-ACCEPTANCE-AND-FULL-DEVELOPMENT-BOARD-2026-10-31.md\` (all original V-01..V-42 rows and historical statuses);
- \`docs/roadmap/VRES-FULL-SCOPE-FUNCTIONALITY-REGISTER-2026-10-22.md\` (original requirements);
- \`docs/roadmap/VRES-PERSONAL-DAILY-OPERATIONS-DELIVERY-PLAN-2026-10-30.md\` (original M0..M8, #165..170/#174/#176);
- \`docs/architecture/VRES-PERSONAL-SINGLE-USER-PRODUCT-CHARTER-AND-METHOD-2026-10-30.md\`.

## 1. Decision and evidence boundaries

The former proposed next step ("build another standalone P1 launcher / Daily Home immediately") is **not** the default next feature. The accepted three side-by-side P1 portable apps and real Daily Review have proven a small bounded workflow. A new UI/launcher is a subcomponent only if genuinely needed by the full release's single-user experience. First establish a full feature-to-release and UAT dependency plan, then develop meaningful integrated work.

Verified remote state at this planning decision:
- Documentation branch \`docs/chatgpt-continuity-20261023\`, prior HEAD \`d868e2c0c6a82fcddb1302f9a48da3b5ebee392c\`, TREE \`d2d0afd28a0751d8162430a21d52bc3cf07c891a\`, sole parent \`04663e307f1c3fb15b7c27379557515c5bb870c9\` (this plan's eventual publication will create a NEW documentation head).
- Product \`main\` HEAD \`9a8acc5d464b96432a93cb95daa9581412fb07ee\`, TREE \`659d3fdd6e635dbaecbd5c492ba7279754edaec7\`, DO NOT MERGE.
- Accepted Daily Review feature \`feature/personal-p1-daily-review-20261105\` HEAD \`2c0783338cb2bb3488ed1be5d61cac3349b3b8d7\`, TREE \`d4de20da7e43e60662f9bd52519bd042e07f3cdb\`, sole parent \`b0e22725213f312773f36cd474f8cb277e453747\`; source parent \`648d90ef4832bb9b73a2fe8ef3364cb6aa9929d7\`.
- A separate offline release no-launch environment-fence source branch exists at \`23908842246ab148ba645386486426f210917980\`; its exact source/artifact Windows acceptance is NOT_RUN. Do not silently presume these features are already integrated with Daily Review.
- Historical original installed P2 source \`82c82430b38f93bd6b9d5c3af3b5de9c1368af9c\`; actual CURRENT Windows installed identity is NOT independently refreshed in this planning turn.
- P1 owner-pasted Windows integrated review and real side-by-side adoption PASS; \`TASK-DAY-01\` COMPLETED, zero active, one completed snapshot; original Markdown and both prior portable apps reported unchanged. Standalone full exact-source pytest NOT_RUN; physical host evidence not directly observed.
- GitHub issue states checked on 2026-11-05: #163/#164/#174 CLOSED at historical/source level; #165/#166/#167/#168/#169/#170/#176 OPEN. Issue closure is NOT evidence of final installed acceptance.

**Permanent restrictions pending independent disposal and owner authorization:** \`LIVE_SCHEMA_048_INCIDENT=OPEN\` (NO PostgreSQL even SELECT, direct/indirect); \`HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN\` (NO normal native Claude or installed hooks); independent positive F1/Fable authority NOT GRANTED; protected P2 installation NOT_REQUESTED/NOT_AUTHORIZED. NO \`install.ps1\`/\`update.ps1\`, PRISM, existing Windows profile modifications, real credential use, legacy project mutation, main merge, or Sandbox R2 first launch. Existing signed offline Python 3.13.17 requires re-verification before any new Windows action; never change PowerShell execution policy to make a launcher work. Previous rejected attempts and all PASS/FAIL/NOT_RUN remain authoritative, not overwritten.

## 2. One full-scope delivery train, with integration-first dependency order

| Stage | Integrated user-visible outcome / owner | Source and acceptance scope | Exit and dependencies |
| --- | --- | --- | --- |
| **W0 — Release baseline and gap reconciliation (NEXT)** | One accurately scoped release map, not another microfeature or portal | Exact Git ancestry, source/test delta, legacy installed P2 provenance, accepted portable Daily Review, main, M0–M8, #165–170/#174/#176, E7/F2, original 42 requirements. Inventory what source is actually packaged/runnable; label AVAILABLE, SOURCE_ONLY, ACCEPTED_OFFLINE, NOT_RUN, HELD, UNSUPPORTED. Explicit feature enablement, release changed-path allowlist, no-DB/no-native-launch design, dependencies and acceptance trace. | Output is a single integrated candidate contract and frozen impacted-surface test matrix. No Windows or database effect. Do not presume independent branches have been merged. |
| **W1 — One everyday conversational task-to-outcome journey** | Single Chairman/task context, real code/research/document output, checkpoint, resume/restart without wrong-task hop | Integrate accepted task/continuity code with M3, relevant #165 personal NON-F1 policy, task/decision state and applicable #176 experience owners. Only offline/simulated host tests while Claude hooks are held. Keep already accepted P1 Daily Review unchanged. | New exact-parent source + focused integration test showing planning, result, refusal, persistence boundaries and resume. No installed/real native Claude test until host clearance. |
| **W2 — First use, fresh/legacy project onboarding and governed global adoption** | One predictable first start, project inventory, numbered KEEP/DROP, canonical minimal project scaffold, interrupted adoption recovery | Integrate #166/#168/#174, V-04/V-12/V-13/V-16/V-24/V-28–30 with sanitized disposable fixtures; no executing imported project hooks, browser, DB or native Claude. Inventory user-selected config with no ambient permissions. | One end-to-end disposable fresh + legacy fixture acceptance with exact rollback. Do not mutate user's real PRISM/Claude HOME/legacy project. |
| **W3 — Reuse memory, safe resources and verified experience** | Recall attributable decisions/procedures; link approved same-user credential handle/data-source metadata across projects; deny unbound reuse | Integrate core #176 E7/E8 and #163/#164/#167 using synthetic secrets and offline resource metadata; A/B allowed with explicit bindings, C denied, stale/poisoned/history rejection. Held F1 issuer is not replaced by a self-asserted trusted signer. | One focused cross-project offline journey with evidence; direct PostgreSQL catalog refresh and real Credential Locker remain pending separate P3/P2 permission. |
| **W4 — Coherent reproducible Windows release and recovery** | One candidate package that can be read, verified, staged and recovered predictably | Integrate product M1/M2 candidate, host-fence fix as applicable, versions, manifest, pinned dependencies, 001–041 migration exclusion, verified package/plugin bytes, update journal and interrupted rollback; no installer/native Claude/DB invocation. Make limited P1 launch usability part of this package if needed, not a fourth stand-alone task app. | ONE full impacted-surface disposable offline Windows package and failure-injection acceptance; exact remote source/tree/blobs, artifact/rollback proof, printed feature-on/held summary. This is not permission to install P2. |
| **G1 — Independent critical-incident dispositions** | Demonstrated safe effective host and separately safe database target, with explicit decisions | P3-HOST lifecycle, exact effective hooks/other plugin routes, non-DB static+physical evidence by separately approved safe mechanism; P3-DB schema-048 incident forensic/restore/authority resolution WITHOUT any DB contact while hold open. Need independent evidence, not printed assertions alone. Protected F1 positive authority remains held unless separately granted. | The relevant holds are explicitly cleared by competent independent evidence and owner authorization. No automatic clearance from W4, offline tests or a disposable sandbox. |
| **P2 — Single controlled current-user installation** | Install one approved, recoverable integrated release, never an indiscriminate update to all existing copies | Only after W4 + relevant G1 clearance and exact target/version/old/new hashes, changed paths, backup and verified rollback; specific approval from owner for THIS action. Preserve original P2, earlier P1 apps and real task notes until owner separately authorizes disposition. | Report actual installed identity, before/after/restore and unintended-effects check from operator-visible Windows evidence; no silent profile/credential changes. |
| **U1 — Real Windows / Visual Studio UAT (#169)** | Normal one-user real task with fresh & sanitized legacy project adoption, resource reuse, continuity and rollback | Host-observed current package, actual Visual Studio workflow, full exact UAT matrix in §4; user-selected real project only after separate scope approval, controlled current-user/profile changes with preimages. | Record observed PASS/FAIL/NOT_RUN per scenario, issue/defect and required fix; fix only impacted source and rerun affected scope. Original #169 criteria reconciled, not silently waived. |
| **U2 — Personal pilot and readiness (#170)** | Real repeated daily use with recovery, user-reported usefulness, cost/privacy limits | Small explicitly approved pilot on the accepted target installation across several different real work types, with genuine restart/resume, bounded project reuse and deliverable acceptance. Optional growth M8 separated from core release but never deleted. | Owner approves LIMITED PILOT or FULL ACCEPTANCE with explicit open V requirements. Do not label #170 complete without original evidence or owner-approved proportional reconciliation. |

**Critical path:** W0 → W1/W2/W3 (can progress in separate dedicated feature branches without irreversible external effects; integrator must reconcile ancestry) → W4 → G1 / P2 consent → U1 → U2. G1 investigation may proceed in parallel ONLY through independently safe, separately authorized methods and without violating existing holds. Nothing in W1–W4 authorizes local P2 activation. Earlier P1 real-use acceptance stays accepted at its own SHA.

## 3. Complete V-01..V-42 remaining-outcome trace (original row statuses preserved in source register)

This table is a **planned action/acceptance map**, not a replacement for the original rows or a claim that every source feature is absent. The original register's BUILT/PARTIAL/VERIFIED/DEFERRED/HELD facts and historical proofs remain unchanged.

| Requirement | Required remaining integration or acceptance | Planned gate |
| --- | --- | --- |
| V-01 | One actual usable conversational Chairman entrance, no second master controller | W1, U1 |
| V-02 | Task/decision/checkpoint continuity across restart, exact project/task | W1, U1 |
| V-03 | Bounded context/host cost behavior and optional compaction without overriding user settings | W1, U1 |
| V-04 | Real project architecture governance and reversible decision flow | W2, U1 |
| V-05 | Evidence/provenance/refusal integrity and actual reviewer limits | W1–W4, U1 |
| V-06 | Honest host-observed model policy and no silent protected downshift | W1, G1, U1 |
| V-07 | Configurable PERSONAL Chairman Opus/medium + explicit governed switch; strict F1 remains held | W1, P2, U1 |
| V-08 | Empirical model quality/cost optimization, not synthetic performance claims | M8 after U2 |
| V-09 | Optional specialists/Directors only where useful; one Chairman | W1, U1 |
| V-10 | Specific retail/business specialist skills and outcomes, not compulsory board | M8 |
| V-11 | One-worker default, bounded project-local DAG and failure handling when needed | W1, U1 |
| V-12 | Capability lifecycle/proof/reuse with no uncontrolled installer | W2, M8 |
| V-13 | Current-user external plugins/MCP inventory and guarded adapters | W2, M8 |
| V-14 | Optional Superpowers advisory compatibility | M8 |
| V-15 | Explicitly opted-in browser/GUI tool and reproducible audit task | M8 |
| V-16 | Governed Claude–Codex handoff; no ordinary native Claude under current hold | W2, G1, M8 |
| V-17 | Reusable validated procedures and corrections from real tasks | W1, W3, U1 |
| V-18 | Measured Pareto procedure improvement/promotion with approval | M8 |
| V-19 | Relevant, traceable personal memory and controlled retrieval | W3, U1 |
| V-20 | #176 E7 negative transfer, poisoning rejection and held-out evidence; do not pretend held gate cleared | W3, M8 |
| V-21 | #176 E8 just-in-time relevant experience and abstention, not massive injected context | W3, U1 |
| V-22 | Evidence-linked supersession, contradictions, freshness and revocation | W3, U1 |
| V-23 | Existing historically company-wide APIs interpreted as strictly single-user bound scopes, not enterprise expansion | W3, U1 |
| V-24 | Historical Office/PDF/code/project material: safe useful intake and refinding | W2, U1 |
| V-25 | Greek/Greeklish semantic/OCR evaluation only with a real bounded need | M8 |
| V-26 | Credible source-grounded research outputs in W1; scheduling/monitoring after baseline | W1, M8 |
| V-27 | Current-user Credential Broker and scoped approved handles, never plaintext in transcripts | W3, P2, U1 |
| V-28 | Fail-closed secret-safe legacy ingestion at project boundary | W2, U1 |
| V-29 | #166 user's global Claude HOME snapshot/KEEP-DROP/rollback, not enterprise adoption | W2, U1 |
| V-30 | #168 fresh/legacy project scaffold plus project-architecture alignment | W2, U1 |
| V-31 | #167 source registry and permission-bound reusable metadata | W3, U1 |
| V-32 | #167 schema/semantic graph and drift; real DB testing only after P3 clearance/approved target | W3, G1, U1 |
| V-33 | A/B allowed and C denied cross-project reuse, never cross-Windows-user authority | W3, U1 |
| V-34 | Current-user exact versioned installation/start/restart after incident clearance | W4, P2, U1 |
| V-35 | Actual interruption and rollback/restore proof, not optimistic dry-run assertion | W4, P2, U1 |
| V-36 | PostgreSQL schema 048 incident and migration/target safety, NO DB contact until cleared | G1, U1 |
| V-37 | Strict experimental C2B/F2/R0/K0 issuance; positive authority HELD, no false grant | HELD M8 only on new approval |
| V-38 | Original #169 full Visual Studio/PRISM/real-legacy integrated proof | U1 |
| V-39 | Original #170 real-world pilot and proportional final user signoff | U2 |
| V-40 | Reproducible package, hashes/dependencies, separated safe migration set | W4, U1 |
| V-41 | Useful user-approved research/document/code/analysis deliverables | W1, U1/U2 |
| V-42 | One natural start/resume, bounded approvals, low operator/Git ritual | W1–W4, U1/U2 |

The M8/HELD entries are **not erased, closed or quietly waived**. They have explicit later gates or await a new owner choice. Before claiming "FULL Vres-OS" acceptance, publish a final per-V acceptance disposition, showing which are accepted, explicitly optional, held or unresolved.

## 4. Real-world UAT scenario register (future tests, ALL NOT_RUN for the new integrated release)

| UAT | Scenario and acceptance evidence |
| --- | --- |
| UAT-01 | One natural user launch; exact active installed version, current project and capability enabled/held summary; no unexpected subprocess/DB contact. |
| UAT-02 | User-authored non-sensitive task → explicit approve creation → focus → actual deliverable → complete → original note unchanged → review/history. Do NOT replay TASK-DAY-01. |
| UAT-03 | Native session clear/restart, correct selected task/project, decisions, source provenance and pending action restored without asking to re-explain. |
| UAT-04 | One real user-accepted software or document artifact and one sourced research result; correct outputs and bounded relevant tests. |
| UAT-05 | Fresh project from Visual Studio: exact scaffold/inventory, no dummy roles, minimal native project files, safe rollback. |
| UAT-06 | Existing legacy/PRISM fixture: non-executing discovery, numbered KEEP/DROP, protected vendor state, reversible approved adoption. Real user project ONLY with new permission. |
| UAT-07 | Same-user synthetic credential A/B project bindings allowed, unbound C denied, redacted logs; actual Credential Locker only after specific P2 permission. |
| UAT-08 | Source registry/schema metadata reuse and stale/poisoned data denial; **any actual database connection held** until separate schema-048 incident resolution and exact safe target consent. |
| UAT-09 | Relevant verified memory reuse on later task, contradiction/stale/project-crossing denial, no fabricated positive F1 validation. |
| UAT-10 | Governed Chairman model switch/report: requested vs host-observed identity and no silent fallback, only after approved host activation; Fable protected positive remains held. |
| UAT-11 | Deliberate interrupted update/adoption against approved disposable/restorable target, compare before/after hashes, recover old release and verify next launch. |
| UAT-12 | Actual routine pilot: several ordinary personal outcomes, accurate limitation reporting, repeat restart, accepted recovery and owner judgment of usefulness. |

For every UAT record: exact candidate/source/release hashes, source of evidence (GitHub observed vs operator pasted/uploaded vs independently verified host), actual PASS/FAIL/NOT_RUN, changed path/approval scope, rollback outcome and next defect action. Do not invent elapsed times, exact resource measurements, native subprocess logs, F1 authority or automatic installation success. Failures should produce targeted fixes and one impacted-surface retest, not repetitive accepted historical gate reruns.

## 5. Installation and multi-copy preservation contract

Three retained offline P1 personal applications exist according to operator-pasted evidence:
1. \`C:\Projects\Vres-PortableDesk-Personal\Vres-PortableDesk\` (earlier P1, preserve).
2. \`C:\Projects\Vres-PortableDesk-Lifecycle-Personal-20261105\Vres-PortableDesk\` (earlier P1 lifecycle, preserve).
3. \`C:\Projects\Vres-PortableDesk-DailyReview-Personal-20261105\Vres-PortableDesk\` (latest adopted P1, preserve).
The original protected P2 installation is a **separate** product and release boundary, historically tied to source \`82c82430b38f93bd6b9d5c3af3b5de9c1368af9c\`. Do NOT mistake a new P1 side-by-side application for an upgrade of P2, or blindly update/delete all copies.

Until specifically permitted, local Windows files/installations/user profile are NOT accessible or mutable from ChatGPT; operator must execute verified commands. Distinguish an approved **create-only P1 side-by-side trial** (if useful and separately approved) from a **protected P2 user-profile/Claude update** requiring both P3 disposition and explicit P2 approval. Never use broad "proceed" as approval to run real installers or migrate existing data.

For an eventual protected installation, produce **BEFORE APPROVAL**: identified source/parent/tree, feature inventory and held capabilities, manifest/package hash, affected installed paths, old/target release identity, exact process/database route analysis, non-secret backup destination, tamper/rollback results, expected Windows effects and specific owner-confirmation phrase. After approval, owner runs a scoped verified Windows operation; collect before/after hashes, confirm usable real UAT and rollback. If any safety gate fails, remain on old installed P2.

## 6. Efficient milestone methodology

- Author and publish **one real integrated user outcome per development wave**, exact-parent dedicated feature branch, nonforce expected-old-SHA publication, remote commit/tree/blob readback. Make failed attempts/provenance explicit.
- **One selected coherent offline integration acceptance for impacted changes**; preserve previous Windows PASS, standalone NOT_RUN and all failed/declined paths. No full-historical reruns for paperwork.
- The feature train is **not** a blind "merge everything": reconcile owner modules against accepted parent and compare exact ancestry/tree/changed-path allowlist; leave rejected or unaccepted feature branches untouched.
- Keep real data and sensitive material out of development fixtures; review closed #163/#164/#174 source evidence before claiming host integration. No second credential broker, second task DB, second Chairman or new enterprise identity layer.
- Preserve original V-01..V-42, M0..M8, #163–170/#174/#176, E7/F2/C2B/R0/Stages1–6, all protected worktrees, rejected attempts, owner permissions and historical installed identity.
- Document checkpoints at or before 20 completed replies or conservative half-context; no fake exact context percentage and no background handoff.

## 7. EXACT NEXT ENGINEERING ACTION

**W0: integration and release gap reconciliation on GitHub, read-only first.** Compare the actual accepted Daily Review source chain, full original personal release/source ancestry, no-launch-fence feature and M0–M8 capabilities; produce one exact-source release composition and acceptance matrix with source file owners, missing integration edges, blockers and branch parents. This determines whether the first necessary source milestone is W1 conversational continuity, W2 project adoption or W4 packaging; **do not prematurely implement a fourth P1 launcher**. Do not install anything or test native Claude/PostgreSQL.

**Next action after W0:** one prioritized functional integrated source milestone chosen from verified actual gaps, with exact-parent commit and one focused offline Windows integration gate. **Later**, after W4 and independent G1 safety dispositions, request a SPECIFIC protected P2 installation approval and run U1 real-world UAT. No future execution is implied by publishing this plan.
