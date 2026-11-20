# Vres-OS — 2026-11-20 R13N original recovery-path consistency; same-October-install hybrid HELD

**READ FIRST / VERIFIED GITHUB SOURCE-ONLY CHECKPOINT.** Owner authorized "proceed" for integrated R13N source engineering after receiving unsigned Claude Fable R13M advisory. Original installer caught-error rollback bypass removed IN SOURCE, original interrupted-install inspector classified and held, five source/docs/test paths committed. This checkpoint is NOT independent review, tests PASS, live migration clearance, native Windows/Claude permission, release or an asynchronous handoff. Exact GitHub data below was authenticated and remotely read back. The actual Windows laptop, installed P2 and PostgreSQL were NOT accessed; no precise ChatGPT context-window percentage is available.

## 1. Binding one practical original Windows CLI/FastMCP application

Build ONE complete production-quality PERSONAL Windows daily-operations companion for ONE user. The ORIGINAL Claude Code CLI is PRIMARY; the ORIGINAL FastMCP server is integral. Preserve the ORIGINAL Chairman, Authoritative Repository, tasks and explicit selection, real provider-session-bound task_resume, sessions, results, history, checkpoints, projects, credentials and data sources, experience retrieval and governed learning, install.ps1, update.ps1 and recovery.

Preserve ALL original V-01..V-42, M0..M8, W0..W3, W4 R1..R13N, C2B/K0 and October 22/30/31 plus November 5 roadmaps. NO second Vres application, Windows installation, GUI/Tk expansion, duplicate Chairman/task/result owner, parallel MCP runtime/installer, enterprise IAM or multitenancy. Use proportional P0/P1/P2/P3 controls and useful integrated milestones. No real PRISM/legacy or TASK-DAY-01 changes.

Original Windows hybrid destination remains exactly: approved GitHub source -> separately authorized CLEAN SOURCE checkout on ACTUAL laptop (NOT a second installation) -> verified HEAD and TREE -> ORIGINAL update.ps1 -PreflightOnly -> ORIGINAL update.ps1 into SAME existing October Vres installation -> original Claude Code CLI and FastMCP integrated Windows UAT -> GitHub fixes. This is a future destination, NOT an operational order now.

## 2. Authenticated identity and verified repository state

Repository https://github.com/vosser24/Vres-OS, account vosser24, account ID 62554356, repository ID 1368577038, GitHub App installation ID 85535881 (NOT the Windows installation).

