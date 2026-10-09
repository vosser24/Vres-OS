# E7 G7 design freeze and errata (additive to rev 5) — 2026-10-09

Status: **freeze candidate**. It becomes the frozen G7 design only after an independent review returns ACCEPT. This record is additive: the rev-5 document is not edited. Where this record and rev 5 differ, **this record governs**.

## 1. Identities
- Baseline design: `EXPERIENCE-INTELLIGENCE-E7-G7-SOURCE-TRUST-ATTESTATION-CONTRACT-2026-10-09.md` (rev 5), SHA-256 `b4fc3a84f3fac9017fe9e0da2b1bfc9e5ddc4c50ce2826c1e59456940b5d53a1`, byte-identical, passed review `VAL-ca09c908c83247e2`. Earlier failed reviews, preserved: `VAL-ea1520bbb051493f`, `VAL-ada05e213965497f`, `VAL-168d073866974f8d`, `VAL-b3ea906804df4cce`.
- Product base: branch `issue-176-e7-benchmark-security`, commit `0b4d5cdd79ec1e14366f9edce06575fbb8429294`, tree `49068e09a8a90e80dcffaf44980b5f3348d83c84`, migration head 046.
- Policy: `policy_version` `176.g7.v1`, `schema_version` 1. Digest (SHA-256 of the canonical JSON of the policy dict below, repo convention `json.dumps(sort_keys=True, separators=(",",":"), ensure_ascii=False, default=str)`): **`f20b037b00d0a5711666fd6c1d98538101708d99e7f6f32cf5a490ff6b96cf03`**.

Policy dict (key order canonical; values verbatim):
```
actions=[grant,revoke]
anchor_event=task_events_USER_INSTRUCTION_actor_user_payload_source_user_prompt
anchor_freshness=newest_user_authority_event_of_task_USER_INSTRUCTION_or_USER_CONTROL
anchor_ordering=task_events.id_never_created_at
approval_events=not_read_not_written
attestation_class=user_authored_event_in_database_not_host_authenticated_g8_open
authorization=whole_message_exact_equality
authorization_template=I authorize <subject_key>
authorization_trim=ascii_space_tab_cr_lf_at_both_ends_only
basis=user_approval
company_scope=disabled
content_digest=sha256_hex_of_lf_joined_lines_'<ordinal>:<sha256_hex(content)>'_over_persisted_chunks_sorted_by_ordinal_then_hash
default_trust=unverified
descriptor_change=requires_new_authorization
descriptor_digest=sha256_hex_of_lf_joined_'source_type=<v>','origin=<v>','version=<v>','project_id=<v>'_null_as_empty
expiry=none
idempotency=unique_user_event_id_subject_key_replay_returns_existing
legacy_grandfathering=none
policy_version=176.g7.v1
refused_bases=[provider_verified]
revoke_target=active_ledger_grant_row_digests_not_current_source_state
schema_version=1
scope=project_only
subject_key=source_trust:<action>:<project_id>:<source_key>:<content_digest>:<descriptor_digest>
```
The executable dict in the Chunk 1 implementation is authoritative for the bytes (this listing is a human-readable rendering of it, with arrays and strings as JSON in the dict). Chunk 1 must reproduce the digest above from that dict; a mismatch is stop-and-redesign. The dict was computed by `.vres/local-tools/g7_policy.py` (ignored, product worktree).

## 2. R3 result (executed, not read)
A disposable-cluster proof ran on the isolated PostgreSQL cluster with the real split-role topology (runtime, provenance writer, migrator): **55 checks, 0 failures** (run `b7ac81c1`; value-free artifact `.vres/local-tools/results/g7-r3-b7ac81c1.json` in the product worktree, git-ignored). Fixture database and exact-name roles were removed (0 remaining, verified).

