# 2026-11-18 — Original Repository strict persistence boundary (R-3 candidate)

**SOURCE-ONLY / AUTHOR ENGINEERING / TESTS AUTHORED NOT_RUN / NOT APPROVED FOR LAUNCH.**

## Scope and purpose

One personal Windows Vres-OS companion to the ORIGINAL Claude Code CLI (PRIMARY) and ORIGINAL FastMCP. This changes only the canonical redaction helper plus the ORIGINAL authoritative Repository write call sites. It does not add a task/result store, Chairman, MCP runtime, GUI, installer or enterprise role model. Existing Tk Desktop remains untouched. Preserve V-01..V-42, M0..M8, W0..W3, W4 R1..R13, C2B/K0 and October 22/30/31–November 5 roadmaps.

The 2026-11-18 advisory R-2/R-3 found that direct redact()/redact_text() is not a fail-closed persistence API: "password=abc,def" may leave ",def" and "password: correct horse battery" may leave " horse battery" after masking a prefix. The preceding c81b0cb commit mitigated only two outbound original FastMCP views. No database was read or touched to confirm historical content.

## New original-owner source policy

- Add redact_for_persistence() to existing src/vres_os/redaction.py. It recursively inspects each ORIGINAL string with sanitize_text() before any partial redaction can erase evidence of canonical substitution. A string with any eager rule count OR unresolved residual becomes the value-free "[REDACTED_UNSAFE_FIELD]". Clean strings and safe siblings are preserved; known secret dict keys stay "[REDACTED]". Date, tuple/list, scalar, nested depth behavior follows original redact().
- Route all TEN original src/vres_os/repository.py redact() call sites through this dedicated strict helper, including task title/objective, state writes and comparisons, checkpoint summary/position/action/context, JSONB events and completion summary. No table/schema/SQL migration and no new ownership.
- Keep redact_text(), redact() and outbound display API semantics unchanged. This strict write-side substitution deliberately discards an entire tainted string, sacrificing some human-readable context to avoid ambiguous stored suffixes. A clean string in another list/dict element remains useful.
- New synthetic regression tests verify strict recognized shapes, safe structure preservation, unchanged default display behavior, and original Repository write parameter tuples through an in-memory connection double. **AUTHORED NOT_RUN**. Current branch compile, pytest, native FastMCP, PostgreSQL even SELECT, PowerShell and Windows execution remain NOT_RUN/HELD.

## Non-claims and residual risks

This is a **candidate preventive write boundary**, not proof of universal credential detection or an automatic repair of already persisted rows. Unknown secret formats, crafted pre-masked historical values with suffixes, unreviewed paths outside the canonical Repository, direct redact_text() consumers, logging, imported modules and external credentials remain unresolved. R-2/R-3 broader outward/persistence inventory must continue. No PostgreSQL inspection, cleanup or migration is allowed under LIVE_SCHEMA_048_INCIDENT. Independent #185 THREAT_MODEL / RELEASE_DESIGN / OPERATIONS verdict and source-specific tests/review are still missing. Advisory F-1..F-9, pre-execution publisher SHA-256/toolchain trust, offline wheels, NTFS/recovery and native Claude pinning are NOT cleared.

## Nonnegotiable holds

LIVE_SCHEMA_048_INCIDENT OPEN: NO PostgreSQL, even SELECT. HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED OPEN: NO ordinary native Claude Code/installed FastMCP/hooks. Independent F1/Fable positive authority NOT_GRANTED. P3, Git Windows L2, R13 staging, Windows install/update/recovery, installed P2 and full original V-01..V-42 UAT HELD. Do not modify main, protected R13/Tk worktrees, real credentials, user profile, original TASK-DAY-01, PRISM or legacy project. Fresh original install.ps1 prerequisite detection/offers with separate default-NO informed consent for Claude Code, PostgreSQL 17, optional Node LTS and npm Codex remain mandatory; -Update must not silently install any external package.

## Next gate

Read exact current GitHub branch HEAD/TREE/PARENT/new blobs, full issue #185/body/comments and newest continuity before any next step. Obtain a genuinely independent, attributable, full current-commit review; independently resolve both incidents and separately authorize each Windows/host/DB action before integrated original Claude/FastMCP/PostgreSQL UAT. No self-issued security acceptance.
