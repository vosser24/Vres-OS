"""G7 source-trust policy identity (policy 176.g7.v1). Chunk 1: constants only; migration 047 embeds the digest literal.

The digest is SHA-256 of the canonical JSON of POLICY (repo convention). A unit test pins it to the migration.
"""
from __future__ import annotations

import hashlib
import json

POLICY = {
 "policy_version": "176.g7.v1",
 "schema_version": 1,
 "basis": "user_approval",
 "refused_bases": ["provider_verified"],
 "actions": ["grant", "revoke"],
 "scope": "project_only",
 "company_scope": "disabled",
 "expiry": "none",
 "descriptor_change": "requires_new_authorization",
 "default_trust": "unverified",
 "legacy_grandfathering": "none",
 "subject_key": "source_trust:<action>:<project_id>:<source_key>:<content_digest>:<descriptor_digest>",
 "content_digest": "sha256_hex_of_lf_joined_lines_'<ordinal>:<sha256_hex(content)>'_over_persisted_chunks_sorted_by_ordinal_then_hash",
 "descriptor_digest": "sha256_hex_of_lf_joined_'source_type=<v>','origin=<v>','version=<v>','project_id=<v>'_null_as_empty",
 "authorization": "whole_message_exact_equality",
 "authorization_template": "I authorize <subject_key>",
 "authorization_trim": "ascii_space_tab_cr_lf_at_both_ends_only",
 "anchor_event": "task_events_USER_INSTRUCTION_actor_user_payload_source_user_prompt",
 "anchor_freshness": "newest_user_authority_event_of_task_USER_INSTRUCTION_or_USER_CONTROL",
 "anchor_ordering": "task_events.id_never_created_at",
 "revoke_target": "active_ledger_grant_row_digests_not_current_source_state",
 "idempotency": "unique_user_event_id_subject_key_replay_returns_existing",
 "approval_events": "not_read_not_written",
 "attestation_class": "user_authored_event_in_database_not_host_authenticated_g8_open",
}


def canonical_policy_json(value: object = POLICY) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


POLICY_VERSION = POLICY["policy_version"]
POLICY_DIGEST = hashlib.sha256(canonical_policy_json().encode("utf-8")).hexdigest()


def authorization_text(subject_key: str) -> str:
    """The exact whole-message text the user must send to authorize one subject (database-authoritative)."""
    return "I authorize " + subject_key
