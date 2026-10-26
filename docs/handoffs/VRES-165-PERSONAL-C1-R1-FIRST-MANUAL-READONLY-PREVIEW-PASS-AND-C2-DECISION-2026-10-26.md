# Vres-OS #165 — PERSONAL C1 R1 first real Windows READ-ONLY Chairman preview PASS; C2 model-change decision remains separate

**Date:** 2026-10-26, Europe/Athens.
**Repository:** vosser24/Vres-OS.
**Canonical docs branch:** docs/chatgpt-continuity-20261023.
**Feature source branch:** feature/165-chairman-policy-foundation-20261023.
**New operational milestone:** **OPERATOR_MANUAL_C1_R1_READONLY_PREVIEW_PASS** on the ALREADY INDEPENDENTLY OFFLINE_ACCEPTED R1 source and test boundary.
**Not achieved / not authorized:** actual current installed Chairman model measurement; Opus/medium installation or provider invocation; explicit permission to apply a change; protected F1/#165 validation; rollback of an actual change; production CLI installation; Vres task/database persistence.
**Single-user PERSONAL:** make usable and reversible choices, not commercial enterprise certification or public trust ceremonies.

## 0. Read-first and accepted source boundary

Read docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md (CURRENT), then THIS manual preview milestone, then:
1. docs/handoffs/VRES-165-PERSONAL-C1-R1-INDEPENDENT-OFFLINE-ACCEPT-AND-READONLY-MANUAL-PREVIEW-NEXT-2026-10-26.md — already independently STATIC_PASS + Windows 29-case PASS/exit0 + Claude report-only OFFLINE_ACCEPT at exact C1 R1 source.
2. docs/handoffs/VRES-165-PERSONAL-C1-R1-WINDOWS-29-PASS-INDEPENDENT-OFFLINE-EVAL-PENDING-2026-10-26.md — historical original complete 220-line Windows test transcript, including [oversized-template], restored process PYTHONPATH, post-run clean, process AppData fixture.
3. docs/handoffs/VRES-165-PERSONAL-C1-R1-WINDOWS-ENV-LIMIT-FAILURE-AND-BOUNDED-PYTEST-ID-SOURCE-2026-10-26.md — OLD C1 Windows selected pytest EXIT1 at prior SHA; corrected R1 uses a short pytest ID without weakening the 524289-byte oversized negative test.
4. docs/handoffs/VRES-165-PERSONAL-C0-INDEPENDENT-OFFLINE-ACCEPT-PROCEDURAL-ANOMALY-AND-NEXT-PHASE-2026-10-26.md — accepted C0 in-memory read-only preview parent; older C0-PROC-01 PowerShell orphan ELSE after successful test was independently nonblocking.
5. Prior accepted A1 R2/A1 R1/B2A R3 and historical exact-SHA accept/reject/hold ledger, original V-01..V-42 PERSONAL Vres roadmap.

The CURRENT source branch remains **7ac041018d4ec5a06be07318ecce5e140faccd91**, Git tree **0ef7af10335865231f4350e2dbb7ba561538ee00**. The last source commit modifies ONLY tests/test_chairman_selection_cli.py blob **e69b09cfca0878819096f8a6d211fbec0d7b3de1** relative to old failed C1 parent **c545556a4ba9ba48f140e7379da960708a7f3c8d**. Production C1 module **src/vres_os/chairman_selection_cli.py** blob **6fd0ddcd2b82fca4a48f6a790fee3d0e6ae657d1** is unchanged since R1 acceptance. Accepted C0 source blob **1fb133e5d1b79bc4d6f6e305f5c9b03f6c752658**, Phase A materializer **36e62d6a2712ac305fd4070bac658b94d61d155e**, source plugin template **64cba93d6f69960350a0006b594734288f087ccc**, protected conftest **1c33bb206dbf42691a6af9a709514bf3cc9994af** and pyproject **b2d5e30d10d7be0613e90bf3ed1e346be5678969** were not edited.

