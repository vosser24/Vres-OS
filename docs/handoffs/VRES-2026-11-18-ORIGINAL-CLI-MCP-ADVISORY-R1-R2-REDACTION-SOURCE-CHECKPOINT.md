# 2026-11-18 — Canonical READ FIRST: original CLI/FastMCP advisory R1/R2 source correction

**STATUS: SOURCE PUBLISHED and GitHub SHA/tree/parent/exact six changed source blobs verified. New regression tests AUTHORED NOT_RUN. NO independent approval, live test, installation or operational hold clearance.**

## Binding owner scope

Build ONE practical production-quality PERSONAL Windows companion for ONE Windows user, with original Claude Code CLI PRIMARY and original FastMCP integral. Preserve original Chairman; Repository task/session/result/history, checkpoints, explicit selection and real Claude session-bound task_resume; projects, credentials, data sources and experience/governed learning; original install.ps1, update.ps1, journal and recovery. Do not create any additional GUI, prioritize or alter Tk Desktop, duplicate the task store/Chairman/MCP runtime/installer, or add enterprise IAM/multitenancy. Preserve V-01..V-42, M0..M8, W0..W3, W4 R1..R13, C2B/K0, and original October 22/30/31 and November 5 plans. P0/P1/P2/P3 approvals remain proportionate and consent-bound.

## LIVE GitHub verification (2026-11-18)

Repository https://github.com/vosser24/Vres-OS, ID 1368577038; authenticated vosser24 ID 62554356, App installation 85535881.

Current dedicated engineering feature/personal-w4-cli-mcp-redaction-review-r1-r2-20261118:
- HEAD c81b0cb30846ea05e90fcf2683151097b4e54f72
- TREE 610f7a83c2703b03d2fc6d3571c6cff4695c0c29
- SOLE PARENT 8c722b1db8ecca7950c7efd7333d634e65c19e09
- https://github.com/vosser24/Vres-OS/commit/c81b0cb30846ea05e90fcf2683151097b4e54f72
- Non-force expected-SHA lease publication verified by authenticated remote ref/readback; parent comparison exactly 1 ahead/0 behind and SIX changed files:
  1. src/vres_os/redaction.py 83305d5715573f8d8059457b86eb2be26c1187cf
  2. src/vres_os/mcp_server.py 9795ac26baa3bb9d9c8f48cfef1e830937173b17
  3. tests/test_redaction.py 3172559e75528a9cad9614454e9737097582bf5f
  4. tests/test_task_continuity_preview_mcp.py c620db3d89d7c078aaad7359192bf5b3f2beed67
  5. tests/test_workday_overview_mcp.py 773415d3773c00ec384479b27327fa5c93161f79
  6. docs/architecture/VRES-W4-ORIGINAL-CLI-MCP-REDACTION-REVIEW-R1-R2-2026-11-18.md d0c4b377807087d9413a42eb706b48e994149e49

Engineering relative to main: 244 ahead / 0 behind, base 9a8acc5d464b96432a93cb95daa9581412fb07ee. Relative to protected R13: DIVERGED 135 ahead / 13 behind, merge-base 982e77f2f4974b4fbca5da91d3e11aeb56e40271. DO NOT MERGE.

Protected main HEAD 9a8acc5d464b96432a93cb95daa9581412fb07ee, TREE 659d3fdd6e635dbaecbd5c492ba7279754edaec7, parents 6af7bddf246e0f628c3e52add9528742e85189ca and 8ae041721bf0418f6472ab541b6838fd73fec46a. Protected R13 feature/personal-w4-r13-universal-staging-hold-20261106 HEAD bcf62460d68caebfdbd0e838d44c5997992c5fbc, TREE 9bbc5615fef4a8f785e9ddb0056e9430ffe25d63, parent 0badcd34d1eafbce5f815512a489d70cb240eecd.

