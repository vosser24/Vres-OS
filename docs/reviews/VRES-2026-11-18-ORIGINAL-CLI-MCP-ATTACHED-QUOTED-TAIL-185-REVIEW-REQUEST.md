# 2026-11-18 — CURRENT original Claude CLI/FastMCP attached quoted credential-tail source: independent #185 reviewer request

**READ-ONLY REQUEST ONLY, NOT REVIEW VERDICT OR EXECUTION APPROVAL.** Independent reviewer must be distinct and attributable, read the COMPLETE https://github.com/vosser24/Vres-OS/issues/185 and all eight owner comments, D1–D4, original V-01..V-42 and M0..M8 roadmap, current full canonical handoff and this source. Read-only GitHub only; no native host, DB or Windows commands.

## LIVE authenticated source identity

Repo https://github.com/vosser24/Vres-OS ID 1368577038; account vosser24 ID 62554356, App installation 85535881. Current dedicated feature/personal-w4-cli-mcp-attached-quoted-credential-tail-20261118 HEAD 8c722b1db8ecca7950c7efd7333d634e65c19e09, TREE d07c3be591574b7d30858cae803ae8320249260a, SOLE PARENT 2a168713bb6de4610456677cc163731add4d5502. https://github.com/vosser24/Vres-OS/commit/8c722b1db8ecca7950c7efd7333d634e65c19e09 . Source nonforce expected-SHA publication and remote ref/raw commit/blob readback verified; direct parent 1 ahead/0 behind, exactly THREE changed files:

1. src/vres_os/redaction.py blob 09ea436429239031072eb73eb9a55c5a84291d1a (canonical regex; line 27–35 and sanitizer logic line 97 onward).
2. tests/test_redaction.py blob cafdf7cad8a5584611b0fdb4b483971145e3278d (two appended parameterized regression functions AUTHORED NOT_RUN).
3. docs/architecture/VRES-W4-ORIGINAL-CLAUDE-SELECTED-TASK-CONTINUITY-PREVIEW-2026-11-18.md blob e0740e08a05ab1fb50ae620b066212db495ca5f5.

Against product main 243 ahead/0 behind. Against protected R13 DIVERGED 134 ahead/13 behind, merge base 982e77f2f4974b4fbca5da91d3e11aeb56e40271. Main 9a8acc5d464b96432a93cb95daa9581412fb07ee and R13 bcf62460d68caebfdbd0e838d44c5997992c5fbc unchanged; no merge.

Current exact original mcp_server.py f75f3a4f32dfa2e89b3feb93145088d6edeb0319, repository.py b975ce796eac5a4334d8a1d998c9e7fddbee5490, install.ps1 4aea9d94794c17ec9c74d28a6b8db108fde73d7d and update.ps1 eb0fc000e15ef3df3823d38ceb31d3b7145127ac remain unchanged.

## Focused new static issue for reviewer

At parent source, balanced quote match had no lookahead field boundary, so password="synthetic-first"synthetic-attached could leave synthetic-attached visible in direct redact_text or nested redact. Existing FastMCP scalar residual check can reject certain surviving tails, but does not protect all direct callers. CURRENT source now requires a field delimiter immediately after a balanced quoted credential, else the existing unclosed/malformed fallback masks to end of field. Assess correctness for both quote styles, escaped quotes, whitespace/newline, JSON/INI/log delimiters, idempotent already-redacted values, tail false negatives, backtracking complexity and over-redaction. Four attacker-shaped cases and four separated-field controls were AUTHORED NOT_RUN; neither old failure nor new PASS was observed in Python/pytest.

## Required THREE independent determinations and evidenced findings

1. THREAT_MODEL: ACCEPT / REVISE / REJECT. Separately selected pre-execution source/publisher SHA-256 root, Git SHA-1 integrity versus authority, GitHub compromise, active same-user/admin exclusions, local host/toolchain, Windows path swap and TOCTOU.
2. RELEASE_DESIGN: NARROW_DESIGN_ACCEPT / DESIGN_REVISE / STATIC_REJECT. Original source-only 248-file carrier and real original CLI/FastMCP owner, native Python/packaging/wheel closure, original R13 refusal, old independently callable stage()/POSIX route, migration 001–041 and 042+ exclusion, current release bootstrap trust, Windows NTFS ACL/junction/reparse/ADS/hardlink/object identity and interrupted recovery, proportionate one-operator solution.
3. OPERATIONS: explicit PERMITTED/BLOCKED/CONDITIONAL matrix for read-only source review, source Python/AST/pytest, original host/Claude/MCP/hooks, PostgreSQL including SELECT, Windows/Git/PowerShell/installer/stage/recovery, P2/profile/credentials, PRISM/legacy, V-01..V-42 UAT, F1/Fable and main/R13.

Provide severity, exact file and lines, minimal corrections, attributable reviewer provenance, observed PASS/FAIL/NOT_RUN and residual risk. The unsigned 2026-11-17 external Claude report said THREAT_MODEL REVISE, RELEASE_DESIGN DESIGN_REVISE, OPERATIONS conditional/blocked but did not read complete issue #185; NOT positive approval. This ChatGPT author-side correction is NOT independent review.

## Absolute holds unchanged

LIVE_SCHEMA_048_INCIDENT OPEN: NO PostgreSQL, even SELECT. HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED OPEN: NO ordinary native Claude Code/installed MCP/hooks. Independent F1/Fable positive authority NOT_GRANTED, P3 and Git L2/R13 staging/Windows installation/full UAT/installed P2/main merge HELD. Source Python/AST/pytest/PowerShell and all host/DB/Windows tests NOT_RUN. Historical 732/732 only older 9e2b538b. Do not access real credentials, profiles, protected P2/worktrees, TASK-DAY-01, PRISM/legacy, external packages, install or rollback. The eventual original Git fetch -> approved clean checkout -> original update.ps1 preflight/install requires separate incident, toolchain/publisher/wheel/NTFS evidence AND informed owner consent. Fresh missing prerequisites remain individual DEFAULT-NO offers, and -Update never silently acquires.