**Operator's Windows source checkout:** C:\Projects\Vres-ChatGPT-Review-165C1-R1-20261026, previously verified as detached clean at exact source SHA. The earlier OLD failed C1 worktree stays preserved.

## 1. Exact reported Windows manual CLI demo — NO INSTALL/ACTIVATION

The user pasted this successful short console transcript:

    === C1 R1 PERSONAL READ-ONLY PREVIEW ===
    PASS: CLI
    PASS: Chairman template
    PASS: Accepted C0
    === PROPOSED CHAIRMAN CONFIGURATION ===
    Source checkout only; not installed state
    Vres Chairman - PERSONAL READ-ONLY PREVIEW
    Reported baseline (NOT live-verified): sonnet/high (policy v1)
    Proposed candidate (NOT installed): opus/medium (policy v1)
    Differences:
      - Model: sonnet -> opus
      - Effort: high -> medium
    Supplied template SHA-256: bc730a7439e8d7d801143afc34bdea1cc41fde2ab23bbf9f88925145b7b66025
    Rendered candidate SHA-256: d0cd8821fcddb6ef76344d513e0f33595ab6fc2954db800c5960c1198d64550f
    The baseline is caller-supplied, not a measurement of the installed model.
    No approval, settings change, model activation or installation was performed.
    PYTHONPATH_RESTORED
    PREVIEW_EXIT_CODE=0
    POST_PREVIEW_WORKTREE_CLEAN
    VRES_165_C1_R1_READONLY_PREVIEW_DEMO_COMPLETE
    PS C:\Users\User>

The previously supplied PowerShell operator command guarded the R1 exact Git HEAD and tree, checked the C1 source/template/accepted C0 blob identities and original clean worktree, then:
- Push-Location into the exact accepted R1 checkout, temporarily set process PYTHONPATH to that checkout's src.
- Run exactly one **py -3.12 -B -m vres_os.chairman_selection_cli** with explicit --source-root equal to the accepted R1 checkout, --reported-model sonnet, --reported-effort high, --proposed-model opus, --proposed-effort medium. This is the stand-alone pure preview entrypoint, NOT existing vres-os.cli or registered global vres script.
- Restore original process PYTHONPATH in finally, check restored value equals previous, check post-preview tracked/untracked worktree clean and exit0. No existing Chairman agent file or global Claude settings were written.
- Its stdout is a report, NOT an apply operation. No explicit operator consent or actual system change was issued.

The demo result is **operator-reported Windows source-checkout preview PASS**, not independent local host instrumentation, a signed release, an installed-model verification, or a new automated test suite. No new independent static/test review is necessary merely to archive this user-visible smoke/demo after C1 R1 OFFLINE_ACCEPT.

## 2. Independently recomputed hashes — exact local CRLF bytes matter

ChatGPT separately read the official GitHub source template blob **64cba93d6f69960350a0006b594734288f087ccc** at accepted C1 R1 commit and the exact accepted Phase A deterministic renderer, then computed SHA-256 in a pure tool-side JavaScript implementation independently checked against standard SHA-256 vectors (empty string and "abc").

The GitHub source template contains uniform LF bytes, **24,455 UTF-8 bytes / 112 LF separators**, while Git for Windows' source checkout can produce **uniform CRLF**, adding 112 bytes: **24,567 UTF-8 bytes**. The renderer permits either uniformly and preserves body, line endings and all fields except explicit model/effort.

Independent SHA-256 computations:

| Materialization and newline format | SHA-256 |
| --- | --- |
| Official GitHub blob template, LF | 767433be2ad174f8e28bd9741ffb39adf5d544f5927c7451f71a2f29bcb63d58 |
| Pure candidate Sonnet/high -> Opus/medium, LF | 7b306ae93b4f185f9eebcbfbba7c2d239435400e6e68fa4334924b71071e63d0 |
| **Source-checkout template bytes, Windows CRLF** | **bc730a7439e8d7d801143afc34bdea1cc41fde2ab23bbf9f88925145b7b66025** |
| **Read-only candidate with Opus/medium frontmatter, Windows CRLF** | **d0cd8821fcddb6ef76344d513e0f33595ab6fc2954db800c5960c1198d64550f** |

