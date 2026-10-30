# Vres-OS native Claude host-hook incident — Stage 3 exact installed read post-hook risk CONFIRMED, Stage 4 comparison NEXT

**Date:** 2026-10-30 Europe/Athens. **Repository:** vosser24/Vres-OS. **Evidence type:** operator-pasted ordinary Windows PowerShell output of Stage 3 strictly read-only matcher reconciliation; not independently byte-hash-attested original Windows console output or any live hook/SQL packet capture. No native Claude, hook, database or installed configuration change occurred.

## Stage 3 exact SHA-pinned static result

The operator ran the complete Stage 3 script `docs/handoffs/VRES-HOST-HOOK-STAGE3-PINNED-STATIC-MATCHER-COMPARISON-2026-10-30.ps1`, Git blob **a10b24b6511d62102948cf486330d47bb50642fd**. Both SHA256/JSON preflights PASS:
- Accepted A18 source `C:\Projects\Vres-ChatGPT-Review-168-Record-Leaf-Rebind-A18-20261030\plugins\vres-os\hooks\hooks.json`, **8,286 bytes, SHA256 88EA7AE078821A2DE85693DF0EE785EEEA847EA100469818DD0FBE0E4F1142B2**.
- Installed current-user `%USERPROFILE%\.claude\skills\vres-os\hooks\hooks.json`, **7,921 bytes, SHA256 700BF6AD711212C3A3A22419E42E0E5D62A491A7454C55C07AFED8409F0C34F7**.

The script evaluated **30 fixed tool/event comparisons** (3 events × 10 nonsecret tool names) against the exact pinned source and installed regex matchers without running hooks. **Exactly SIX combinations DIFFERED**:

| Event | Tool | Accepted A18 source group/command/MCP | Installed Vres group/command/MCP |
|---|---|---|---|
| PostToolUse | Read | 0 / 0 / 0 | 2 / 1 / 1 |
| PostToolUse | Glob | 0 / 0 / 0 | 2 / 1 / 1 |
| PostToolUse | Grep | 0 / 0 / 0 | 2 / 1 / 1 |
| PostToolUseFailure | Read | 0 / 0 / 0 | 1 / 0 / 1 |
| PostToolUseFailure | Glob | 0 / 0 / 0 | 1 / 0 / 1 |
| PostToolUseFailure | Grep | 0 / 0 / 0 | 1 / 0 / 1 |

The **9** reported installed entries are **static matching declaration counts** across three tools and two events, **not nine observed hook executions**: three command and three MCP matches for successful Read/Glob/Grep, and three MCP matches for failures. Source totals for those post-hook combinations were ZERO. `STATIC_TOOL_EVENT_MATCH_DIFFERENCES=6`, `SOURCE_READ_GLOB_GREP_POSTHOOK_ENTRIES=0`, `INSTALLED_READ_GLOB_GREP_POSTHOOK_ENTRIES=9`, `INSTALLED_READ_POSTHOOK_MATCH_RISK=DETECTED`.

The other 24 sampled tool/event comparisons matched: Read/Glob/Grep PreToolUse zero in both, and ReadFile/Bash/Write/Edit/TaskOutput/ToolSearch/AskUserQuestion match counts identical across the three events. **ReadFile remains non-exempt even in accepted source**; no broad claim that arbitrary read-like aliases are safe. Lifecycle **counts** were equal: SessionStart, UserPromptSubmit, PreCompact, PostCompact, Stop, SessionEnd each 1 group/1 entry per manifest, and SubagentStop 3 groups/3 entries per manifest. Equal counts do NOT prove command bodies/payloads identical or lifecycle execution safe.

The Stage 3 result is **strong, directly relevant static evidence consistent with the seven historical refused native Claude Read/Grep posttool database-routing attempts**; it is NOT runtime enablement verification, a trace of which hook contacted a database, proof that no other plugins could route database activity, or permission to launch native Claude Code. `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`. Separately `LIVE_SCHEMA_048_INCIDENT=OPEN` and PostgreSQL contact of ANY kind, even SELECT, stays forbidden.

