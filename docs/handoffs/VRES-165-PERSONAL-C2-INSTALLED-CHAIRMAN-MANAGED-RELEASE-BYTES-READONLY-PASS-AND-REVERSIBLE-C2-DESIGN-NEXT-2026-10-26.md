# Vres-OS #165 — PERSONAL C2: current-user installed Chairman managed file equals selected release, read-only evidence PASS

**Date:** 2026-10-26, Europe/Athens.
**Repository:** vosser24/Vres-OS.
**Canonical docs branch:** docs/chatgpt-continuity-20261023.
**Accepted C1 R1 feature source branch:** feature/165-chairman-policy-foundation-20261023.
**CURRENT C2 OBSERVATION:** **USER REPORTED READ-ONLY INSTALLED MANAGED FILE INSPECTION PASS**, active pointer and exact selected release identity verified, current-user managed Chairman and corresponding immutable release distribution copy headers and SHA-256 identical, independently reconciled with the original P2 GitHub release-source blob. **NOT effective currently-running Claude model attestation; NOT operator approval of Opus/medium; NOT model activation; NOT C2 apply/rollback acceptance.**
**Last reported actual installed release ID:** 20261022172833-4d82147b, now independently supported by the new operator-read active-install pointer excerpt.
**Permanent DB restriction:** LIVE_SCHEMA_048_INCIDENT=OPEN; ABSOLUTELY NO PostgreSQL CONTACT, EVEN SELECT.

## 0. Read-first chronology and authorization scope

Read CURRENT docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md, then THIS latest C2 observed installed-file evidence, then:
1. docs/handoffs/VRES-165-PERSONAL-C2-EXPLICIT-READONLY-INSTALLED-CHAIRMAN-IDENTITY-AUDIT-SCOPE-2026-10-26.md — user's explicit "proceed" authorized ONLY these three managed files read-only; did NOT authorize Claude settings/secret/database queries or model switching.
2. docs/handoffs/VRES-165-PERSONAL-C1-R1-FIRST-MANUAL-READONLY-PREVIEW-PASS-AND-C2-DECISION-2026-10-26.md — accepted source-checkout CLI manual preview user result, Sonnet/high caller-reported vs Opus/medium NOT INSTALLED and CRLF source/candidate digests; this was NOT a live installed file inspection.
3. docs/handoffs/VRES-165-PERSONAL-C1-R1-INDEPENDENT-OFFLINE-ACCEPT-AND-READONLY-MANUAL-PREVIEW-NEXT-2026-10-26.md — independent STATIC_PASS and independent OFFLINE_ACCEPT for read-only C1 source/tests at exact source commit.
4. docs/handoffs/VRES-165-PERSONAL-C0-INDEPENDENT-OFFLINE-ACCEPT-PROCEDURAL-ANOMALY-AND-NEXT-PHASE-2026-10-26.md — independent C0 pure preview acceptance at its own SHA.
5. Prior accepted A1 R2/A1 R1/B2A R3, R3 denial-only design/erratum, historical reject and phase states and entire V-01..V-42 personal development plan.

This is the FIRST read-only operator-evidenced INSTALLED current-user file snapshot, not source-checkout preview and not an inspection of Claude's running session. No new C2 code, tests or independent Claude reviewer report was executed; this operator read-only evidence is independently reconciled with public immutable P2 release source as described below.

## 1. Grounded P2 managed installation topology

The personally installed Windows release was built from original P2 source HEAD **82c82430b38f93bd6b9d5c3af3b5de9c1368af9c**. ChatGPT separately verified original source installer install.ps1 blob **29a5f0da235021cc8c5607eb92218e5ea98145fa**. That installer defines:
- A current-user local app-data Vres root: %LOCALAPPDATA%\VresOS.
- An active pointer file: %LOCALAPPDATA%\VresOS\active-install.json.
- A managed personal plugin: %USERPROFILE%\.claude\skills\vres-os, unless a distinct CLAUDE_CONFIG_DIR override is configured.
- The managed target's one agent file: %USERPROFILE%\.claude\skills\vres-os\agents\chairman.md.
- A matching historical release distribution snapshot: %LOCALAPPDATA%\VresOS\releases\<active-release>\distribution\vres-os\agents\chairman.md.
- The active pointer is expected to contain at least whitelisted fields product, release, plugin_path. Only these fields were displayed/used in the current read-only audit; no recursive "previous" content or credentials were printed.

