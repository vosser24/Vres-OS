# Experience Intelligence E4: implementation notes (2026-10-02)

Status: implementation notes for issue #176 E4 (branch `issue-176-e4-temporal-lifecycle-revocation`). These notes
record post-freeze decisions and residual debt. They do not edit the frozen contract
`EXPERIENCE-INTELLIGENCE-E4-CONTRACT-2026-09-30.md`. The two approved deviations from it (migration 040 and
company-support eligibility) are recorded in the dated addendum
`EXPERIENCE-INTELLIGENCE-E4-CONTRACT-ADDENDUM-2026-10-02.md`.

## Post-freeze notes

- `knowledge_supersede` and `knowledge_promote(status='challenged')` route through `ExperienceLifecycleService` and
  require `approval_key` and `reason`. The three new tools (`source_revoke`, `knowledge_lifecycle`,
  `context_refresh_ack`) take one closed `request` object.
- The registered MCP tool count stays 51.
- Migration `040_context_refresh_attestation.sql` is the one additive migration after 039. It adds:
  - the table `vres.context_refresh_attestations`;
  - the functions `vres.issue_context_refresh_attestation`, `vres.consume_context_refresh_attestation` and
    `vres.require_attested_context_refresh`;
  - the trigger `trg_require_attested_context_refresh` on `vres.experience_lifecycle_events`.

  It edits no released migration. It does not alter migration 029's metadata trigger or rewrite any ledger row.
  The former `vres.sessions.metadata.ack_attestation` path and its code are removed.

## Ack session binding (migration 040)

Invariant: the model must not be able to acknowledge another session's contamination by supplying its key. The
acknowledgement fails closed when the trusted current-session identity and host invocation cannot be established.

Design (the trusted writer mints, the host rewrites, the runtime consumes, the ledger enforces):

1. **Recognise.** `control_preflight` (PreToolUse) recognises the recovery call only by:
   - the exact tool name `mcp__plugin_vres-os_vres__context_refresh_ack`;
   - the exact input `{"request": {"contaminated_event_key": K}}` (`_ack_key`). A model-supplied `attestation` field
     makes the input non-exact, so the call is denied.

   Subagent calls are denied.
2. **Mint.** For a parent call the hook runs `issue_refresh_attestation(<payload session_id>, K, <payload tool_use_id>)`
   in `session_contamination.py`:
   - It generates a random nonce.
   - It calls `vres.issue_context_refresh_attestation` over the provenance writer connection.
   - The function refuses every role except `provenance_authority.writer_role` (authority `user_event_writer`).
   - It mints only when K is the latest `context_contaminated` event of the one open Claude session with that
     `provider_session_id`.
   - Only `sha256(nonce)` is stored, with a 120 s window and `UNIQUE(provider_session_id, tool_use_id)`.

   No mint, or any exception, denies. The denial never carries the nonce.
3. **Rewrite.** The hook returns `hookSpecificOutput.updatedInput` with
   `{"request": {"contaminated_event_key": K, "attestation": <nonce>}}`. The host replaces the model's tool input with
   it.
4. **Consume.** `context_refresh_ack` (`mcp_server.py`) reads the host invocation id from the MCP request meta
   `claudecode/toolUseId` (`_host_tool_use_id`), never from tool input. It calls
   `ContextRefreshService.acknowledge_attested`, which:
   - takes the project lock;
   - calls `vres.consume_context_refresh_attestation(project, tool_use_id, sha256(nonce), K)` in the same
     transaction.

   An unknown or already consumed (nonce, tool_use_id) pair is refused. A matching row is consumed once, with outcome
   `ok`, `foreign_project`, `key_mismatch`, `expired`, `closed_session` or `stale`. The consumption commits even when
   the acknowledgement is then denied:
   - `stale` maps to `stale_contamination`;
   - every other non-`ok` outcome maps to `refresh_not_attested`.
5. **Enforce.** On `ok`, the unchanged locked acknowledgement appends the `context_refreshed` ledger row. The
   `AFTER INSERT` trigger requires one unused `ok` consumption from the same transaction, for the same project,
   session and acknowledged key, and binds it to the row (`refresh_event_key`, unique). Any `context_refreshed`
   insert without it raises: a forged ledger row, a second row per consumption, or a direct SQL insert.
