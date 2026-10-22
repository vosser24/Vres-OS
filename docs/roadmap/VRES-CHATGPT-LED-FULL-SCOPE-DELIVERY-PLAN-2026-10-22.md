# Vres-OS — ChatGPT-Led Full-Scope Development and Closure Plan

Issued: 2026-10-22, Europe/Athens
Owner decision: restore ALL original and subsequently approved functionality to the active development backlog, while retaining genuinely necessary security and data-protection gates.
Owner: user is operator/approver. ChatGPT is primary architecture, code, test, documentation and Git development author. Claude consumes the implementation locally as reviewer and test executor, reports independent evidence, and does not own the plan.

## A. Outcome and non-goals

Desired result: one dependable personal Windows Vres installation that can, through conversational Chairman, understand a fresh or existing project, inspect its capabilities/architecture/knowledge safely, propose and execute scoped work through proven experts, retain validated experience and reusable procedures across sessions, operate authorized external tools and registered data sources, and improve measured efficiency over time. Advanced full-scope items must have explicit enabled-versus-disabled outcomes with evidence; no unfinished feature can be portrayed as completed.

Do not restart an enterprise key-signing theater simply because it exists. Do not mistake personal-use simplification for deleting the original ambitions. Do not remodel the entire product before touching a small gap. Do not re-run comprehensive review suites on every commentary or docs edit. Do not run Vres on the schema-048 incident database. Do not print, copy or ask for secrets. Never silently enable external side effects, Codex workspace writes, credentials, model replacement, global rules or unsigned trust issuance.

A documentation scope reactivation is NOT proof of functional readiness and not approval for a blocked runtime action.

## B. Role and Git operating model (binding)

### B1. ChatGPT leads development

1. Read the latest branch checkpoint, functionality register and this plan before coding.
2. Reconcile GitHub main versus accepted local product commit and unpublished work; do not assume remote main is current product truth.
3. Select the smallest independently useful gap and freeze a plain-English behavior contract and affected files. Reuse existing Vres modules and tests.
4. Implement the code, targeted tests and concise documentation directly on a dedicated GitHub feature branch through the connected GitHub repository tools. Use exact parent SHA and non-force ref updates.
5. Report exact branch, commit, parent, changed paths, proposed tests, safety exclusions and known limitations. No claim that GitHub editing alone ran Windows tests.
6. Review Claude's returned failing cases and output. Fix confirmed defects in a further bounded commit on the SAME branch. Preserve rejected results.
7. Only after green evidence, prepare the next scoped commit or guarded integration request. Do not silently merge, force-push, delete history, publish product main or deploy on the user's PC.
8. GitHub CI may be used for code validation as explicitly authorized; CI cannot contact the operator's incident database.

### B2. Claude consumes, evaluates and reports

- Operator fetches the exact branch/commit into a separate local clean worktree. Do NOT overlay the active installed release or unpublished K0/C2B worktrees.
- Claude receives the exact commit and acceptance matrix. It independently inspects the changed code; runs ONLY agreed, offline targeted tests and, when separately approved, a non-incident disposable PostgreSQL or actual host scenario.
- Claude does not rewrite the product plan, own independent source edits, add unsolicited frameworks, change routing/model policy, merge branches, alter secrets, launch Vres against unknown DB config, or pronounce an unrun test PASS.
- Review output is concise: PASS / FAIL / BLOCKED / NOT_RUN for each criterion; exact command, working directory, commit, test result, minimal failing trace (sanitized), and specific defect. No speculative fixes; ChatGPT authors corrections.
- The user relays output to ChatGPT and approves only consequential installation, database, native credential, global Claude and external-write actions. No remote machine actions can be inferred from GitHub access.

### B3. No redundant testing

