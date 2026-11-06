# Vres-OS — 2026-11-06 W4 R10 independent read-only review; W4 R11 bounded source published; Windows NOT_RUN

**HARD GITHUB CONTINUITY CHECKPOINT. END THIS CHAT AFTER REMOTE DOCS READBACK. NEW CHAT: INDEPENDENT R11 READ-ONLY REVIEW FIRST.**

## 1. Product identity, canonical references and scope

Vres-OS is a PRACTICAL PERSONAL daily-operations app for ONE Windows user. It is NOT enterprise IAM, multitenancy, an additional Chairman, duplicate task/memory database or collection of disconnected applications.

Repository: https://github.com/vosser24/Vres-OS
Canonical docs branch: docs/chatgpt-continuity-20261023
Docs parent HEAD verified before this handoff publication: ba93f042c0e81caa78c389741899356ff3c7c266
Docs parent TREE verified raw: 538428b67f2c99565ebec8143e552fe85afeeec7
Docs parent SOLE parent: 0a194270cb962f4f43943859b7faa0a472221399
Index at parent blob: 7b1140e66d9a842b6c9c45a7404fedd3e903fff7
R10 prior handoff blob: 43e9817cfa6df14e872bb8fc6f0b712eea84918c

Product main: 9a8acc5d464b96432a93cb95daa9581412fb07ee — independently rechecked unchanged. NO MERGE.
Accepted W3 R2: 982e77f2f4974b4fbca5da91d3e11aeb56e40271.
W4 R9: cdbf6824333bc257854dcc4cdcfbfc3cfaa7222d.
W4 R10: 2ee0c09050245ee03c630660ef08e38b4236b136.
W4 R10 TREE: 2d8603a78fc8419d8f6780bc817964ac2f4d30d0.
All these historical SHA claims are recorded for continuity; verify live refs again in the next chat.

Preserve ALL original V-01..V-42 requirements and integrated M0..M8 roadmap, issues #163/#164/#165–170/#174/#176, W0 exact original-owner integration audit, original P1 W1 W2 W3 narrow evidence, ALL W4 R1–R10 failures and published corrections, E7/F2/F1/P3/Stage1–6 decisions, original unmerged protected worktrees and proportional PERSONAL P0/P1/P2/P3 approval rules.
Roadmap: docs/roadmap/VRES-PERSONAL-COMPLETE-PENDING-DEVELOPMENT-RELEASE-AND-REAL-WINDOWS-UAT-PLAN-2026-11-05.md
W0 audit: docs/handoffs/VRES-2026-11-05-W0-EXACT-GITHUB-RELEASE-INTEGRATION-AUDIT.md

## 2. Independent R10 READ-ONLY review performed in the preceding assistant reply

R10 docs/main/feature refs verified live. Raw Git commit TREE and sole-parent headers for R10 and the prior docs commit were independently fetched: PASS, superseding earlier NOT_INDEPENDENTLY_VERIFIED header records. R10 source five blobs, unchanged release_inputs and pyproject plus docs two blobs were independently recomputed via Git blob SHA-1: 9/9 PASS. Eight accepted inherited owner module blob identities were verified. R9→R10 one commit ahead, zero behind, exact five source/test paths. W3 R2→R10 ten ahead, zero behind. Complete R10 original release owner, Git adapter, POSIX writer, W4 entrypoint, all 34 authored tests, unchanged inputs, pyproject and R9 handoff read.

R10 independent THREE VERDICTS:
1. Operational original-source archive staging: STATIC_REJECT.
2. Read-only interruption advisory: NARROW STATIC_ACCEPT solely for stable, explicitly selected, ordinary disposable file inventory; NO concurrent ownership or deletion proof.
3. Destructive rollback: STATIC_REJECT; unconditional refusal is mandatory.

Material R10 findings (static counterexamples, NOT executed exploits):
- P1 mkdir→open POSIX initial output root adoption race and same-UID substitution.
- P1 pathname ancestry/parent relocation and post-completion root movement; checks do not grant atomic identity or immutability.
- P1 per-directory os.walk enumerates potentially huge names lists BEFORE global node budget.
- P1 independently trusted external Python entrypoint publisher authentication and Windows NT handle-bound containment NOT_ESTABLISHED.
- P2 owner Git 4 MiB tree budget checked after object materialization.
- P2 34 authored tests only; main scenario uses simulated-owner and simulated output writer, not a real end-to-end owner gate.

R10 Python syntax, pytest, original-source ZIP, Windows gate NOT_RUN. R9 SQL 001–041 pinned SHA256 41/41 PASS for original R9 source bytes unchanged by R10; NOT an R10 gate.

## 3. R11 coherent integrated source-only correction PUBLISHED, no Windows operation