## Stage 4 exact next read-only action

Complete **Stage 4 SHA-pinned non-matcher payload comparison** script `VRES-HOST-HOOK-STAGE4-PINNED-NONMATCHER-PAYLOAD-COMPARISON-2026-10-30.ps1`, Git blob **475360edf8e7145974ec7252edf453cf7e5b2259**, 148 lines. Supply it to the operator as ONE FULL INLINE PowerShell code block, not a file-only instruction or fragments. Run in an ordinary Windows PowerShell window, NOT Claude Code.

The script separately revalidates both exact Stage 3 file SHA256 identities; refuses network-path/reparse ancestors and oversized (>1MiB) manifest files. It parses only the two pinned manifest JSONs in memory, scans all event names and aligned hook groups, compares exact matcher equality and **all other hook-group fields** through canonicalized in-memory JSON serialization. It does NOT print the matcher regex strings, command strings, hook paths, MCP input/payload, secrets or settings contents; outputs only event/group counts and matcher/nonmatcher equality booleans. It does not write any source/installed file and does not execute hooks, MCP, Claude or PostgreSQL.

Success marker: `VRES_HOST_HOOK_STAGE4_PAYLOAD_COMPARISON_COMPLETE`. Interpret `STATIC_NARROW_MATCHER_CORRECTION_CANDIDATE=YES_REVIEW_REQUIRED` only as confirmation that source/installed differences can be represented by matcher field declarations while nonmatcher payloads and group counts match in the inspected manifests. This is NOT installed remediation authorization, native Claude runtime hook clearance or schema-048 clearance. Any `NONMATCHER_PAYLOAD_DIFFERENT_GROUPS>0`, `GROUP_COUNT_DIFFERENCES>0`, unknown or timeout is a STOP/hold for further source-level inspection, not permission to blindly update installed hooks. Obtain separate explicit operator authorization before any user-scoped installed configuration change and preserve rollback/identity checks.

## Other held surfaces and program continuation

Stage 2 had confirmed installed user-scoped `.claude\skills\vres-os` with source vs installed manifest mismatch; current `.claude\settings.json` SHA256 **5E36A7DBC5D676A5C43C2FAC435D64342E329DA361B9244F0CC5140C0892076B** valid, zero root hooks and no Vres `enabledPlugins` entries; installed plugin registry/cache not found but user skills install exists. Correct Windows managed `C:\Program Files\ClaudeCode\managed-settings.json`/drop-ins/managed MCP and HKLM/HKCU policies not found on checked paths, but server-managed policies and other plugins remain unverified. This does NOT attest effective host hook enablement.

Latest selected Windows accepted source is A18 `7bace7758e5c7f9a00f26179eb741ef3a319bc77`, tree `4d17344a9510de6394840092cf33729ab153fbb5`, **49 PASS, zero fail/skip, 33 before/after protected blobs, saved-value verified environment restoration**; see `VRES-168-A18-WINDOWS-49-PASS-EXIT0-ACCEPTANCE-2026-10-30.md`. A19 state-directory write-side candidate was identified but its GitHub source-writing actions were blocked by automated safeguards; **A19 is NOT committed/test-ready**. Earlier original rejected A12 Windows 18PASS/1FAIL and A13 28PASS/1FAIL remain preserved, as does A16 env-copy uncertainty.

**No PostgreSQL contact, ordinary native Claude review, installed/global Vres/Claude/PRISM change, Fable/high trusted positive issuer, real legacy project activation, PR/merge/product-main or go-live.** Preserve PERSONAL P0-P3, PT1/PT2A-D, Hook-R1, #168 A1-A18 acceptance/rejection/skip history, V-01..V-42, #165-170, #174, #176 E7/E8, global Claude/PRISM #166, Data Source Registry #167, Visual Studio real legacy #169 and readiness/go-live #170.