- Each small change: static/diff + exact affected tests, isolation tripwire, relevant regression.
- Each material security/DB/trust change: independent critique + disposable test fixture; preserve negative proof.
- At coherent feature boundary: one targeted integration set.
- Before release: one full relevant suite, source/package identity check and only affected physical PA cases. Never convert 761 skipped tests into a PASS claim.
- A passed test on one SHA does not automatically pass a different SHA. Use exact-head readback.
- Commit tests with their implementation; use measured outputs and avoid fabricating models, costs, token usage or benchmark quality.

## C. Starting boundaries, not to be lost

Product main on GitHub at review: 9a8acc5d464b96432a93cb95daa9581412fb07ee (accepted E6).
Personal source in operator's local Windows Git: 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c, branch personal/p2f-postinstall-hardening-20261022; NOT pushed according to the operator's 2026-10-22 proof.
Installed active release: 20261022172833-4d82147b; installed package 147/147 and plugin 40/40 verified; PostgreSQL was STOPPED; Vres activation NOT RUN. Earlier source 5142e0149a1ca1eeab87917d3a606495760b3b4c and local P2-A1..F accepted source chain. Preserve the protected original backup, old-release rollback and the failed E.5/61-pyc quarantine evidence.

Incident ledger (unchanged by this plan): LIVE_SCHEMA_048_INCIDENT=OPEN; D2=OPEN; F2=QUARANTINED; R0_DB_READ=NOT_RUN; NATIVE_TRUST_APPROVAL=NOT_GRANTED; K0_T1=BLOCKED; L-04=OPEN; positive production trust issuance DISABLED. No contact to the incident server, even SELECT, and no post-install bootstrap or Vres start that might point at it. The database service was left stopped; no restart or reboot authorized.

Remote canonical docs branch inspected at a2f867a07ad2916f938fe13776f3aed3971f0d7b (2026-10-13). Reported newer LOCAL docs from October 15–16, K0 scripts and the personal local source chain are not presumed pushed. This plan lives on a NEW documentation checkpoint branch to avoid overwriting them. An eventual merge must reconcile local and remote contents explicitly.

## D. Program phases and exit criteria

### Phase 0 — Align source and execution surface

P0.1. Inventory current GitHub refs and operator's local personal branch, all open unpublished K0/G7 branches, exact accepted commits and local worktree cleanliness by read-only checks.
P0.2. Decide a traceable integration path for 82c8243: create GitHub source import/push only by operator action or an explicitly reviewed content-equivalent ChatGPT-created branch. Compare exact tree/blob before accepting it. Never substitute old main bytes silently.
P0.3. Establish one issue/feature matrix: IDs V-01..V-42, mapped #176 and #165..170, owner, test, status and dependencies.
P0.4. Freeze the installed release/previous-release/backup evidence; keep all current local source and K0 worktrees. Record known current-user CLAUDE_CONFIG_DIR behavior and Python/PATH launcher selection.
P0.5. Determine whether Claude can perform offline code evaluation without invoking installed Vres startup/hooks. If the evaluation environment tries DB access, stop rather than workaround the incident.
Exit P0: unambiguous source parent and safe review worktree; no product edits on the docs branch.

### Phase 1 — Safe personal operation, not a production-blind startup

P1.1. Isolate schema-048 incident. Use OFFLINE manifests/logs/backups to identify 041-vs-048 lineage, last compatible runtime, affected data and external risk. Evidence-only; no service start or direct DB login.
P1.2. Propose a separate non-incident disposable cluster/DB with explicit port, identity, release migration ceiling, isolated VRES_DATA_DIR and least-privilege roles. User approval required BEFORE touching/starting any database process. Do not recycle the incident cluster and do not use remote main migration identity for local personal code without proving equivalence.
P1.3. Prove backup and restore into a NEW empty isolated restore target, including Windows credential handling, project adoption records and protected holds. Show that rollback cannot erase newer operator-owned state.
P1.4. PA-01 and PA-04: current managed launchers, safe exact-release startup/restart, non-incident connection and test role/migration behavior. Preserve native Claude auth, no unintended global files.
P1.5. PA-02/03/05/06/07/08: one fresh and one sanitized legacy project; A/B/C fake secret; relevant validated experience reuse and revocation; host-observed worker/validator; one supervised low-risk task, plus simple bounded rollback.
Exit P1: personal operational status only when all applicable eight PA cases have observed PASS and the configured Vres database target is non-incident. If unavailable, mark BLOCKED and continue offline feature development without implying go-live.

