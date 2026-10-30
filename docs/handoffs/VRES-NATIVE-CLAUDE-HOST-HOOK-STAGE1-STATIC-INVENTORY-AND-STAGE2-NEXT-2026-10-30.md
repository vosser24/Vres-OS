# Vres-OS — HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED incident, static host inventory Stage 1 reviewed; Stage 2 next

**Date:** 2026-10-30, Europe/Athens. **Repository:** vosser24/Vres-OS. **Scope:** current Windows user only, no Claude Code launch, plugin execution, credential data, model, PostgreSQL, installer, live real project or config mutation. This host-hook inventory is NOT an incident clearance.

## Stage 1 operator Windows console, verified as reported

Operator ran prior ChatGPT read-only PowerShell over accepted A18 checkout `C:\Projects\Vres-ChatGPT-Review-168-Record-Leaf-Rebind-A18-20261030`, full HEAD **7bace7758e5c7f9a00f26179eb741ef3a319bc77**, tree **4d17344a9510de6394840092cf33729ab153fbb5**, clean. Reported:
- Claude current user `C:\Users\User\.claude\settings.json`: PRESENT, JSON VALID, 3102 bytes, SHA256 **5E36A7DBC5D676A5C43C2FAC435D64342E329DA361B9244F0CC5140C0892076B**; no **root-level** hook event names detected; DB-route literal regex indicator false. It may still include `enabledPlugins`, env and unrelated settings, which were NOT examined by stage 1; do not print raw content or secret values.
- Current user `settings.local.json` checked path NOT_FOUND.
- Marketplace `.claude\plugins\installed_plugins.json` checked path NOT_FOUND (NOT proof Vres not installed via another user-scoped mechanism).
- Accepted A18 source `plugins/vres-os/hooks/hooks.json`: PRESENT, JSON VALID, 8286 bytes, SHA256 **88EA7AE078821A2DE85693DF0EE785EEEA847EA100469818DD0FBE0E4F1142B2**; hook event types **SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PostToolUseFailure, PreCompact, PostCompact, Stop, SessionEnd, SubagentStop**. Literal DB-route regex false is not a guarantee those command wrappers or MCP tool hooks cannot contact a database.
- A18 project `.claude\settings.json` at checked path NOT_FOUND.
- Earlier checked `C:\ProgramData\ClaudeCode\managed-settings.json` NOT_FOUND. **This legacy location is not the current Claude Code Windows managed policy location**; source must be reevaluated.
- `NO_CLAUDE_CODE_EXECUTED`, `NO_DATABASE_ACCESS_ATTEMPTED`, and `VRES_HOST_HOOK_READONLY_INVENTORY_COMPLETE` reported. No runtime/effective hook discovery, no independent SQL packet trace, no installed hook source hash attestation.

## New independently verified source context

The accepted A18 source GitHub hook manifest `plugins/vres-os/hooks/hooks.json` has Git blob `e286e4be47d058ee6ed6a3169fc45803aedc0df1`. It declares lifecycle command hooks (e.g. SessionStart, UserPromptSubmit, Stop, SessionEnd), and an `mcp_tool` PostToolUse observer `reply_activity_observe`, with targeted builtin Read/Grep/Glob matcher exclusions in **source**. Test `tests/test_hook_readonly_posttool_fence.py` Git blob `97c2bb75ae31ff98a5ce66c450d4f51d6e12f15a` validates only pinned source matcher behavior; it explicitly does not attest installed hooks or broader lifecycle safety.

The Windows installer `install.ps1` at A18 exact source installs its user-scoped Vres plugin under `$ClaudeHome\skills\vres-os`, with `$ClaudeHome` determined by `CLAUDE_CONFIG_DIR` or `%USERPROFILE%\.claude`; therefore absence of a marketplace registry is not a conclusive installation-state signal.

Anthropic current official docs `https://code.claude.com/docs/en/managed-settings` identify Windows managed `C:\Program Files\ClaudeCode\managed-settings.json`, optional `managed-settings.d\*.json`, `managed-mcp.json`, and `HKLM\SOFTWARE\Policies\ClaudeCode`/`HKCU\SOFTWARE\Policies\ClaudeCode` Settings registry values. Current docs explicitly say older `C:\ProgramData\ClaudeCode\managed-settings.json` is not read. Sources also include settings enabled plugins, project settings and server-managed policies. Anthropic `https://code.claude.com/docs/en/plugins` states enabled plugin hooks fire at lifecycle events and their MCP servers run alongside sessions.

## Stage 2 exact next safe operator action

The complete archived read-only [Stage 2 static surfaces PowerShell](VRES-NATIVE-CLAUDE-HOST-HOOK-STAGE2-STATIC-INVENTORY-2026-10-30.ps1) is Git blob **c92d78c01e678c656b833cdb1190f73368a6315d**, 215 lines. ALWAYS give the operator the full script INLINE as ONE complete PowerShell code block; do not substitute file-only instructions.

Run in ordinary Windows PowerShell, **not** inside Claude Code, no hook launch, database CLI/MCP/test, model or installed file modification. The script reads only bounded JSON metadata or hashes, does not print commands/settings raw/credentials, checks reparse-point ancestors and refuses UNC paths. It inspects:
- accepted A18 source hook hash/event structure,
- Claude default user config and optional `CLAUDE_CONFIG_DIR` shell override,
- current-user settings JSON root-level hooks and Vres-specific `enabledPlugins` booleans (never other settings values),
- installed expected `skills\vres-os` root, its hook manifest, plugin metadata and bounded source wrapper hashes,
- optional marketplace plugin registry and bounded Vres cache manifest discovery,
- PT2D incident checkout and accepted A18 checkout's project/local settings,
- correct Windows managed file, drop-ins and managed MCP metadata,
- HKLM/HKCU registry policy Settings presence and root hooks without displaying values,
- Vres local installed `active-install.json` metadata-only hash.

Success marker `VRES_HOST_HOOK_STAGE2_STATIC_INVENTORY_COMPLETE`, but **NOT equivalent to incident closure**. Other enabled plugins, server-managed policy, Claude Code effective hook registration and historical installed runtime behavior remain unverified. If any surface unreadable, oversized or reparse-linked, treat as unresolved; do not bypass with writes or normal Claude Code.

## Binding holds and current program

`HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN` until separately authorized source/configuration and installed/managed hook review addresses seven refused native Claude post-tool routing attempts. `LIVE_SCHEMA_048_INCIDENT=OPEN`: absolutely **NO PostgreSQL even SELECT** through any direct or indirect path. No ordinary native Claude Code session, MCP task, model, protected Fable/high approval, installed Vres/Claude/PRISM changes, credentials, real legacy project onboarding, product main/PR/merge or go-live.

A18 Windows-selected accepted at SHA **7bace7758e5c7f9a00f26179eb741ef3a319bc77** with 49 distinct passing tests, 33 pinned pre/post Git blobs and saved-value verified environment restoration; canonical [A18 acceptance](VRES-168-A18-WINDOWS-49-PASS-EXIT0-ACCEPTANCE-2026-10-30.md). A19 write-side ancestor safety candidate was identified but repository writes were blocked by automated safety controls, so **A19 has NO committed source and NO Windows test readiness**. Preserve original A12 (18PASS/1FAIL) and A13 (28PASS/1FAIL) rejections, A16 environment script-copy caveat, all PT1/PT2A-D/Hook-R1 and #168 A1-A18 chronology, PERSONAL P0-P3, V-01..V-42, #165-170, #174, E7/E8, global Claude/PRISM, current-user data registry, Visual Studio #169 and readiness/go-live #170.
