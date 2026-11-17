# 2026-11-17 — Vres-OS CLI/MCP-first original installer correction — READ FIRST

**SOURCE-ONLY checkpoint; all exact-tree execution NOT_RUN. No Windows, PostgreSQL or native Claude Code action.** This handoff supersedes the obsolete no-auto-provision design from engineering commit `d620c679` and preserves the owner-approved original application intent.

## The owner's latest explicit design decision
- Vres-OS is **one personal Windows companion to Claude Code CLI, with MCP capabilities**. Claude Code CLI is the main interface; the original Chairman, task/session/result/history, project, credential, data-source, and learning/experience owner must stay integrated.
- **Do not build or prioritize a visual Tk Desktop UI**, second application, separate GUI runtime, alternate Chairman, multitenant enterprise IAM or parallel task store. Existing Tk source is untouched; do not silently delete original V-01..V-42 requirements. Prioritize actual Claude CLI/MCP daily usability.
- **Preserve the original installer's ability to detect and offer to install missing prerequisites with explicit operator consent.** The assistant's previous removal was an overcorrection. Fresh-install WinGet/npm prompts are restored in original `install.ps1`; maintenance `-Update` is still prohibited from quietly provisioning host packages.
- Owner-selected future installation route, **only after all individual clearances and consent**: separately clean Windows Git checkout, independently approved release HEAD/TREE, vetted Git.exe and Python.exe paths+SHA-256, complete externally approved offline hash-locked wheelhouse, original `update.ps1 -PreflightOnly`, original `update.ps1` normal update (original `install.ps1 -Update`) and original journal/recovery. This is NOT permission today.

## Fresh authenticated GitHub identity and canonical refs
- Repository `vosser24/Vres-OS`: https://github.com/vosser24/Vres-OS, ID `1368577038`; account `vosser24`, user ID `62554356`, App installation `85535881`; repo admin/push verified.
- **Current engineering branch**: `feature/personal-w4-claude-cli-mcp-original-prereq-consent-20261117`.
  - HEAD `31e585f633acbecbb9212933dc299a876c4311bb`
  - TREE `e46e81966a3306627ec59e3b4a13166021a93101`
  - SOLE PARENT `d620c67956b95957196e07c121b0bead19a6e844`
  - Commit https://github.com/vosser24/Vres-OS/commit/31e585f633acbecbb9212933dc299a876c4311bb
  - Non-force, expected-SHA branch publish succeeded and remote readback matched; **1 ahead / 0 behind its direct parent** with **SIX changed files**.
  - `install.ps1` **restored exact Git blob `ca4fe49aa296fc3863a056b4cb77b719b904aadb`**, identical to original from earlier approved source-only commit `52b17c85fa9e89f6a4f4c9d3a3e8346577b4e3b4`; includes WinGet/Claude/PostgreSQL 17 optional Node/npm Codex consent and original W4 early hold.
  - `tests/test_install_contract.py` blob `fed8a3ac06df716e14b92a0718830683084e01a4`; authored, NOT_RUN; restores original install-consent and update-limit static assertions, preserves prior rollback-source assertion repair.
  - `README.md` blob `e285605e17f06793ffdae84f5311ab351c1cfd96`: Claude CLI/MCP is primary, no new GUI.
  - `docs/INSTALL-WINDOWS.md` blob `f6ce076d23f14f67437f02bdb1609985270ccea1`: restores original fresh-install consent text, maintains current HELD warnings.
  - `docs/architecture/VRES-W4-ORIGINAL-HOST-PACKAGE-AUTOPROVISION-CLOSURE-2026-11-17.md` blob `4745e00b99c1cc5099f33930a0642f13bd3a6578`: original erroneous d620 source-only note retained and marked SUPERSEDED.
  - `docs/architecture/VRES-W4-CLAUDE-CLI-MCP-INSTALLER-CONSENT-OWNER-CORRECTION-2026-11-17.md` blob `f2bdcde2fe2a8de9ae514868bd33eef3715de098`: owner correction and limits.
- **Rejected, then corrected:** engineering commit `d620c67956b95957196e07c121b0bead19a6e844`, TREE `a1d891d9bd17037ff365571657dc7f3ef28b0a1f` authored original installer without WinGet/npm host auto-provision; owner rejected that design deviation; next exact commit restores it. Preserve provenance rather than erase the prior commit.
- Protected `main`: HEAD `9a8acc5d464b96432a93cb95daa9581412fb07ee`, TREE `659d3fdd6e635dbaecbd5c492ba7279754edaec7`, parents `6af7bddf246e0f628c3e52add9528742e85189ca` + `8ae041721bf0418f6472ab541b6838fd73fec46a`. Engineering now **233 ahead / 0 behind** main, no merge or write.
- Protected R13 `feature/personal-w4-r13-universal-staging-hold-20261106`: HEAD `bcf62460d68caebfdbd0e838d44c5997992c5fbc`, TREE `9bbc5615fef4a8f785e9ddb0056e9430ffe25d63`, parent `0badcd34d1eafbce5f815512a489d70cb240eecd`. Engineering **DIVERGED 124 ahead / 13 behind**, merge base `982e77f2f4974b4fbca5da91d3e11aeb56e40271`. No R13 merge or staging authority.
- Canonical docs branch before this publication: `docs/chatgpt-continuity-20261023`, HEAD `7aa7c04a6fb463c38ec6ba20822fac16d6726396`, TREE `6b10edbce417e4c25440c223c8db522121264128`, sole parent `6a9420fde5b34e2ad085f0a7ddb4970d211c70da`. This handoff is authored before its own docs commit; read back new docs HEAD/TREE separately, never infer them.

