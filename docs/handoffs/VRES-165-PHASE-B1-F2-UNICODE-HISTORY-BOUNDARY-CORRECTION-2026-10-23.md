# Vres-OS #165 — B1 F2 Unicode history-size correction (candidate, not tested)

Date: 2026-10-23, Europe/Athens.
Repository: vosser24/Vres-OS.
Current branch for ChatGPT source development: feature/165-chairman-policy-foundation-20261023.
Authoritative documentation branch: docs/chatgpt-continuity-20261023.
Decision: **source correction COMMITTED; independent exact-commit Windows tests NOT_RUN.**
No authorization to activate/install Opus, migrate/contact PostgreSQL, access credentials, merge branches or change global Claude.

## 0. New exact commit and accepted immutable baseline

- **CURRENT source HEAD: b77e0eef07976877e7f198a00484f5d13ce36889**.
- **IMMEDIATE parent: f8237bb301dec160f33cab524727e6a0ec79b2c0**. This parent is independently ACCEPTED for Phase B1 OFFLINE (Claude Windows: 99 selected tests passed, exit 0); it was NOT amended or rewritten.
- New Git tree: edfc69d29764a8a9e6ccb2120cf0a29ac6b109ff.
- GitHub compare parent..current: one new commit, zero behind; ONLY two MODIFIED paths:
  - src/vres_os/chairman_policy_history.py (+9/-2).
  - tests/test_chairman_policy_history.py (+35/-1).
- Reviewed Phase A R2 ancestor at 11f2f8689308dfe43e482bca73aa57bb6467c788 was independently ACCEPTED for 53/53 Windows CRLF offline tests. Phase A R1 9c919271 was independently REJECTED and remains evidence.
- P2-A1 database guard R4 source 3ba41d5ae6b8f2c2abd93d27f82cce0755878237 independently ACCEPTED offline (183/183); prior R1–R3 rejections remain evidence.
- GitHub feature ref and new source/parent/tree/two-path diff were verified by read-back in this turn; no CI checks were available at the new source SHA.
- Installed Vres remains last reported 20261022172833-4d82147b from original P2 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c. New source is NOT installed or physically model-tested. Main remains last observed 9a8acc5d464b96432a93cb95daa9581412fb07ee.

## 1. Why this change is strictly F2 only

The independent Phase B1 ACCEPT reviewer identified:
- F1 LOW: prefix-truncated or forked candidate histories may be internally valid; only a trusted external record of the expected head/count/history digest can distinguish them. Candidate hashes alone are never trusted approval.
- F2 LOW: the old model allowed 128 proposals and each printable rationale to be 512 UTF-8 bytes, but capped the whole serialized history read at 192 KiB. For example, 128 maximum-length Greek rationales can produce about 228 KB of canonical JSON due to ensure_ascii escaping; a valid in-memory history would serialize but fail to deserialize.

A prior broad source-write attempt that mixed F1 expected identity comparison and F2 size repair was **blocked by tool safety checks**, and produced NO source commit. The accepted B1 branch was checked and retained. The user subsequently explicitly requested continuing development. This new commit is an INDEPENDENT, materially narrower F2-only correction that was permitted and published; it does not retry the blocked F1 compare/authority implementation, redefine trusted authority or bypass the earlier tool block.

The F2 correction:
1. Increases canonical history-document byte limit from 192 KiB to 256 KiB. A legal 512-byte Unicode rationale expands to at most approximately 1536 ASCII JSON bytes; 128 entries and their fixed metadata fit within that capped budget.
2. Applies the same bound to both to_document (fails closed if a malformed/mutated object exceeds it) and from_document (existing strict parse bound).
3. Adds a deterministic offline 128-entry Greek-rationale serialization/reload test, verifies byte-preserving canonical round-trip and candidates_only state, checks refusal of attempted 129th proposal, and updates the oversize-document test to 256 KiB plus one byte.
4. Does not modify authority, approval, history chain semantics, model routing or any installed artifact. It does not change any source path outside the two existing B1 module/test files.

This is a source implementation claim pending independent local verification, NOT proof of Windows PASS.

## 2. Pending independent Windows review contract

One NEW detached review worktree (do not overwrite original accepted B1 checkout):

C:\Projects\Vres-ChatGPT-Review-165B1-F2-20261023

- Expected new HEAD: **b77e0eef07976877e7f198a00484f5d13ce36889**.
- Expected parent: **f8237bb301dec160f33cab524727e6a0ec79b2c0**.
- Allowed parent-to-HEAD changed paths exactly:
  src/vres_os/chairman_policy_history.py,
  tests/test_chairman_policy_history.py.
