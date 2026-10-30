# Vres-OS — Binding PERSONAL Single-User Product Charter and Proportionate Engineering Method (2026-10-30)

**Status:** OWNER-DIRECTED HARD RULE FOR FUTURE PRODUCT/PLANNING/METHODOLOGY. **Target:** one Windows user and their own projects, tools, accounts, work and data. **Repository:** vosser24/Vres-OS. **Evidence scope:** this is a prospective product rule, not evidence that an unbuilt or untested capability exists.

## A. Non-negotiable product identity

1. **Vres-OS is a PERSONAL desktop/workstation operating assistant, not an enterprise SaaS, corporate platform or multi-tenant product.** Deliver one dependable local installation for the current Windows user that helps with routine software engineering, research, tasks, documents, websites and the user's personally authorized project/business work. Its target is reliable **daily personal operations**, not enterprise certification.
2. **User experience first:** a single conversational Chairman, a predictable start/resume, supported real-world work, explicit succinct approvals when necessary, recoverability and low repeated overhead. The user should not have to manage Git worktrees, retrieve credentials for each project, repeat known context, read large internal audit packets or manually orchestrate agent workers during ordinary use.
3. **Single-user locality is an architectural constraint.** Durable secrets stay in that Windows user's protected credential store; metadata, procedures, experience and catalogs are scoped to that user. Projects may reuse one resource only with explicit project binding and the user's permission. Another Windows account is a separate principal; no ambient cross-user, company-wide or machine-wide authority.
4. **Company/enterprise terminology in inherited modules is historical, not an invitation to build enterprise infrastructure.** Existing governed company-wide APIs remain guarded for backward compatibility, but no corporate IAM, SSO, department hierarchy, approvals board, employee roles, hosted identity provider, certificate PKI, hardware multi-signer ceremony or multi-tenant control plane is a default prerequisite for PERSONAL daily use. Add one only when an actual personal use case, real security requirement and evidence justify it.
5. **Never shrink the original functionality ledger by deletion.** V-01..V-42 and issue #165–170/#174/#176 remain the historical source of feature intent. Mark each as daily-use essential, required integration, optional later, deliberately held or not applicable; do not disguise pending items as already delivered, erase historical failures or rename a held feature as complete.
6. **One trusted owner:** Chairman coordinates, proposes and explains. Specialists, model workers, memory, Claude/PRISM adoption, credentials and external tools are supporting capabilities, not competing executive control planes. Reuse existing Vres services; do not invent new frameworks, duplicate registries or artificial committees.

## B. PERSONAL threat model — protect the real risks

Protect against inadvertent overwrites, stale/false-positive validation, unauthorized external effects, malicious project text/prompt injection, secret leakage, cross-project reuse without permission, mismatched installed releases, wrong-task/session continuation, untrustworthy remembered lessons and recoverability failures. Preserve provenance when decisions, approvals or validations matter.

**Honest assurance limit:** ordinary same-user files/hashes/user confirmations do not constitute independent cryptographic protection against an attacker with arbitrary code execution as the same Windows user. Do not claim T2-independent authorization, independent signing or physical provider attestation merely because a local JSON receipt, hash or model response exists.

### Risk tiers; apply to actual actions, not paperwork

| Tier | Personal examples | Proportionate required behavior |
|---|---|---|
| **P0 — ephemeral** | explanation, analysis, drafting, harmless local calculation, nonpersistent read-only summaries | Respond promptly; no ticket/committee/protected signing or persistent decision ceremony |
| **P1 — reversible project work** | source edits in an explicitly chosen project/worktree, ordinary tests, approved local artifact creation | Verify target and change scope; normal regression tests, clear result, local undo; avoid second redundant review when no material risk |
| **P2 — protected personal changes** | installed Vres version, user Claude/PRISM hooks/settings, Chairman or validator policy, credential linking/use, durable security rules, irreversible third-party transactions | Explicit **specific** user authorization at the consequential action; exact before/after identities, complete changed-path allowlist, sensitive-output handling, bounded tests and tested rollback before active switch |
| **P3 — incident/high-stakes hold** | prohibited PostgreSQL, unknown installed hooks, unapproved protected Fable/issuer, real secrets in chat, ambiguous destination, unrecoverable changes | STOP until the separate incident/authority gate is cleared; PERSONAL scope never downgrades an active P3 hold |

An explicit "continue development" or "commit all" **does not** mean permission to launch native Claude, touch live DB, write to installed user settings, use secrets, move branches, merge main or deploy. Source/doc commits on isolated branches are separate from real installation authority.

**Binding current holds, as of 2026-10-30:** LIVE_SCHEMA_048_INCIDENT=OPEN ⇒ absolutely no PostgreSQL contact even SELECT, including indirect Vres CLI/MCP/hooks/doctor/bootstrap/F2/migration/recovery. HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN ⇒ no normal native Claude Code launch/review until host-hook lifecycle and installed effective route safety are separately established. Positive independent #165/F1 authority and protected Fable/high are NOT granted by a PERSONAL decision; governed NON-F1 development is allowed, but a real protected approval still requires its separately accepted evidence and specific permission.