### Phase 2 — Complete learning loop and Chairman control plane

P2.1. Reconcile #176 E1–E6 accepted on main versus E7 local G7, B4B, trust/revocation, shadow 047/048 migrations and the P2-B production episode path. Protect original benchmark held-out from tuning and preserve failed reviews.
P2.2. Finish E7 remaining security/negative-transfer/poison/flood cases, development benchmark modes, honest owner-gap accounting, frozen thresholds and ONE held-out final assessment. No fake benchmark corpus or positive issuance through held trust code.
P2.3. Implement E8 smallest relevant trusted experience packet at real Chairman decision points; abstain on unsupported/untrusted facts, keep raw refinding bounded, measure context/latency. Validate task completion -> episode -> later-relevant retrieval and retirement.
P2.4. Implement #165 Chairman policy as distinct from worker selection: configurable generation-tolerant initial Opus/medium (user choice), materialized agent identity, explicit unavailable-model behavior and observed family/effort. Fable/high remains protected.
P2.5. Evaluate live provider cost/time/token data from real host envelopes; preserve ordinary reported telemetry as advisory. No unattended model-policy mutation on one experiment.
Exit P2: memory actually helps one later task, avoids harmful transfer, and Chairman control policy behaves as selected; exact source/protected evidence for consequential changes.

### Phase 3 — Seamless single-user Claude and project adoption

P3.1. #166 global Claude/PRISM migration: strictly bounded snapshot and hash manifest, legacy governance deactivation/quarantine, no native auth reset, GLOBAL_ADOPTION_PENDING, number-by-number KEEP/DROP, user-decision provenance, exact Fable validation, journaled atomic activation and rollback.
P3.2. #167 single-user Data Source Registry: current-user credential handle not password, explicit per-project binding, read-only PostgreSQL discovery, structural object/edge graph, code-to-DB references, semantic interpretation tagged inferred vs verified, drift fingerprint and cheap repeat-use. Other DB engines only upon a new concrete need.
P3.3. #168 complete fresh/legacy/adopted/interrupted-state machine, canonical Claude scaffold, proportional architecture audit and protected alignment plan, actual KEEP/DROP for legacy content, no fake agents/hooks, idempotent start and rollback. Reuse P2-D minimal implementation rather than rebuild it.
P3.4. Use sanitized actual legacy project and an established PRISM setup in a non-incident disposable Windows profile/project. Never load unsafe legacy hooks while merely performing inventory.
Exit P3: user can open a project, say start vres, understand an actionable adoption plan, approve clearly, and return to work across sessions and authorized projects without re-entering stored credentials.

### Phase 4 — Full capability, expert, research and optimization ambitions

P4.1. Expert/director capability lifecycle: request only missing specialists, evidence-backed capability proof, safe reuse and replacement; evaluate practical business/retail/domain outcomes with realistic tasks. Avoid promising best-in-world talent without comparison.
P4.2. Catalog native Claude skills, agents, plugins, MCP services, authenticated connectors, local tools and optional Superpowers. Classify for each scope, permission, credential, model authority, provenance and context cost. Add adapters only when they materially help tasks. JEV was withdrawn; no silent restoration or external API-key dependency.
P4.3. Browser/UI: provide a scoped browser capability and an account-creation UX audit/redesign case only after an explicit disposable website/target and permitted action list are fixed. Preserve screenshots/artifact provenance and user approval for irreversible actions.
P4.4. Codex: consider enabling separately bounded CLI execution only after isolated worktree, declared changed paths, truthful JSON/exit/postconditions and no danger-full-access fallback. Personal Codex fence stays enabled until that approval.
P4.5. Research: governed on-demand discovery, source refresh and optional scheduled reviews with real source provenance, expiry and validation. No automatic annual research claim without an installed scheduler.
P4.6. Knowledge: robust Office/PDF/code extraction, Greek/Greeklish retrieval benchmarks, useful OCR exception path, provenance/conflict handling, scoped company/project graph and real document/analysis outputs.
P4.7. Procedure evolution: extend registered executors only through deterministic authorization, sandboxed input/output, measured paired runs, fixed quality criterion, non-regression, rollback and explicit higher-scope approvals.
P4.8. Model optimization: accumulate comparable actual host measurements, not persona assertions; propose rather than secretly change costly/privileged policy.
Exit P4: representative chosen task families demonstrate measurable benefit, maintained security limits and reversible deployment, with separately held optional features explicitly documented.

