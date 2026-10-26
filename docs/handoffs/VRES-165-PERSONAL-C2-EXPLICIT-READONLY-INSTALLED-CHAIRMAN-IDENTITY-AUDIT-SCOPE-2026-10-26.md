# Vres-OS #165 — PERSONAL C2: explicitly authorized READ-ONLY inspection of installed managed Chairman files (NOT run)

**Date:** 2026-10-26, Europe/Athens.
**Repo:** vosser24/Vres-OS.
**Docs branch:** docs/chatgpt-continuity-20261023.
**CURRENT STATE:** **C2_READONLY_INSPECTION_SCOPE_AUTHORIZED_BY_OPERATOR / WINDOWS_HOST_INSPECTION_NOT_RUN / NO_MODEL_APPLY / NO_SOURCE_CHANGE / NO_C2_ACCEPTANCE**.
**Operator decision:** The user responded "proceed" directly to ChatGPT's explicit offer: "narrowly scoped read-only inspection of the current-user installed Chairman files, without modifying anything." This authorizes ONLY the bounded READ described here, NOT access to secrets or any installed model change.

## 0. Read-first and exact existing accomplishments

Read canonical docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md first, then THIS limited C2 scope and:
- docs/handoffs/VRES-165-PERSONAL-C1-R1-FIRST-MANUAL-READONLY-PREVIEW-PASS-AND-C2-DECISION-2026-10-26.md — first real Windows source-checkout Sonnet/high reported vs Opus/medium UNINSTALLED candidate, real exit0/hashes verified, but no installed-target observation.
- docs/handoffs/VRES-165-PERSONAL-C1-R1-INDEPENDENT-OFFLINE-ACCEPT-AND-READONLY-MANUAL-PREVIEW-NEXT-2026-10-26.md — C1 R1 independently STATIC_PASS and OFFLINE_ACCEPT at source 7ac041018d4ec5a06be07318ecce5e140faccd91, 29 individually PASSED Windows selected pytest cases/exit0, protected in-process AppData fence and clean worktree. Not installed CLI.
- docs/handoffs/VRES-165-PERSONAL-C0-INDEPENDENT-OFFLINE-ACCEPT-PROCEDURAL-ANOMALY-AND-NEXT-PHASE-2026-10-26.md — separately accepted pure C0 read-only rendering.
- Previous independently accepted A1 R2 and A1 R1, B2A R3 and all prior exact source approvals/rejections, original V-01..V-42 personal functionality roadmap.

**Latest accepted feature SHA** 7ac041018d4ec5a06be07318ecce5e140faccd91, tree 0ef7af10335865231f4350e2dbb7ba561538ee00. No new feature commit, standalone preview invocation, test rerun, installed target probe, model install or plugin setting is performed in this docs checkpoint. Installed Chairman historically Sonnet/high, NOT independently measured in C1.

## 1. Grounded PERSONAL Windows installer topology: exactly scoped safe targets

ChatGPT independently read actual P2 original user release source installer install.ps1 at SHA **82c82430b38f93bd6b9d5c3af3b5de9c1368af9c**, installer blob **29a5f0da235021cc8c5607eb92218e5ea98145fa**, plus P2 source install guide and static plugin template.

That installer defines:

    InstallRoot = %LOCALAPPDATA%\VresOS
    ActivePath = %LOCALAPPDATA%\VresOS\active-install.json
    ClaudeHome = CLAUDE_CONFIG_DIR override if configured, else %USERPROFILE%\.claude
    PluginTarget = ClaudeHome\skills\vres-os
    NewRelease = InstallRoot\releases\<release-id>
    DistributionRoot = NewRelease\distribution
    StagedPlugin = DistributionRoot\vres-os

It copies the staged plugin into the user-scoped Claude skills-directory plugin target and writes the active pointer JSON with fields product="Vres-OS", release, previous, plugin_path, installed_at, autocompact_owned. It stores a distribution copy under a matching release. The old P2 source plugin agent header is name: chairman, model: sonnet, effort: high; its exact Git blob is **6f2239c4dd0d52090d31415c17f763505f93b900**, which differs from the later accepted C1 source plugin body blob **64cba93d6f69960350a0006b594734288f087ccc**. Therefore **NEVER assume the accepted C1 source checkout's template equals the installed release**; C1's preview was knowingly caller-supplied NOT live-verified. Do not automatically treat an installed managed plugin as the effective running model because Claude project/session/managed overrides can exist; this narrow read does NOT inspect global Claude settings.

The operator's historical installed personal release ID was **20261022172833-4d82147b**, expected but NOT newly host-confirmed. Do not claim the installed pointer still names it until the Windows read-only script outputs real evidence.

### Exactly allowed read-only Windows paths

1. The current-user installed Vres **active-install.json** pointer under %LOCALAPPDATA%\VresOS; only extract product, release and plugin_path and only display whitelisted non-secret values. Do not print original JSON, its recursive "previous" pointer, or any config/credential content. Bounds-check pointer file length and deny path links.
2. The single current-user managed plugin target **%USERPROFILE%\.claude\skills\vres-os\agents\chairman.md**, if current CLAUDE_CONFIG_DIR is empty or resolves exactly to expected default. STOP on an override to a different path rather than searching or reading arbitrary Claude homes.
3. The single immutable release-distribution plugin copy **%LOCALAPPDATA%\VresOS\releases\<confirmed active release>\distribution\vres-os\agents\chairman.md**. Do not inspect entire distribution or release manifest until later explicitly scoped.
4. Read file metadata, raw bytes (bounded 512KiB per agent) solely for cryptographic SHA256 and a whitelisted six-line Markdown/YAML frontmatter check; print ONLY sanitized "name=chairman", model sonnet/opus, effort low/medium/high, newline convention, byte count and digest. DO NOT output prompt body or description, secret-like values, installation config, log files, broad directory listings or modified timestamps unrelated to this proof.
5. Follow NO symlinks/junction/reparse points along inspected managed file paths. Check expected release ID and active pointer plugin path strictly before any agent file read. On mismatch/unknown path STOP; do not heuristically search projects or arbitrary user profile locations. No writes, no program execution, no Claude/Vres CLI/plugin invocation, no Python/pytest tests.