- Anchor the fetch using original clean personal P2 worktree C:\Projects\Vres-P2F-Postinstall-Hardening-20261022, at original 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c. Do not change its branch or checkout.
- Guard full 40-character SHAs, official origin URL, exact remote/fetched ref, immediate parent, clean detached review status and git diff --check. Use an entire single PowerShell scriptblock that aborts on any STOP/native Git error BEFORE printing a READY marker. Historical 38-character SHA typo and false-success incident were resolved with this procedure.
- Start Claude independent evaluator in supported safe mode only after correct local review worktree. Do not type start vres or allow Vres project hooks, MCP or automatic database work.
- Claude MUST inspect tests/conftest.py isolation: disposable app-data and LocalAppData, protected live roots, psycopg connection tripwires, inherited DB/GIT env cleanup, keyring/secret risk, child-process restrictions. On unsafe preflight STOP/BLOCKED.
- One authorized offline targeted command (after preflight, not run by ChatGPT):

    py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_policy_history.py tests/test_chairman_policy_materialization.py

- Verify previous 99/99 B1 history/materialization assertions still work at new SHA; test valid maximum 128 with 512 UTF-8 byte Greek reasons; verify 192 KiB smaller limit no longer blocks, canonical bytes reload within <=256KiB, malformed or 256KiB+1 payloads fail and attempt to append 129 is refused. Ensure no new active/approved/installed fields, no runtime policy write, source import side effects, credential/network/PostgreSQL calls or weakening of protected worker pins.
- Reviewer returns exact Git SHAs, diff/cleanliness, command, exit code, collected/passed/failed/error/skipped/deselected counts, independent findings and ACCEPT/REJECT/BLOCKED limited to F2 offline source scope. Do not claim accepted if only source readback succeeds.

## 3. F1 external history authority remains OPEN — separate future tranche

Never imply that an expected hash/count supplied by an arbitrary caller authenticates operator approval, or that SHA-256 prevents an attacker rewriting an entire history document and manifest. A future dedicated authority boundary must obtain the expected chain head from actual trusted user-event evidence and protected Fable validation, with a distinct review/commit and no silent activation. B1 source remains an inert candidate-only history. The earlier broad source-tool safety block is preserved as an historical event, not reframed as a successful F1 fix.

Additional B1 reviewer INFO F3–F8: standalone unverified proposals, canonical-versus-raw digest meaning, unauthenticated rationale, Python low-level frozen-object tampering/untrusted pickle, Unicode semantics and test-coverage opportunities. Previous Phase A I1–I5 and P2-A1 R4-1–R4-5 remain in their accepted evidence handoffs.

## 4. All runtime and release holds unchanged

LIVE_SCHEMA_048_INCIDENT=OPEN. POSTGRESQL_SERVICE=STOPPED at last operator report. NO DB contact, even read-only SELECT, migrations, setup, bootstrap, selftest, service start, installer activation, real Windows vault/credentials, model provider calls, global Claude mutations or native signing/trust.
D2 OPEN; F2 quarantined; R0 NOT_RUN; K0-T1 blocked; native trust not approved; L-04 OPEN; positive trust issuance disabled; PA-01 through PA-08 incomplete. No PR/merge/main push or personal release update was performed.
The #165/V-07 issue remains OPEN/PARTIAL, requested opus/medium remains candidate only, installed Chairman remains sonnet/high. All original V-01..V-42 development features remain active BACKLOG only.

## 5. New ChatGPT session resume prompt

RESUME Vres-OS ChatGPT-led development from CURRENT GitHub HEAD docs/chatgpt-continuity-20261023. Read docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md, then THIS #165 B1 F2 256-KiB Unicode history bound correction handoff, then B1 independent ACCEPT and Phase A R2 ACCEPT. Exact NEW unreviewed feature HEAD is b77e0eef07976877e7f198a00484f5d13ce36889 (parent accepted B1 f8237bb301dec160f33cab524727e6a0ec79b2c0) on feature/165-chairman-policy-foundation-20261023. Exactly two B1 history source/test files changed. NEXT: one guarded Windows detached review worktree C:\Projects\Vres-ChatGPT-Review-165B1-F2-20261023, followed by one isolated Claude test of two offline pytest modules; no new result yet. Preserve prior B1 99/99 ACCEPT, Phase A R2 53/53 ACCEPT, Phase A R1 REJECT, P2-A1 R4 183/183 ACCEPT. F1 externally anchored truncation/fork approval still OPEN and earlier combined F1/F2 source tool attempt was BLOCKED, not committed. All schema-048, K0, credential, installed release, trust/PA blocks remain. ChatGPT commits source and separate docs handoff after each substantive turn; Claude independently evaluates; user performs bounded local Windows commands.