6. **Boundary.** `database_boundary._activate_context_refresh_attestations` runs on every `activate_boundary`, guarded
   by `to_regclass`, so it is upgrade-safe. In split-role topology:
   - it revokes every non-owner grant on the table, the sequence and the three functions;
   - it grants EXECUTE on `issue` only to the writer;
   - it grants EXECUTE on `consume` only to the runtime.

   In single-role topology the migration's `REVOKE ... FROM PUBLIC` applies and the writer gate still restricts
   minting to the configured writer role.

`ContextRefreshService.acknowledge(project_id, provider_session_id, ...)` stays as the internal trusted API used by
services. No public adapter reaches it. Since 040, any path that appends `context_refreshed` needs a consumed
attestation in its transaction. Contamination stays derived from the ledger. `is_contaminated`,
`contaminated_sessions_for_host_session` and `_latest` do not read `metadata` (pinned in
`tests/test_session_contamination.py`).

### Trust root and correlation evidence

The trust root is the host. Claude Code runs the PreToolUse hook with the payload `session_id` and `tool_use_id`,
applies its `updatedInput`, and passes the same id to the MCP server as request meta `claudecode/toolUseId`.

A disposable probe confirmed this on the installed Claude Code, which reports version 2.1.286:
- The probe used a stdio MCP server and a PreToolUse hook. The model asked for `{"x":1,"nonce":"MODEL-CHOSEN-123"}`.
- The hook returned `updatedInput` with a hook-chosen nonce.
- The server received the hook's nonce, not the model's.
- The server's request meta `claudecode/toolUseId` equalled the hook payload `tool_use_id`.

The probe was one observation. It is not a host guarantee. If a future host drops either behaviour, the
acknowledgement fails closed (`refresh_not_attested`) rather than open.

Proofs in tests:
- `tests/integration/test_e40_attestation_split_role_journey.py`: split-role privileges, forged-row refusal,
  writer-cannot-consume, single use and idempotent re-activation.
- `tests/integration/test_e4_ack_session_binding.py`, `tests/integration/test_e4g_public_adapters_journey.py`:
  - one session cannot consume another session's attestation;
  - the key is not a bearer credential;
  - a direct MCP call without the hook fails;
  - replay is refused.
- `tests/test_e4_ack_attestation_hook_unit.py`: hook exactness and nonce non-disclosure.

### Classification against the frozen contract

- Contract lines 48 and 125 ("no new protected metadata key", "no mutable marker") still hold. Migration 040 adds no
  metadata key and no marker; contamination stays ledger-derived. The new protected state is a separate table,
  approved in the addendum.
- Contract line 137 says only `context_refresh_ack` joins `_SAFE_VRES_TOOLS`. The tool is **not** added to that set.
  It is admitted through a separate exact-name recovery branch that needs a host-correlated attestation. This branch
  is **outside the frozen contract**: it is stricter than lines 126 and 137, and the addendum does not change it.
  `_SAFE_VRES_TOOLS` is unchanged.
- Duplicate acknowledgement (contract line 100): replaying the same, still-latest key through hook and tool returns
  `replayed=true` and appends nothing. A key that is no longer the latest is refused at mint
  (`refresh_not_attested`). Only an attestation already minted before a newer revocation yields
  `stale_contamination` at consumption.

### Residual limits

- The nonce and `tool_use_id` appear in the session transcript. The same OS user, also holding the runtime database
  credential, could call the consume function directly within the 120 s window. This works only for that session's
  latest contamination, and only once.
- The writer credential is in the same OS credential store as the runtime credential (the migration 023 trust
  boundary).
- Single-role topology: the runtime owns the objects, so privilege separation is nominal. The table owner or a
  superuser can disable the trigger.
- With no writer role configured, the hook cannot mint, so every acknowledgement fails closed.
- The runtime role can still append `context_contaminated` rows. That direction only fails closed (more
  contamination).
- An unconsumed attestation expires after 120 s and is never usable for another invocation.
- Binding to a process id was considered and rejected, because hook and MCP server are different processes.

## E-debt classification (Chunk E retrieval carry-over)

