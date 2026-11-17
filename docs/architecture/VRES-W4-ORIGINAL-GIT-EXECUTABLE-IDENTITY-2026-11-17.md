# W4 — Original Git executable identity propagation (source-only)

2026-11-17 (Europe/Athens). **AUTHOR SOURCE / TESTS NOT_RUN / NO RELEASE AUTHORITY.** This correction belongs to the ONE original personal Windows Vres-OS; no second installer, task store, Chairman, Desktop or permanent reduced mode is introduced.

## Observed original source inconsistency

The original `update.ps1` already required an independently specified absolute `-GitExecutable` and `-GitSha256` and used that executable for checkout verification. However the original `release_artifact.py` source-check runner and the `git cat-file --batch` object reader still directly invoked ambient `git` through PATH, risking execution of a different binary after preflight. That was a static source observation, not an executed exploit.

## Integrated source change

- Preserve original updater's exact Git executable+SHA-256 parameters and the original direct installer→updater `-PreflightOnly` check. `update.ps1` forwards both pins on normal updates.
- Original `install.ps1` now passes the **same** `--git-executable` and `--git-sha256` to original `release_artifact.py check` and `stage`; it no longer treats a different PATH `git` or automatic Git WinGet installation as a substitute for the approved pinned tool.
- Original release `check`/`stage` CLI requires both flags; `verified_source`, `_git_runner`, `_CatFile` and `_object_reader` propagate them to each direct Git subprocess. Both subprocess routes recheck absolute path, ordinary final executable file and SHA-256 before launch and use that **explicit** path instead of PATH.
- The existing Git environment sanitization additionally strips GCM and SSH_ASKPASS overrides. Original source object verification, release wheel/metadata checks, offline pip, one versioned install journal and recovery stay with their original owners.
- Existing release-artifact synthetic test helpers were updated to supply a *test-only* path/digest; a separate authored source/negative-pin regression covers both subprocess routes. No source Python or test execution was performed.

## Hard limitations and holds

**This does not prove** Git for Windows publisher authenticity, loaded DLL/GCM/SSH/helper identity, Windows NTFS ancestor reparse/ACL/protected worktree identity, OS/process isolation, signed release, external wheelhouse trust, Git object origin or race-free executable handle pinning. A digest check before starting a process is susceptible to filesystem races without separately trusted OS-level protection. External independent #185 THREAT_MODEL, RELEASE_DESIGN and OPERATIONS verdicts remain absent. `LIVE_SCHEMA_048_INCIDENT=OPEN`: **NO PostgreSQL even SELECT**. `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`: **NO ordinary native Claude/hooks**. Windows Git L2, Python/Tk/native DLLs, complete approved wheelhouse/lock, publisher/release, P3, original WPR/R13/main and installed P2 authorizations remain HELD.

All current-tree Python parse/compile/AST, pytest, PowerShell, native Git, pip, installer/update/recovery, Tk/CLI/MCP/Chairman, Claude/hooks, PostgreSQL and full Windows V-01..V-42 UAT: **NOT_RUN**. Historical 407/407 and 732/732 apply ONLY to older source `9e2b538b`, not this candidate. No local Windows state, credentials, installed P2 or protected worktrees were inspected or changed.

NEXT: independently close Git DLL/GCM/config + NTFS identity and approved wheelhouse/Python/Tk evidence, obtain actual external issue #185 review and separate informed authorization before any native Windows verification or installation; preserve all original V-01..V-42, M0..M8, W0..W3, W4 R1..R13, C2B/K0 and dated delivery roadmaps.
