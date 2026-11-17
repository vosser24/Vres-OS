# W4 original Windows administrative, DB-test, MCP dispatch and runtime-resolver direct-route interlocks

**Date:** 2026-11-17 (Europe/Athens). **State:** SOURCE AUTHORED; ALL EXECUTION/TESTS NOT_RUN; NO RELEASE AUTHORITY.

## One original Vres-OS; one integrated next source boundary

This milestone changes **four existing original owners**: root `uninstall.ps1`, `scripts/run_live_db_tests.py`, `scripts/windows/resolve-runtime.ps1`, and `src/vres_os/mcp_server.py`. It adds an authored static regression contract only. No second application, installer, Desktop, CLI, MCP server, task store, credential owner or PostgreSQL data owner is created. Original V-01..V-42 and M0..M8/W0..W4 remain intact.

1. Original uninstaller: a hard source literal and explicit refusal are inserted after PowerShell declarations and before looking at LOCALAPPDATA, the active-install pointer, native process/CIM state, Claude profile or any removal action. `-RemoveLocalData` cannot bypass the hold. No local uninstall was run.
2. Original live DB integration-test helper: an independent Python source literal and first-call refusal in `main` prevent even the credential prompt or a pytest subprocess, not merely a DB connection. No PostgreSQL even SELECT.
3. Original shared PowerShell `Resolve-VresPython` helper: refuses on its own direct invocation before reading `LOCALAPPDATA` or the installed active pointer. All original launchers retain their earlier source holds.
4. Original single `VresMCP.call_tool` dispatch: refuses through existing `require_w4_native_host_clearance` before the unconfigured-state probe (which can inspect config), and before any registered tool body. Original registrations and semantics after future clearance are retained.

These changes are negative source tripwires, **not** an independent publisher identity, OS-enforced sandbox, signed interpreter, DLL/GCM/NTFS trust root, true Windows-installation proof or an assurance that arbitrary local edits cannot remove a source hold. The MCP dispatcher fix does **not** guarantee safety for direct Python calls to decorated functions, imports, extension hooks or outside dispatch. No code was imported or executed here.

## Remaining first-FULL closure and direct-route inventory

| Area | Current evidence | Remaining gap / next dependency |
| --- | --- | --- |
| Original installer/update/release helpers | Source-owned holds at original launch/stage/main paths | Trusted exact SHA/TREE, publisher, Git executable/DLL/GCM/config, filesystem object identity, hardlink/reparse/ADS/ACL/TOCTOU and interrupted recovery NOT_DONE |
| Tk Desktop, launchers and shared runtime resolver | Original Tk main/constructor and launchers source-held; resolver now source-held | Independently trusted Python x64/Tcl-Tk, transitive native wheels and bootstrap closure; actual GUI NOT_RUN |
| Original uninstaller and local profile | Source refusal before installed pointer/process observation and deletion | Independent review of original uninstall recovery/transactionality; real PC P2 state UNKNOWN |
| Live DB tests and DB drivers | DB driver/source guards and direct opt-in runner source-held | Schema-048 incident OPEN; independently authorized safe isolated DB proof NOT_RUN; NO PostgreSQL even SELECT |
| MCP, CLI and native Claude | Main entrypoints and MCP call_tool dispatch held | Direct Python decorated tool functions, import-time side effects, CLI internal direct functions, host native hooks and MCP external routes still require exhaustive audit; native Claude incident OPEN |
| PowerShell/process/file helpers | Original launchers, installer and previous process helpers source-held | Other directly callable helper functions/scripts, delegated binaries and OS sandbox boundary NOT fully audited |
| R13 staging and release | Preserved separate protected R13 | DIVERGED; not merged or accepted as authorization |
| #185 independent security review | Full issue and 8 owner-authored comments read | Three attributable THREAT_MODEL / RELEASE_DESIGN / OPERATIONS verdicts NOT_GRANTED |

## Evidence / test ledger

New source: GitHub commit/tree/file blobs and parent only after published and independently reread. Static regression test **AUTHORED NOT_RUN**. Python source import, AST/compile, pytest/integration, PowerShell, Windows local Git, original installer/update/uninstall/recovery, Tk GUI, CLI/MCP, native Claude/hooks, PostgreSQL even SELECT, V-01..V-42 Windows UAT **NOT_RUN / HELD**. Never transfer historical 732/732 or 407/407 from source 9e2b538b. Earlier 727/730 with 3 fixture failures, 9 held child tests NOT_RUN, 3 psycopg modules NOT_COLLECTED, rejected incomplete-stub 11 FAIL, later separate synthetic 11/11 PASS and rejected original SessionEnd assertion remain historical only.

Both incidents **OPEN**: LIVE_SCHEMA_048_INCIDENT (NO PostgreSQL even SELECT) and HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED (NO ordinary native Claude/hooks); P3 OPEN; F1/Fable trusted positive NOT_GRANTED; #185 OPEN. No Windows actions, developer source Python or tests, repository protected main/R13 merge, installed P2 overwrite, original TASK-DAY-01 edits, credentials/profile/global KEEP/DROP, real PRISM/legacy or outside OS/network process actions. Owner's future clean Git fetch + ORIGINAL update.ps1 preflight/normal update remains contingent on independent exact-tree trust and separate scoped owner authorization.

## Next substantive milestone

Trusted external pre-execution source/Git/Python/Tk/native-wheel/NTFS/original installer closure plus genuine distinct #185 three-verdict review. Then separate owner clearance of incidents and isolated exact-tree tests. Prioritize a functional first-FULL Windows release and the original integrated real daily acceptance, not further independent prototype apps.