The user-activated current-user read-only script refused an unexpected custom Claude home, out-of-bounds pointer release format or product, mismatched managed plugin target, reparse points and missing/oversized/malformed Chairman files. It checked exact pointer release against previously reported 20261022172833-4d82147b and all release-copy ancestors before bounded file reads. It printed no Chairman instruction body, Claude global settings, credential/value, database target registry or secrets.

## 2. Actual user-provided Windows PowerShell excerpt, supported positive findings

User pasted the terminal transcript beginning at the already-defined variable claudeHome, **not** the original initial variable/environment preamble of the script. The excerpt includes script code and outputs for the critical pointer/managed file/release-copy checks. Therefore do NOT call it the complete byte-for-byte original script transcript or independently attest the omitted preamble, but preserve all observed result markers and no errors.

**Observed identity and target checks:**

    ACTIVE_PRODUCT=Vres-OS
    ACTIVE_RELEASE=20261022172833-4d82147b
    PASS: Active pointer targets current-user managed plugin

The script validated release ID shape and expected historical ID, checked plugin_path string equals current-user expected skills/vres-os root and traversed only expected managed/current-release directory ancestors, refusing reparse points. No STOP or stack/error appeared in the provided excerpt.

**Observed current-user MANAGED plugin file:**

    MANAGED_MODEL=sonnet
    MANAGED_EFFORT=high
    MANAGED_BYTES=24208
    MANAGED_NEWLINES=LF
    MANAGED_SHA256=a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73

**Observed immutable release DISTRIBUTION plugin copy:**

    RELEASE_MODEL=sonnet
    RELEASE_EFFORT=high
    RELEASE_BYTES=24208
    RELEASE_NEWLINES=LF
    RELEASE_SHA256=a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73

**Observed final comparison/status:**

    PASS: Managed Chairman bytes match selected release copy
    ACTIVE_RUNNING_SESSION_MODEL_NOT_CHECKED
    NO_MODEL_CHANGE_OR_INSTALLATION_PERFORMED
    VRES_165_C2_CURRENT_USER_INSTALLED_CHAIRMAN_READONLY_INSPECTION_COMPLETE

The PowerShell helper enforced UTF-8, 32..524288 byte bounded input, validated frontmatter name Chairman, model sonnet/opus and effort low/medium/high, uniform LF or CRLF, then calculated raw SHA-256 without displaying the agent's body/description text. The two file SHA-256 digests match. These are **operator-observed file snapshots and script assertions**, not native running Claude session telemetry, process trace, OS proof of no network/PG contact, or automatic authorization to change settings. The helper read the active pointer and two files but not credentials or unrelated global configuration. No files were written by this scripted inspection.

**Confidence boundary:** It supports file-level managed installation identity and equality against release distribution; it does NOT prove no session/model/project/managed-host override, actual provider model dispatch, enabled plugin registration, database state, Vres task persistence or unchanged future filesystem state. The copied plugin may be replaced later, so this is a point-in-time snapshot, not ongoing file attestation.

## 3. Independent GitHub historical P2 source SHA-256 reconciliation

ChatGPT independently fetched source commit **82c82430b38f93bd6b9d5c3af3b5de9c1368af9c** file plugins/vres-os/agents/chairman.md: exact P2 original Git blob **6f2239c4dd0d52090d31415c17f763505f93b900**. Its source frontmatter name=chairman, model=sonnet, effort=high and **uniform LF**. Its GitHub-exposed source is **24,206 JavaScript characters / 24,208 UTF-8 bytes**. ChatGPT independently computed SHA-256 using a pure JavaScript SHA-256 implementation validated against known SHA-256 empty and abc vectors:

    SHA256(original P2 LF Chairman file) =
    a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73

**This EXACTLY matches BOTH the operator-reported managed file and release distribution copy digests.** The installed managed release snapshot is therefore byte-consistent with the committed original P2 source file as of the operator's inspection, not merely mutually consistent between two local copies. It does not establish which model a running Claude session selected.

Important source distinctions:
- Original P2 selected installed Chairman Git blob **6f2239c4dd0d52090d31415c17f763505f93b900**, UTF8 source 24208 bytes LF, installed SHA256 **a524...f250b73**.
- NEWER independent C1 source-checkout Chairman Git blob **64cba93d6f69960350a0006b594734288f087ccc**, a DIFFERENT body/release source; its earlier Windows CRLF source preview SHA256 **bc730a7439e8d7d801143afc34bdea1cc41fde2ab23bbf9f88925145b7b66025** and candidate digest **d0cd8821fcddb6ef76344d513e0f33595ab6fc2954db800c5960c1198d64550f** are NOT the installed original P2 release file identity.
- Never treat the newer C1 source checkout's candidate SHA as the candidate for the actual installed old P2 release without re-rendering from the installed baseline bytes.

