# Experience Intelligence E4: implementation notes (2026-10-02)

Status: implementation notes for issue #176 E4 (branch `issue-176-e4-temporal-lifecycle-revocation`). These notes
record post-freeze decisions and residual debt. They do not amend the frozen contract
`EXPERIENCE-INTELLIGENCE-E4-CONTRACT-2026-09-30.md`; where the implementation is stricter than the contract, that is
stated here and left for Chairman arbitration.

## Post-freeze notes

- `knowledge_supersede` and `knowledge_promote(status='challenged')` route through `ExperienceLifecycleService` and
  require `approval_key` and `reason`; the three new tools (`source_revoke`, `knowledge_lifecycle`,
  `context_refresh_ack`) take one closed `request` object.
- The registered MCP tool count stays 51. There is no migration 040. No new store: the attestation lives in the
  existing `vres.sessions.metadata` column.

## Ack session binding (final security)

Invariant: the model must not be able to acknowledge another session's contamination by supplying its key, and the
acknowledgement fails closed when the trusted current-session identity cannot be established.

Design (the hook writes, the MCP tool consumes):

1. `control_preflight` (PreToolUse) recognises the recovery call only by the exact tool name
   `mcp__plugin_vres-os_vres__context_refresh_ack` and the exact input `{"request": {"contaminated_event_key": K}}`
   (`_ack_key`). Subagent calls are denied. For a parent call it runs
   `attest_refresh_ack(<hook payload session_id>, K)`.
2. `attest_refresh_ack` (`session_contamination.py`) writes `{event_key, issued_at=clock_timestamp()}` under
   `metadata.ack_attestation` of the one open Claude session row of that host session, and only when K is that
   session's latest contamination event. Otherwise it writes nothing and the hook denies ("Nothing executed; the tool
   did not execute"). An attestation exception also denies.
3. `context_refresh_ack` (`mcp_server.py`) no longer resolves a session from the key. It calls
   `ContextRefreshService.acknowledge_attested(project_id, contaminated_event_key=K)`. That method consumes every
   attestation for K in the project (single use), requires exactly one that is fresh (TTL 120 s), and then runs the
   unchanged locked acknowledgement for that session. Without an attestation it raises `refresh_not_attested`.
   Consumption commits even when the acknowledgement is then denied.
4. `ContextRefreshService.acknowledge(project_id, provider_session_id, ...)` stays as the internal trusted API used by
   services and tests. No public adapter reaches it.

Contamination stays derived from the ledger. `is_contaminated`, `contaminated_sessions_for_host_session` and `_latest`
do not read `metadata` (pinned in `tests/test_session_contamination.py`).

### Deviations from the frozen contract (for arbitration)

- Contract lines 125 and 48 say "no mutable marker" and "no new protected metadata key". `ack_attestation` is a new,
  non-protected, mutable metadata key. It gates admission only and never encodes contamination state. There is no
  trigger change and no migration.
- Contract line 137 says only `context_refresh_ack` joins `_SAFE_VRES_TOOLS`. The tool is not added to that set.
  Instead it has a separate exact-name branch that needs a host-session attestation. This is stricter than line 126.
- Duplicate acknowledgement (contract line 100): replaying the same, still-latest key through hook and tool returns
  `replayed=true` and appends nothing. A key that is no longer the latest (after a second revocation) is rejected,
  not replayed, even when an attestation for it is still in flight.

### Residual limits

- The trust root is the `session_id` in the host's PreToolUse payload. If the hook does not run, the tool fails
  closed. It does not fall back to trusting the key.
- The runtime database role can write the non-protected metadata key, so it could forge an attestation. That role can
  already append ledger rows, so this adds no new authority.
- An unconsumed attestation stays for up to 120 s. Only that session's own latest key can use it. An attestation
  written for another project's session stays unconsumed until it expires.
- Binding to a process id was considered and rejected, because hook and MCP server are different processes.

## E-debt classification (Chunk E retrieval carry-over)