## C. What DAILY PERSONAL usefulness means

Expected ordinary user journeys, to be implemented and tested, not silently asserted available:

1. **One start / one Chairman.** On the intended Windows workstation, launch the approved installed Vres/Claude workflow with a clear explanation of current project, task and safe/held capabilities. No accidental migration or DB contact during mere inspection.
2. **Resume without re-explaining.** Restore exact project/task, recent decisions, pending work and evidence after native clear, compaction, restart or switching projects. No unrelated task hop, unsourced memory authority or invented completion.
3. **Understand a fresh or existing project.** Offer deterministic architecture and secret-safe inventory; create only supported Claude-native files and recommend grouped numbered KEEP/DROP for legacy material. Never run legacy hooks/app/browser/DB during discovery.
4. **Useful bounded work.** Make reversible source/document/research/analysis outputs, run relevant tests, cite important evidence and leave a user-readable outcome. One worker by default; governed specialists or parallel work only for demonstrably independent tasks.
5. **Reuse what the user already has.** Same-user credential handles, project-specific bindings, validated procedures, relevant lessons and optional data-source catalogs can be reused across authorized projects without repeated plaintext secret requests.
6. **Reliable recovery.** User can inspect last known good release, recovery status and exact rollback procedure; interruptions must not silently leave half-active Claude configuration, project adoption or Vres update.
7. **Cost-aware operation.** Avoid unnecessary model calls, all-context replays, reflection per turn, compulsory parallel agents, repeated scans and enterprise provider subscriptions. Use user-selected model policy; clearly label actual requested versus host-observed model/effort where measurable.

## D. Engineering workflow: MILESTONE-FIRST, evidence once, no ceremony treadmill

**Binding work ownership:** ChatGPT owns plan, scoped source/tests/docs authoring and GitHub commits. The operator executes approved Windows-only checks. Claude is an independent review/execution provider **only when host hooks are independently safe**; its absence cannot be disguised as a review PASS. No implicit background work or silent completion.

1. **Select a user-visible outcome** and freeze its definition of done, safety boundary and dependencies. Bundle closely related functions into one coherent, useful milestone (e.g., integrated release + rollback), rather than a new Axx branch for each tiny parser branch or informational finding.
2. **Choose existing owners and an explicit allowlist.** Reconcile accepted source SHA, product main SHA, installed release SHA and documentation head. Read the current source/requirements before editing. Never overwrite previously accepted or rejected evidence, clean worktrees or incident fixtures.
3. **Implement in GitHub on a dedicated nonforce, exact-parent feature branch**, with tests and docs. No force push, blind merges, unsafe hook/install/credential changes, or work on local user PC from a source commit alone. Preserve failing original commits and use a distinct corrective commit or branch when required.
4. **Run proportional gates:** static/deterministic local source checks first; selected Windows offline pytest/integration for changed behavior; full impacted suites and disposable end-to-end flows **once at the milestone boundary**, not per trivial edit. Keep source and test SHA pins, one complete self-contained PowerShell block (never fragmented or file-only), preflight HEAD/tree/blobs/clean, process PG/DB/integration-variable scrub and **actual saved-value restoration verification**, temporary AppData fence and postflight integrity. Prefer a single integrated batch that yields a useful acceptance decision.
5. **Report epistemic state precisely:** AUTHOR_ONLY, SOURCE_COMMITTED, STATIC_PASS, WINDOWS_SELECTED_PASS, INDEPENDENT_REVIEW_ACCEPT, INTEGRATED_ACCEPT, INSTALLED_ACCEPT, DAILY_PILOT_ACCEPT, BLOCKED, NOT_RUN, REJECTED are distinct. No claim that GitHub object creation ran pytest, or that 49 selected regressions prove production. Include exact failing cases and do not repeat a green suite without a material code or environment change.
6. **Review only actionable blockers.** One independent material review when safe; one corrective cycle for real defects. Architectural disagreements without executable impact or evidence become tracked informationals, not an endless new charter/reviewer loop.
7. **Promote the WHOLE release**, not a manual one-file patch that breaks a pinned release manifest. Protect previous release manifest, staged bytes and current-user data. Rehearse failure injection and restore on disposable fixtures before asking for approval of an installed switch.
8. **Finish with a practical demonstration**: the intended workflow on the intended platform with the installed candidate and a user verdict; observe restarts, exact task/source selection, provenance, permissions, recovery and cost. Do not call an offshore CI green check equivalent to installed daily use.
9. **Commit one durable checkpoint** containing product state, evidence, changes, deferred cases, known unresolved holds, the first next operation and a full resume prompt. Avoid calling document-only work a released software feature.