- Product main protected by PROJECT policy: HEAD `9a8acc5d464b96432a93cb95daa9581412fb07ee`, TREE `659d3fdd6e635dbaecbd5c492ba7279754edaec7`, two parents `6af7bddf246e0f628c3e52add9528742e85189ca` and `8ae041721bf0418f6472ab541b6838fd73fec46a`; branch HEAD unchanged at R13N check.
- Original R13 protected by PROJECT policy: `feature/personal-w4-r13-universal-staging-hold-20261106` HEAD `bcf62460d68caebfdbd0e838d44c5997992c5fbc`, TREE `9bbc5615fef4a8f785e9ddb0056e9430ffe25d63`, parent `0badcd34d1eafbce5f815512a489d70cb240eecd`, unchanged.
- R13C baseline `3bd8d8a8fa2bccc87286432657302db34ed13e2b`.
- R13M parent branch `feature/personal-w4-original-host-recovery-acl-hold-r13m-20261120` HEAD `13fdc941aa1ac65d45d78641c7ebee9721cd1baf`, TREE `b21807ddd8c1a5a50d3858d38efbdb6291460159`, parent R13L `5b3cf638a1ef3a138d2cc7007373578460ae7eff`.
- NEW R13N unprotected source branch `feature/personal-w4-original-install-recovery-consistency-r13n-20261120`: HEAD **`9c02ee1f57f445ee05461170ced0ced94c9c658c`**, TREE **`4b4f769cb3c5a6fe2f994e39c0dd346c721a22ec`**, sole parent **`13fdc941aa1ac65d45d78641c7ebee9721cd1baf`**. Commit https://github.com/vosser24/Vres-OS/commit/9c02ee1f57f445ee05461170ced0ced94c9c658c . The remote branch, Git tree, one parent, immutable compare and ALL FIVE changed blob SHA IDs were READ BACK and matched.
- Exact R13M -> R13N compare: https://github.com/vosser24/Vres-OS/compare/13fdc941aa1ac65d45d78641c7ebee9721cd1baf...9c02ee1f57f445ee05461170ced0ced94c9c658c : **one commit ahead / zero behind, 5 paths**.
- Verified R13N file blobs: `install.ps1` 4d8b4889369336ad57bbadabb234490c99a9722b; `src/vres_os/install_recovery.py` f32441770121ec4be50bc92812a01e2486d7d9fc; `docs/INSTALL-WINDOWS.md` fb6eff83cb921f661046ce0f87417d4b2788918f; `tests/test_original_install_recovery_consistency_r13n.py` c09fb261c172d0bfda61027f5de6f3593f7727c9; `docs/reviews/VRES-2026-11-20-R13N-ORIGINAL-RECOVERY-CONSISTENCY-SOURCE-REVIEW.md` c3e7f5e2b9ae2d83a0b06c650e08b969599c9041.
- Review: https://github.com/vosser24/Vres-OS/blob/9c02ee1f57f445ee05461170ced0ced94c9c658c/docs/reviews/VRES-2026-11-20-R13N-ORIGINAL-RECOVERY-CONSISTENCY-SOURCE-REVIEW.md .

Canonical docs `docs/chatgpt-continuity-20261023` before this handoff: HEAD `c6eec94bc18c47df5eb4d4269ae909e903bc5c15`, TREE `e057406bcd43a71af4c85c8a74256e47e2be284e`, sole parent `80316080f010179d21216ae4c85722de9627c37a`. **After** publishing this handoff and index, obtain and record actual newest docs HEAD/TREE/PARENT by remote readback: do not put a guessed new SHA here. READ FIRST `docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md`.

## 3. R13N coherent source-only correction and explicit limits

Original R13M had TWO divergent recovery routes: `install.ps1` exception `catch` directly restored active pointer, plugin, launchers and protected Claude files, bypassing the original `install_recovery.py inspect` schema hold. Original release pin SQL 001-041 remains incompatible with original strict-stage 042-047; prospective 048 NOT_APPLIED.

R13N fixes SOURCE ONLY:

1. `install.ps1` caught-failure path now preserves existing installed/profile files, pending-install journal, snapshots and staged evidence instead of separately attempting any automatic pointer/plugin/launcher/Claude-file rollback. It emits `VRES_W4_HELD_INSTALL_FAILURE_RECOVERY` and rethrows; no false recovery success. The success path stops swallowing pending-journal deletion failure. **A partly published installation can remain unusable**; this is consistency and safety, not a recovery PASS.
2. `src/vres_os/install_recovery.py` now classifies local managed-file differences as `NO_MANAGED_FILE_RESTORE`, `CLAUDE_PROFILE_RESTORE_HELD`, `RUNTIME_RESTORE_HELD`, or `UNKNOWN_ACTION_HELD`. Changed runtime/plugin/launchers and profile are categorically refused pending independent review. No source-author flag or same-user writable migration marker proves live schema or host. Existing all-operations source interlock remains HELD.
3. `docs/INSTALL-WINDOWS.md` adds a held explanation and a specific future post-clearance owner recovery decision path. It does NOT instruct current hook disable, profile changes, DB probes, Windows commands, restart or updater. It records install-time v2.1.295 check cannot guarantee runtime identity after independent Claude updates/downgrades or PATH substitution and same-user/admin local exclusions.
4. `tests/test_original_install_recovery_consistency_r13n.py`: source assertions plus pure action-classifier test authored, **NOT_RUN**. No Python AST/compile/pytest, PowerShell or native execution.
5. `docs/reviews/VRES-2026-11-20-R13N-ORIGINAL-RECOVERY-CONSISTENCY-SOURCE-REVIEW.md` contains source correction/residual findings.