### Phase 5 — Full end-to-end closure and ongoing personal baseline

P5.1. #169 physical Windows/Visual Studio journey: established global Claude/PRISM, current-user migration, real legacy project, credential reuse A/B/C, non-incident data source, memory across days/clear/compact, agent DAG, protected validation, scoped external capability and rollback/recovery. Use exact source+installed identities.
P5.2. #170 appropriately scoped local readiness: one signed-off installed personal state file, maintained clean backup, restore drill, validated operator recovery steps, minimal health monitoring, provenance/permissions audit, pilot and explicit enabled/held inventory. Commercial multi-tenant/enterprise certification remains separate and is not artificially made a personal prerequisite.
P5.3. Branch and issue closure only after relevant exact-head tests and physical evidence; retain unresolved larger ambitions with a concrete next decision, never erase them.
Exit P5: confirmed personal workflow from start vres to reviewed outcome with continuity/reuse, and a truthful completed-versus-held ledger.

## E. First ChatGPT implementation move after this checkpoint

Do not start with K0 key scripts, more general architecture planning, a DB restart, fresh Vres installation or repetitive full tests.

1. Verify new docs checkpoint Git SHA and read all four checkpoint files.
2. Read GitHub main SHA and determine exact status of local 82c8243 source. User may need to publish only the reviewed personal source branch for remote ChatGPT development; no speculative file reconstruction.
3. Select ONE smallest unblocked source work item from the register, ideally safe startup/evaluation boundary or PA-01 offline prerequisite. Freeze affected code and tests, create a dedicated source branch and commit by ChatGPT.
4. Supply the operator exactly one git fetch/read-only local update step and one concise Claude evaluator prompt; receive output and correct only confirmed findings.
5. Continue the program using short, observable milestones rather than further handoff churn.

## F. Safety and authorization policy

- Planning holds are lifted for DEVELOPMENT SCOPING only. Feature flags remain off until real independent evidence and operator consent.
- A distinct clean test DB does not retroactively resolve the incident database. No PostgreSQL service start, live migration, restore into existing DB, destructive file operation, credential materialization, external browser/write action, key/signing operation or K0 bypass without exact fresh approval.
- Runtime schema/migration incompatibility, irreversible state, secret exposure, scope bypass, misleading validation PASS, or source mismatch remain stop conditions.
- Experiments can be superseded by a safer design but their failure history, source artifacts and Git pointers cannot be erased.
- No capability is blocked merely by an old scheduling rule if its dependencies are independently satisfied; the user reopens the formerly sequential roadmap for implementation planning. Order independent source work sensibly by dependencies, without falsely announcing prior acceptance.
- Avoid new privileges or generalized enterprise infrastructure unless demanded by a concrete active personal-use requirement.

## G. Done means observed

For each V-xx row track: source SHA, affected files, functional change, test command/result, host evidence if needed, data target/connection proof, source of credentials (handle only), known limitations, recovery, approval and final disposition. Mark older claims HISTORICAL, not current. Do not declare all Vres scope done until every accepted row has an explicit implemented, live-verified, disabled-by-user, or separately accepted non-goal decision.
