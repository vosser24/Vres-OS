# Vres-OS — 2026-10-30 AUTO-CHECKPOINT / 20 ASSISTANT REPLIES OR >50% CONTEXT — DETAILED RESTART HANDOFF

**Type:** owner-requested documentation-only continuity checkpoint and binding ChatGPT Project instruction text. **Status:** source and release identities are historical/verified as specified; no new Vres source, Windows test, installed change, Claude Code invocation, PostgreSQL contact or production readiness is claimed by this checkpoint.

**Repo:** https://github.com/vosser24/Vres-OS
**Canonical docs branch:** docs/chatgpt-continuity-20261023. Prior verified docs HEAD at this checkpoint's start: **0ece9b94ef60cf7765cc60de3d91f99dc6eb9839**, tree **63b7f9c7695392e9cd273a4aa2ef515f72e9f9c2**. The GitHub HEAD generated when this document is published will be the new authoritative latest docs checkpoint; ALWAYS verify remote refs, never rely solely on hardcoded text here.

## 1. Owner's new HARD Project instruction — automatic checkpoint / session rollover

**TRIGGER at the earlier of:**
- the **20th completed assistant reply** after the last verified checkpoint or start of the ChatGPT session; OR
- **more than 50%** of the active context window reported reliably or conservatively ESTIMATED to be consumed. Model does not expose an exact context-usage percentage by default, so never claim precise measurement; checkpoint proactively at or before a plausible 50% boundary. If count unknown, checkpoint immediately instead of risking history loss.

Upon trigger, stop starting another implementation phase; finish/abort only the current safe atomic action, mark all incomplete tests/writes/approvals pending; exact-ref-verify GitHub; commit **all completed and authorized** source/test/docs changes on appropriate branch with nonforce CAS; verify commit tree and remote; update canonical index with a dated detailed handoff, status, proof, open holds and one precise next step; provide the **ENTIRE resume prompt in an inline fenced code block**, never file-only, then recommend beginning a new ChatGPT session.

This rule operates **in active turns only**. There is no background monitor or guaranteed precise context meter. ChatGPT cannot directly edit this Project's UI instructions with the currently available tools; operator must paste the exact rule from **docs/handoffs/VRES-CHATGPT-PROJECT-INSTRUCTIONS-20-REPLIES-50PCT-CHECKPOINT-RULE-2026-10-30.txt** into the Project instructions. The identical text is supplied inline in the committing ChatGPT response. This document and the charter/index are repository commitments, **not proof the UI rule is already installed**.

**No rewriting product history, enterprise-control additions, forced test reruns for docs-only changes, unrequested merges/PR/force push, deletion of local worktrees or source claims beyond available evidence.** If a future GitHub write is blocked, report the actual block and provide the available inline handoff rather than saying it was committed.

## 2. Binding application scope and development priorities (PERSONAL, never enterprise by drift)

The application is a practical PERSONAL assistant for **one Windows user's** own day-to-day software projects, research, documents, websites, credentials and continuity. One conversational Chairman, honest governed specialists, accurate task/project resume, local user-scoped protected credential handles and explicit project-resource bindings, reusable validated experience/procedures, safe Claude/PRISM adoption and recoverable updates are the core goals.

No default multi-tenant IAM/SSO/enterprise approval board/corporate issuer/hardware co-signature architecture. Preserve all historic **V-01..V-42** intentions; the newer owner-approved PERSONAL charter/roadmap are priority/method constraints, not deletion of pending capabilities. P0 ephemeral trivial actions no ceremony, P1 reversible scoped work/tests, P2 installed/user-scope/credential/critical action needs specific consent + proven rollback, P3 incident STOP.

**Methodology:** no more endless A19/A20 or Stage 7 same-matcher checks; plan useful complete software milestones, author source/test/docs on exact-parent GitHub branch, run one meaningful guarded Windows offline integration/release/rollback acceptance for substantive milestone, then move to actual limited daily pilot via #169/#170 prerequisites. Don't claim a SHA pin is independently signed authority or that synthetic pytest covers host/DB contact. Independent native Claude review is held during host-hook incident, not silently reported passed.

Canonical docs available on docs branch:
- **Personal charter:** docs/architecture/VRES-PERSONAL-SINGLE-USER-PRODUCT-CHARTER-AND-METHOD-2026-10-30.md
- **M0–M8 delivery roadmap:** docs/roadmap/VRES-PERSONAL-DAILY-OPERATIONS-DELIVERY-PLAN-2026-10-30.md
- **Earlier comprehensive 21,907-char handoff:** docs/handoffs/VRES-PERSONAL-2026-10-30-COMPLETE-DAILY-OPERATIONS-RESUME-HANDOFF.md
- **Historical 42-function ledger:** docs/roadmap/VRES-FULL-SCOPE-FUNCTIONALITY-REGISTER-2026-10-22.md
- **Historical ChatGPT-led delivery plan:** docs/roadmap/VRES-CHATGPT-LED-FULL-SCOPE-DELIVERY-PLAN-2026-10-22.md
- **All chronological accepts/rejections/test outputs:** docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md

