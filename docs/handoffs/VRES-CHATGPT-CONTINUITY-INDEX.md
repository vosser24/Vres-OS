# Vres-OS — ChatGPT-led CURRENT continuity index

**Current record date: 2026-10-23, Europe/Athens.**
**Authoritative branch for new ChatGPT continuity commits: docs/chatgpt-continuity-20261023.**
This branch inherits the 2026-10-22 full-scope documentation checkpoint at dc76d7c1305530ac685ef153753aae7d700b39e8. It does not replace or overwrite any older docs or local K0/C2B handoff.

## Read first

1. [P2-A1 R4 independent acceptance and resume](VRES-CHATGPT-P2A1-R4-INDEPENDENT-ACCEPTANCE-HANDOFF-2026-10-23.md) — newest exact evidence, decisions, residuals, safety, and next-session prompt.
2. [October 22 ChatGPT-led product-direction checkpoint](VRES-CHATGPT-LEAD-SCOPE-REACTIVATION-CHECKPOINT-2026-10-22.md) — original full development ambition.
3. [Full 42-item functionality register](../roadmap/VRES-FULL-SCOPE-FUNCTIONALITY-REGISTER-2026-10-22.md).
4. [Phased ChatGPT-led delivery plan](../roadmap/VRES-CHATGPT-LED-FULL-SCOPE-DELIVERY-PLAN-2026-10-22.md).
5. [October 22 new-session historical resume](VRES-CHATGPT-NEW-SESSION-RESUME-2026-10-22.md), whose old source-publication action is now CLOSED/superseded.
6. For the schema-048 incident, historical [E7 C2A/C2B incident handoff](PREPRODUCTION-E7-C2A-C2B-CONTROL-INCIDENT-RESUME-HANDOFF-2026-10-13.md) and local unpublished documents when the operator supplies them.

## Current exact boundaries

- **Latest independently ACCEPTED source correction (OFFLINE ONLY):** 3ba41d5ae6b8f2c2abd93d27f82cce0755878237, branch fix/p2a1-loopback-hold-aliases-20261022.
- **Latest accepted correction test:** Claude R4, 183 passed, 0 failures, offline; accepted only for the tested security scope; see detailed handoff.
- **Source corrections since personal release:** exactly four Git commits on that feature branch; all change only database_targets.py and test_database_contact_guard.py.
- **Prior independent failures:** R1 42/42 REJECT, R2 117/117 REJECT, R3 153/153 REJECT, R4 183/183 ACCEPT. Do not erase failures.
- **Parent personal source:** 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c, published on personal/p2f-postinstall-hardening-20261022, still source of the installed release.
- **Product main:** 9a8acc5d464b96432a93cb95daa9581412fb07ee; unchanged and behind personal feature development.
- **Installed release:** 20261022172833-4d82147b, unchanged and not yet activated; source patch NOT installed.
- **Schema-048 incident database:** held; PostgreSQL service stopped at last operator observation; NEVER contact without separate explicit safe-target authorization.
- **Unfinished PA-01..PA-08 and E7/K0 security holds:** unchanged.
- **R4 residuals:** nonloopback translated IPv6 routing risk (conditional), invalid config status, terminal control characters in hold status, missing config-failure test, stale CLI help/docstring.
- **Next development:** an unblocked OFFLINE functional backlog tranche (initial candidate V-07/#165 Chairman model policy), avoiding unnecessary re-review of unchanged accepted security source.

## Continuity rule from user

After every substantive Vres development or review response, commit updated durable handoff evidence and update this index, using a docs-only commit on this branch separate from reviewed product commits. Always read back and report the exact docs SHA. No background execution claims; no false test result; no force-push or blind merge; no unapproved DB, credential, K0, install or global config actions.

If a current-turn checkpoint Git commit did not succeed, state the blocker instead of inventing a SHA.

## Fast new-session instruction

Read this index and follow the detailed R4 handoff's ready-to-paste resume prompt. First verify live GitHub refs. Do not re-ask for the already published P2 source or re-run R4 solely due to a docs commit.
