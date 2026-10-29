# Vres-OS — CLAUDE CODE bare review feasibility and no-launch preflight

Date: 2026-10-29 Europe/Athens. Repo: vosser24/Vres-OS.
**CURRENT STATE:** USER_SELECTED_CLAUDE_CODE_NOT_WEB_CHAT / NORMAL_HOOKED_CLAUDE_CODE_REVIEW_BLOCKED / NO_LAUNCH_OPERATOR_PREFLIGHT_NEXT / PT2A_PT2B_PT2C_PT2D_INDEPENDENT_REVIEW_NOT_RUN / NO_DATABASE_OR_INSTALL.

**Correction to continuity:** The previous GitHub-only hook audit remains valid source evidence; its suggested browser Claude web Chat reviewer flow is superseded by the user's explicit requirement to use Claude Code. Do not ask the user to review via the browser. No independent PT2A–D review has run.

## 1. Exact source and documentation boundaries

- Previous canonical docs HEAD 40a6160e945f1eae2df36ec6c420f70dfd6c6ab5; tree 9e1bdc26ca5d4fae91902c8d11a7b6aa9680b57f.
- PT2D published source HEAD a5913288b7748693adafc36c9c1cb35af3ea3949, tree d45ffc91781be6681124ff369af5df4d06300ce9, sole PT2C parent 81149beab52750c93db91453e18efbd5f7a21da4; no new source modifications.
- Preserved ten-file full-source packet: docs/handoffs/VRES-PERSONAL-PT2A-PT2D-INDEPENDENT-STATIC-REVIEW-EXACT-SOURCE-PACKET-2026-10-29.txt, Git blob 7eb30e0ef2f2288e4e5951da4057352f256091d5, 122713 text characters/2764 LF-separated lines; prior GitHub readback confirmed all ten embedded files exactly matched their expected Git source blobs. Source packet is not a trusted publisher attestation, installed-profile evidence or a reviewer verdict.
- Scoped Windows test evidence by pinned source: PT2A 213, PT2B 43, PT2C 54, PT2D 50 distinct guarded Windows selected PASS/exit0, independent reviews NOT_RUN. PT1 R1 independently STATIC_ACCEPT zero blocker/five informational and 189 selected Windows PASS/exit0. Older R0 failed attempts and unattached PT2C alternative remain preserved.

## 2. Why normal Claude Code review is still unsafe

Pinned GitHub source hooks.json blob 5833973d9be6ccf4263dda2d461cc5994d30416c contains broad PostToolUse and PostToolUseFailure Vres MCP reply_activity_observe matcher covering Read/Grep/Glob, plus broad experience-observe CLI hook and additional lifecycle hooks. The historical independent PT1 Claude reviewer triggered FOUR Read and THREE Grep automatic database-route ATTEMPTS; guard refused each, but the no-attempt discipline was breached. Changing working directory or instructing Claude not to query PostgreSQL is not a control. Neither the installed hook set nor managed host settings has been inspected or attested in this tranche.

ABSOLUTE: LIVE_SCHEMA_048_INCIDENT=OPEN — no PostgreSQL even SELECT, direct or through Vres CLI/tasks/hooks/MCP/health/doctor/bootstrap/F2/recovery. HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN. No new ordinary Claude Code session, no closing existing hooked Claude session just for review, no installed/global hook or profile edits, no contact-guard bypass. VRES_REPLY_GUARD_WARNING and VRES_PERSISTENCE_WARNING remain unresolved.

## 3. Anthropic official CLI isolation facts and authentication limitation

Official current vendor docs read on 2026-10-29:
- https://code.claude.com/docs/en/headless — noninteractive Claude Code bare mode, invoked as claude --bare -p, avoids automatic hook/plugin/MCP/skills/CLAUDE.md discovery from user/project sources, unlike ordinary Claude -p. A fresh no-tools source review can receive input through stdin without native file reads. Bare mode does not read OAuth/keychain authentication; it requires ANTHROPIC_API_KEY already securely available or a separately provided apiKeyHelper. Existing Claude Code subscription login alone does not satisfy bare mode.
- https://code.claude.com/docs/en/cli-reference — --tools "" removes built-in tools; --disallowedTools "mcp__*" separately denies MCP tools; --no-session-persistence works in print mode. Never add --mcp-config, --plugin-dir, --add-dir, custom agents, or resumed conversations for review. If local CLI lacks a required flag, STOP.
- Same CLI reference: --safe-mode suppresses ordinary customizations but MANAGED SETTINGS POLICY INCLUDING POLICY-CONFIGURED HOOKS STILL APPLIES. It is not proven safe without independently establishing no managed hook. --restricted also loads managed settings and must not silently replace bare-mode verification.
- https://code.claude.com/docs/en/env-vars — CLAUDE_CODE_SIMPLE=1 is the equivalent of --bare, not an authentication bypass.