## 3. Exact source / product main / installed release boundaries

**GitHub PRODUCT MAIN** at last verified checkpoint: **9a8acc5d464b96432a93cb95daa9581412fb07ee**. No authorized product-main merge. Latest selected Windows-accepted **A18 source** branch feature/168-personal-record-leaf-rebind-a18-20261030 at HEAD **7bace7758e5c7f9a00f26179eb741ef3a319bc77**, tree **4d17344a9510de6394840092cf33729ab153fbb5**, parent accepted A17 **edcc347cd51c7a14e553a034d89bb7bb45da63ae**. As last verified, main→A18 ahead 74 commits, behind 0, 111 changed paths. **A18 NOT merged, not installed, independent native Claude A18 review NOT_RUN.**

A18 Windows guarded selected test: **49 individually named PASS**, 0 FAIL/SKIP, exit0, **33 SHA-pinned protected Git blobs pre/post**, AppData fence unexpected refusals0, exact Git worktree SHA/tree/ancestry, **process environment restoration with original-value verification**. Full acceptance: docs/handoffs/VRES-168-A18-WINDOWS-49-PASS-EXIT0-ACCEPTANCE-2026-10-30.md. Selected 12 A18 leaf-rebind +12 A13 R1 ancestor +16 A12 R1 record read +4 A17 finite float +4 A16 JSON +1 A11 synthetic activation/rollback. This is best-effort pathname leaf identity safety, not atomic filesystem traversal/cryptographic trust, native host safety or full release integration.

**Original P2 current-user INSTALLED release** source commit **82c82430b38f93bd6b9d5c3af3b5de9c1368af9c**, tree **205c081277ece483c634e1c801c39595abd4549c**. Installed plug-in root under current user's \`.claude\skills\vres-os\`, active pointer under current-user \`%LOCALAPPDATA%\VresOS\active-install.json\`. Installed P2 hooks Git blob **5833973d9be6ccf4263dda2d461cc5994d30416c**, SHA256 **700BF6AD711212C3A3A22419E42E0E5D62A491A7454C55C07AFED8409F0C34F7**. Stage 6 validated installed and staged hook bytes both match immutable old P2 release manifest SHA256 **FE2472B4C0F9CE247085F8D9DBF9ABB89087EAF849E2A29BE3775824922A9289**, five local file hashes unchanged. Do not hot-patch installed P2 hooks, which would violate source-manifest provenance.

Source A18 hooks Git blob **e286e4be47d058ee6ed6a3169fc45803aedc0df1**, SHA256 **88EA7AE078821A2DE85693DF0EE785EEEA847EA100469818DD0FBE0E4F1142B2**, differs from installed P2 hooks. Stage 3 fixed-name Read/Glob/Grep successful/failed post-hook matcher comparison: **6 different tool-event combinations, 9 matched installed declaration entries vs source 0**, NOT 9 observed hook executions. Stage 4 examined **17** hook groups: exactly **3** matcher differences (PostToolUse groups 2 and 4, PostToolUseFailure group 1), **zero** nonmatcher payload/group-count differences. Stage 5 simulated replacement **IN MEMORY ONLY** and proved full structure matches source plus 30 sample tool/event comparisons, read-posthook 9→0, both on-disk files unmodified; backup/rollback NOT performed. Stage 6 proved P2 release coherence, not full package integrity or host lifecycle safety.

**A19:** proposed state-directory ancestry hardening source writes were blocked by safety controls: UNCOMMITTED, UNTESTED. Do not bypass controls or call A19 accepted; reassess only as part of a needed integrated release risk, not a new micro-test treadmill.

## 4. Historical rejections and high-value evidence — DO NOT LOSE

- **Original rejected A12:** HEAD **345a568b551ac23183c54f10611335adee903b96**, Windows **18 PASS, 1 FAIL, exit1** (unbounded deep JSON accepted), original checkout preserved. Corrected A12 R1 **80cee6fe9f0f0dbe55c70d2103e54c1d9bc5b966**, 23 selected PASS.
- **Original rejected A13:** HEAD **cdaa39aaa774cef88a4831bf6b157e380fbb69d9**, Windows **28 PASS, 1 FAIL, exit1** (parent junction diagnostic), original checkout preserved. Corrected A13 R1 **007a51b05d6c0e3d43086a864558fb666853d58d**, 32 selected PASS.
- A14 **06fc9ddb488f7aa7ef1f980f0bfbe59b3a29b0fc**, 23 PASS; A15 **9d63044012e59663fbeb9448a08e9aabae5dbe7d**, 22 PASS; A16 **fc2e52ab8feac3ce784bbb6a4484e4a37e3f4bf5**, 23 PASS but its original Windows script-copy environment restoration remains **UNVERIFIED**; A17 **edcc347cd51c7a14e553a034d89bb7bb45da63ae**, 24 PASS with env restored; A18 49 PASS with verified env restored.
- PT2A historical Windows 213 PASS and PT1 189 PASS, Hook-R1 source-only exemptions and seven posttool hook DB-routing attempts refused; independent native A18 reviewer NOT_RUN. Earlier #165 design, credential, E7/E8 memory and K0/C2B/R0/F2 historical risk/test records in the complete chronology must be retained without false acceptance labels.
- Previously accepted/rejected local Windows worktrees are not available for this GitHub-only docs checkpoint, and cannot be claimed freshly clean or all locally committed.