| # | Debt | Frozen clause | Current behaviour | Why acceptable / status | Pinning test | Future cleanup |
|---|---|---|---|---|---|---|
| 1 | Historical episode state is the current ledger state, not the state at `as_of` | L67: revoked is "tombstone only" historically; L69: revocation "is the only state that hides content from historical queries" | `experience_retrieval._episodes` reads the latest `invalidate_derived`/`restore_derived` event with no `created_at <= as_of` filter; `episode_item` returns a tombstone for every revoked state | Conservative: a revoked episode is a tombstone for every `as_of`. E4 has no `restore_derived` writer (only readers in `experience_lifecycle.py` and `experience_retrieval.py`), so a restored-later state cannot occur | `tests/test_experience_retrieval_e4.py::test_tombstone_is_shown_regardless_of_as_of_before_or_after_revocation`, `::test_revoked_episode_never_returns_content`; `tests/integration/test_experience_retrieval_lifecycle.py::test_episode_revocation_corruption_and_dead_support` | Add an `as_of` filter when a `restore_derived` writer exists |
| 2 | Raw fallback has no cross-scope support gate | L83: company support in a revoked project source must be treated "as absent"; L114: "a lesson or episode grounded only in revoked sources is excluded"; L116: `_raw` gains "the same conditions" | `_raw` gates the chunk's own source and the knowledge status, approval and window. Unlike `_knowledge`, it has no `support_active=0 AND support_inactive>0` exclusion for company rows | **Violation (now fixed).** Verified on the disposable DB: a raw chunk of an approved company lesson whose only support is a revoked project source is returned under current and historical intent | `tests/integration/test_experience_retrieval_lifecycle.py::test_raw_chunk_of_a_company_item_whose_only_support_is_revoked_is_never_returned` | Fixed by the Chairman in the closure stage: `_raw` now applies the `_knowledge` dead-support gate; xfail removed, test passes. `knowledge_search`/embedding readers are not covered (future cleanup) |
| 3 | A tombstone discloses that a revoked key matched; counters count revoked rows | L67 permits "key, state, time, reason class" | `_tombstone` emits only key, state, time and reason class. Exclusion counters are integers | Within the contract. Already listed in `KNOWN-LIMITATIONS.md` | `tests/test_experience_retrieval_e4.py::test_historical_revoked_knowledge_is_a_metadata_only_tombstone`, `::test_historical_pack_with_tombstones_is_closed_schema_deterministic_and_leak_free`; integration `::test_knowledge_get_returns_only_tombstone_metadata_for_revoked` | None required |
| 4 | Retrieval-side episode support checks direct `derived_from` sources only | L73: support graph episode -> {task, decision, validation, artifact, source}, artifact -> source | `_episodes` LATERAL counts only direct `derived_from` sources | Revocation itself traverses the full graph and writes the episode's ledger state, which retrieval gates on. The direct-source check is defence in depth for non-revocation inactivity (for example `archived`) | `tests/integration/test_source_revocation_service.py::test_transitive_episode_and_lesson_via_real_writers` (episode via artifact is revoked); `test_experience_retrieval_lifecycle.py::test_episode_revocation_corruption_and_dead_support` | Reuse the revocation traversal if archived indirect support must also hide episodes |
| 5 | `experience_consolidation._derived_items` uses a status deny-list | L114 (never use revoked/retired as premises) | `status NOT IN ('rejected','superseded') AND status NOT IN ('retired','revoked')`. Status is `NOT NULL` and constrained by migration 039 to nine values | Equivalent to the live allow-list plus `challenged`. A challenged lesson still counts for duplicate/conflict detection, which blocks rather than permits a new lesson | `tests/integration/test_experience_consolidation_lifecycle.py::test_f_retirement_foreign_kinds_projects_and_episodes_do_not_suppress`; `tests/test_knowledge_status.py` | Switch to `status_in_sql(LIVE_KNOWLEDGE_STATUSES + ('challenged',))` for one obvious rule |

Not verified: whether `knowledge_search` semantic/chunk readers have the same company dead-support gap as debt 2.

## Latency (disposable test DB, n = 30 each, no telemetry written)

Measured with a scratch script on the disposable E4 test database. Five open sessions. Median, p95 and max are in ms.

| Path | n | median | p95 | max |
|---|---|---|---|---|
| preflight lookup + evaluate, clean | 30 | 44.1 | 50.6 | 154.6 |
| hook `main()` in process, clean | 30 | 84.2 | 195.7 | 291.3 |
| hook process `python -m vres_os.control_preflight`, clean | 30 | 136.3 | 143.1 | 158.1 |
| `open_session` | 30 | 54.3 | 162.1 | 171.5 |
| preflight lookup + evaluate, contaminated | 30 | 49.9 | 58.7 | 166.4 |
| hook `main()` in process, contaminated deny | 30 | 94.9 | 199.4 | 206.5 |
| ack: hook `main()` (attestation write) | 30 | 162.6 | 349.1 | 372.6 |
| ack: `context_refresh_ack` tool (consume + ledger append) | 30 | 105.5 | 203.1 | 306.8 |
| ack: hook + tool, first ack | 30 | 285.4 | 546.5 | 607.5 |

The hook-process row ran with an unconfigured data directory, so it measures interpreter start, imports and config
load, not the database lookup. Zero attestations remained after the ack loop.

## Mechanical public-adapter inspection (disposable DB)

All steps ran through the public MCP adapters and the real hook `main()`. The script printed only keys, statuses and
counts.

- Source revocation:
  - A wrong-subject approval was denied and the source stayed active.
  - `source_revoke` returned `revoked` with counts: chunks_cleared 2, revoked 1, sessions_marked 2, nodes_visited 2.
  - Source and knowledge were revoked, and embedded chunks went from 2 to 0.
  - Two sessions were contaminated with distinct events.
- `knowledge_lifecycle`:
  - retire, then reinstate (back to validated), then refresh.
  - The revoked state cannot be set through `knowledge_promote` or `knowledge_lifecycle`.
  - 51 tools are registered and none is a restore or set-status tool.
- Acknowledgement:
  - The tool alone returned `refresh_not_attested`.
  - Cross-session attempts were denied at the hook, and the tool then failed closed.
  - An own-key acknowledgement cleaned only that session.
  - Replay through the hook returned `replayed=true`. A second tool call without the hook was denied.
  - After a second revocation, the old key was denied and the new key acknowledged.
  - Zero attestations were left.
