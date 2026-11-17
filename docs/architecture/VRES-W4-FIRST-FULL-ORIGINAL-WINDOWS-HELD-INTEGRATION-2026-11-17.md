# W4 — first-FULL ORIGINAL Windows installer held integration (SOURCE ONLY)

2026-11-17 Europe/Athens. Parent engineering SHA `bf655d5e3afb6a4cc39162c30ec33b1878fd370a`.

One complete practical Windows Vres-OS for one personal operator, ONE original Chairman/task/session/result/history and CLI/MCP/Desktop; no permanent PersonalDayOnly mode, second installer/store or duplicate app. Preserve ALL V-01..V-42, M0..M8, W0..W3, W4 R1..R13, C2B/K0 and October 22/30/31 + November 5 roadmaps.

## Source changes, not operational clearance

- NEW `w4-operations-holds.json` ledger plus hardcoded `HELD_SOURCE_ONLY` gate at the very beginning of original `update.ps1` (both modes) and original `install.ps1` (both modes), prior to Git, protected P2, Claude profile reads or imported W4 code. Ledger edits alone cannot grant authority; new exact independently reviewed source commit and explicit owner authorization required.
- ORIGINAL `release_artifact.stage()` direct calls now mechanically refuse before even inspecting output paths. This is not externally trusted verification or the held R13 universal refusal; alternate release writers are not cleared.
- ORIGINAL installer delays three protected Claude-profile reads until existing recovery snapshot, restores only surface groups actually attempted, uses same-directory atomic replacement, and refuses deleting an originally absent file; retain journal for manual recovery if uncertain. Windows NTFS/rollback tests NOT_RUN, further protections still required.
- ORIGINAL managed bin adds `vres-day.cmd` pointing to the new `scripts/windows/vres-day-launch.ps1` and same active versioned runtime; `personal_w4_windows_entry.py` retains source-only refusal, only conditionally imports original `personal_day_desktop.main()` behind HELD interlock. No new app or owner.
- `update.ps1` now requests both separate `-SourceCommit` and `-SourceTree` identity; this is an unexecuted checkout-matching tripwire, NOT independent source trust. K3 Git environment scrubbing, trusted executable and byte/index proof are still outstanding. `install.ps1` reorders release check before explicit release_inputs call and uses `-I -B`; `release_artifact.py` still imports release_inputs before its own check, so pre-import trust remains NOT_PROVEN.

## Holds and unfinished work

Uploaded external advisory Claude report: ISSUE_185_READ COMPLETE for copied thread; THREAT_MODEL REVISE, RELEASE_DESIGN DESIGN_REVISE, operations BLOCKED. Independent attributable signed review NOT_OBTAINED, full roadmaps/D1-D3/R13 source review incomplete. P0/P1 Schema-048 incident (NO PostgreSQL even SELECT), HOST_HOOK_DB_ROUTE incident (NO native Claude/hooks), original P3, F1/Fable, WPR/R13 staging, Windows Git L2 and protected installed P2 all OPEN.

Still required before any execution: independent exact SHA-256 pre-execution verification outside Vres code, official interpreter/Tk and hash-locked whole-product native wheel closure, Git version/config/NTFS hardening, credible original full app runtime holds and stage/recovery review, kernel-enforced isolation with separately approved testing, complete V-01..V-42 acceptance plan and fresh exact owner consent. Current GitHub source/test changes have NOT_RUN Python, pytest, PowerShell, GUI, Windows, database, native Claude, staged release or installer; historical 732/732 pass on earlier `9e2b538b` is not transferable.

**DO NOT EXECUTE** git fetch / checkout / PowerShell preflight / installer, Python source/tests, Windows Sandbox, release stage, PG/Claude/hooks, credentials/profile/P2, PRISM/legacy, TASK-DAY-01, migration, rollback, main/R13 merge. Source-only engineering is not a release.
