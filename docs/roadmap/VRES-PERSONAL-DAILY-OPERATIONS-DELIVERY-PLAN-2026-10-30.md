# Vres-OS — PERSONAL Daily Operations Delivery and Acceptance Plan (2026-10-30)

**STATUS: IMPLEMENTATION ROADMAP, NOT SOURCE/RELEASE APPROVAL.** Owner: one Windows user. Binding charter: docs/architecture/VRES-PERSONAL-SINGLE-USER-PRODUCT-CHARTER-AND-METHOD-2026-10-30.md. Historical requirement source: docs/roadmap/VRES-FULL-SCOPE-FUNCTIONALITY-REGISTER-2026-10-22.md (all V-01..V-42) and docs/roadmap/VRES-CHATGPT-LED-FULL-SCOPE-DELIVERY-PLAN-2026-10-22.md.

## 1. Final product and the two separate finish lines

One daily-use Windows installation should let the current user ask a conversational Chairman for help with a real project, preserve task/decision/checkpoint continuity across restarts and project switches, safely recognize and adopt existing Claude/project materials, produce useful code/research/documents, reuse securely stored same-user credential handles and verified experience, and restore exactly after interrupted change. No enterprise tenant/employee administration, artificial signing ceremony or compulsory review board.

- **Limited personal daily pilot:** a user-approved, explicitly bounded installed release with working core flows, restored backup, accurate enabled-versus-disabled inventory and no critical unsafe effect. It does NOT automatically close the original #169 integrated/real-legacy contract or #170 production-readiness gate.
- **Full personal daily-operations acceptance:** the agreed user-critical workflows are actually demonstrated on the target Windows installation, original required #169 and #170 criteria satisfied or explicitly reconciled with user-approved personal scope, incident holds separately cleared, and an operational pilot accepted by the user. Do not claim success from synthetic tests alone.

## 2. Verified starting versions and pending dependencies

| Surface | Exact verified reference or observed result | Operational meaning |
|---|---|---|
| GitHub product main | 9a8acc5d464b96432a93cb95daa9581412fb07ee | Still authoritative product main; NOT latest selected candidate |
| Latest Windows-selected accepted feature | A18 HEAD 7bace7758e5c7f9a00f26179eb741ef3a319bc77, tree 4d17344a9510de6394840092cf33729ab153fbb5 | 49 PASS, 0 FAIL/SKIP, exit0; 33 pre/post pinned blobs, environment restored and verified, NOT installed |
| Main→A18 compare | ahead 74 commits, behind 0, 111 changed paths | Main ancestry verified, but no permission to merge 74 commits or claim full integrated release |
| Installed personal P2 | HEAD 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c, tree 205c081277ece483c634e1c801c39595abd4549c | Current-user installed; not A18; no authorized change |
| Installed release-hook identity | Hook blob 5833973d9be6ccf4263dda2d461cc5994d30416c, SHA256 700BF6AD711212C3A3A22419E42E0E5D62A491A7454C55C07AFED8409F0C34F7 | Installed and staged bytes both match original P2 release manifest (SHA256 FE2472B4C0F9CE247085F8D9DBF9ABB89087EAF849E2A29BE3775824922A9289) |
| Accepted A18 source hook identity | Git blob e286e4be47d058ee6ed6a3169fc45803aedc0df1; SHA256 88EA7AE078821A2DE85693DF0EE785EEEA847EA100469818DD0FBE0E4F1142B2 | Read/Glob/Grep posthook exemptions are SOURCE ONLY |
| Stage 5 | Three matcher-only changes simulated in memory; 17 groups equal outside matchers; 30 tool/event comparisons; Read/Glob/Grep posthook counts 9→0; both on-disk hashes unchanged | Narrow static candidate, no backup/real rollback or installed repair |
| A19 state-directory idea | Repository writes blocked, no commit or Windows test | Held; do not represent as implemented |
| Current hard holds | LIVE_SCHEMA_048_INCIDENT=OPEN; HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN | NO PostgreSQL even SELECT; NO ordinary native Claude Code/hooks until cleared |

