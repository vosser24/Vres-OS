# Vres-OS #165 — B2B-0 independent DESIGN REVIEW operator runbook

Date: 2026-10-23, Europe/Athens.
Review category: STATIC DESIGN / DOCS ONLY / NO EXECUTION.
Repository: vosser24/Vres-OS.
Canonical docs branch: docs/chatgpt-continuity-20261023.
**B2B design status: DRAFT, independent review NOT_RUN.**
Source feature remains independently accepted offline at 32847410952e9d4620bf7046cbee4a41a7ddc73b; no source or installed release changed through this document.

## Exact review target

Full design: docs/architecture/VRES-165-B2B-TRUSTED-CHAIRMAN-AUTHORITY-CONTRACT-DRAFT-2026-10-23.md.
Draft Git blob SHA (unchanged): 851f5323888bfd3043ba992abc8096834ee356d0.
Supporting read-only handoff: docs/handoffs/VRES-165-B2B-DESIGN-FIRST-DECISION-CHECKPOINT-2026-10-23.md.
This runbook plus docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md is an operator guide, NOT authority or production evidence.

## Safe step-by-step Windows procedure

1. Exit any open Claude Code session with /exit. Use Windows PowerShell, never 'start vres'.
2. In ONE fail-stop PowerShell scriptblock, verify the original anchored clean P2 worktree C:\Projects\Vres-P2F-Postinstall-Hardening-20261022 at commit 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c, exact official GitHub origin, remote docs branch HEAD, full 40-hex SHA and parent.
3. Fetch docs/chatgpt-continuity-20261023 only; create a NEW detached checkout at C:\Projects\Vres-ChatGPT-Review-165B2B-Design-20261023. Fail if destination exists. Do not mutate source worktrees or previous acceptance folders.
4. Guard the expected two-file docs change relative to this runbook commit's parent: newly added this operator runbook and modified continuity index. Confirm git diff --check and clean review; confirm draft blob equals 851f5323888bfd3043ba992abc8096834ee356d0. Print VRES_165_B2B_DESIGN_REVIEW_READY only on complete success.
5. Run a SECOND guarded PowerShell block in the same review folder, repeating full HEAD/parent/blob/diff/cleanliness checks; launch Claude Code using '--safe-mode --permission-mode default --tools "Read,Glob,Grep" --disallowedTools "mcp__*"'. Claude must have no Bash, Python, pytest, MCP, write, native trust, DB, credential, installer, network or source-edit privileges. If safe-mode rejects options or hooks start, STOP and do not fall back.
6. Paste the independent static design-review prompt; Claude uses only Read, Glob and Grep to inspect this design draft and supporting docs. It must not run Git or claim independently checked SHA after the PowerShell gate; source identity is operator-verified.
7. Collect Claude's complete sanitized review: source and Git evidence limitations, trust-boundary findings with severity/file sections, missing invariants and negative tests, what must be revised, and exactly one DESIGN_ACCEPT, DESIGN_REVISE or DESIGN_BLOCKED verdict. Include VRES_165_B2B_DESIGN_REVIEW_COMPLETE and explicitly state TESTS_NOT_RUN, NO_AUTHORITY_ISSUED. Return report to ChatGPT.
8. After report, ChatGPT authors a separate docs-only corrective commit if design is revised. Only after an accepted design may a separately scoped B2B-1 offline deny-only implementation be considered; no positive trust/provider/integration actions without explicit authority.

## Independent reviewer requirements and threat model

Review actor identity and current-user/session binding, explicit consent versus chat text/rationale; trusted anchoring of head/count/canonical history SHA/latest proposal SHA independent from mutable candidate file; monotonic epochs and CAS against replay/fork/truncation/rollback and concurrent writers; protected Fable validation evidence bound to exact operator event, policy, source/template/release, target and pins; state machine proposed/evaluated/authorized/installed/host-observed; missing/expired/conflicting evidence fails closed; no silent model downgrade or telemetry policy auto-promotion. Test whether an attacker controlling both a proposal and an expected SHA could ever authorize a change (it MUST NOT). Scrutinize positive trust issuance boundaries: this design must not fabricate signatures, provider identity, protected validator approval or user event. Demand concrete fixes and test cases, not an invented positive PASS.

The draft currently does NOT implement authentication. The accepted B2A comparator is a pure equality primitive that returns None on match. F1 trusted external authority remains OPEN and issue #165 is OPEN/PARTIAL.

## STOP and unchanged production boundaries

LIVE_SCHEMA_048_INCIDENT=OPEN; PostgreSQL last observed STOPPED. Never connect, even read-only SELECT, or start/migrate Vres. No Windows Credential Locker or actual secret, global Claude setting/plugin/hook mutation, signing/native trust, installed release change, provider calls, host tests, force push, PR/main merge or model activation. D2 OPEN, F2 quarantined, R0 NOT_RUN, K0-T1 blocked, L-04 OPEN, positive trust issuance disabled, PA-01..PA-08 incomplete.

Installed user-scoped Windows Vres release 20261022172833-4d82147b remains sourced from original P2 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c; Chairman Sonnet/high still installed, Opus/medium candidate-only. Product main last observed 9a8acc5d464b96432a93cb95daa9581412fb07ee.

Earlier offline accepted evidence retained: B2A R3 32847410952e9d4620bf7046cbee4a41a7ddc73b, 95 PASS lines, exit 0 and procedural deviation R3-PROC-01; B2A R2 060756b02786c146b87a5262ba2b3b2cc6bf2784 independent REJECT, initial B2A c01152e374c4e7e0ae8e0a01eab5148cdf71e84e STATIC_REVIEW_REJECT. Also F2 follow-up 36a41b6151b7520329ccc0ada0ff827d836ec579 3/3 PASS, F2 b77e0eef07976877e7f198a00484f5d13ce36889 101/101, B1 f8237bb301dec160f33cab524727e6a0ec79b2c0 99/99, Phase A R2 11f2f8689308dfe43e482bca73aa57bb6467c788 53/53, P2-A1 R4 3ba41d5ae6b8f2c2abd93d27f82cce0755878237 183/183. Retain all earlier rejection evidence.

## New-session resume

Read docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md, then this B2B-0 operator protocol and the trusted authority architecture draft. Only a DOCS-ONLY design review is next, not a source/test/release operation. The architecture draft's SHA is 851f5323888bfd3043ba992abc8096834ee356d0 and its independent review remains NOT_RUN. The new isolated Windows design review checkout may be prepared by following the exact one-scriptblock guard, then Claude may run only Read/Glob/Grep; no Bash, pytest, DB or vault. Operator provides full output; Claude report follows. After each substantive response, commit detailed docs handoff and current index with SHA read-back. ChatGPT develops/commits, Claude independent evaluator, Windows operator approves consequential actions.
