# Vres-OS — Claude Code managed-policy NO-LAUNCH preflight: local paths clear, server policy UNKNOWN

**Date:** 2026-10-29 (Europe/Athens). **Repo:** vosser24/Vres-OS.
**CURRENT GATE:** MANAGED_POLICY_LOCAL_PATHS_CLEAR_OPERATOR_REPORTED / SERVER_MANAGED_POLICY_UNKNOWN_NOT_INSPECTED / CLAUDE_CODE_NOT_LAUNCHED / CLAUDE_VERSION_NOT_VERIFIED / PT2A_B_C_D_INDEPENDENT_SOURCE_REVIEW_NOT_RUN / STRICT_NO_POSTGRESQL_CONTACT / NO_ACTUAL_INSTALLATION_OR_OPUS_ACTIVATION.

This result advances only the previous [Claude Code bare no-launch authentication STOP checkpoint](VRES-PERSONAL-PT2A-PT2D-CLAUDE-CODE-NO-LAUNCH-AUTH-BLOCKED-AND-REVIEW-GATE-2026-10-29.md). The prior checkpoint remains valid: a single direct claude.exe was located, but **BARE_MODE_API_KEY_ALREADY_AVAILABLE=False** and no native Claude review was run. The operator explicitly uses **Claude Code, not Claude web Chat** for independent source reviews. Do not revive the superseded browser-chat reviewer recommendation. No secret, subscription or managed server policy has been inspected.

## 1. Exact user-reported next no-launch evidence

The user pasted a full-looking output of the read-only Windows MANAGED POLICY PREFLIGHT from the original source anchor C:\Projects\Vres-P2F-Postinstall-Hardening-20261022. Archive the normalized pasted output as [operator managed-policy preflight](VRES-PERSONAL-CLAUDE-CODE-MANAGED-POLICY-OPERATOR-CONSOLE-CHAT-COPY-2026-10-29.txt), Git blob **6b99dca057b368ab5ffb30dd33d12538586b6ded**. This is **LF-normalized CHAT transcription**, not independently uploaded original Windows raw bytes or authenticated OS trace; original Windows log byte SHA256 is unknown and must not be fabricated.

Reported flags and checks:
- **MODE=READ_ONLY_NO_CLAUDE_LAUNCH**, **PASS: Single direct claude.exe**, **CLAUDE_PROCESS_STARTED=False**.
- MANAGED_SETTINGS_FILE_PRESENT=False: Windows Program Files/ClaudeCode/managed-settings.json.
- MANAGED_SETTINGS_DIRECTORY_PRESENT=False: Windows Program Files/ClaudeCode/managed-settings.d.
- MANAGED_MCP_FILE_PRESENT=False: Windows Program Files/ClaudeCode/managed-mcp.json.
- HKLM_MANAGED_SETTINGS_PRESENT=False: no registry value Settings at HKLM/SOFTWARE/Policies/ClaudeCode.
- HKCU_MANAGED_SETTINGS_PRESENT=False: no registry value Settings at HKCU/SOFTWARE/Policies/ClaudeCode.
- **LOCAL_MANAGED_POLICY_PRESENT=False**, but **SERVER_MANAGED_POLICY=UNKNOWN_NOT_INSPECTED**.
- **CLAUDE_VERSION=NOT_VERIFIED**, **CLAUDE_HOOKS=NOT_EXECUTED**, **CREDENTIAL_VALUES=NOT_READ**, **NATIVE_SOURCE_REVIEW=NOT_RUN**.
- **DECISION=LOCAL_POLICY_PATHS_CLEAR_SERVER_POLICY_UNKNOWN** and final VRES_CLAUDE_CODE_POLICY_PREFLIGHT_COMPLETE; normal PowerShell prompt restored. No STOP/ABORT marker in pasted output.

**Verdict:** Local managed-policy file/registry path presence checks PASS as reported. This is NOT proof that server-managed policies or managed hooks are absent: an eligible Claude Code login can fetch a policy from the claude.ai admin console/gateway at startup. File/registry *absence* is not proof of no managed source under a server-managed plan, nor does it attest the loaded CLI version or exact host hook set. A normal hooked Claude Code review remains BLOCKED.

## 2. Fresh vendor documentation verification

Current official Anthropic documents checked during this gate (source-derived facts; NOT host evidence):
- https://code.claude.com/docs/en/managed-settings: supported Windows local managed paths are C:\Program Files\ClaudeCode\managed-settings.json, optional managed-settings.d, and registry Settings value under HKLM or HKCU SOFTWARE\Policies\ClaudeCode; server-managed settings from claude.ai/gateway are a **separate higher-precedence remote source** that can be fetched at startup.
- https://code.claude.com/docs/en/cli-reference: **--safe-mode** disables ordinary customization hooks/plugins/MCP and preserves authentication, but **managed policy hooks still apply**. **--tools ""** removes built-in tools but not MCP; **--disallowedTools "mcp__*"** denies MCP, and **--no-session-persistence** works in print mode. Local flags/version are NOT verified on this Windows host.
- https://code.claude.com/docs/en/hooks: **--settings '{"disableAllHooks":true}'** overrides user/project/local hooks for one run but **cannot override managed hooks**. Do not interpret it as a managed-policy bypass.
- https://code.claude.com/docs/en/headless: **--bare -p** avoids automatic local hooks/plugins/MCP but does not read the existing subscription OAuth/keychain and needs an independently authorized API key or approved apiKeyHelper. Prior no-launch process check found no ANTHROPIC_API_KEY; this is not an assertion that a helper exists or does not.
- https://support.claude.com/en/articles/9267400-move-your-personal-claude-account-to-a-team-or-enterprise-organization: a user can have an individual Free/Pro/Max personal account and/or a Team/Enterprise organization account with the same email; switching workspaces changes the active account context. **Do not infer the active account type from the presence of claude.exe.**