If both managed target and exact release distribution copy are read and hashes compare, the script may report **MANAGED_INSTALLED_PLUGIN_FILE_READONLY_CONSISTENT_WITH_ACTIVE_RELEASE_COPY** and the header fields, NOT "active Claude model verified" or "operator approved Opus". If different/missing, report and STOP preserving the evidence. A file being byte-identical to a release copy is only a local snapshot, not ongoing authority, native plugin registration proof or session model telemetry.

## 2. Next operator step and no automatic activation

The user should run ONE guarded Windows PowerShell READ-ONLY scope script provided directly by ChatGPT after this docs handoff seals. Expected final marker:

    VRES_165_C2_CURRENT_USER_INSTALLED_CHAIRMAN_READONLY_INSPECTION_COMPLETE

The script should report:
- Expected anchor/current-user scope, pointer product/release and exact expected plugin target match;
- active managed plugin header/model/effort, hash, byte count/newline style;
- release distribution plugin copy header/model/effort, hash, byte count/newline style;
- whether the two snapshots agree;
- no writes/read other paths and no DB contact by the script (scope of commands, not OS/network attestation).

User pastes the ENTIRE sanitized output; on any STOP do not rerun by bypassing path guards, inspect error evidence and clarify actual installed topology separately. Do NOT run model switch, installer, signing, backup/restore or global Claude file mutation. After operator readback, commit another docs-only C2 observation/assessment handoff and decide whether a reversible apply/rollback feature should even be designed next. Need separate fresh approval for any write/apply/rollback or privileged protected validator/provenance event.

## 3. Incident holds, personal proportionality and full continuity

**LIVE_SCHEMA_048_INCIDENT=OPEN: ABSOLUTELY NO PostgreSQL contact, EVEN SELECT**. Do not Vres bootstrap, task resume, cli doctor, database health, migration, backup or recovery. D2 OPEN, F2 quarantined, R0 NOT_RUN, K0-T1 blocked, L-04 OPEN, PA-01..PA-08 incomplete. VRES_PERSISTENCE_WARNING and VRES_REPLY_GUARD_WARNING remain unresolved, no task or DB access allowed to investigate them.

Installed PERSONAL Chairman last operator-reported Sonnet/high (not C1 live verified), proposed Opus/medium remains UNINSTALLED. Original issue #165 F1 independently authorized operator event, protected state history, validator authority OPEN. No credentials/vault/keyring, unrelated ~/.claude settings, global hooks/plugins files, provider/Fable/real model calls, installer, native signing, production source/main merge or other account effects. Do not create public/commercial multiuser IAM requirements for a PERSONAL local user; use clear state, byte hashes and explicit operator consent before any later operation.

Historical previous C1 R1 independently STATIC_PASS/OFFLINE_ACCEPT (29 Windows PASS/exit0 plus successful one human source preview), old C1 at c545556a4ba9ba48f140e7379da960708a7f3c8d Windows pytest EXIT1 and NOT independently accepted; C0 pure preview 34 PASS/exit0/independent OFFLINE_ACCEPT and separate late PowerShell C0-PROC-01 nonblocking; A1 R2 93 PASS/exit0, A1 R1 71, B2A R3 95/R3-PROC-01, B2B design R3 limited DENY-ONLY acceptance, older B2A REJECT and all Phase A/B1/F2/P2-A1/legacy states and V-01..V-42 ambitions remain tracked.

## 4. Documentation-only checkpoint and exact resume

Commit this new C2 AUTHORIZED-SCOPE handoff and ONLY docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md modified, on canonical docs branch atop verified HEAD **4341d4c2d4555a9d90a47af1f53400c314766f99**, tree **002db7408c56177cfe02163ff1690850d16bbb35**. Strict recursive Git tree compare exactly 2 docs paths/no deletes, single-parent unsigned commit and expected-old-head nonforce update, final source branch HEAD still **7ac041018d4ec5a06be07318ecce5e140faccd91**.

**NEXT-SESSION RESUME:** C1 R1 source, tests and first Windows manual read-only preview independently accepted and operationally confirmed, all at SHA **7ac041018d4ec5a06be07318ecce5e140faccd91**; docs handoff already records both source/candidate CRLF SHA256 and PREVIEW_EXIT_CODE0/worktree clean. Operator responded "proceed" to C2 CURRENT-USER installed Chairman READ-ONLY inspection proposal. GitHub P2 installer defines ACTIVE POINTER %LOCALAPPDATA%\VresOS\active-install.json, current-user plugin %USERPROFILE%\.claude\skills\vres-os\agents\chairman.md (or custom CLAUDE_CONFIG_DIR, which requires separately confirmed consent if different), release copy %LOCALAPPDATA%\VresOS\releases\<pointer.release>\distribution\vres-os\agents\chairman.md, expected old release id 20261022172833-4d82147b. **C2 host inspection NOT_RUN** as of scope docs. NEXT guarded normal PowerShell one-shot, no broad scan/secret, only pointer field checks, exact two agent-file hashes and frontmatter model/effort, refuse links, compare hashes and return marker. NO writes, model switch, source changes, provider calls, global Claude config/credentials or PostgreSQL even SELECT. After actual output seal evidence and plan separate explicit confirm/reversible C2 apply/rollback only if user further approves. Original F1/#165 and V-01..V-42 remain OPEN as appropriate.