Established: the immutable event stores `payload.text` and `payload.source` (`user_prompt` or `ask_user_question`); `USER_INSTRUCTION` and `USER_CONTROL` are distinguished; the runtime role cannot insert, update, delete or reclassify user events, cannot TRUNCATE, disable or drop the protecting trigger, replace its function, set `session_replication_role`, SET ROLE / SET SESSION AUTHORIZATION to the writer, read `provenance_authority`, or execute `stage_user_input` / `commit_user_inputs`. The writer holds no direct DML on `task_events` or `provenance_authority`.

**Finding F-R3-1 (binding):** `created_at` is the hook-supplied `observed_at`, so `created_at` order can differ from commit order (demonstrated). The freshness anchor MUST order by `task_events.id`. Ordering by `created_at` is forbidden.

Residual: the migrator (deploy-time table owner) could in principle disable the protecting trigger; it is a deploy-time principal in the same class as G8, not a runtime path.

## 3. Corrected affirmative-authorization contract (replaces rev 5 "text contains the subject")
Rev 5 §4 requires the anchor text to "contain the recomputed subject key verbatim together with the action word". Containment is **too weak**: quoted examples, negations and explanations that mention the subject would match. Replacement, evaluated only inside the protected database function:

1. Recompute the subject key `source_trust:<action>:<project_id>:<source_key>:<content_digest>:<descriptor_digest>` in the database (digests recomputed from stored rows).
2. Let `T = btrim(payload.text, E' \t\r\n')`. Authorized iff `T = 'I authorize ' || subject_key`: **case-sensitive whole-message equality**. No regex, no `LIKE`, no substring, no normalization beyond the ASCII trim.
3. The action is inside the subject, so GRANT and REVOKE are separate messages; one message authorizes exactly one subject.
4. The anchor row must have `event_type='USER_INSTRUCTION'`, `actor='user'`, `payload.source='user_prompt'`, belong to the named task and project, and be `max(id)` over that task's `USER_INSTRUCTION` and `USER_CONTROL` events (id order, F-R3-1). A later control event or any later instruction makes it stale. `ask_user_question` answers are not accepted as the anchor.
5. Revoke requires an active grant ledger row and matches that row's recorded digests (not the source's current state), so a revoke works after the source changed.
6. Idempotency: first look up `(user_event_id, subject_key)`; if present return that row. A repeated grant for an identity with an active grant returns the existing row. `UNIQUE(user_event_id, subject_key)` plus the row lock on the source serialize concurrent calls.
7. Errors are value-free (no text and no digest values echoed).
8. A Python pre-check may give a friendlier message but is advisory only; the database check is the only authority. No weaker heuristic may replace step 2 to satisfy a test.

Redaction (R4), executed: `redact()` leaves `I authorize source_trust:grant|revoke:7:SRC-<hex>:<64hex>:<64hex>` unchanged with or without a trailing newline, and the entry classifier labels it `instruction`. This is measured for this representative form only. If the redactor were later changed to alter such a line, the grant fails closed (no match), never open.

### Required negative matrix (PG tests; every row expects refusal and no ledger row, except P1)
| # | Case | Why refused |
|---|---|---|
| N1 | `do not grant ...` / `I do not authorize <subject>` | not equal to template |
| N2 | `I reject this grant` plus subject | not equal |
| N3 | subject copied inside a quoted example or code block | not equal (extra text) |
| N4 | explanatory prose mentioning the subject | not equal |
| N5 | `I authorize <subject>` followed by contradictory wording | not equal |
| N6 | malformed or unknown action (`GRANT`, `allow`, empty) | action validated before matching; unknown rejected |
| N7 | wrong content digest or descriptor digest in subject | recomputed subject differs |
| N8 | wrong project, source of another project, company-scope source | project binding / scope refused |
| N9 | stale instruction (newer instruction or control exists), including a created_at-versus-id divergence case | not `max(id)` |
| N10 | AskUserQuestion answer (`source='ask_user_question'`) with exact text | wrong source |
| N11 | forged `approval_events` row; forged `user_event_id`; assistant-actor event; another task's event | anchor predicates |
| N12 | genuine latest instruction lacking the template | not equal |
| N13 | runtime role inserting a `USER_INSTRUCTION` | privilege and trigger (R3) |
| N14 | GRANT text used for REVOKE and the reverse | subject differs |
| P1 | valid exact GRANT issues; exact replay returns the same row; concurrent callers yield one row | positive / idempotency |