### Derived offline preview of the P2 RELEASE bytes ONLY — NOT installed

ChatGPT also computed, **purely in memory from the original immutable P2 LF Git file**, the derived SHA-256 if only frontmatter model sonnet -> opus and effort high -> medium were changed, preserving all existing body/other fields/newline style. This uses the exact deterministic materializer contract accepted in Phase A.

    Proposed model=opus, proposed effort=medium
    Derived P2 candidate UTF-8 bytes=24208, newline LF
    DERIVED_P2_CANDIDATE_SHA256=b73e7497454a464f6b6bc1df00f42422696da786a07eb2936ae73ad73abedf54

This candidate hash is **NOT the same** as the newer C1 source-checkout candidate hash, because original P2 and C1 source plugin bodies differ and checkout line endings differ. **No such candidate file was written or applied**; this is only a deterministic read-only planning calculation, NOT a model-change warrant or proof that an installed patch is safe. A real future change would need an independently reviewed actual-target plan, exact current installed byte re-read, signed/trusted proof if applicable to protected F1, current-user explicit consent and verified rollback.

## 4. C2 operational findings and NEXT bounded design-only tranche

**What has now been verified as a point-in-time operator file snapshot:**
- The active Vres product pointer names release **20261022172833-4d82147b**, which was historically reported before.
- The pointer references the current-user managed Vres plugin rather than an unrelated path.
- The installed current-user Chairman file and its selected release distribution original copy both say **sonnet/high**, uniform LF, 24208 raw bytes.
- Both have SHA-256 **a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73**, which independently matches original P2 immutable release-source blob bytes.
- The inspection ended with marker **VRES_165_C2_CURRENT_USER_INSTALLED_CHAIRMAN_READONLY_INSPECTION_COMPLETE**, no model change/install.

**What remains UNVERIFIED and OPEN:**
- Claude running/session effective model, model provider dispatch, project override, plugin registration and native host preference;
- whether an in-place edit would violate release manifest/integrity or F1 protected validator requirements;
- authority to change a globally read Claude agent for the current user, operator consent issuance, model activation and true reversible rollback;
- whether a later running session would pick up changed settings without restart;
- incident PostgreSQL state, Vres task persistence, F2/D2/R0/K0/PA/L-04 and all later stages.

**Next recommended single-user C2 work is DESIGN-ONLY, WITHOUT host reads or writes:** use P2 install topology, recorded actual baseline SHA and source candidate hash to propose a minimal reversible current-user Chairman model switching contract. Keep changes specific: (a) approved target path; (b) fail closed on unexpected installed release/model/hash/owner/line endings; (c) only patch model/effort fields, preserve original bytes and body; (d) stage candidate in a disposable reviewed location, not active plugin; (e) exact current-user affirmative approval and pre/post state, atomic-like backup/apply/restore procedure without silently invalidating installed release manifest; (f) distinguish source-only preview, installed managed-file evidence, and native runtime observed model; (g) ROLLBACK on any failure, restore active release cleanly and verify original sha; (h) preserve original F1/#165 trust boundaries and avoid introducing enterprise/multitenant PKI complexity.

**This is a DESIGN PROPOSAL, NOT CODED, TESTED, REVIEWED, INSTALLED OR AUTHORIZED TO APPLY.** The user previously approved read-only inspection only. Actual mutation of %USERPROFILE%\.claude, an installer update, model switch, provider invocation or altering a release cannot proceed without a NEW explicit affirmative user instruction and independent protected release/authority gates. User may now review the C2 contract or prioritize other personal Vres usability work.

## 5. Permanent holds and historical per-SHA continuity

**LIVE_SCHEMA_048_INCIDENT=OPEN — ABSOLUTELY NO PostgreSQL contact, even SELECT.** Do not call Vres tasks/health/bootstrap/doctor, migrate, open connections or probe any incidental database driver to address VRES_PERSISTENCE_WARNING (Claude instruction staging uncertain) or VRES_REPLY_GUARD_WARNING (pre-reply task verification uncertain). The current file inspection script made no DB calls; that is an observation about commands, not OS/network attestation.

Last operator-observed installed Chairman file is sonnet/high; newer Opus/medium remains UNINSTALLED. Original #165 F1 real independently trusted operator consent/history/protected Fable validator remains OPEN; no agent/user-global installation or runtime model change. No secrets/vault/keyring, global Claude settings/hooks/plugins, provider/Fable, signing, main merge or physical host #169 verification authorized by this read-only audit.

