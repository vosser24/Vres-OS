# W4 — Original Windows bootstrap Python executable pin (SOURCE ONLY)

2026-11-17, Europe/Athens. **AUTHORED; Python, pytest, PowerShell, Git, Windows, installer, Tcl/Tk and all UAT NOT_RUN. NO operational authority.**

## Practical original-owner outcome

The existing ORIGINAL `update.ps1` receives independently selected absolute
`-PythonExecutable` and `-PythonSha256` inputs alongside the existing exact
source commit/tree and pinned Git executable/digest. The future preflight
checks the Python .exe file, rejects final-path reparse and digest mismatch,
and forwards the **same two Python pins** to ORIGINAL `install.ps1 -Update`.

A directly invoked original installer delegates to the original updater
preflight, then rechecks the approved Python executable's digest immediately
before a bounded `-I -S -B` Python version/path/bitness self-report.
Only the explicit path may run the existing ORIGINAL release input verification,
release artifact staging, offline root-wheel parity, pip and recovery pipeline.
The old `py`/PATH `Find-Python` probe and automatic winget Python bootstrap
have been removed from the original installer. No alternate installer, Chairman,
task store, runtime or application is created.

Author-side static regression tests were adjusted for previously changed
offline pip isolation, and new Python pin contracts authored **NOT_RUN**.

## Trust limits and held gates

SHA-256 of `python.exe` is NOT an independent publisher signature or proof of
the loaded python3*.dll, VC runtimes, Tcl/Tk binaries, other native libraries,
stdlib integrity, NTFS ancestor aliases/reparse/ACLs, process isolation, or
absence of executable swaps between check and spawn. A self-reported version
and x64 identity are not independently authenticated. Complete approved
offline root wheel/transitive wheelhouse and #185 independent positive
THREAT_MODEL/RELEASE_DESIGN/OPERATIONS evidence remain missing.

Original source interlocks remain HELD. LIVE_SCHEMA_048_INCIDENT OPEN =>
NO PostgreSQL even SELECT; HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED OPEN =>
NO ordinary native Claude/hooks. No Windows Git/PowerShell/preflight, Python,
pytest, pip, Tk/Desktop, CLI/MCP/Chairman, release, install, recovery, local
P2 overwrite, real credentials or PRISM, F1/Fable positive issuance, protected
main or R13 merge is authorized. All actual tests and operations NOT_RUN.

Next integrated milestone: independently validate the entire Git DLL/helper/
config and Python/Tk/native dependency/source trust closure; obtain accepted
independent issue #185 evidence, clear incidents separately and obtain
specific owner approvals BEFORE any isolated/native runtime or installation.
