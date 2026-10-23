# Vres-OS — #165 Phase A operator SHA transcription incident and guarded resume

**Date:** 2026-10-23, Europe/Athens.
**Status:** Operator worktree creation FAILED; Claude independent #165 Phase A test NOT_RUN.
**Owner:** ChatGPT primary developer and author of the incorrect operator command. Operator supplied full Windows PowerShell log.
**Canonical continuity branch:** docs/chatgpt-continuity-20261023.
**This is a documentation-only correction and does not supersede the source feature commit or the P2-A1 R4 ACCEPT.**

## 1. Root cause and exact correction

An earlier ChatGPT PowerShell review-worktree instruction copied a SHORTENED and INVALID 38-character source SHA. It omitted two hex characters ("af") after the substring "c62ab":

- INCORRECT SHA used in the displayed operator script and apparent READY printout: 9c919271ba63fb979478c62ab6c2c3d2679ae7 (38 hex characters; not a commit).
- CORRECT source SHA, independently re-read from the GitHub feature branch: 9c919271ba63fb979478c62abaf6c2c3d2679ae7 (40 hex characters).
- Feature branch: feature/165-chairman-policy-foundation-20261023.
- Correct feature parent: 3ba41d5ae6b8f2c2abd93d27f82cce0755878237, the accepted offline P2-A1 R4 source.
- Source changed-path allowlist remains exactly: plugins/vres-os/agents/chairman.md; src/vres_os/chairman_policy.py; tests/test_chairman_policy_materialization.py.

The operator's previous Windows Git commands behaved predictably:
1. Exact remote SHA preflight printed STOP: Remote source mismatch because it compared the correct remote 40-character SHA with the incorrectly transcribed 38-character string. This stop condition was legitimate.
2. The operator pasted the remaining commands sequentially in an interactive PowerShell window rather than as a single stop-on-error script. The subsequent git fetch SUCCEEDED and created/updated origin/feature/165-chairman-policy-foundation-20261023 (read-only to remote; only local git metadata changed).
3. git worktree add --detach targeting the 38-character string FAILED with fatal: invalid reference. No review directory was created by that attempt.
4. Further git commands failed because the review directory was absent. Despite those failures, unconditional Write-Host statements printed VRES_165_PHASE_A_REVIEW_READY and displayed the invalid SHA.
5. Therefore the READY marker is a FALSE SUCCESS, not evidence of a verified worktree. No Claude test is authorized on that absent path, and #165 remains NOT_RUN.

This was a ChatGPT instruction-generation defect, NOT a defect in the GitHub feature branch and NOT an operator test failure. Preserve the original failure instead of erasing it.

## 2. New operator-shell rule (mandatory)

For all subsequent Windows source-sync/review scripts:
- Use exactly verified full-length Git commit SHAs from the current GitHub ref, with a 40-hex format check before any worktree operation.
- Enclose the entire PowerShell operation in ONE top-level script block (for example ampersand + opening brace on the first line and matching close on the last). A throw aborts that script block; interactive PowerShell can otherwise continue with separately pasted statements.
- Check LASTEXITCODE immediately after EVERY native Git operation before consuming output or making the next action.
- Preflight branch, remote and parent identity, clean source worktree, absent target directory and actual fetched remote-tracking ref before creating the review directory.
- Print a final READY marker ONLY after actual reviewed-worktree HEAD, parent, changed-file allowlist, clean git status and diff --check all pass.
- Do not infer success from a printed marker when preceding STOP/fatal/error lines exist. No use of $? or ErrorActionPreference alone substitutes for checking native Git exit codes.
- Never reset/clean/force-push, overwrite an existing review folder, modify original personal worktree, start Vres, access the held database or install any release as a workaround.

## 3. Next action — exact 40-byte SHA and one bounded evaluation

A new Windows detached review worktree is still intended at:

C:\Projects\Vres-ChatGPT-Review-165A-20261023

Review branch: feature/165-chairman-policy-foundation-20261023.
Correct HEAD: 9c919271ba63fb979478c62abaf6c2c3d2679ae7.
Expected parent: 3ba41d5ae6b8f2c2abd93d27f82cce0755878237.
Original published local personal baseline: 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c.

The GitHub feature HEAD is unchanged. Reuse the existing original personal source worktree as the read-only worktree creation anchor, but DO NOT change its checkout or installed Vres. The previous successful fetch is harmless; a repeated guarded fetch is permitted only after the exact remote ref check. If the target directory actually exists, STOP for inspection rather than clobbering it.

After a TRUE review-ready result, the Windows operator may start Claude Code using the previously bounded safe-mode/no-MCP evaluator launch. The only proposed offline pytest command remains:

    py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_policy_materialization.py tests/test_chairman_continuity_contract.py tests/test_plugin_contract.py

The test run must be preceded by isolation preflight; no live DB, Windows vault, Vres activation, installed release or model API calls. Claude is an independent evaluator and does not own source edits. Do not claim #165 Phase A ACCEPT before exact-source independent evidence is returned.

## 4. Inherited program state

- P2-A1 R4 offline ACCEPT remains valid at 3ba41d5ae6b8f2c2abd93d27f82cce0755878237, 183/183 selected offline tests PASS; R1-R3 earlier REJECT preserved.
- #165 Phase A source candidate remains at 9c919271ba63fb979478c62abaf6c2c3d2679ae7 and #165 remains OPEN/PARTIAL, not installed. The static shipped Chairman frontmatter remains Sonnet/high; Opus/medium is only a requested policy candidate from the new pure offline module.
- GitHub main remains last observed at 9a8acc5d464b96432a93cb95daa9581412fb07ee, and published P2 personal source base at 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c.
- Windows installed release remains 20261022172833-4d82147b from P2 at the last accepted report; no source deployment took place.
- LIVE_SCHEMA_048_INCIDENT=OPEN; D2=OPEN; F2=QUARANTINED; R0_DB_READ=NOT_RUN; NATIVE_TRUST_APPROVAL=NOT_GRANTED; K0_T1=BLOCKED; L-04=OPEN; POSITIVE_PRODUCTION_TRUST_ISSUANCE=DISABLED.
- PostgreSQL service last known STOPPED; incident contact forbidden even for read-only SELECT, no unsafe source/model activation or credential access.
- All PA-01 through PA-08 current-release physical cases remain NOT_COMPLETE.
- All original V-01..V-42 development ambitions remain active backlog, without granting runtime permissions.

## 5. Durable resume guidance

For a new ChatGPT session: Read docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md FIRST, then THIS erratum, then the #165 Phase A source handoff and R4 acceptance handoff. The operator's latest PowerShell transcript contains a FALSE READY caused by a 38-character SHA typo introduced in ChatGPT's command; the successful fetch is not proof a worktree exists. Only issue ONE corrected, single-scriptblock PowerShell operation using the exact verified 40-character SHA and halt on any STOP. Then instruct Claude offline targeted independent review after verified worktree creation, with no Vres or database contact. Keep committing an updated docs handoff at each substantive development/evaluation checkpoint. Do not require the user to repeat already-supplied evidence.