NEW feature branch: feature/personal-w4-r11-lazy-bounded-source-20261106
R11 HEAD: 4bdc5f3b2d9417270938a3da2956517ad676a068
R11 raw Git TREE: 0c54a99f7e2bc79ab3f9702a7f7edd2f5bd16bdb
R11 verified SOLE PARENT: 2ee0c09050245ee03c630660ef08e38b4236b136
Feature non-force expected-SHA update PASS; branch created at R10 first.
Remote HEAD readback PASS; R10→R11 ahead 1/behind 0, EXACTLY FIVE paths.
W3 R2→R11 ahead 11/behind 0; no product-main merge.

Exact R11 modified source/test Git blob SHA-1 identities, re-computed independently from GitHub blob contents before publication and independently remote-read after publication, 5/5 PASS:
- src/vres_os/release_artifact.py: 0381fe1c772e7f9a218010a2f3101b1fae154ca0
- src/vres_os/personal_w4_inert_git.py: c83e4fc4b7c73b761c4b21a7375a8a15f3e5075b
- src/vres_os/personal_w4_bound_output.py: 972c7c8276025c0cc2d68bd1be2d7173a29cb439
- src/vres_os/personal_w4_no_launch_release.py: 9ef1a1a9f4753f33b14086e567bb6f36440c7847
- tests/test_personal_w4_no_launch_release.py: 6fe2a3d8963318be6542b2df8d592848a6fb9783

R11 unchanged release_inputs.py blob f6008f391305840645a707407fa8f464b0e27389 and pyproject.toml blob b2d5e30d10d7be0613e90bf3ed1e346be5678969; all EIGHT inherited owner source blobs additionally reread at R11 PASS. Existing 001–041 migration digest evidence is pinned unchanged by R11, NOT rerun in R11.

Source-level changes, NOT an operational acceptance:
- Original release_artifact keeps legacy owner interface unchanged for ordinary callers. Bounded W4 reader now accepts read_bounded for pre-inflation capped 64 KiB Git commit and remaining 4 MiB tree read budgets. Fallback legacy callers are checked after bytes materialize, not pre-inflation.
- No-spawn loose Git adapter adds bounded reader method and limits inflated byte materialization, uses O_NOFOLLOW for regular input final components, and replaces os.walk release-scope inventory with lazy capped os.scandir. Source TOCTOU and path ancestry still unproven.
- W4 entrypoint replaces os.walk .git metadata inventory with lazy capped os.scandir, adds 64 KiB Git config read bound, no-follow final-file open, checked file identity/size, and root identity recheck; refreshes three sibling embedded Git blob hashes in BOTH their use sites.
- POSIX output writer requires private same-effective-UID parent with no group/other permissions (mode 0700 profile). Adds no-follow post-mkdir child/root stat identity check before open. These reduce the race window but cannot authenticate actual mkdir-created inode against a hostile same-UID process that swaps the name before stat.
- Existing original-owner memory manifest, 001–041 source-only validator, in-memory deterministic ZIP and receipt identity, hard Windows staging refusal, no W4 Git subprocess, preserved incomplete journals, and destructive rollback refusal remain.
- 34 previous authored tests retained, five pre-existing unsupported-Windows direct loose Git tests marked skip on Windows, six new R11 authored tests for bounded inflation, lazy scope, lazy metadata, config byte limit, private parent and owner bounded reader. TOTAL: 40 DISTINCT AUTHOR-WRITTEN TEST FUNCTIONS.

## 4. Honest PASS/FAIL/NOT_RUN provenance

PASS: R11 GitHub source branch publication with expected-SHA lease, remote HEAD/tree/sole parent readback, exact five-path diff, W3 ancestry through compare, five recomputed + five remote blob readbacks.
PASS: Ten unchanged inherited module/inputs/pyproject Git blob identities on the R11 commit.
NOT_RUN: R11 Python AST/syntax/compile, original owner pytest and full original-source offline integration.
NOT_RUN: R11 40 authored test functions — NO pytest PASS is claimed.
NOT_RUN: R11 complete original owner actual source ZIP / ZIP SHA256 / reproducibility.
NOT_RUN: signed independent PSF Python 3.13.17 with -I -B Windows filesystem gate and any Windows source/test/output creation.
NOT_RUN: R11 genuine external Python entrypoint publisher verification, Windows NT containment proof, hosted same-user hostile concurrency race, filesystem post-close immutability, runtime wheel closure/recovery, real UAT.
NOT_REVERIFIED: physical installed P2 identity.
NOT_GRANTED: R11 independent STATIC_ACCEPT or any F1/Fable positive authority.
R10 previous review was independent source reading but NOT an independently executed R11 test or second-agent sign-off.
No R11 tests were executed by the assistant; no mocked-owner tests are transferred as PASS.