**BOTH Windows CRLF computed digests EXACTLY MATCH the user's demo output.** This independently verifies the claimed source/candidate digest relationship against shipped source bytes and accepted deterministic frontmatter rendering. It is consistent with a Windows CRLF working-tree checkout; it does NOT independently open/measure the user's physical filesystem or installed active model.

No bytes were signed, stored as credentials, uploaded to a provider, rendered as installed configuration, or written back to the source. The user-specific actual live model remains unverified by the CLI's own explicit contract.

## 3. Next practical C2 decision — separate design and separate authorization

The last accepted PERSONAL feature now does something useful: shows a human-readable read-only source-template comparison. **Do not repeat C0/C1 tests, build additional pytest ceremonies or claim C1 shipped**. The next possible development stage (C2) is an explicitly reversible and operator-confirmed personal Chairman configuration workflow, which requires a distinct real-world change boundary.

**Recommended C2 planning / design tranche only, not yet authorized to run/implement/install:**
1. Resolve **actual installed-target read-only provenance** and exact target path without contacting the incident PostgreSQL database or querying vault/credentials. The current source checkout is NOT the live installed model; do not infer live state from C1 preview. Any real installed configuration inspection is a separately user-approved narrow read.
2. Distinguish SAFE source preview from **protected local installed target diff**; display actual currently installed model/effort if independently confirmed. Never let caller-supplied model baseline masquerade as host-observed fact. Preserve original exact installed agent bytes/line endings and a deterministic read-only rollback preview.
3. Before any apply, design **explicit affirmative current-user confirmation**, exact candidate bytes/hash, a reversible backup/restore method scoped to the current user and exact installed file; no general provider/DB credentials or global config changes.
4. Implementation and testing of positive apply/rollback must be a separately committed C2 source tranche, independently STATIC-reviewed then locally offline-tested. Actually applying to an installed Chairman/global Claude environment requires its OWN fresh user authorization and pre/post evidence, with rollback read-back; **no automatic switch** merely because C1 preview ran.
5. Respect original F1/#165 authenticated operator consent, protected authority/independent provenance and validator OPEN. Prefer a small PERSONAL approval boundary over enterprise IAM/certificate apparatus, but do not bypass applicable existing protected Vres release/authority rules.
6. Keep V-01..V-42 future usability including legacy-project onboarding, procedural memory, credential-handle reuse and Visual Studio, no false program completeness from C1.

**No C2 source changes, tests, installed-target inspection or model changes have occurred** as a result of this demo or this documentation checkpoint. If proceeding, the user should explicitly choose whether to FIRST inspect installed source read-only, design apply/rollback on paper, or defer activation.

## 4. Hard holds and historical scope

**LIVE_SCHEMA_048_INCIDENT=OPEN: absolutely NO PostgreSQL contact, even SELECT.** D2 OPEN, F2 quarantined, R0 NOT_RUN, K0-T1 blocked, L-04 OPEN, PA-01..08 incomplete. No Vres task/bootstrap/database query despite both VRES_PERSISTENCE_WARNING (Claude instruction not safely staged) and VRES_REPLY_GUARD_WARNING (pre-reply task gate unverified).

Last operator-reported installed Chairman still **Sonnet/high**, proposed Opus/medium **UNINSTALLED**; the C1 CLI never measured actual installed state or issued permissions. Original F1/#165 operator-event and protected historical validator authority remains OPEN. No real credentials/vault/keyring, global Claude settings/hooks/plugins, protected Fable/provider, signing, installer, native model switch, physical #169 installed-model observation, PR/main merge or release are authorized.

