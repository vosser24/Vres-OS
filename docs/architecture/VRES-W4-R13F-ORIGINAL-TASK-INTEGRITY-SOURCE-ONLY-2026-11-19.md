# W4 R13F — original task integrity / cancellation SQL boundary (source-only)

**2026-11-19 / REVIEW_REQUIRED / NOT_RUN / NOT_APPLIED / NO RELEASE OR OPERATIONAL AUTHORITY**

This source-only milestone extends original R13D pre-DB cancellation denial and R13E host failure refusal. It does **not** replace the original Chairman, Repository, FastMCP, task/event/checkpoint tables, Claude Code CLI, installation or updater. The owner targets an eventual verified GitHub fetch + original `update.ps1` into the **same** October Windows installation, only after separate incident clearances, independent review and exact owner authorization.

## Concrete source changes

1. Prospective `048_original_task_terminal_hold_r13f.sql` adds a *single original-table* BEFORE UPDATE OF status OR DELETE guard on `vres.tasks`. It rejects every transition into `cancelled` regardless of model/runtime/writer invocation, forbids task-row DELETE, and refuses reopening a terminal completed/cancelled task. Normal `active`, `waiting_user`, `blocked` transitions and original governed `completed` contract are not deliberately changed.
2. `database_boundary.py` removes direct runtime DELETE on existing `vres.tasks`, `vres.task_state`, `vres.task_events`, `vres.checkpoints` during trusted role provisioning and post-migration boundary activation. Missing tables in a new empty schema are skipped until activation; protected user-input provenance tables remain owned by the original writer boundary. PostgreSQL is **never** touched in this milestone.
3. Static source-regression expectations are authored under `tests/test_original_task_integrity_hold_r13f.py`, **NOT_RUN**.

## Safety limits and known incomplete work

- **NO PostgreSQL even SELECT** while `LIVE_SCHEMA_048_INCIDENT=OPEN`. Current live schema ledger and privileges are UNKNOWN. Source has not been applied, parsed by SQL engine, tested or installed.
- **NO ordinary Claude Code, FastMCP or hooks** while `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`.
- `#185` independent attributable three-verdict review is not granted. The original 044/047 cancellation writer remains dormant and no operator-only capability is authorized.
- Broad runtime UPDATE/DELETE grants on **other tables** and broad *default* privileges still require comprehensive integration-preserving least-privilege engineering. This patch does not constitute full role hardening, first-FULL readiness or P0 incident resolution. Runtime can still attempt other sensitive mutations; reviewers must assess all PostgreSQL pathways.
- Existing migrations 001–041 remain pinned as the only release inputs. 042–048 are **SOURCE ONLY / NOT_APPLIED**. Do not edit protected historical migration blobs; do not run `migrate()` under any current hold.
- An independently attributable reviewer must inspect the trigger interaction with 018, 028, 036, 042–047, `task_lifecycle.py`, task deletion/dependency recovery, role provisioning, runtime grants, schema drift, and the host version/identity before any separate offline test or operational permission. The trigger denies even legitimate operator cancellation until a reviewed future design enables it; this is intentional and not feature completion.

## Provenance

GitHub branch based on R13E verified source commit `6b71553a1c4f7b2949c22ceb9abeac17dac3f917`. AST / compile / pytest / SQL execution / PostgreSQL / native Claude / Windows updater / real UAT **NOT_RUN**. GitHub object/ref/tree verification only. Protected main, R13, docs continuity and installed P2 untouched. Preserve V-01..V-42, M0..M8, W0..W3, W4 R1..R13F, C2B/K0, October/November roadmaps.

**NEXT:** attributable #185 review and integrated least-privilege source corrections; then separately authorized offline validation, evidence-based P0 incident remediation, exact released source/release compatibility review, and finally gated same-install Windows hybrid testing.
