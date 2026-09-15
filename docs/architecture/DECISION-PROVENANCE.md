# Task decision provenance

Vres task decisions are descriptive continuity state. They are not approvals, publication authority, or independent validation.

## Storage

Migration 020 adds an append-only `vres.task_decisions` ledger while retaining `task_state.decisions` as the ordered plain-text projection of currently active records. The projection is database-managed; callers cannot silently replace it to erase history.

Each structured decision has:

- a durable `decision_key`;
- decision `text`;
- optional `rationale`;
- lifecycle status `active`, `superseded`, or `retired`;
- a mechanically derived source kind;
- optional source event/session provenance;
- `decided_at`, when the decision time is actually known;
- non-null `recorded_at`, when Vres wrote the ledger record;
- an optional supersession link plus superseded/retired timestamps.

`task_decision_record`, `task_decision_supersede`, and `task_decision_retire` require the current Claude session to be bound to the target task. A caller cannot freely claim `source_kind=user_instruction`: that source is accepted only when `source_event_id` identifies a real persisted `USER_INSTRUCTION` event belonging to the task. Otherwise the source is the bound Chairman session.

## Legacy decisions

Migration 016 decision strings are retained exactly and backfilled as `legacy_unstructured`. Vres does not invent rationale, source events, sessions, or decision times for them. Therefore legacy records have `decided_at = NULL`; `recorded_at` only says when migration 020 created the structured ledger row.

## Checkpoints and compaction

Every checkpoint created after migration 020 snapshots the active immutable decision record IDs into `vres.checkpoint_decisions`. The checkpoint JSON context is also enriched with the active plain-text decisions and structured records. This is database-triggered, so automatic lifecycle checkpoints such as PreCompact receive the same decision snapshot even when the caller does not explicitly pass decisions.

Historical checkpoints created before migration 020 are not backfilled with guessed as-of decision membership.

## History

Changing a decision creates a replacement record that points to the superseded record. Removing a decision from active continuity uses retirement. Neither path deletes the old record. This makes later reconstruction independent of summary rewrites while preserving the small `task_state.decisions` compatibility surface used by continuity and validation fingerprints.