Remaining material P1 blockers:
1. POSIX output mkdir/open initial adoption remains non-atomic against hostile same-UID rename, including nested components; private 0700 alone cannot prevent same-UID activity.
2. External independently trusted publisher identity for the INITIAL Python entrypoint NOT_ESTABLISHED.
3. Windows NT handle-based creation, junction/reparse, safe rename, and protected artifact containment NOT_IMPLEMENTED; Windows staging MUST remain HARD REFUSED.
4. Post-completion movement/substitution and same-UID source checkout TOCTOU remain unproven.
5. Windows offline real original-owner gate (source, 001–041, ZIP actual SHA256, reproducibility, negative interruption and nonmutation) NOT_RUN.
6. Cross-platform directory fsync and crash/power-failure durability not proven.
The corrections are bounded hardening, NOT a trusted release. Do not bypass the Windows refusal to make tests pass.

## 5. ABSOLUTE HOLDS, user and installation identity

LIVE_SCHEMA_048_INCIDENT=OPEN — NO PostgreSQL even SELECT, direct OR indirect.
HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN — NO ordinary native Claude Code, installed hooks or hook-routed commands.
Original P3 incident OPEN. Independently trusted F1/Fable positive authority NOT_GRANTED.
No real credentials/user profile, PRISM, real legacy project, protected worktrees or installed P2 writes.
No Vres runtime, installer, migration, Windows Sandbox R2 launch, product-main merge or installed P2 overwrite.
No Windows source/test/output creation and no Windows gate without NEW separately explicit operator approval.
No automated deletion of interrupted W4 stages.

Protected installed P2 source identity: 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c.
Actual installed Windows identity: NOT_REVERIFIED. Chairman previous report Sonnet/high; Opus/medium NOT_INSTALLED.
Completed real task: TASK-DAY-01.
Original note: C:/Projects/Vres-Personal-Notes/TASK-DAY-01.md
Desk: C:/Projects/Vres-Desk-Personal
DO NOT reopen, recreate, change or delete either task, note or desk.

## 6. NEXT single operation and release holds

Next fresh ChatGPT chat: independently distinct READ-ONLY senior Python, original Git source supply-chain, Windows NT/filesystem and release-recovery security reviewer on live exact R11. FIRST read current live canonical index and this newest dated handoff, reverify docs/R11/main HEAD, raw trees and sole parents, exact five source/test blobs, ten inherited original owner blobs, R10→R11 exact diff and W3 ancestry. Read ALL R11 five source/test files, complete 40 authored tests, unchanged release_inputs.py/pyproject, R10 independent review and historical R9/R8 incidents. Review original-owner no-spawn API, bounds, inflation and lazy directory enumeration, config sizes/path races, migration 001–041 memory parity, manifest/ZIP identity, POSIX root/child adoption, parent movement and fd semantics, hostile same-user concurrency, Windows NT hard refusal, initial Python entrypoint trust, advisory bounds, and mandatory disabled destructive rollback. Record precise file/line counterexamples. Return THREE INDEPENDENT verdicts: operational staging, stable selected read-only interruption inventory, destructive rollback. Do NOT automatically accept R11 merely because source publication and Git blob hashes PASS.

If required, propose ONE cohesive next source fix / R12 milestone with explicit unresolved NT handle boundary and independently authenticated external entrypoint; avoid endless isolated microtests. Only AFTER independent static clearance AND trustworthy Windows handle-bound containment may the user authorize ONE pinned, full ORIGINAL-owner SOURCE-ONLY OFFLINE NO-LAUNCH Windows gate. Gate requires separately verified signed PSF Python 3.13.17 -I -B, exact commit/ancestry and source blobs, source-only original 001–041 validation, true ZIP SHA256/reproducibility, negative interruption, no Git subprocess in W4 release path, and protected state nonmutation. Operator must separately AUTHORIZE Windows root creation/execution. Never use the legacy owner path-based stage() or bypass Windows refusal.

Later held: runtime wheel closure + recovery, independent P3 incident disposition, F1/Fable trusted authority, explicit installed P2 consent, #169 Visual Studio actual Windows UAT, #170 bounded single-user daily-use pilot, original V-01..V-42 complete daily-use roadmap.

## 7. Hard checkpoint instructions

At/before 20 assistant replies or conservatively approaching >50% context, stop new feature work, safely halt, record PENDING and NOT_RUN, publish authorized GitHub source/tests on dedicated correct branch using exact parent and non-force expected-SHA lease, and publish a new dated docs/handoffs/ handoff with newest READ FIRST index entry. Independently remote-read commit/tree/parent and blob identities. Supply GitHub handoff/commit links, exact docs SHA/tree and FULL ONE-BLOCK inline fresh-chat resume prompt; explicitly END the session and recommend NEW CHAT.

This handoff is authored BEFORE its own documentation commit exists; its own resulting docs HEAD/TREE/sole parent must be independently read from GitHub after non-force publication, never inferred here.
