# 2026-11-18 — Original CLI/FastMCP redaction source correction, advisory review R-1/R-2

**SOURCE-ONLY engineering candidate. NO execution, security acceptance or release authority.**

## Input and provenance

Owner-supplied unsigned cloud Claude/Fable 5.2 review, timestamp approximately 2026-11-18 15:30 Europe/Athens, reports THREAT_MODEL REVISE, RELEASE_DESIGN DESIGN_REVISE, OPERATIONS all host execution BLOCKED. Reviewer says same AI reviewer as previous three reports, not independently attributable formal acceptance, and explicitly did not read every D1–D3 or original V-01..V-42/M0..M8/Nov 5 file. Static source reading only; NO Python/pytest/Windows/host/DB observed PASS. This correction is author-side implementation, NOT independent signoff under GitHub issue #185.

## Narrow correction on ORIGINAL owners

1. Original canonical src/vres_os/redaction.py: a balanced quoted credential with attached non-delimiter text now masks only that immediate contiguous token through the next whitespace, comma, semicolon, closing brace/bracket, rather than swallowing the entire persisted task summary. Truly unclosed credentials still swallow to end-of-field. The new bounded branch masks adjacent syntactic characters such as close-parenthesis, period, XML close angle, and backtick rather than discarding all later task text. Malformed fields may be over-redacted; whitespace-separated credential words and unquoted comma-separated values remain ambiguous.
2. Original src/vres_os/mcp_server.py: both existing read-only workday_overview and task_continuity_preview now suppress a WHOLE untrusted hint whenever canonical sanitize_text reports any eager credential redaction OR unresolved residual. This is performed before clipping and applies to raw JSONB before nested redact() can erase taint provenance. The sentinel remains [REDACTED_UNSAFE_HINT]. Ordinary untainted fields and safe structured scalar hints remain available. The change does not introduce another Chairman, Repository, MCP server or task/result store.
3. Existing tests/test_redaction.py, tests/test_workday_overview_mcp.py and tests/test_task_continuity_preview_mcp.py expectations updated and new synthetic regressions added. ALL AUTHORED NOT_RUN; no Python/AST/compile/pytest execution.

## Review findings that remain OPEN

- R-2 is only mitigated for those TWO original MCP views. Ambiguous direct redact_text/redact calls at Repository persistence still exist: password=abc,def may leave a suffix, and password: correct horse battery may leave additional words. R-3 inventory and canonical storage/outbound strategy require further independently reviewed source work; no universal redaction proof. No database access.
- F-1 through F-9 of the owner-supplied unsigned review remain proposals/findings needing severity validation and later source-specific correction. P1 open: lift-commit review/test gap; absent complete approved offline wheel lock/wheelhouse provenance; missing independently owner-held pre-execution source/toolchain trust and OS isolation. P2 open: native Claude executable provenance, recovery when installer-created profile files exist, Python DLL/Tk closure, CLAUDE_CONFIG_DIR/reparse, held plugin hook failure behavior. P3 open: venv isolation details, reserved Windows names, pointer history nesting, Git minimum/version, Windows Git L2 and stage() alternative route clarification. Do not misclassify these as verified runtime bugs or release clearance.
- Original installer and updater remain mechanically HELD; no hold constant or w4-operations-holds.json change, no stage or recovery execution, no prerequisite removal. Preserve fresh separately informed default-NO installation offers, never silently acquire during -Update.
- Source identity alone (Git SHA-1, in-repo SHA-256) does NOT establish publisher trust. Issue #185 complete independent THREAT_MODEL/RELEASE_DESIGN/OPERATIONS acceptance still absent. Schema-048 PostgreSQL including SELECT and native Claude Code/installed FastMCP/hooks incidents OPEN. F1/Fable authority NOT_GRANTED; P3, Windows Git L2, R13 staging, product main, installed P2, real Windows UAT and original TASK-DAY-01 HELD.

## Original scope

ONE personal Windows companion to ORIGINAL Claude Code CLI (PRIMARY), integral original FastMCP, one Chairman and authoritative Repository tasks, sessions, recorded results/history, checkpoints, user-selected task_resume, projects/credentials/data sources, experience retrieval/governed learning and original install.ps1/update.ps1/recovery. No new GUI/Tk changes, alternate runtime, second task store, enterprise IAM or multitenancy. Preserve V-01..V-42, M0..M8, W0..W3, W4 R1..R13, C2B/K0 and Oct 22/30/31 + Nov 5 plans.
