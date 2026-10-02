# Experience Intelligence E4: contract addendum (2026-10-02)

Status: dated addendum to the frozen contract `EXPERIENCE-INTELLIGENCE-E4-CONTRACT-2026-09-30.md` (frozen at
`a69b836fa3fbf6a97c00f830b05495c48c5af563`). The frozen file is not edited. This addendum governs only the two
changes below. Everything else in the frozen contract stands.

Approval: approved by the user in session 4a77f618-324d-43f3-87a9-f0729186e712 on 2026-10-02.

## 1. Protected context-refresh attestation (migration 040)

### Original frozen requirement

- Line 48: the session metadata trigger is "Not migrated (deliberately)": contamination is derived from the ledger,
  "so no new protected metadata key is introduced".
- Line 125: contamination is derived; "No mutable marker, no protected-metadata trigger change".
- Line 126: while contaminated, only the safe tools plus `context_refresh_ack` are allowed.
- Line 137: "only `context_refresh_ack` joins `_SAFE_VRES_TOOLS`".
- The frozen E4 scope allows only migration 039.

### Discovered gap

`context_refresh_ack` takes only a contamination event key. Without a trusted correlation, any caller that can see a
key (for example another session's key in a shared notice) could acknowledge that other session's contamination. The
interim fix stored a short-lived attestation under `vres.sessions.metadata.ack_attestation`. That key is not
protected. The ordinary runtime role can write it, so it is a mutable marker that the frozen contract forbids, and
it can be forged.

### Why no existing surface fits

- Migration 029's trigger `vres.protect_user_input_metadata` protects a fixed list of keys:
  `pending_user_instructions`, `pending_user_instruction`, `committed_user_input_tool_ids` and
  `vres_read_only_hold`. Adding a key means changing a released migration's trigger. Released migrations are
  immutable, and line 125 forbids a protected-metadata trigger change.
- `vres.stage_user_input` is the writer's only protected session write. Using it for an attestation would record a
  hook-minted value as user-authority input. That fabricates user provenance.
- `vres.experience_lifecycle_events` is writable by the ordinary runtime role (the ack itself appends there). A row
  there cannot prove that the trusted hook ran.
- Files (data directory, transcript-adjacent files) are writable by the same OS user and are forgeable.

### Why migration 040 is required

The invariant needs state that the runtime role cannot create or reset. The only owner of such state in Vres is a
table whose privileges the boundary controls (migration 023's writer/runtime split). That is new DDL, so it needs one
additive migration.

### Replacement invariant

A `context_refreshed` ledger row exists only if all of the following hold:

1. The trusted provenance writer role (`provenance_authority.writer_role`, authority `user_event_writer`) minted a
   single-use attestation through `vres.issue_context_refresh_attestation`, called from the PreToolUse hook. It is
   minted only for:
   - the latest `context_contaminated` event of the one open Claude session whose `provider_session_id` equals the
     hook payload `session_id`; and
   - the hook payload `tool_use_id`.
2. The hook rewrote the tool input (`updatedInput`) to carry the nonce. Only `sha256(nonce)` is stored.
3. The MCP tool consumed the attestation through `vres.consume_context_refresh_attestation`. Consumption uses the
   nonce hash plus the host's `claudecode/toolUseId` request meta, inside the acknowledging transaction. An unknown
   or already consumed (nonce, tool_use_id) pair is rejected. A matching attestation is consumed exactly once. The
   consumption commits even when the acknowledgement is then denied. It is denied when any of these hold:
   - foreign project;
   - key mismatch;
   - expired or future-dated (120 s maximum window);
   - session closed;
   - no longer the latest contamination (stale).
4. The `AFTER INSERT` trigger `trg_require_attested_context_refresh` on the ledger refuses a `context_refreshed` row
   unless one unused `ok` consumption from the same transaction matches its project, session and acknowledged key. It
   then binds that consumption to the row.

Privileges (granted by `database_boundary.activate_boundary`, after every migrate):

- The writer may only EXECUTE the mint function.
- The runtime may only EXECUTE the consume function.
- Neither role nor PUBLIC has any right on the table, the sequence or the trigger function.

The `sessions.metadata.ack_attestation` path and its code are removed. Contamination stays derived from the ledger. No
contamination marker is added, and migration 029's trigger is unchanged.

### Security effect

- Session binding: a session cannot acknowledge another session's contamination by key. The key is not a
  credential.
- Invocation binding: a nonce without the matching host invocation id is not a bearer credential.
- Hook requirement: a direct MCP call without the hook fails closed (`refresh_not_attested`).
- Forgery resistance: a forged ledger row or forged metadata has no effect. In split-role topology, the runtime role
  cannot create, read, reset or delete an attestation.

### Scope limitation

- Correlation relies on Claude Code passing the PreToolUse `tool_use_id` to the MCP server as request meta
  `claudecode/toolUseId`, and on `updatedInput` replacing the model's input. Both were observed on the installed
  Claude Code, which reports version 2.1.286. If either is absent, the ack fails closed.
- The nonce and tool_use_id appear in the transcript. The same OS user, holding the runtime DB credential, could replay
  them within 120 s, for that session's latest contamination only.
- In single-role topology the runtime owns the objects, so privilege separation is nominal there. The writer gate
  still applies to minting.
- The table owner or a superuser can disable the trigger.

### Expected migrations

The expected migration set changes from 39 migrations ("no 040") to 40 migrations, latest
`040_context_refresh_attestation.sql`. No migration after 040 is introduced by E4.

## 2. Company-knowledge support eligibility (no migration)

### Original frozen requirement

- Line 83: a company (`project_id IS NULL`) item with support in a revoked project source is not mutated. It is
  listed as `unresolved_cross_scope`, and E3 "must treat that support as absent".
- Line 114: a lesson or episode grounded only in revoked sources is excluded.

### Discovered gap

The E4 closure fixed E3 `_raw` only. `knowledge_get`, `knowledge_search`, chunk/hybrid search and
`EmbeddingService.semantic_search` (JSON and pgvector) still returned a company item (`project_id IS NULL`) whose only
applicable support was revoked or inactive.

### Replacement invariant

One SQL helper, `knowledge_status.company_support_usable_sql`, defines usability. Its support roots are
`knowledge_evidence` sources plus `derived_from` relations to sources. A knowledge row is usable when any of these
hold:

- it is project-scoped;
- it has an active support root;
- it has no non-active support root.

The helper is used by:

- `chunk_eligible_sql`, which covers chunk, hybrid and semantic search in both modes;
- `KnowledgeService.search`;
- `KnowledgeService.get`, which returns a metadata-only tombstone with `reason_class` `company_support_unusable` and
  no content;
- E3 `_knowledge` and `_raw`.

The company row is not mutated, and `unresolved_cross_scope` labelling is preserved.

### Scope limitation

- Transitive company support is not evaluated.
- Evidence with a NULL `source_id` and dangling relations are neutral.
- The embedding fence does not lock company support sources; read-time filtering covers them.
