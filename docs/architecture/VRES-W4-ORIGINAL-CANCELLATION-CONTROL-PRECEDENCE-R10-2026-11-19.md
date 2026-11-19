# 2026-11-19 — R-10 original cancellation control precedence (SOURCE ONLY)

**Status:** Author-side GitHub source and synthetic tests; NOT_RUN, NOT independently reviewed and NOT authority to execute, apply migration 042, connect to PostgreSQL, launch Claude/FastMCP, install or release.

## Original source correction

- Preserve migration 032 and its existing instruction-only reader for other consumers; add **migration 042** with a new role-guarded read-only `vres.latest_observed_user_input` function returning the newest user observation **including controls**. No table, schema rewrite, backfill, historical scrub or application of migration is performed.
- Original `session_prompts.py` strict-sanitizes historical text returned by the new trusted-writer reader before caller use.
- Original `task_lifecycle.py` cancellation accepts only a **newest direct `user_prompt` instruction** with explicit cancellation text, refuses a newer read-only/control or AskUserQuestion answer and declines *any already committed* cancellation as replayable history.
- After the original writer commits pending entries, check the **final committed event**, not any earlier matching event, as an extra precedence fence. Keep the original task/session/event/Chairman/MCP owner; no alternate store, UI, schema owner or installer.

## Exact limits and critical unresolved work

- This is **partial cancellation precedence hardening**, **NOT** proven full current-Claude-turn authorization or atomic cancellation. The current two-transaction cancellation authorization/status transition still has an intervening host-turn/concurrent-session race, and stopped/unobserved host turns cannot be independently proven here. A trusted reviewer must assess atomic per-turn/provenance binding before release.
- **P0 historical persistence NOT FIXED:** original migration 023 `commit_user_inputs` still forwards historical raw `obs.text` and `obs.question` into task_events and task_state. R8/R9/R10 do not clean prior rows; unknown credential formats and writer bypasses remain. Any safe future migration must be reviewed separately, without modifying applied 023/029/032 or destructively scrubbing user data.
- Migration 042 is prospective source only. It changes future migration inventory beyond the older 001–041 pins; original release-source recipe and R13 no-launch/exclusion assumptions must be re-reviewed before any execution.
- Synthetic tests AUTHORED NOT_RUN. Exact source Python/AST/compile/pytest, SQL migration, host/Claude, FastMCP, Windows and V-01..V-42 UAT: NOT_RUN. Historical 732/732 PASS applies only to 9e2b538b.
- Both absolute incidents OPEN: LIVE_SCHEMA_048_INCIDENT (no PostgreSQL even SELECT) and HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED (no ordinary native Claude or hooks). #185 independent three-part review NOT_OBTAINED; F1/Fable NOT_GRANTED; protected main/R13, installed P2, credentials, profiles, PRISM/legacy and installer are HELD.

**Next:** independent attributable CURRENT-source THREAT_MODEL / RELEASE_DESIGN / OPERATIONS review; plan original-schema-safe historical observation writer protection and atomic current-turn cancellation; no migration or runtime execution before separate approvals.