## 5. HARD INCIDENT HOLDS, not relaxed by scope or checkpoint

**LIVE_SCHEMA_048_INCIDENT=OPEN**: absolutely NO PostgreSQL contact, EVEN SELECT; includes Vres CLI/MCP/hook/bootstrap/doctor/F2/migration/recovery. No "just verify database" shortcut.

**HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN**: seven historical native Claude Read/Grep posttool DB routes attempted/refused; no ordinary native Claude Code startup/static review/hook execution or installed Claude runtime until separately cleared. Static Stage 5 does not prove managed/lifecycle plugin safety or physical no-contact. No F1 independently trusted positive authority issuer/Fable-high protected call, real model switch, credentials retrieval, installing or modifying global Claude/PRISM, real Visual Studio legacy project, product-main PR/merge or go-live without the separate owner approvals and actual evidence. Source-only offline development on approved branch is distinct and still possible.

## 6. Pending cases, dependencies and full path to DAILY OPERATIONS

Closed source dependency issues: **#163 Credential Broker**, **#164 secret-safe ingestion**, **#174 architecture**. These do not certify installed behavior. Open: **#165** personal Chairman Opus/medium governed policy versus strict F1 blocked, **#166** current-user existing Claude/PRISM global governance migration, **#167** same-current-user credential-bound Data Source Registry and read-only semantic catalog (requires separately cleared DB), **#168** full fresh/legacy project adoption, **#176** Experience E7/E8 memory/retrieval security, **#169** integrated Visual Studio/PRISM/real legacy physical acceptance, **#170** practical production/daily-operations readiness and pilot. Explicitly preserve all original **V-01..V-42** registered needs, including optional agent-board domains, Codex, browser, procedure evolution, model efficiency, OCR/embeddings/research and held experimental trust issuers.

**M0 NEXT:** perform read-only source/release compatibility analysis of A18 versus main/P2 and approved personal release inputs, the current installer/release_artifact/release_inputs/install_recovery, hooks, model/Chairman, task continuity, credential/adoption and DB guards. Pin 001–041 personal migrations and exclude C2B/R0/F2/schema-048 experiments. Define one integrated release-candidate exact changed-file/test/rollback acceptance contract. Do NOT do another Stage 7 regex inventory.
**M1 FIRST SOURCE DELIVERABLE:** ONE versioned, coherent personal upgrade candidate with accepted source hook fixes, full release manifest/distro identity, **disposable** guarded offline source→artifact→simulated install/rollback/failure injection, broad relevant Windows tests only once at substantive milestone. The real installed updater/installer invokes Claude and/or DB-sensitive paths and is forbidden during incidents. Complete the source+test GitHub branch and operator full PowerShell validation block before asking the user to perform tests.
**M2:** independent host-hook and schema-048 incidents separately resolved before any actual user-profile/DB action; a specific reversible P2 operator permission before installed release switch.
**M3:** real Chairman, correct task/session continuity, protected credential handles, useful experience retrieval.
**M4:** global Claude/PRISM and fresh/legacy adoption with exact approval/rollback.
**M5:** current-user datasource registry, read-only schema map and project binding after DB clearance.
**M6:** Windows Visual Studio integrated PRISM/real legacy acceptance #169.
**M7:** real limited personal daily pilot/readiness #170 (not merely automated tests).
**M8:** optional advanced ambitions after dependable personal baseline.

Proportionate methodology P0–P3, ONE relevant Windows offline integration gate per substantive milestone, exact GitHub nonforce refs, no source/installed/credential actions without scope/approval, no forced enterprise review ceremony. User preference: **every PowerShell or Claude prompt fully inline in a SINGLE fenced code block**, never broken into steps or file-only.

## 7. Exact next session restart protocol

1. Verify GitHub docs HEAD and READ FIRST in \`docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md\`, and read this new dated handoff, the binding PERSONAL charter, M0–M8 roadmap and prior full 2026-10-30 handoff.
2. Verify product main and A18/P2 identities; if any SHA drift, reconcile before source changes; never infer local Windows state.
3. Keep the two incidents OPEN, no PostgreSQL/normal native Claude/installed changes or real secrets.
4. **Start actual M0 source/release compatibility analysis immediately, progress into M1 integrated offline candidate** on permitted exact-parent GitHub source/test branch; do not ask to re-investigate solved three hook matcher differences.
5. Produce only verified source/test statuses, exact Git commits, and a WHOLE copy-paste PowerShell script when M1 substantive test readiness exists; never claim test or background completion prematurely.
6. Operate under new automatic 20-reply / >50%-context checkpoint rule again; count reply 1 from the new conversation and checkpoint by reply 20, or conservatively earlier.

**This checkpoint contains no new software release or installed update.** The ChatGPT Project UI requires the owner to paste the Project rule manually, because no available tool can change its instructions directly.