## 4. G8 host ingress (open; not solved; not implemented)
**Classification: REQUIRES_DEVELOPMENT.** The prompt hook is a same-user process taking unsigned JSON on stdin; the provenance-writer credential comes from the OS secret store key `postgres.provenance_writer` or an environment variable, readable by any same-user process. A shell-capable agent running as the user can therefore invoke the hook with forged prompt text and cause a genuine-looking `USER_INSTRUCTION` (T11/R5). Nothing in the repository consumes a host signature. A nonce or token available to the agent is not independent authentication.

Candidate closures, none present today: host-signed hook events; a host-owned broker or separately protected principal holding the writer credential; an out-of-band user-only channel. Each needs its own design and review.

Binding wording consequence: G7 positive issuance proves *a user-authored event in the database carries the exact subject*, **not** that a human typed it. It must not be described as unforgeable attestation or a full security guarantee, and positive issuance is not enabled for normal production while G8 is open. Negative effects (revocation, fail-closed reads) stay safe under forgery.

## 5. Errata to rev 5
1. **"Append-only" attribution (rev 5 §4, ledger paragraph).** The wording implies migration 040 supplies append-only behaviour. It does not for this ledger: immutability comes from the new G7 triggers (UPDATE/DELETE/TRUNCATE) and the INSERT guard created by the Chunk 1 migration. Migration 040 is not a source of ledger protection.
2. **R4 missing from §14.** Add residual **R4: redaction may alter or reject an authorization line; consequence is fail-closed (grant not issued); measured for the representative form only.**
3. **Q4** says "(resolved in this revision)": stale. Q4 is resolved by this record: per-source subjects only, no set-digest batch.
4. **"Observed" redaction behaviour (rev 5 R4 text):** it was untested when rev 5 was written ("No test or database was run"). It is now measured (§3), for the representative form only.

Also resolved: Q6 — the full subject line is required (§3). Q5 — `provider_verified` stays reserved and refused.

## 6. Resolved design choices (no invented behaviour)
- A descriptor change (type, origin, version, project) changes `descriptor_digest`; the old grant no longer matches and a new authorization is required. No auto-carry.
- Company-scope (`project_id IS NULL`) positive raw-source eligibility stays disabled.
- No expiry and no frequency or count threshold.
- `provider_verified` basis unavailable; no grandfathering of existing `authority_level` labels.
- One exact authorization per source/action/content/descriptor identity.
- `approval_events` is neither read nor written.

## 7. Minimum implementation boundary (Chunk 1 only)
In scope: a grants-inventory regression test; additive migration `047` creating `vres.source_trust_events` with UPDATE/DELETE/TRUNCATE rejection and a SECURITY INVOKER INSERT guard requiring `current_user` = owner role; `vres.record_source_trust_decision` (SECURITY DEFINER, `search_path = pg_catalog, vres`) per §3; explicit revocation of runtime/PUBLIC DML on the ledger and its sequence, including default privileges; restoration of those revocations and EXECUTE grants in `activate_boundary`; value-free errors; the policy dict and digest constant (§1).

Out of scope: `source_effective_trust` (Chunk 2), Python service and MCP tools (3), E5 v6 (4), audit tool (5), any change to E1/E2 policy, the E7 scorer or corpus, any exposure of positive issuance to ordinary production, G8.

Tests: regression-first, Python 3.12, real PostgreSQL with a runtime-role login, exact-resource cleanup, no live routes.

## 8. Unverified (carried forward, none claimed)
`onboarding.py` re-scan interaction with digests; read-time digest cost on large sources; E3 policy rows beyond E5; whether other readers rank by `authority_level`.

## 9. Gate
Only an independent ACCEPT of this record authorizes Chunk 1 implementation. Chunk 1 itself needs a distinct security review before any product commit.