### Reviews, approvals and tests should be small but real

- Routine P0/P1: tests appropriate to changed surface, normal deterministic assertions, no synthetic enterprise gate.
- P2: explicit user consent, source/target SHA identities, rollback protection, clear installed-file allowlist and focused independent assessment if safe.
- P3: no activity under the hold; do not route around a DB incident by renaming it or launching a provider to "check" host hooks.
- Never run all historical regression suites simply for a documentation-only change; run broad integration once when real milestone behavior changes.

## E. Built vs enabled vs desirable; scope triage

**Must be working for routine personal use (CORE):** personal Windows installation/start/update and rollback; one Chairman; safe current project; persistent tasks/decisions/continuity; bounded source/docs work; secure credentials; fresh/legacy project intake; basic memory retrieval; reliable reporting and explicit P2 consent.

**Must be proven where the user's real usage requires it (CONDITIONAL CORE):** global old Claude/PRISM adoption; current-user credential reuse and data-source catalog with explicit per-project binding; host-observed model policy/validator; real Visual Studio project; PostgreSQL only after an authorized nonincident target and cleared incident conditions.

**Useful but not prerequisite for the first low-risk daily pilot (LATER):** large boards of agents, recursion, empirical automatic model replacement, new global procedure executor families, optional embeddings/OCR, autonomous scheduled research, browser automation, rich enterprise-grade dashboards, experimental C2B/K0 trust publisher ceremony, multi-tenant/SSO facilities. Preserve as backlog with state and owner; no premature enterprise architecture.

**Never silently abandon the roadmap:** the canonical V-01..V-42 register remains a linked requirement ledger. A daily pilot may proceed only within a separately safe and explicitly limited supported feature set, without asserting #169 full integration PASS or #170 full production readiness until their own exact evidence and original gate conditions are met.

## F. Immediate priority and exit objective

**FIRST NEXT MILESTONE = PERSONAL INTEGRITY-PRESERVING UPGRADE CANDIDATE**, starting from Windows-selected A18 source HEAD 7bace7758e5c7f9a00f26179eb741ef3a319bc77 (not installed). Consolidate the accepted read-tool matcher exemptions with legitimate P2 source/release/installer compatibility, publish an exact versioned candidate, run one broad guarded Windows **disposable** offline release-artifact/rollback rehearsal with relevant unit tests, verify no DB calls, and prepare an explicit approval packet for any later installed switch. Stage 6 proved original installed P2 hooks and staged copies match the old release manifest: a direct hot patch is NOT an acceptable upgrade. Do not execute the installed installer, Claude or Vres to "test" in the open incident.

**Second**: separately close native hook host/scope and PostgreSQL schema-048 incidents through accepted evidence, not by assertion. **Third**: complete PERSONAL-first #165/#166/#167/#168 and #176 E7/E8 integration for the user's real requirements. **Fourth**: #169 controlled Visual Studio/PRISM/real legacy physical acceptance, then #170 personal operational readiness and a genuinely used limited pilot, while honestly tracking any held optional features.

This is a binding personal-use method and prioritization decision. It does NOT supersede actual security holds, modify source code, issue provider authority, merge product main or authorize user-profile installation.

## G. Automatic ChatGPT conversation checkpoint and session rotation (owner hard rule added 2026-10-30)

This is a **binding continuity/process requirement**, not a live model usage quota or a guarantee of background operation. At the earlier of **20 completed assistant replies** since the latest verified continuity checkpoint / the current chat start, or **more than 50% of the active context capacity** when reliably known or conservatively estimated, ChatGPT must stop launching new development phases, commit every completed authorized GitHub source/test/document change with exact parent and nonforce branch update where possible, verify remote readback, publish a complete fresh-session handoff and update the canonical docs index, and supply the complete resume prompt **inline in one copyable code block**. Recommend a new ChatGPT session; reset reply count after a verified checkpoint. If the context percentage is inaccessible, do not fabricate its measurement; estimate cautiously and checkpoint early. If count state is uncertain, checkpoint immediately.

**Exact ChatGPT Project Instructions paste text:** [20 replies / >50% context owner hard rule](../handoffs/VRES-CHATGPT-PROJECT-INSTRUCTIONS-20-REPLIES-50PCT-CHECKPOINT-RULE-2026-10-30.txt). **Current dated continuation example:** [checkpoint handoff](../handoffs/VRES-2026-10-30-AUTO-CHECKPOINT-20-REPLIES-50PCT-HANDOFF.md). GitHub documentation records the rule but **does not change the ChatGPT Project UI instructions automatically**; the owner needs to paste that text there. No unsupported claim that local Windows unpushed files were committed, no silent main merge, no unsafe incidental operations. Preserve both OPEN incident holds, protected approvals and every original rejected/accepted evidence record.