Historical independently accepted source/test boundaries:
- C1 R1 7ac041018d4ec5a06be07318ecce5e140faccd91 independently OFFLINE_ACCEPT: 29 selected Windows PASS/exit0 plus successful new manual read-only preview.
- OLD C1 c545556a4ba9ba48f140e7379da960708a7f3c8d STATIC_PASS but Windows pytest EXIT1, NOT accepted.
- C0 e6bd8cb8f92a779da1469efe738709918e9da6df independently OFFLINE_ACCEPT 34 individual Windows PASS/exit0, C0-PROC-01 late PowerShell orphan ELSE independently nonblocking.
- A1 R2 9754b190083a0ada757ebee07f2ef5b8f312b58e independently OFFLINE_ACCEPT 93 observed individual PASS/exit0.
- A1 R1 1b406c788057f0cb2a8a57578b89110a11b76161 OFFLINE_ACCEPT 71 PASS/exit0.
- B2A R3 32847410952e9d4620bf7046cbee4a41a7ddc73b independently accepted 95 PASS/exit0 and separate historical R3-PROC-01 extra version probe.
- Earlier B2A R2/initial STATIC_REJECT, older B2B v0/R1/R2 DESIGN_REVISE and R3 DESIGN_ACCEPT strictly DENY-ONLY, old Phase A/B1/F2/P2-A1 accept/reject/holds by exact SHA and original V-01..V-42 capability plan remain.

## 5. Documentation-only seal and exact next-session resume

Add THIS manual-preview handoff and update ONLY docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md on canonical documentation branch from old verified HEAD **8cfb1f25ee24537dcd9fb59404a692aacdfb28bc**, tree **a9331c6e224598bd1563322eae2ede2dc46a097d**. Require recursive old/new Git tree diff EXACT two docs paths, no deletions, single-parent unsigned GitHub docs commit, expected-old nonforced ref update, then read back docs and unchanged feature source SHA **7ac041018d4ec5a06be07318ecce5e140faccd91**. No source branch/main/installed model/credential/DB/provider changes.

**NEW-SESSION RESUME:** C1 R1 accepted source SHA **7ac041018d4ec5a06be07318ecce5e140faccd91**, tree **0ef7af10335865231f4350e2dbb7ba561538ee00**, old failed C1 parent **c545556a4ba9ba48f140e7379da960708a7f3c8d**, one corrected test blob **e69b09cfca0878819096f8a6d211fbec0d7b3de1** and unchanged CLI blob **6fd0ddcd2b82fca4a48f6a790fee3d0e6ae657d1**, C0 and Phase A/plugin/conftest/pyproject unchanged. Independent static PASS and report-only OFFLINE_ACCEPT after 29 individual Windows PASS incl oversized-template/exit0/appdata protected fence unexpected0/integration False/scoped PYTHONPATH restored/post HEAD/tree/worktree clean. NEW user executed one actual PERSONAL read-only source preview from existing R1 Windows checkout: source SHA-256 **bc730a7439e8d7d801143afc34bdea1cc41fde2ab23bbf9f88925145b7b66025**, candidate SHA-256 **d0cd8821fcddb6ef76344d513e0f33595ab6fc2954db800c5960c1198d64550f**, both independently recomputed from source-blob CRLF and deterministic frontmatter renderer. Output Sonnet/high reported NOT live-verified -> Opus/medium proposed NOT installed, differences model/effort; PREVIEW_EXIT_CODE=0, PYTHONPATH_RESTORED, POST_PREVIEW_WORKTREE_CLEAN and **VRES_165_C1_R1_READONLY_PREVIEW_DEMO_COMPLETE**. No installed model verified/switched or global config written, C2 NOT STARTED; original F1/#165 OPEN. NEXT user decision: separately authorize C2 read-only installed-target discovery or C2 design for reversible apply, NOT automatic apply; maintain LIVE_SCHEMA_048 NO PostgreSQL even SELECT and original personal credentials/provider/global Claude/installer/host/main holds, V-01..V-42 roadmap and old per-SHA verdicts.