Historical per-SHA:
- CURRENT C1 R1 independently OFFLINE_ACCEPTED source/test SHA **7ac041018d4ec5a06be07318ecce5e140faccd91**, 29 observed individual Windows test PASS/exit0 and one successful manual READ-ONLY SOURCE preview, NOT installed CLI.
- OLD C1 SHA **c545556a4ba9ba48f140e7379da960708a7f3c8d**, independent STATIC_PASS but selected Windows pytest EXIT1, NOT OFFLINE_ACCEPT.
- C0 SHA **e6bd8cb8f92a779da1469efe738709918e9da6df** independent OFFLINE_ACCEPT after 34 individual PASS/exit0 and separate late orphan PowerShell ELSE anomaly C0-PROC-01 NONBLOCKING.
- A1 R2 **9754b190083a0ada757ebee07f2ef5b8f312b58e** accepted 93 PASS/exit0; A1 R1 **1b406c788057f0cb2a8a57578b89110a11b76161** accepted 71 PASS/exit0; B2A R3 **32847410952e9d4620bf7046cbee4a41a7ddc73b** accepted 95 PASS/exit0 and R3-PROC-01.
- B2A R2 and original static REJECT, B2B v0/R1/R2 DESIGN_REVISE and R3 limited DENY-ONLY DESIGN_ACCEPT, earlier Phase A/B1/F2/P2-A1 per-SHA acceptance/rejections and entire V-01..V-42 PERSONAL backlog remain.

## 6. Docs-only transaction and exact new-session resume

This handoff is an ADD and docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md the ONE MODIFY on docs/chatgpt-continuity-20261023 atop previous verified docs HEAD **a8cac09880214b3723f3182de54857454c58f2fe**, tree **3da374e704371eb67722f6c869f43c4782fd13cc**. Require recursive old/new tree diff EXACT TWO docs paths, NO deletions, one-parent GitHub commit and nonforced expected-old-HEAD branch update, then read back new docs and unchanged C1 feature source. No C2 source/test commit, installed-model write, release change, PostgreSQL/credential/provider/globals or live installer.

**NEW SESSION RESUME:** User read-only C2 host inspection DONE, no model change: original P2 active installed release **20261022172833-4d82147b**, managed target current-user plugin verified, installed plugin file and selected immutable release distribution Chairman copy BOTH say sonnet/high LF, 24208 bytes, SHA256 **a524add0c6e2c7429d117410a532307bb158dcfc60733f85e84b7d5a4f250b73**. ChatGPT independently fetched GitHub original P2 commit **82c82430b38f93bd6b9d5c3af3b5de9c1368af9c**, Chairman Git blob **6f2239c4dd0d52090d31415c17f763505f93b900** and recomputed SHA256 = a524...f250b73 over LF UTF-8 24208 bytes. This matches BOTH installed reported hashes. Distinct newer accepted C1 source plugin blob **64cba93d6f69960350a0006b594734288f087ccc**; its CRLF candidate Opus/medium hash **d0cd8821fcddb6ef76344d513e0f33595ab6fc2954db800c5960c1198d64550f** is NOT appropriate for applying to P2 installed body. Pure in-memory simulated P2 model/effort-only candidate digest **b73e7497454a464f6b6bc1df00f42422696da786a07eb2936ae73ad73abedf54** LF/24208 bytes, NOT installed. Final observed marker **VRES_165_C2_CURRENT_USER_INSTALLED_CHAIRMAN_READONLY_INSPECTION_COMPLETE**, plus ACTIVE_RUNNING_SESSION_MODEL_NOT_CHECKED, NO_MODEL_CHANGE_OR_INSTALLATION_PERFORMED. Current C1 R1 source independently accepted at **7ac041018d4ec5a06be07318ecce5e140faccd91**, tree 0ef7af10335865231f4350e2dbb7ba561538ee00, C1 tests 29 individual PASS/exit0 and one source-preview PASS; no new source change. **NEXT C2 reversible user-confirmed model switching DESIGN ONLY, not apply; actual mutation needs new explicit user authorization.** F1/#165 remains OPEN, last running Claude model UNVERIFIED, LIVE_SCHEMA_048 no PostgreSQL even SELECT, D2/F2/R0/K0/PA/L-04 and credentials/provider/global Claude/installer/main holds; two Vres persistence warnings unresolved. Full earlier per-SHA verdict ledger and V-01..V-42 backlog preserved.