Documented bare-mode behavior is NOT local version/managed-hook/contact attestation. If API credentials are unavailable, no silent fallback to ordinary Claude, safe-mode or restricted-mode. Do not request the user to paste keys. A separate API key might incur different billing than existing subscription; no new API-key provisioning or charge is authorized by this documentation.

**CONDITIONAL FUTURE ONLY:** After a clean no-launch preflight and independently checked version/isolation support, a separate guarded one-shot Claude Code command could use a fresh ordinary disposable folder (not Vres installed or source worktree), stdin containing only the verified review packet, claude --bare -p, --tools "", --disallowedTools "mcp__*", no persistence or MCP, and a fixed report-only prompt. The normal Claude Code reviewer remains BLOCKED until these conditions are demonstrated. Do not execute future review just because preflight reports prerequisite booleans.

## 4. Immediate step: ONE atomic NO-LAUNCH Windows PowerShell preflight

Archived proposed 72-line PowerShell: docs/handoffs/VRES-PERSONAL-PT2A-PT2D-CLAUDE-CODE-BARE-NO-LAUNCH-PREFLIGHT-2026-10-29.ps1, Git blob 91679f2a42f68eb40a471e2c6e9652b23effeb6d.

User must receive the ENTIRE PowerShell & { ... } block inline in a code block, not merely a file link. The script does not launch Claude or use a credential value. It only checks source review worktree HEAD and tree/clean via read-only git at C:\Projects\Vres-ChatGPT-Review-Personal-PT2D-20261029, identifies the command *type and basename only* of matching claude executables (without running them), and reports process-only yes/no presence of ANTHROPIC_API_KEY and custom ANTHROPIC_BASE_URL, without printing either secret or endpoint. It explicitly prints CLAUDE_VERSION=NOT_CHECKED_NO_LAUNCH, INSTALLED_HOOKS=NOT_READ, NATIVE_CLAUDE_CODE_REVIEW=NOT_RUN.

Decision: if no API key, STOP_BARE_MODE_AUTH_NOT_AVAILABLE; if multiple commands/wrapper, STOP_AMBIGUOUS_CLAUDE_COMMAND; if endpoint override, STOP_CUSTOM_ENDPOINT_REQUIRES_SEPARATE_REVIEW. Otherwise only PREREQUISITES_SEEN_BUT_BARE_MODE_NOT_YET_ATTESTED. No printed preflight status is independent proof of a safe Claude Code launch.

After user supplies entire console, review all output, do not re-run passed tests. If any blocker, preserve EVIDENCE_BLOCKED and do not launch. If prerequisites exist, prepare a NEW separately reviewed one-shot Claude Code launch with exact version/flags verification, no native tools and process-only environment guards; review still NOT_RUN at this checkpoint.

## 5. Retained product and review constraints

No source or installed current-user Claude change, no Opus/medium activation; original installed P2 Chairman last observed Sonnet/high, effective model/effort UNKNOWN, strict F1 positive issuer BLOCKED. PERSONAL P0/P1/P2/P3, protected Fable/high router/validator and worker pins, local current-user credential handles and cross-project binding, Visual Studio fresh/legacy onboarding, V-01..V-42 roadmap, E7/PA/F2 and production holds remain. No protected installed write without independently accepted source/recovery design, real release-v2 provenance and rollback readiness and new explicit user consent, subject to open P3 incidents.

Canonical methodology: SHA/tree/parent/blob and changed-path allowlist; docs-only handoff update single-parent nonforced GitHub CAS/readback; one whole fail-fast Windows PowerShell block, report exact output; no hook-bearing session or database probe under incident; source-review verdict distinguished from passing Windows tests.