**Not resolved:** M-1 actual interrupted mid-update automatic recovery, M-3 release pin, M-4 self-service host recovery, dynamic host hook version/provenance, the actual SQL ledger, Windows/NTFS/toolchain/wheel/publisher proof, all integration and security tests. The original caught-error recovery source has been made consistent by REMOVING an unsafe bypass, not by producing successful real rollback. No executable permission was introduced.

## 4. Independent review #185 and CI hazard

https://github.com/vosser24/Vres-OS/issues/185 : verified **OPEN**. Authenticated owner updated ISSUE BODY ONCE, NOT a comment, to `W4 #185 — independent READ-ONLY R13D–R13N review (3 verdicts; operations blocked)`, inserting a current R13N intake above the complete prior R13M and D4 history. Readback verified exact body/title, **14 comments ALL authored by vosser24**, and no independently attributable reviewer. An unsigned Claude Fable 5.2 advisory on R13M dated 2026-11-20 ~13:50 Athens gave THREAT_MODEL=REVISE, RELEASE_DESIGN=DESIGN_REVISE, OPERATIONS=BLOCKED for DB/host/Windows/release, but expressly has no verifiable own GitHub identity; **ADVISORY ONLY**, not trusted F1/Fable or #185 independence.

A genuine reviewer must independently inspect the latest exact R13N plus R13M and R13D–L ancestry, cite SHA/file/line, P0–P3 severity, actual PASS/FAIL/NOT_RUN, residual risks, and issue their OWN attributable three decisions THREAT_MODEL, RELEASE_DESIGN, scoped OPERATIONS using their own verifiable account. Do not impersonate or owner-relay AI verdicts, do not add repetitive owner comments.

**DO NOT CREATE A PR, even draft**: existing `.github/workflows/ci.yml` triggers on pull_request, provisions PostgreSQL 16 and runs pytest/release. Immutable commit/compare links only. No CI was triggered by R13N Git-ref source publication.

## 5. Absolute incident holds, reviewed risks, test provenance

`LIVE_SCHEMA_048_INCIDENT=OPEN`: NO PostgreSQL EVEN SELECT direct or indirect, no migrations or SQL execution; real live schema ledger UNKNOWN, prospective SQL 042–048 NOT_APPLIED and release PINNED 001–041.

`HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`: NO ordinary native Claude Code, installed FastMCP, hooks or untrusted host execution. Independently trusted F1/Fable positive authority NOT_GRANTED.

No Python AST/compile/pytest, SQL parser/SQL/PG, Windows Git/preflight/update/install/recovery/rollback, original selftest, user profile/credential mutation, main/R13 merge, release or integrated UAT. No destructive recovery or untrusted local Windows code. Source-only R13N engineering authorized; isolated offline test operations require separate owner consent and independently reviewed isolation. Trusted incident clearance and target-specific owner permission required before any host or Windows step.

Open core risks retained:
- F1/M-3 P1 original strict-stage 042–047 vs release pin 041.
- F2 P1 Schema-048 collision / live ledger unknown, no DB probes.
- F3 P2 effective SQL runtime/writer grants, inheritance/transaction rollbacks unverified.
- F4 P2 original selftest held.
- F5/M-5 P2 host hook runtime fail-closed/availability/version/precedence/timeout, genuine human provenance unverified.
- F6 P2 operator-only cancellation unavailable, model-facing cancellation deliberately blocked.
- F7 P2 credential notification/history exposure and genuine human provenance uncertainty.
- F8/M-7 P2 runtime-writable turn fence and broad table writes, caller asserted session, passed-validation parking and task lifecycle.
- F9/M-6 P2/P3 wheel publisher/Tk/Python/DLL/NTFS/profile config and recovery trust, launch source closure, full Windows UAT unverified.
- M-1 P1 interrupted update still cannot safely auto-restore changed runtime.
- M-2 P2 original catch-path bypass removed in source but no execution provenance.
- M-4 P2 owner recovery/host bypass not safely executable while incidents open.
- M-8 P3 all recent tests NOT_RUN.