Original unchanged owners at parent (this 6-file diff does NOT change them): Repository src/vres_os/repository.py blob b975ce796eac5a4334d8a1d998c9e7fddbee5490; install.ps1 4aea9d94794c17ec9c74d28a6b8db108fde73d7d; update.ps1 eb0fc000e15ef3df3823d38ceb31d3b7145127ac; Tk Desktop src/vres_os/personal_day_desktop.py 241a7688321a2e65f3e14d99cc7f8c7335315f4d.

## Owner-uploaded advisory AI review, NOT independent acceptance

A user-supplied Claude (claimed Anthropic Fable 5.2) report dated approximately 15:30 Athens time 2026-11-18 says THREAT_MODEL REVISE, RELEASE_DESIGN DESIGN_REVISE and OPERATIONS host BLOCKED. The reviewer identifies as same Claude cloud reviewer behind earlier reports, unsigned, unassigned, not an independently attributable F1/Fable positive authority. The review says complete #185 and eight comments were read but NOT full D1–D3, original V-01..V-42, M0..M8, Nov 5, whole continuity index, R13 tests and most changed tests. Its 'static PASS' statements are code-reading judgements, NOT observed Python/PowerShell/runtime PASS. The reviewer itself reported all execution/test behavior NOT_RUN.

R-1 (P2) highlighted over-redaction after a balanced quoted credential followed by punctuation or attached bytes. R-2 (P2) highlighted potentially exposed suffix after partial redaction of unquoted values (password=abc,def; password: correct horse battery), including existing MCP views. R-3 (P2) highlighted direct redact/redact_text and Repository persistence wider than sanitize_text. F-1 through F-9 require independent source-specific validation and further corrections before release.

## Published narrow source remediation

Canonical redaction.py now uses a bounded attached-token alternative for balanced quoted values and keeps the existing conservative unclosed-quote fallback. Following independent task text is preserved after whitespace; immediate punctuation/attached bytes are masked. Original mcp_server.py now outputs [REDACTED_UNSAFE_HINT] if any canonical eager redaction rule fired OR any residual remains, checking complete persisted scalar before clipping. For JSONB lists it examines the raw structured value before nested redact() can hide taint; unsafe full hints are suppressed. This is a VIEW-ONLY defence, and intentionally hides some otherwise useful sanitized hints. Existing test fixtures changed appropriately, new synthetic tests authored NOT_RUN. No host/DB/user-profile/native Python execution, no R13/main merge, no new GUI/store/runtime/installer.

**R-2 and R-3 remain OPEN for direct Repository persistence and other consumers.** Existing repository.py uses redact() before persistence, which may not mask suffixes of ambiguous values. Do not claim this change gives universal credential safety. Next source remediation should inventory direct redaction callers and address persistence/output strategy with precise tests and reviewer input, not by invoking PostgreSQL.

Release findings still OPEN:
- P1 F-1: release lift would be a NEW source commit, requires its own review and tests; current holds intentionally protect every entry.
- P1 F-2: exact trusted offline transitive wheel lock/wheelhouse/root wheel origin missing.
- P1 F-3: externally owner-held pre-execution SHA-256/source publisher trust and disposable Windows isolation unproven.
- P2 F-4 to F-8: pin native Claude executable/version, recovery of installer-created profile files, Python DLL/Tk closure, CLAUDE_CONFIG_DIR profile/reparse safety, held plugin hooks exit/refusal.
- P3 F-9: venv -I, Windows reserved names, pointer chain, Git minimum, L2 metadata and original stage() alternate routes all pending review. Do not automatically trust advisory severity without independent confirmation.

## Issue state and prohibited actions

Live GitHub #165–170 and #176 OPEN; #174 CLOSED for foundation only; #185 OPEN with eight owner-authored comments, NO independent three-part signoff. https://github.com/vosser24/Vres-OS/issues/185 .