| # | Debt | Frozen clause | Current behaviour | Why acceptable / status | Pinning test | Future cleanup |
|---|---|---|---|---|---|---|
| 1 | Historical episode state is the current ledger state, not the state at `as_of` | L67: revoked is "tombstone only" historically; L69: revocation "is the only state that hides content from historical queries" | `experience_retrieval._episodes` reads the latest `invalidate_derived`/`restore_derived` event with no `created_at <= as_of` filter; `episode_item` returns a tombstone for every revoked state | Conservative: a revoked episode is a tombstone for every `as_of`. E4 has no `restore_derived` writer (only readers in `experience_lifecycle.py` and `experience_retrieval.py`), so a restored-later state cannot occur | `tests/test_experience_retrieval_e4.py::test_tombstone_is_shown_regardless_of_as_of_before_or_after_revocation`, `::test_revoked_episode_never_returns_content`; `tests/integration/test_experience_retrieval_lifecycle.py::test_episode_revocation_corruption_and_dead_support` | Add an `as_of` filter when a `restore_derived` writer exists |
| 2 | Raw fallback has no cross-scope support gate | L83: company support in a revoked project source must be treated "as absent"; L114: "a lesson or episode grounded only in revoked sources is excluded"; L116: `_raw` gains "the same conditions" | `_raw` gates the chunk's own source and the knowledge status, approval and window. Unlike `_knowledge`, it has no `support_active=0 AND support_inactive>0` exclusion for company rows | **Violation (now fixed).** Verified on the disposable DB: a raw chunk of an approved company lesson whose only support is a revoked project source is returned under current and historical intent | `tests/integration/test_experience_retrieval_lifecycle.py::test_raw_chunk_of_a_company_item_whose_only_support_is_revoked_is_never_returned` | Fixed by the Chairman in the closure stage: `_raw` applies the dead-support gate. The xfail is removed and the test passes. The addendum closes the remaining readers with one helper, `knowledge_status.company_support_usable_sql`, used by `chunk_eligible_sql` (chunk, hybrid and `EmbeddingService.semantic_search` in JSON and pgvector modes), `KnowledgeService.search`, `KnowledgeService.get` (metadata-only tombstone, `reason_class` `company_support_unusable`) and E3 `_knowledge`/`_raw`. The company row is not mutated and `unresolved_cross_scope` is preserved. Pinned by `tests/integration/test_e40_company_support_eligibility.py` |
| 3 | A tombstone discloses that a revoked key matched; counters count revoked rows | L67 permits "key, state, time, reason class" | `_tombstone` emits only key, state, time and reason class. Exclusion counters are integers | Within the contract. Already listed in `KNOWN-LIMITATIONS.md` | `tests/test_experience_retrieval_e4.py::test_historical_revoked_knowledge_is_a_metadata_only_tombstone`, `::test_historical_pack_with_tombstones_is_closed_schema_deterministic_and_leak_free`; integration `::test_knowledge_get_returns_only_tombstone_metadata_for_revoked` | None required |
| 4 | Retrieval-side episode support checks direct `derived_from` sources only | L73: support graph episode -> {task, decision, validation, artifact, source}, artifact -> source | `_episodes` LATERAL counts only direct `derived_from` sources | Revocation itself traverses the full graph and writes the episode's ledger state, which retrieval gates on. The direct-source check is defence in depth for non-revocation inactivity (for example `archived`) | `tests/integration/test_source_revocation_service.py::test_transitive_episode_and_lesson_via_real_writers` (episode via artifact is revoked); `test_experience_retrieval_lifecycle.py::test_episode_revocation_corruption_and_dead_support` | Reuse the revocation traversal if archived indirect support must also hide episodes |
| 5 | `experience_consolidation._derived_items` uses a status deny-list | L114 (never use revoked/retired as premises) | `status NOT IN ('rejected','superseded') AND status NOT IN ('retired','revoked')`. Status is `NOT NULL` and constrained by migration 039 to nine values | Equivalent to the live allow-list plus `challenged`. A challenged lesson still counts for duplicate/conflict detection, which blocks rather than permits a new lesson | `tests/integration/test_experience_consolidation_lifecycle.py::test_f_retirement_foreign_kinds_projects_and_episodes_do_not_suppress`; `tests/test_knowledge_status.py` | Switch to `status_in_sql(LIVE_KNOWLEDGE_STATUSES + ('challenged',))` for one obvious rule |

### Company support eligibility (addendum)

A company row (`project_id IS NULL`) is usable when either holds:
- it has no support root;
- at least one support root's source status is exactly `active`.

Support roots are `knowledge_evidence` sources plus `derived_from` source relations. Revoked, inactive, NULL-status or
unknown-status support fails closed. Project rows are untouched by this rule.

Residual limits:
- Transitive company support (through other knowledge or artifacts) is not evaluated.
- Evidence with a NULL `source_id` and dangling relations are neutral.
- The embedding fence does not lock company support sources; read-time filtering covers this.

## Latency (disposable test DB, n = 30 each, no telemetry written)

Measured with a scratch script on the disposable E4 test database. Five open sessions. Median, p95 and max are in ms.
The three `ack` rows were measured on the pre-040 metadata-attestation design. They were not re-measured for the
migration 040 mint/consume path.

