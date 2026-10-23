# Vres-OS — ChatGPT-led CURRENT continuity index

**Updated:** 2026-10-23, Europe/Athens.
**Authoritative documentation branch:** docs/chatgpt-continuity-20261023.
This branch inherits dc76d7c1305530ac685ef153753aae7d700b39e8 and preserves older historical C2B/K0 records and installed Vres evidence.

## READ FIRST

1. [#165 F2 test-only Windows review worktree VERIFIED](VRES-165-B1-F2-TEST-ONLY-WINDOWS-WORKTREE-VERIFIED-2026-10-23.md) — **NEWEST** local checkout PASS, full SHA 36a41b6151b7520329ccc0ada0ff827d836ec579, only one test file, Claude tests NOT_RUN.
2. [#165 B1 F2 independent offline ACCEPT and test-only follow-up](VRES-165-B1-F2-INDEPENDENT-ACCEPTANCE-AND-TEST-HARDENING-2026-10-23.md) — parent F2 source b77e0eef accepted after 101/101 selected Windows PASS; explains new one-file test commit.
3. [Original F2 source correction](VRES-165-PHASE-B1-F2-UNICODE-HISTORY-BOUNDARY-CORRECTION-2026-10-23.md) and [successful original F2 review worktree](VRES-165-PHASE-B1-F2-WINDOWS-WORKTREE-VERIFIED-2026-10-23.md) — original 256-KiB Unicode history change and local review.
4. [#165 B1 original independent offline ACCEPT](VRES-165-PHASE-B1-INDEPENDENT-ACCEPTANCE-2026-10-23.md) — 99/99 PASS; F1 external anchored head risk.
5. [#165 Phase A R2 independent ACCEPT](VRES-165-PHASE-A-R2-INDEPENDENT-ACCEPTANCE-2026-10-23.md) — 53/53 Windows CRLF PASS. Original Phase A R1 REJECT remains in earlier handoff.
6. [P2-A1 R4 database-contact guard offline ACCEPT](VRES-CHATGPT-P2A1-R4-INDEPENDENT-ACCEPTANCE-HANDOFF-2026-10-23.md) — 183/183 offline PASS, earlier REJECT reports and unresolved release residuals.
7. [Full original functionality register V-01..V-42](../roadmap/VRES-FULL-SCOPE-FUNCTIONALITY-REGISTER-2026-10-22.md) and [phased development plan](../roadmap/VRES-CHATGPT-LED-FULL-SCOPE-DELIVERY-PLAN-2026-10-22.md).

## CURRENT EXACT SOURCE AND EVIDENCE

- **Latest HEAD, test-only, NOT independently tested:** 36a41b6151b7520329ccc0ada0ff827d836ec579 on feature/165-chairman-policy-foundation-20261023; parent b77e0eef07976877e7f198a00484f5d13ce36889, exactly ONE changed path tests/test_chairman_policy_history.py. Three 129-entry/writer-bound regression cases under review, no production module change and no reported CI checks at this exact SHA.
- **Latest operator worktree SUCCESS:** C:ProjectsVres-ChatGPT-Review-165B1-F2-Tests-20261023 exists as clean detached checkout at 36a41b6151b7520329ccc0ada0ff827d836ec579; user supplied successful VRES_165_B1_F2_TESTS_REVIEW_READY and one-path diff with no STOP/fatal. NO need to re-fetch/recreate.
- **Last accepted F2 implementation:** b77e0eef07976877e7f198a00484f5d13ce36889, Claude independent ACCEPT, 101/101 Windows Python 3.12 offline PASS; production module unchanged by descendant tests.
- **Earlier accepted B1 proposal history:** f8237bb301dec160f33cab524727e6a0ec79b2c0, Claude 99/99 offline PASS; earlier Phase A R2 at 11f2f8689308dfe43e482bca73aa57bb6467c788, 53/53 PASS; Phase A R1 REJECT persisted (39 passed, five failed, two errors).
- **P2-A1 R4 guard:** 3ba41d5ae6b8f2c2abd93d27f82cce0755878237, offline 183/183 PASS, NOT merged/installed; prior R1-R3 REJECT.
- **Open F1:** proposal-history prefix/truncation/forks require independently authenticated expected chain identity and protected authority; caller-supplied SHA alone is NOT permission to activate or change Chairman.
- **#165/V-07:** OPEN/PARTIAL; Opus/Medium remains requested in-memory candidate, active shipped/installed Chairman still Sonnet/High. No policy approval/install/host model evidence.
- **Main:** 9a8acc5d464b96432a93cb95daa9581412fb07ee last observed; original personal P2 source 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c; installed release 20261022172833-4d82147b last reported unchanged.
- **LIVE_SCHEMA_048_INCIDENT=OPEN; PostgreSQL last observed STOPPED.** No contact including SELECT. D2 OPEN; F2 QUARANTINED; R0 NOT_RUN; K0-T1 BLOCKED; native trust not approved; L-04 OPEN; positive trust issuance disabled; PA-01..08 incomplete. No vault, installed release update, global Claude mutation, signing or model activation.
- All original V-01..V-42 product functionalities remain ACTIVE DEVELOPMENT backlog, not runtime enabled. Preserve Phase A/B1/F2 and P2-A1 reviewer residuals and earlier failed evidence.

## NEXT STEP — CLAUDE IN PREPARED F2 TEST-ONLY WORKTREE

DO NOT create a new worktree. Launch Claude with previously used safe-mode and limited built-in tools from C:ProjectsVres-ChatGPT-Review-165B1-F2-Tests-20261023 after strict read-only check of full HEAD/parent/diff/clean status. Before any pytest, read tests/conftest.py; require isolated app-data, no real DB/credential access, restricted child-process behavior. Then authorize exactly ONE pytest invocation:

    py -3.12 -B -m pytest -q -rA -p no:cacheprovider tests/test_chairman_policy_history.py -k "full_128_entry_unicode_history_round_trips_under_same_byte_limit or reader_rejects_documents_over_declared_byte_limit or writer_refuses_canonical_output_over_its_effective_bound"

Claude independently reports exact source SHA, command/exit counts/side effects and ACCEPT/REJECT/BLOCKED for the new TEST-ONLY commit. ChatGPT owns source corrections. Do NOT rerun the accepted 101-case suite simply for a docs update.

## CONTINUITY

Per user's explicit instruction, after EACH substantive Vres response create a durable new detailed Git handoff and update this index on docs/chatgpt-continuity-20261023 with actual commit readback. Separate docs SHA from source SHA, do not imply earlier tests apply to new commits, preserve all incident/credential/K0/PA controls. ChatGPT codes, Claude independently evaluates, Windows operator approves consequential local actions. No background promises.

## NEW SESSION PROMPT

Resume vosser24/Vres-OS from current GitHub HEAD docs/chatgpt-continuity-20261023. Read this index and newest F2 test-only Windows review worktree VERIFIED handoff first, then accepted F2 and B1/Phase A/P2-A1 handoffs. Source feature branch HEAD 36a41b6151b7520329ccc0ada0ff827d836ec579, parent accepted F2 b77e0eef07976877e7f198a00484f5d13ce36889, changed ONE TEST file only. The Windows operator ALREADY created C:ProjectsVres-ChatGPT-Review-165B1-F2-Tests-20261023 successfully; its new three focused tests remain NOT_RUN. Next: guarded Claude safe-mode launch and one exact -k selected offline pytest invocation; return report to ChatGPT. Keep Opus/Medium unactivated, F1 external anchored history authority OPEN, schema-048 DB NEVER touched and all PA/trust/install holds. After each substantive reply commit docs handoff/index with SHA readback.