**Issue status as inspected 2026-10-30:** #163 Credential Broker, #164 secret-safe ingestion and #174 architecture foundation CLOSED (source/historical status, not physical acceptance); #165 Chairman, #166 global Claude, #167 data sources, #168 project adoption, #169 real Windows/Visual Studio acceptance, #170 final readiness, #176 Experience Intelligence OPEN. User wants PERSONAL_GOVERNED non-F1 model path, but the separate strict F1 trusted-positive issuer remains blocked, and protected Fable/high is not granted by the personal scope decision.

## 3. Priority milestones — real deliverables, not consecutive parser microtests

### M0. Lock a complete PERSONAL release-candidate contract (first next ChatGPT action)

Reconcile canonical GitHub main, accepted A18 lineage, installed P2 and docs head. Read changed source/test and installer/release_artifact/release_inputs/install_recovery, Hook-R1, Chairman, task/continuity, current-user credential, and database guard surfaces. The A18 feature is 74 commits ahead of main; do not assume all additions have integrated release acceptance. Freeze a source and change-path allowlist, product promise, feature enablement inventory, planned test coverage, rollback and known gaps. Preserve A19 as blocked/uncommitted and all historical rejected originals. **Exit:** one actionable versioned release-candidate specification and evidence plan; no source/user-profile installation required.

### M1. ONE integrated integrity-preserving PERSONAL upgrade candidate (FIRST SOFTWARE DELIVERABLE)

Use accepted A18 source as the tested reference, but prove compatibility with the personal release artifact before calling it releasable. Release inputs restrict migrations to **001–041** and exclude C2B/R0/F2/schema-048 experimental files; do not bring preproduction migrations into a personal install silently. Reuse the existing Git-object-sourced manifest/staged plugin/installed package verification and recovery contracts.

Source stage should bundle the accepted hook Read/Glob/Grep matcher exemptions with the appropriate runnable package and exactly pinned metadata. **Do not hot-patch the user's P2 hooks.json**: Stage 6 established that doing so would invalidate its original immutable release-manifest hash. Preserve P2 release, staged distro and manifest as recoverable evidence. Do not falsify an old manifest to fit changed files.

**One meaningful offline Windows integrated acceptance:** clean SHA-pinned detached candidate; protected AppData, PG/DB process-env scrub/restored with saved-value checks; broad applicable source/secret/continuity/hooks/adoption/regression tests; full non-DB release artifact checks; disposable source→manifest→staged plugin; failure-injected update and rollback in a TEMP-only simulated user profile with exact byte/hash restoration. Verify changed-path allowlist, original baseline, end-state and no unauthorized external effects. Source-only or disposable work; DO NOT run the real installer because install.ps1 invokes Claude Code and has database-related dependency logic. No native Claude launch in an open hook incident.

**Exit:** candidate source HEAD/tree, manifest hashes, test matrix with actual results, complete disposable install-and-rollback evidence, exact prospective current-user changed paths and approved rollback procedure. A candidate does not authorize installing it.

### M2. Two separately controlled incidents and a protected CURRENT-USER installation (not a shortcut)

**M2-HOST:** Stage 3/4/5/6 already established a narrow static posttool matcher correction and P2 release provenance. Avoid repeating the matcher inventory. Separately assess relevant installed lifecycle/managed/other-plugin/indirect DB paths. After M1 full offline proof, produce a specific, user-only before/after/backup/rollback consent packet. Actual release switch requires a NEW explicit user authorization, a coherent new release/manifest, exact readback and genuinely tested rollback. Preserve old P2. Only then run a separately approved host-lifecycle/no-DB acceptance; a static regex PASS is not effective runtime proof. Keep HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED OPEN until explicit independent clearance.

**M2-DATABASE:** Independently investigate and resolve LIVE_SCHEMA_048_INCIDENT without connecting to PostgreSQL until incident closure and a separately approved safe target. No SELECT, health/doctor/bootstrap, Vres MCP/CLI/hooks/F2, migration or recovery against any held DB. Disposable PostgreSQL may be used only AFTER incident conditions are separately cleared and an exact nonincident target/permissions approved. Physical no-contact requires appropriate host evidence, not just printed text.

**Exit:** independent recorded disposition for each hold. Safe offline source work on other milestones can continue even if either gate remains open.

### M3. Everyday conversational loop, models and experience (#165, #176)

Prove a useful reversible low-risk task from start→plan→work→test→checkpoint→native reset/restart→resume with correct project/task, decisions and evidence. The Chairman should be the one visible control plane and present actionable output, not a network of compulsory roles. Test a real document/code/research artifact and a repeat task that reuses validated experience. One worker first; only add specialists/parallel DAG when independent work justifies it.