LIVE_SCHEMA_048_INCIDENT=OPEN: NO PostgreSQL even SELECT, directly or indirectly, no migrations. HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: NO ordinary native Claude Code, installed FastMCP host or hooks. Independently trusted F1/Fable authority NOT_GRANTED; P3, Windows Git L2, R13 staging, Windows installation/update and real original V-01..V-42 UAT HELD. Installed Windows P2 status UNKNOWN; do not touch or infer local unpushed files. No real credentials/profile, PRISM/legacy, original TASK-DAY-01, global KEEP/DROP, protected worktrees, source imports on the Windows PC, destructive rollback or main/R13 merge.

Original fresh install.ps1 requirement: detect and OFFER missing Claude Code, PostgreSQL 17, optional Node.js LTS and npm Codex with separate informed DEFAULT-NO permission for EACH. -WithCodex is NOT blanket approval; maintenance -Update must NEVER silently install external packages. Eventual, only with independent incident/source/toolchain/NTFS/wheel/recovery clearance AND separate informed owner consent: clean separate Windows Git checkout -> approved exact SHA/TREE -> original update.ps1 preflight -> original install/update/recovery -> integrated original Claude CLI/FastMCP/PostgreSQL/Windows V-01..V-42 UAT. DO NOT RUN NOW.

## Test/attempt provenance and next action

Current c81b0cb exact six changed Git blobs, commit tree/parent and branch readback VERIFIED. Current-source Python/AST/compile/pytest, PowerShell, native Claude/FastMCP/hooks, PostgreSQL even SELECT, Windows release/install/recovery, V-01..V-42 UAT: ALL NOT_RUN/HELD. Historical 732/732 eligible PASS and 407/407 compile only on 9e2b538b. Preserve earlier 727/730 three fixture FAIL, 9 deselected child cases, 3 uncollected psycopg modules, rejected incomplete-stub 11 FAIL and different corrected 11/11 PASS, rejected SessionEnd assertion, prerequisite-removal rejected SHA d620c67956b95957196e07c121b0bead19a6e844, unpublished rejected provenance c56847b8276581ee66a7aae5b512a94a341a5248, original first source-writing JS SyntaxError before any Git write. This session source publishing orchestration hit a Code Mode tool-call cap AFTER publish; first tool result was not confirmation. Subsequent independent readbacks verified live new branch c81b0cb, raw tree/parent, six paths/blobs and direct compare. Do not call orchestration cap a code/test failure.

Canonical docs pre-publication branch docs/chatgpt-continuity-20261023 HEAD 27320c30afcb928ee5d6cf93328d4e7153447e9a, TREE c77280ab8134b37e630832aaefc906068db1814a, sole PARENT c146526f395fdbf397847efa45e0c7a1c41147ed, prior index blob 2f2b5cd7178a8addf45b6b9a4dd9c387afcf1219. This checkpoint should publish THIS new handoff, new #185 request and prepend canonical index as newest READ FIRST; verify new docs remote SHA/tree/parent/blobs with a non-force expected-SHA lease.

NEXT REQUIRED OPERATION in fresh chat: live authenticated GitHub readback of newest docs, engineering, main and R13 HEAD/TREE/PARENT/blob/ancestry, read newest handoff/index and COMPLETE issue #185 plus comments. Seek genuinely distinct attributable FULL #185 THREAT_MODEL / RELEASE_DESIGN / OPERATIONS review of current c81b0cb (not prior 8c722b). Independently close BOTH incidents before any DB/native host, and solve source/wheel/NTFS/recovery trust + F1/Fable. Only then, after separate informed consent, proceed original clean-Windows-checkout Git fetch/update.ps1/preflight/install/recovery/full UAT.

Hard auto-checkpoint by 20 replies or conservative half-context risk: publish authorized completed changes with exact SHA non-force lease, canonical docs handoff/index, full inline fresh-chat resume prompt, then END session; no background operation or invented context meter. This is a verified checkpoint, not an operational release.