## Exact tests, pending operations, historical failed attempts
- New source HEAD/TREE/PARENT, direct comparison and all six remote changed Git blobs: **VERIFIED**.
- Author-side JavaScript text-boundary / literal anchor checks: performed for source editing, **NOT product tests**. First attempted restoration authoring rejected by a source text boundary exception **BEFORE ANY GitHub write**; corrected attempt published successfully. Source-only tests merely authored **NOT_RUN**.
- NEW EXACT TREE: Python syntax/AST/compile, pytest, PowerShell parsing, native Windows Git, Python/pip/wheels, CLI/MCP/Chairman, native Claude/hooks, PostgreSQL including SELECT, original install/update/recovery, GUI and full V-01..V-42 UAT: **ALL NOT_RUN/HELD**. No current-source PASS.
- Historical DIFFERENT tree `9e2b538b`: 407/407 compiled Python modules PASS, 732/732 eligible guarded cases PASS, **NOT current-tree certification**. Preserve earlier 727/730 with 3 fixture FAIL, 9 child tests NOT_RUN, 3 psycopg modules NOT_COLLECTED, rejected incomplete-stub 11 FAIL vs later distinct synthetic 11/11 PASS, rejected SessionEnd assertion, corrected `cc107213` provenance, prior `a0a44ccd` unpublished static-test correction, and prior authoring errors.
- Windows installed P2 historical source `82c82430b38f93bd6b9d5c3af3b5de9c1368af9c`. **Current installed bytes/services/settings, local unpushed work, protected Windows worktrees, Python/Git/Claude installations and secrets UNKNOWN**. No local Windows access or action occurred.

## Open issues, incidents, first-FULL gates
- At live issue readback: **#165, #166, #167, #168, #169, #170, #176, #185 OPEN; #174 CLOSED FOUNDATION ONLY.**
- #185 has **eight owner-authored comments**, not an independently attributable three-part acceptance (THREAT_MODEL / RELEASE_DESIGN / OPERATIONS). Owner-supplied unsigned advisory: THREAT_MODEL REVISE; RELEASE_DESIGN DESIGN_REVISE; OPERATIONS BLOCKED/CONDITIONAL. F1/Fable independent positive authority **NOT_GRANTED**.
- `LIVE_SCHEMA_048_INCIDENT=OPEN` => **NO PostgreSQL even SELECT**, direct/indirect.
- `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN` => **NO ordinary native Claude Code, host hooks**.
- P3 OPEN, Windows Git L2 NOT_AUTHORIZED, original installer/WPR/R13 HELD. No user-profile or credential changes, no native host process, source runtime, OS/network package install, preflight, migration, recovery, legacy/PRISM/TASK-DAY-01 changes, protected merge or installed P2 overwrite.
- K1–K12 first-FULL remains incomplete: source holds partial; publisher/source independence, Git DLL/GCM/helpers/config/NTFS, Python x64/stdlib/native DLLs/Tcl/Tk, complete approved SHA-256 offline root/transitive wheelhouse, alternate DB/hooks/process closure, original Windows install/recovery, R13 release authority, publisher/installer hygiene, operator packet, exact-tree integration suite and Windows CLI/MCP + all V-01..V-42 UAT **NOT_DONE/NOT_RUN**. No independent release certification.
- Preserved original roadmaps: V-01..V-42, M0..M8, W0..W3, W4 R1..R13, C2B/K0, October 22/30/31 and November 5, plus open issue adoption and experience intelligence scope. Avoid enterprise IAM, multitenancy, split Chairman, alternate installer or duplication.

## Exact NEXT operation (CLI/MCP-first)
1. New ChatGPT chat: fresh authenticated GitHub readback of docs index/handoff, current engineering `31e585f6` HEAD/TREE/PARENT/six blobs, main, R13, active issue states and #185 review comments. Do not trust pasted SHAs without revalidation.
2. Read complete original scope and source. **Do not build a graphical desktop feature phase** or repeatedly author disconnected safety microtests. Focus practical Claude Code CLI + MCP + original Chairman daily operations and installability.
3. Read-only source and native dependency/publisher/NTFS/complete offline wheelhouse review; retain original consent-based fresh install and protected-update semantics.
4. Obtain independent #185 three-part positive review and separately clear both incidents with evidence, then ask for precise target-specific owner authorization before isolated/native tests, Windows git fetch, original preflight, update/install, CLI/MCP/UAT or PostgreSQL contact.
5. At <=20 replies or early when context growth suggests half-window, create verified latest source/docs continuation checkpoint with safe Git expected-SHA writes and full inline fresh-chat resume prompt. Stop session.