Complete the PERSONAL model choice from #165: requested Chairman **Opus/medium**, generation-tolerant family, disclosure of physical host-observed identity when actually available, no silent fallback; preserve routine Sonnet worker and protected Fable/high pins. Distinguish PERSONAL non-F1 practical approvals from historical strict #165/F1 independent provider authority (still blocked). No actual installed model change without explicit P2 permission. Finish essential #176 E7 trust/memory quality and E8 just-in-time compact retrieval sufficient to reject poisoned/stale/project-inapplicable memories. Do not create a separate second memory store or trigger expensive reflection every turn.

**Exit:** operator sees accurate task/phase and useful outputs with no wrong task hop, controlled costs and demonstrable appropriate memory reuse.

### M4. First-install/first-use, global Claude and project adoption (#166, #168, #174)

**#166 global Claude means this Windows user's Claude HOME**, not a company tenant. Snapshot exact existing governance; preserve vendor authentication; quarantine unsafe legacy hooks/rules before executing native Vres/Claude adoption; inventory/secret gate; propose readable grouped, numbered KEEP/DROP choices, preserve separate provenance; protected review/approval for activation; durable journal, exact rollback and idempotent repeat start. PRISM may be a controlled legacy fixture, not the new master agent. No real PRISM installation to current live user profile until #169/consent.

**#168 project:** distinguish fresh versus mature/legacy; audited facts not guessed; concise supported CLAUDE.md and justified .claude directories, no dummy agent/skill; detailed secret-safe inventory with NEVER executing imported commands/hooks/DB/browser; KEEP/DROP decisions frozen and justified, architecture alignment plan per #174 with validation where required, recovery and idempotence. Accepted #168 A1–A18 are partial source/security components, not the full UX.

**Exit:** disposable fresh and sanitized established legacy fixtures work and recover exactly, with an understandable first-use experience before using a real project.

### M5. Reusable current-user credentials and data sources (#163/#164/#167/#168)

#163 and #164 already closed as source requirements. Physically verify one synthetic credential created for one website/service/project can be reused in another approved project under the SAME Windows user, never another Windows user, without plaintext values in durable .env/Claude/chat/logs. Explicit project binding; no cross-project ambient access. Keep existing current-user Credential Locker ownership.

For #167, implement offline registry/catalog identities, project authorization, schema snapshot/relationships/drift/delta and evidence-backed semantic labels without DB contact. After M2-DB clearance + explicit test-target approval, verify read-only least-privilege PostgreSQL audit against a disposable database: no raw data sampling by default, no mutations, bounded refresh, unchanged catalog reuse, authorized A/B project bindings and unbound C denial. A discovered connection string is not consent to connect.

**Exit:** safe two-project reuse and separate unbound denial with validated resource provenance.

### M6. Integrated Visual Studio/PRISM/real legacy acceptance (#169)

Only after required implementation dependencies are accepted and appropriately merged/released, incidents resolved and specific user authorization obtained. Use isolated/snapshotted Windows user profile with independent restore. Test exact candidate packaged installation over a known dirty Claude/PRISM fixture, then new/real legacy project from Visual Studio integrated workflow, grouped KEEP/DROP, correct local sources/secret handling, explicit credentials and datasource links, safe current-user settings, protected review where required, interruption and rollback. Record PRISM commit, host Claude version, source release SHA, installed manifest, before/after file hashes, user decisions, host-observed model and sanitized activity. Visual Studio itself is not evidence; the observed Vres workflows are.

**Exit:** all original #169 critical criteria PASS with no unsafe secrets, wrong-task hop or unrecoverable state. Failures become bounded implementation work and impacted-surface rerun, not a whole new speculative design initiative.

### M7. PERSONAL real-work readiness and an actual daily pilot (#170)

Make a protected but low-friction current-user installation usable: predictable start/stop, backup/restore of needed current-user metadata and approved DB after clearance, update and rollback, secure logs, feature enabled/held summary, practical diagnostics, cost sanity and task continuity. Run a **small, explicit, user-approved pilot** over varied ordinary tasks and one real project, not just synthetic unit tests. Check that after a restart the user can resume correctly, two authorized projects can reuse a handle, a third is denied, a safe legacy project can be adopted with rollback, and a real deliverable can be accepted. Planned acceptance examples are NOT measurements until observed.

