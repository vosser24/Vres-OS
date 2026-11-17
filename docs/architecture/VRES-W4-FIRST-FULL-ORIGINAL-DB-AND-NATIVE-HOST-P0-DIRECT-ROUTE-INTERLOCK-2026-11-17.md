# Original first-FULL: P0 direct database and native Claude host-route interlocks (SOURCE ONLY)

Date: 2026-11-17 Europe/Athens. Baseline exact original engineering parent `20a7b40e77f4875507ca4799956e1d4dbc8f6213`, tree `3b233b5fdba3cb01d5259f0642764fdf9022c85a`. This is one original Vres-OS application for one Windows user, not a new app, installer, data store, Chairman, or permanent PersonalDayOnly operation.

## Source engineering, not runtime acceptance

1. The nine existing `plugins/vres-os/bin/vres-*.ps1` native Claude/plugin entrypoints now refuse with `VRES_W4_HELD_HOST_HOOK` as the first executable statement (after mandatory PowerShell `param` where needed). No managed runtime pointer, profile path, logging, Python, MCP or child process is reached by these source scripts while held. The original scripts, entry paths and hook/MCP registrations remain in place for independent future validation; no installed host was modified.
2. The original `src/vres_os/db.py::_driver` now checks the existing incident interlock before importing psycopg. This covers the shared driver path even when a caller bypasses `connect()`.
3. In the original `pg_recovery.py`, backup and restore entrypoints, driver/conninfo helpers, trusted pg-client discovery, injected-runner seam, archive execution, inspect/verification contact all check the existing incident interlock **before** driver import, archive/profile read, client/process discovery, supplied runner, or database contact. Offline `load_backup()` remains offline-only and unchanged.
4. Original `bootstrap.py` secure setup, provenance upgrade, admin DSN, first-FULL project startup, driver setup and subprocess launch paths refuse before local project adoption, operator password prompts, credential reads, configuration writes, or worker launch. Original `database_boundary.py` role provisioning, rollback, schema activation and direct SQL helper paths check the same gate before importing psycopg or executing on supplied connection objects.
5. New source-only AST/PowerShell-text contract tests describe the entry ordering, but **AUTHORED / NOT_RUN**. Nothing here claims Python/PowerShell parsing, imports, tests, PostgreSQL, host execution, Windows launch or installed P2 acceptance.

## Unchanged hard holds and important limitations

`LIVE_SCHEMA_048_INCIDENT=OPEN`: NO PostgreSQL, including SELECT, direct or indirect. `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`: NO ordinary native Claude Code or installed hooks. Original P3, #185 independent three-part review, F1/Fable positive authority, Git L2, publisher SHA-256, official Python/Tk and transitive hash-locked wheel closure, original updater/installer/NTFS recovery, R13 universal staging and Windows UAT remain OPEN. This source gate is not a trusted out-of-band pre-execution verifier, OS-enforced isolation, Git/PowerShell signature proof, nor exhaustive audit of dynamic module imports, arbitrary subprocesses, third-party drivers or alternate direct routes. Existing installed Windows files, services, credentials and unpushed changes remain UNKNOWN.

No command, local source Python, test, PowerShell, Windows Git, native Claude/hook, PostgreSQL, installer, migration, release staging, rollback, installed P2 or main/R13 mutation was run for this milestone. Do not transfer historical guarded 732/732 PASS to this tree. Before testing, independently verify exact tree/runtime isolation and receive fresh explicit owner consent; before installation, resolve incidents, complete #185 approvals and source/runtime/wheel/NTFS closure, then use the owner's selected separate clean Git fetch and **original** `update.ps1`/`install.ps1 -Update` with previous P2 and recovery preserved.

## Follow-up

Continue an exhaustive source-only inventory of remaining alternate DB/Claude/hook/subprocess reachability; independently verify all changed Git blobs, source HEAD/TREE/PARENT and direct ancestry; publish the authoritative handoff/index. Keep original V-01..V-42, M0..M8, W0..W3, W4 R1..R13, C2B/K0 and 22/30/31 October + 5 November integrated roadmaps.