## 3. Exact source and test/review continuity

Canonical documentation previous HEAD **9e41849fa0db626d3fdf42ee951f7ee2ff4b93ac**, tree **e6738c8d240112921252787e57d0a7d84514a61c**. PT2D feature HEAD **a5913288b7748693adafc36c9c1cb35af3ea3949**, tree **d45ffc91781be6681124ff369af5df4d06300ce9**, remains unchanged. Complete independent 10-file source packet blob **7eb30e0ef2f2288e4e5951da4057352f256091d5** remains exact/full/published but independent reviewer NOT_RUN.

Selected guarded Windows offline pytest: PT1 R1 189 PASS/exit0 and independent STATIC_ACCEPT (0 blockers/5 informationals); PT2A 213 PASS/exit0 independent source review NOT_RUN; PT2B 43 PASS/exit0 independent review NOT_RUN; PT2C selected SHA 81149... 54 PASS/exit0 independent NOT_RUN; PT2D 50 PASS/exit0 independent NOT_RUN. Unselected PT2C alternative SHA 59d811... remains separate, synthetic evidence only. All original R0 failed attempts/history preserved. No source/main/installer release modifications from this checkpoint.

## 4. Next ONE operator gate — determine active Claude ACCOUNT CONTEXT without launching Code

The active account type is the remaining material fact before deciding whether a subscription-authenticated Claude Code --safe-mode review can be considered without managed hooks. **Do not automatically start, stop, resume, or update any existing hooked Claude Code session. Do not run /status or claude doctor.**

Using only ordinary browser **account SETTINGS** (not a Claude web CHAT or reviewer), inspect which account/workspace is active for the same login used by Claude Code: individual **Free / Pro / Max** versus organization **Team / Enterprise** or **UNKNOWN / MULTIPLE**. User may inspect the account switcher/settings without changing subscriptions, login, credentials, or managed settings. Report only one of:
- PERSONAL_FREE, PERSONAL_PRO or PERSONAL_MAX, if confirmed to be the account actually used for Claude Code.
- TEAM_OR_ENTERPRISE, if organization account is active; do not launch while server-managed policy remains unknown.
- MULTIPLE_OR_UNKNOWN, if several workspaces exist or the active Claude Code login cannot be tied to the browser account. In that case STOP, without guessing.

No usernames, email addresses, organization identifiers, user profile files, screenshots with secrets, token values or API keys are needed. This is a new narrowly bounded observation request, not a remote-policy attestation. Even a confirmed personal plan does not yet prove that the locally installed claude.exe supports --safe-mode or that the exact proposed one-run arguments are honored. **Do not issue a Claude Code review launch command until account context and local version/flags and any remaining managed-policy path are separately reconciled.**

## 5. Absolute holds and program scope

LIVE_SCHEMA_048_INCIDENT=OPEN: ABSOLUTELY NO PostgreSQL contact even SELECT, directly or via Vres MCP/CLI/tasks/bootstrap/doctor/health/hooks/F2/recovery. HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: seven automatic Vres PostToolUse DB-route attempts from Claude Read/Grep were all refused; no-attempt discipline was breached despite no successful SQL evidence. VRES_REPLY_GUARD_WARNING and VRES_PERSISTENCE_WARNING unresolved, no probes.

Current user's original P2 installed Chairman last observed Sonnet/high, requested Opus/medium NOT_INSTALLED, physically loaded model and effort UNKNOWN. Strict independently rooted F1 positive authority BLOCKED separately from PERSONAL P0/P1/P2/P3 governance. Protected Fable/high arbiter and validator pins, worker/specialist pins, cross-project current-user credential handles/explicit bindings, full V-01..V-42 product scope, Visual Studio fresh and legacy onboarding, and E7/PA/F2/production gate holds preserved. Any actual protected installation requires specific fresh user consent, independently reviewed source/write/recovery, verified release-v2 provenance, actual backup/rollback readiness and no incident violation.

METHODOLOGY: ChatGPT source-grounded exact Git SHA/tree/parent/blobs, minimal bounded development with two-file changed-path allowlist; nonforced GitHub ref updates and readback; ONE whole atomic Windows PowerShell validation per gate with environment isolation/restore, AppData tripwire, individual test names, pre/post identity; independent Claude Code review only in demonstrably no-hook/zero-DB-attempt mode; detailed docs-only index+handoff per material status, preserve full original continuity. All shell commands and Claude prompts always delivered INLINE CODE BLOCKS. NEVER treat no-hook assumptions or process-key checks as authorization to run normal Claude.