**Exit:** user signs off a specific installed release and limits for normal daily use. Do not call full #170 production-ready before its original evidence gate; a limited pilot is named LIMITED and remains honest about intentional held capabilities.

### M8. Optional growth AFTER the useful baseline

Keep V-08 auto model optimization, V-10 retail/business Agent Board specialties, V-13 external adapters, V-14 Superpowers, V-15 browser/GUI journeys, V-16 optional Codex action adapter, V-18 general procedure executor extensions, V-25 embeddings/OCR Greek/Greeklish, V-26 scheduling/research refresh, and V-37 C2B/K0 experimental issuer/key custody as separate **OPTIONAL** or later tracks. V-23 company-wide publication is not an implicit daily-user goal. Never delete these ambitions, but do not force them or enterprise infrastructure into the critical path.

## 4. Complete V-01..V-42 traceability (original per-item register remains authoritative)

| Topic | Requirement IDs | Milestones |
|---|---|---|
| Chairman, continuity, context/architecture, evidence, governed model | V-01..V-07 | M1/M3/M4 |
| Empirical model tuning, specialists, agents, capability/extensibility | V-08..V-14 | M3/M8 |
| Browser/Codex, procedures, measured optimization | V-15..V-18 | M3/M8 |
| Experience, E7/E8, semantics/temporal knowledge, protected publication | V-19..V-23 | M3/M4/M8 |
| Document onboarding, OCR/embeddings, research refresh | V-24..V-26 | M4/M8 |
| Credential Broker and secret-safe onboarding | V-27..V-28 | M3/M4/M5 |
| Global & project adoption, data source/catalog/project reuse | V-29..V-33 | M4/M5 |
| Windows install/recovery, database safety, optional trust experiments | V-34..V-37 | M1/M2/M7/M8 |
| Real Visual Studio acceptance, readiness, reproducible supply | V-38..V-40 | M1/M6/M7 |
| Useful outputs and low-ceremony UX | V-41..V-42 | M3/M6/M7 |

The existing per-ID statuses and acceptance clauses in the historical [V-01..V-42 Register] are not overwritten. A planned item is not tested, installed, operational or optional by implication; record its accurate current release state before closing it.

## 5. Testing and delivery evidence policy

**One substantive software milestone → one integrated, SHA-pinned Windows offline acceptance where practical.** If a real defect is found, preserve failed original SHA/worktree and add a distinct small correction rather than rewinding history. Do not rerun all 200+ historical tests on a docs-only commit; use impact-driven suites and broad final gates. Single self-contained copy/paste PowerShell block, clean detached checkout, exact official GitHub origin/HEAD/tree/parents/allowlist and relevant protected blobs, one actual pytest command, plugin autoload disabled, process PG/DB/integration variables saved/scrubbed/restored with actual value comparison, protected temp AppData, posttest Git cleanliness. Output must show exact PASSED/FAILED/SKIPPED counts and exit. Never invent a Windows test result from GitHub authoring.

No mutating installed user files, native Claude Code/hooks, Vres MCP/CLI/doctor, PostgreSQL contact, credentials, provider calls, PR/merge/main or product activation under open safety holds. Future P2 user-only installed change requires explicit detailed authorization, tested rollback, source/artifact integrity and accurate after-state. No "quiet" enterprise controls or unproved independent F1 credentials.

## 6. EXACT next ChatGPT action in the new session

Read canonical index newest READ FIRST line, the new PERSONAL Charter and this plan, Stage 6 provenance handoff and original V-01..V-42 register; verify GitHub refs and accepted A18 direct lineage, product main and original P2 installed identity. **Start M0: bounded read-only release-compatibility and gap assessment**, then author the M1 complete offline upgrade candidate and rollback test plan on a new dedicated GitHub source branch with exact A18 parent and appropriate source/test allowlist. Do not request a redundant Stage 7 hook-matcher inventory. If the repository write or tool use is blocked by safety controls, preserve that blocker transparently and continue permissible read-only planning; do not bypass safety. Next Windows action comes only when one integrated candidate/script is ready; supply the whole script inline in ONE code block, no file-only prompt.

**Status:** no M1 source candidate or new installed release is claimed by this plan.
