# Vres-OS W4 — original direct Python/Claude/installer route interlocks (source only)

**Date:** 2026-11-17. **Status: AUTHORED / NOT_RUN.** Changes the ONE original PERSONAL Windows Vres-OS application, not installed P2 or an alternate launcher.

## Source coverage

- Original vres console entry is now guarded via vres_os.cli:main, and original Typer app remains with a root callback. Direct python -m vres_os.cli is gated.
- Three original MCP main() functions gate before mcp.run; existing original tool registrations remain.
- Eight original hooks.py entry functions and subagent_hook.main refuse before payload, repository or DB access.
- Original processes.run_bounded refuses before temporary files and subprocess.Popen; approved future worker logic is retained.
- Original stdlib standalone install_recovery.py retains direct-file execution independence. Snapshot, inspect, verify, recover, write and CLI routes refuse before local file effects.
- Original database_targets.py refuses at direct PostgreSQL parser import and registry hold/main under the existing Schema-048 interlock.

## Distinct negative holds

w4_runtime_holds.py has separate held original Python runtime and held native Claude markers; native requires both. Original standalone installer recovery has a separate held marker; PostgreSQL retains separate db.require_w4_schema_clearance. Neither source markers nor changing them constitute trusted out-of-band verification, independent security authority, release approval or OS isolation.

## Validation/remaining work

Static regression tests AUTHORED / NOT_RUN. No source Python, AST execution, compiler, pytest, PowerShell, Windows, database including SELECT, Tcl/Tk, native Claude Code, child process, installation/recovery, or full V-01..V-42 UAT executed. K2-K12 trust, external F1/Fable and #185 complete three-part attributable reviewer verdict remain OPEN. This addresses identified direct Python routes but **does not** prove every alternate process, CLI/MCP, recovery or PostgreSQL path is closed.

Protected main and R13, installed P2, real credentials/profile, PRISM/legacy remain untouched/unknown. NEXT: remaining read-only source route and dependency audit; independently trusted exact-tree, Git, Python/Tk/wheel and Windows NTFS closure; #185 genuine independent full-source three-verdict review; later separately authorized isolated tests; finally owner-approved clean Git fetch with ORIGINAL PS1 update.