| Path | n | median | p95 | max |
|---|---|---|---|---|
| preflight lookup + evaluate, clean | 30 | 44.1 | 50.6 | 154.6 |
| hook `main()` in process, clean | 30 | 84.2 | 195.7 | 291.3 |
| hook process `python -m vres_os.control_preflight`, clean | 30 | 136.3 | 143.1 | 158.1 |
| `open_session` | 30 | 54.3 | 162.1 | 171.5 |
| preflight lookup + evaluate, contaminated | 30 | 49.9 | 58.7 | 166.4 |
| hook `main()` in process, contaminated deny | 30 | 94.9 | 199.4 | 206.5 |
| ack: hook `main()` (pre-040 attestation write) | 30 | 162.6 | 349.1 | 372.6 |
| ack: `context_refresh_ack` tool (consume + ledger append) | 30 | 105.5 | 203.1 | 306.8 |
| ack: hook + tool, first ack | 30 | 285.4 | 546.5 | 607.5 |

The hook-process row ran with an unconfigured data directory, so it measures interpreter start, imports and config
load, not the database lookup. Zero attestations remained after the ack loop.

## Mechanical public-adapter inspection (disposable DB)

All steps ran through the public MCP adapters and the real hook `main()`. The script printed only keys, statuses and
counts. The acknowledgement steps ran on the pre-040 design. For migration 040 they are covered by
`tests/integration/test_e4g_public_adapters_journey.py`, which drives the hook's `updatedInput` and the host
`claudecode/toolUseId` meta. The scratch inspection was not re-run.

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

## Closure record (migration-040 docs-complete candidate)

- Original frozen E4 contract commit: `a69b836fa3fbf6a97c00f830b05495c48c5af563`. The contract file stays byte-identical to it (blob `cd97bf9807a82b535c845fedabd7bec69a08ae82`). The dated addendum `EXPERIENCE-INTELLIGENCE-E4-CONTRACT-ADDENDUM-2026-10-02.md` records the user-approved migration-040 amendment. `tests/test_e4_frozen_contract_integrity.py` always asserts the contract hash and asserts that the addendum exists.
- E4 commits: A-E; F hardening `b6521b81e377d4ccdb8301540c33d52871d7234c`; G `4dbaccaf46997b9fb7397bff29bd9aa2815c8ce8`; security closure `c3636345588df4167f9414c96456f489daa78250`; previous docs candidate `d89c6dd2b787612947f0caa9dc31cd17f34eb7fe`; migration-040 product commit `b9110d7` (parent `d89c6dd2`); this docs commit follows it. The final SHA/tree is read from git.
- Migration 040 (`040_context_refresh_attestation.sql`, sha256 `73dd705e8b5ec9984c5e6829ef38591d3b09aac5a3562fb01187497085fbb48d` of the working-tree bytes): 40 migrations, latest 040. MCP tools: 51.
- Evidence on the final product bytes: full suite on a fresh disposable JSON `_test` DB, pytest exit 0, skips = 3 known symlink skips plus one pgvector-only test. The pgvector-relevant files ran on a fresh pgvector `_test` DB (company-support eligibility included) and pass, except `test_knowledge_status_guard.py::test_semantic_jsonb_path_and_hybrid_exclude_non_use`. That test is JSON-only (its own comment says pgvector is absent) and fails identically at HEAD on a pgvector DB; it is a pre-existing mode mismatch. 72 targeted ack, public-adapter and split-role tests pass. The local release gate exit 0 (`PASSED_WITH_EXPLICIT_LIVE_GATES`; its DB tests skip by design and are not PostgreSQL acceptance evidence). Critical ruff clean; `git diff --check` clean (line-ending warnings only).
- A first full-suite run on these bytes exited 1: `tests/test_runtime_surfaces.py` stubs `mcp.server.fastmcp` without `Context`, which the new `mcp_server.py` imports. The stub was fixed (test-only) and the full suite re-run to exit 0.
- Real contract violations found and fixed: `_raw` returned the raw text of a company item whose only support was revoked (closure), and every legacy reader could return such an item (Blocker B, now one shared `company_support_usable_sql`).
- Accepted limitations: see `docs/KNOWN-LIMITATIONS.md` (E4). The trust root is the host's hook payload plus its `claudecode/toolUseId` request meta, observed once on Claude Code 2.1.286; if the host drops either behavior the ack fails closed. Not re-measured: ack-path latency.