**TEST PROVENANCE:** R13D–R13N Python AST NOT_RUN, compilation NOT_RUN, pytest NOT_RUN, SQL/PG NOT_RUN, Windows PowerShell NOT_RUN, original updater/preflight NOT_RUN, native Claude/FastMCP/hooks NOT_RUN, integrated UAT NOT_RUN. GitHub commit, tree, parent, readback all 5 blobs/compare VERIFIED. Historical 732/732 pytest and 407/407 compilation belong ONLY to `9e2b538b06f34926f611db7e20120be572577101`; preserve rejected earlier 727/730 and R8/R9/R12/R13A/B/C attempts and failures as historical, not overwritten by untested R13N. No Windows execution, no Python project code execution, no SQL execution occurred during this R13N milestone.

## 6. Existing original October installation — owner-reported evidence only

Existing SAME one Windows user release `20261022172833-4d82147b`, source `82c82430b38f93bd6b9d5c3af3b5de9c1368af9c`, TREE `205c081277ece483c634e1c801c39595abd4549c`. Owner previously reported 194/194 staged source hash matches, zero missing/changed/unsafe, existing original Vres MCP/hooks/launchers/backups/recovery. These are historical READ-ONLY owner observations, NOT live runtime/DB/UAT certification. Do not redo inventory, infer local changes from GitHub, overwrite installed P2, or access actual Windows user files without explicit permission.

Other issues independently rechecked: #165–170 ALL OPEN, #176 OPEN, #174 CLOSED for planning only, #185 OPEN.

## 7. Exact next actions and pending state

1. In a NEW ChatGPT chat, authenticated GitHub read newest continuity index/handoff, actual docs HEAD/TREE/PARENT, exact R13N HEAD/TREE/PARENT + 5 blobs, main/R13 ref status, #185 current reviewer attribution, and PR PostgreSQL CI hazard. Do not assume this checkpoint remains latest.
2. Obtain independent accountable THREAT_MODEL, RELEASE_DESIGN, scoped OPERATIONS three-verdict review on R13N with own-account publication, including M-1/M-2 and remaining incident/release compatibility. If no genuinely attributable reviewer exists, label EXTERNAL BLOCKER; do not fabricate approval, send anonymous Claude review as owner, or churn more low-value source work.
3. Resolve both incidents through independent trusted evidence and explicit owner authorization WITHOUT prohibited DB/host probes. Independently reconcile SQL 042–048, original release pin, real schema ledger, accepted compatible rollback, wheel/publisher/NTFS/toolchain and actual host contract.
4. Only after distinct written owner approval and independently validated isolation, optionally allow specific offline non-DB tests; current exact R13D–N AST/compilation/pytest remain NOT_RUN.
5. Only after proper attributable reviews, incident/compatibility clearances and separate Windows operation consent, move to ACTUAL laptop clean SOURCE checkout -> source SHA/tree independently verified -> ORIGINAL update.ps1 preflight -> ORIGINAL update.ps1 into SAME October installation -> ORIGINAL Claude Code CLI + FastMCP UAT -> GitHub fixes. Preserve original V-01..V-42.
6. Do not start a new feature phase after continuity checkpoint; at ≤20 replies or conservative >50% estimated context, publish next handoff/index, confirm docs remote sha/tree/parent, include a FULL single-inline-code-block fresh-chat resume prompt with links, recommend new chat, and stop. This checkpoint is early after a major source milestone due to large reviews/tools and uncertain context percentage; it makes NO asynchronous claim.

NO pending commands or tests were started. All changed GitHub source and docs described above are published/read back, and the issue body verified; installed Windows P2 and protected main/R13 were NOT modified.
