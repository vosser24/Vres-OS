# G7 Chunk 3A contract R3: project-scoped source-trust interface (additive, PROPOSED / NOT ACCEPTED)

Status: **PROPOSED, NOT ACCEPTED** until an independent design review accepts it. R3 replaces R2 (`files/prior/R2_CONTRACT_FAILED_VAL-f49f4752ef064749.md`: 22/26 checks passed; failed on R4/Scenario E/L5, on Section 2.4 vs T1/T2, and on the two consistency checks that repeat those defects). R1 failed earlier (`files/prior/R1_CONTRACT_FAILED_VAL-397fb4037e9546df.md`). Nothing here amends policy `176.g7.v1` (digest `f20b037b00d0a5711666fd6c1d98538101708d99e7f6f32cf5a490ff6b96cf03`), migrations 047/048 or the four accepted G7 documents. Base: product commit `ac45967f63690b76d41b7303ad43248afed8751f` (tree `7a95990fb4413ddf387e90e9cfad5266f266c643`). Design only; no implementation exists.

Clauses changed from R2 are listed in `CHANGES_R2_TO_R3.md`: 2.2/5.3 (unified `newest_event`), 2.4 (DB access), 5.1 R4 (replaced by the 047 decision table 5.1a), 5.2 (scenario tables), 5.2 guidance for A, 8 (T1, T2, L1-L6, C2). Everything else is carried forward unchanged from R2.

## 1. Facts this contract rests on (verify against `files/`, do not trust)
- F1. The runtime role holds `SELECT` on `vres.source_trust_events` and `EXECUTE` on `vres.source_effective_trust(bigint)` only. It has no EXECUTE on `record_source_trust_decision` or `source_trust_digests`, and no DML or sequence rights (`database_boundary._activate_source_trust`, `_activate_source_effective_trust`; Chunk 2 role-boundary tests).
- F2. `vres.source_effective_trust` (048) is the sole effective-trust authority. The Python layer never recomputes digests, never re-evaluates the ledger as trust, and never infers trust from `authority_level`, `metadata` or `content_hash`.
- F3. 048 evaluates **only the newest ledger event of the source by `id`**. `verified_trusted` requires that event to be an unrevoked `grant`, plus: source `status='active'`, non-NULL project scope, no CR/LF in `source_type`/`origin`/`version` (each `coalesce(...,'')`), label not `external_untrusted_observation`, ledger/source project and key consistency, subject_key consistency, intact authority anchor, `chunk_count>0`, and freshly recomputed content and descriptor digests equal to the granted ones. Anything else is `unverified`. The reader reports no reason.
- F4. 047 `record_source_trust_decision` (owner-only; ledger append-only) evaluates in the fixed order of Section 5.1a. Summary: validity/task/project/source lookup, then **exact replay of `(user_event_id, subject_key)`**, then (grant only) `source_not_active`, `no_content`, `digest_mismatch` against the current recomputed digests, then the anchor checks (`anchor_invalid`, `anchor_stale`, `not_authorized`), and only then **dedup** (any unrevoked grant of the source with identical content+descriptor digests, newest id first; returns it, `replayed=true`, writes nothing) or insert. Revoke: after replay and anchor checks, requires an unrevoked grant whose recorded digests equal the supplied ones (`no_active_grant` otherwise); it is not gated by source status or current digests and records `supersedes_event_id`. Multiple unrevoked grants with different digests can coexist.
- F5. `source_revoke` (E4, `source_revocation.py`) sets `sources.status='revoked'` and cascades to derived memory. It never writes the trust ledger. A ledger `revoke` never changes `sources.status`.
- F6. G8 (host-authenticated origin of the user event) is OPEN. Ledger `attestation_class` is `user_authored_event_in_database_not_host_authenticated_g8_open`. Positive production issuance is DISABLED.
- F7. MCP conventions (`mcp_server.py`): `@mcp.tool()`, `_closed_request(tool, request, required, optional)`, `_trusted_project_id()` (read-only lookup, never upserts). `tests/test_runtime_surfaces.py` pins `len(surface.mcp.registered) == 52`.
- F8. `vres.sources` effective nullability (verified in `files/src/vres_os/migrations/001_initial.sql` lines 82-97 and `010_company_authority.sql`): `source_type text NOT NULL`; `origin text` and `version text` nullable; `project_id` nullable (company scope); `status text NOT NULL`. No later migration alters these (010 only adds `scope_approval_event_id`; a grep of all migrations for `source_type` finds only 001, 047 and 048). The 048 `coalesce(source_type,'')` is therefore defensive for a column that cannot be NULL.
- F9. DB access conventions (`db.py` `connect`, `experience_retrieval.py` `snapshot()`): `db.connect(autocommit=False, purpose="runtime")` opens a psycopg connection (non-autocommit by default, `dict_row`, `ClientCursor`). The accepted snapshot pattern assigns the connection attributes `conn.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ` and `conn.read_only = True` **before any statement**, then executes one `SELECT current_setting('transaction_isolation') ..., current_setting('transaction_read_only') ...` and fails closed unless it equals `("repeatable read","on")`. These two attribute assignments are driver configuration, not SQL statements issued by application code; the driver itself emits the transaction-opening `BEGIN ...` on the first `execute` and `COMMIT`/`ROLLBACK` on exit. This contract does not assert the driver's exact emitted text.

## 2. Public tool surface (exact: two tools, both read-only)
Both tools: bind the project from trusted context; reject `project_id` and unknown fields; use `vres.source_effective_trust` as sole authority; report G8 open; use runtime privileges only; give bounded, deterministic output; and **never echo `project_id` (numeric, key or name) anywhere in any response, error or log line**. The physical ledger `id` and `supersedes_event_id` are never returned.

### 2.1 Input validation, before any SQL or connection
Unchanged from R2. Order is fixed and happens before `_trusted_project_id()` and before any connection factory is touched:
1. `_closed_request`: non-dict, `project_id` present, unknown field, missing `source_key`.
2. `source_key`: exact `str`, non-blank after strip, length at most 200, no U+0000-U+001F or U+007F.
3. `limit` (inspect only, optional): exact `int` (`bool` rejected), 1..50, default 20.
Every failure raises `ValueError` with a value-free message. Zero connections opened, zero SQL executed.

### 2.2 `source_trust_status` and the unified `newest_event` object
Request `{source_key}`. Response (all keys always present on success; failure is an error):
```
{ "source_key": "...",
  "effective_trust": "verified_trusted" | "unverified",   // verbatim vres.source_effective_trust(id), nothing else may set it
  "source_status": "<sources.status, at most 64 chars>",
  "declared_authority_level": "<label, at most 64 chars> | null",   // untrusted declared label, never evidence
  "label_is_evidence": false,
  "policy_version": "176.g7.v1", "policy_digest": "f20b...cf03",
  "attestation_class": "user_authored_event_in_database_not_host_authenticated_g8_open",
  "host_authenticated": false, "g8": "open",
  "ledger_total": <int>,
  "newest_event": null | {"ordinal": <int>, "event_key": "STE-...", "action": "grant"|"revoke", "created_at": "<ISO-8601>"},
  "mutation": {"available": false, "reason": "g8_host_ingress_open"} }
```
**`newest_event` schema (single definition, used verbatim by Sections 2.2, 5.2 and 5.3 and all tests).** Fields, in this order: `ordinal` (int, 1 = oldest event of the source's full ledger), `event_key`, `action`, `created_at`. All four are always present and non-null when the object exists. The object is `null` if and only if `ledger_total == 0`. The object is present in both tools' responses (status and inspect) and is the same value in both. It is never omitted for being "inside" the inspect page, never truncated by `limit`, and carries no other field (no digest, no physical id, no `is_newest`, no task or user-event reference). In `inventory.events` the newest entry carries these four fields plus the per-event fields of 5.3; its four shared fields equal `newest_event`.

Example (Scenario A, three events): `"ledger_total": 3, "newest_event": {"ordinal": 3, "event_key": "STE-<32 hex>", "action": "revoke", "created_at": "2026-10-12T10:00:00+00:00"}`. Example (empty ledger): `"ledger_total": 0, "newest_event": null`.

Unknown source, source of another project, company-scope source (NULL project), all produce the same `ValueError("source not found in the current project")` (project filter is in the WHERE clause so a foreign row is never fetched). No timing-equality claim is made.

### 2.3 `source_trust_inspect`
Request `{source_key, limit?}`. Response = the status object plus `inventory` (Section 5.3) and `trust_explanation` (Section 5.2; deterministic observations and situation codes, never executable steps). NOT returned anywhere: title, path_or_uri, origin, version, metadata, content or chunk text, task keys, user event ids or payloads, anchor text, subject_key text, physical ledger ids, `project_id`, current (recomputed) digests.

### 2.4 Database access: one transaction, five application SELECTs (REPLACES R2 2.4)
**Connection and transaction.**
- `_trusted_project_id()` runs first on its own read-only connection, **outside** the snapshot. No atomicity is claimed between it and the snapshot.
- The tool then opens exactly one runtime connection via `db.connect(purpose="runtime")` (non-autocommit) and, in this order and **before any statement is executed on it**, assigns `conn.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ` and `conn.read_only = True` (F9). These are driver connection attributes, not application SQL; the driver emits the transaction opening itself. If either assignment raises, or the connection has already started a transaction, the call fails closed with a value-free error and no statement is executed. The implementation does not hand-write `BEGIN`, `SET TRANSACTION`, `SET SESSION CHARACTERISTICS` or `START TRANSACTION`, and does not invent any other driver call; if the attribute API cannot express the isolation/read-only pair on the pinned psycopg, the design is blocked, not worked around.
- The snapshot claim is exactly PostgreSQL's `REPEATABLE READ` snapshot: every application SELECT below sees one snapshot taken at the first statement of the transaction. Nothing is claimed about freshness after the response, about concurrent writers beyond that snapshot, or about atomicity with `_trusted_project_id()`.

**Statement classes (the only two classes the contract recognises).**
- **APP-SELECT**: a statement the service code passes to `conn.execute`. Exactly the five below, in this order, and no other.
- **DRIVER-TXN**: statements and protocol traffic the driver or server emit by themselves (connection startup, the transaction-opening `BEGIN` with the isolation/read-only options set by the attributes, `COMMIT`/`ROLLBACK`, and protocol-level parameter or encoding setup). They are not application SELECTs, are not counted, are not traced by T2, and are verified through server-observed state by T1b/D1, never by string-matching them.

**Allowlist of application SELECTs (complete; all begin `SELECT`).**
- S0 (transaction-state inspection, first statement): `SELECT current_setting('transaction_isolation') AS transaction_isolation, current_setting('transaction_read_only') AS transaction_read_only`. The service compares the result with `("repeatable read","on")` and fails closed with a value-free `RuntimeError` otherwise, before S1. S0 is the first statement in the same transaction as S1-S4, so it observes the properties that govern them.
- S1: `SELECT id, status, authority_level FROM vres.sources WHERE source_key=%s AND project_id=%s`. No row: raise the not-found `ValueError`; no further statement runs.
- S2: `SELECT vres.source_effective_trust(%s)` (the only function call permitted).
- S3: one aggregate SELECT over `vres.source_trust_events` (Section 5.3): `ledger_total`, `unrevoked_grant_count`, `distinct_unrevoked_digest_pairs` and the newest event (`ordinal`, `event_key`, `action`, `created_at`).
- S4 (inspect only): one inventory-page SELECT over `vres.source_trust_events` (Section 5.3).
Every ledger SELECT filters on both `project_id` and `source_id`. No `INSERT/UPDATE/DELETE/CALL/DO/SET/RESET/COMMIT/ROLLBACK/SAVEPOINT/LOCK/CREATE/DROP` is ever issued by the service.

**Exact application-SELECT counts per call:** `source_trust_status` on a found source: 4 (S0,S1,S2,S3). `source_trust_inspect` on a found source: 5 (S0..S4). Unknown/foreign/company-scope source: 2 (S0,S1). Validation failure: 0 (and zero connections, Section 2.1). Transaction-state mismatch at S0: 1.

## 3. Mutation: not registered
Unchanged. `source_trust_grant` and `source_trust_revoke` are **not registered**: no stub, alias, shortcut, owner bridge, preview/dry-run, disabled endpoint or token; no third name that grants, revokes, previews or authorizes. The only mutation signal is the static `mutation` field. The service module imports nothing able to write the ledger, never references `record_source_trust_decision` or `source_trust_digests`, never opens a migrator/owner connection, takes no `user_event_id`, `approval_key`, `authority_level` or `project_id` argument.

## 4. Authorization preparation - NOT implemented
Unchanged. Reproducing owner digests in Python would be a second, untrusted digest authority and the runtime role has no EXECUTE on the owner function; a future "subject preview" needs a protected read-only DB function in a new reviewed migration. Consequence (5.4): per-grant "matches current" is knowable only for the newest grant when the reader says `verified_trusted`.

## 5. Trust model, 047 decision table, scenarios and inventory

### 5.1 Rules (each traceable to `files/`)
- R1 (048). Only the newest ledger event (highest `id`) can make the source `verified_trusted`. It must be a grant with no superseding revoke and every other 048 condition.
- R2 (048). If the newest event is a `revoke`, the result is `unverified`, even if other unrevoked grants exist and even if one matches the current source.
- R3 (047). A revoke supersedes exactly one grant (the unrevoked grant with the supplied recorded digests). It does not revoke "all grants" and ignores current digests and source status.
- **R4 (047), REPLACED: ordered decision table 5.1a.** There is no unconditional dedup rule. Dedup of a fresh grant is the **seventh** step and is reachable only after replay, source-active, content, **current-digest equality** and the anchor checks have all passed.
- R5 (047). A fresh grant requires an active source, content, digests equal to the **current** recomputed ones, and a valid newest anchor. Revoke has none of the source/digest gates.
- R6 (048). A non-active source is `unverified` regardless of ledger content. The source lifecycle does not change the ledger.
- R7. Ledger events and source lifecycle are distinct: ledger `revoke` never changes `sources.status`; `source_revoke` never writes the ledger. Responses say "trust revoke" for the ledger action and never link, call or imply `source_revoke`.
- R8. The tool reports observations and the rules. It publishes **no universal repair sequence**: whether a path exists depends on the current digests, which the runtime process cannot compute (F2, Section 4).

### 5.1a Ordered 047 decision table for `record_source_trust_decision` (REPLACES R2 R4; test oracle for the fixture only, the tool never calls it)
Steps are evaluated top to bottom; the first that applies decides. "Refused" = exception, **no ledger row written**.
| Step | Condition (047 source order) | Result | Row written |
|---|---|---|---|
| 0 | invalid request / unknown task / project mismatch / unknown source | refused (`invalid_request`, `unknown_task`, `project_mismatch`, `unknown_source`) | no |
| 1 | a row with the same `(user_event_id, subject_key)` already exists | **Path 1, exact replay:** returns that recorded event, `replayed=true`. Evaluated before every grant-specific gate: no source-status, content, digest, anchor or dedup check is made, and nothing is created or restored | no |
| 2 | grant, source `status != 'active'` | **Path 5:** refused `source_not_active` (fresh request only; Path 1 has already returned for a replay) | no |
| 3 | grant, `chunk_count = 0` | refused `no_content` | no |
| 4 | grant, requested digest pair != **current** recomputed pair | **Path 2:** refused `digest_mismatch`. Fires before the anchor and before dedup, so an older **unrevoked** grant holding the requested digests does not bypass it | no |
| 5 | anchor: `anchor_invalid`, then `anchor_stale` (not the newest USER_INSTRUCTION/USER_CONTROL of the task), then `not_authorized` (text != `I authorize <subject_key>`) | refused with that reason (applies to grant and revoke; precedes dedup and `no_active_grant`) | no |
| 6 | revoke: no unrevoked grant with the supplied recorded digests | refused `no_active_grant` | no |
| 7 | grant: an unrevoked grant with identical content+descriptor digests exists (newest id first) | **Path 3, dedup:** returns that existing grant, `replayed=true`; reached only with source active, content present, requested = current digests, anchor valid. A **revoked** grant never matches | no (newest event unchanged) |
| 8 | grant, no matching unrevoked grant | **Path 4:** inserts a distinct `grant` event (existing issuer semantics only; not production issuance authority, G8 open) | yes |
| 9 | revoke, matching unrevoked grant found | inserts a `revoke` event with `supersedes_event_id` = that grant | yes |
Observations: (i) Path 1 and Path 3 both report `replayed=true` but differ: Path 1 returns the recorded row of that exact authorization, Path 3 returns a different, earlier grant for identical digests after all fresh gates passed. (ii) A dedup (Path 3) creates no record, so a repeated identical request is again Path 3, never Path 1. (iii) Neither path changes the newest event, so neither can make a source whose newest event is a `revoke` effective.

### 5.2 Scenario tables A-F
Notation: ledger rows are numbered in ascending event order = ordinals 1..n. `grant(X)` / `revoke(→k)` (revokes the grant at row k). "src@X" = source's **current** recomputed digest pair is X (A, B, C are distinct pairs). "req" = requested digest pair of the 047 call (grant or revoke); "fresh" = a new authorization event never seen by the ledger; "replay" = same `(user_event_id, subject_key)` as an existing row. "anchor ok" = valid, newest, exact authorization text. "Rows" = ledger row count before→after. Every sub-case lists the 048 result **after** the call. These tables are the test oracle for L1-L6 (the fixture, never the tool, performs the owner writes).

**Scenario A: A granted, B granted, A revoked.** Ledger: 1 grant(A), 2 grant(B), 3 revoke(→1). Unrevoked: G2(B). Revoked: G1(A). Newest = ordinal 3 (revoke). Reader before any call: `unverified`.
| ID | src@ | Request | Fresh/replay | 047 result / reason | Rows | Newest after | 048 after |
|---|---|---|---|---|---|---|---|
| A1 | B | grant req=B, anchor ok | fresh | Path 3 dedup against G2, `replayed=true` | 3→3 | 3 revoke | `unverified` |
| A2 | B | grant req=B, anchor stale | fresh | refused `anchor_stale` (step 5 precedes dedup) | 3→3 | 3 revoke | `unverified` |
| A3 | B | grant req=A | fresh | Path 2 refused `digest_mismatch` (A is revoked anyway; irrelevant) | 3→3 | 3 revoke | `unverified` |
| A4 | B | revoke req=B, anchor ok | fresh | inserts revoke(→2) | 3→4 | 4 revoke | `unverified` |
| A5 | B | re-submit the authorization that produced row 3 | replay | Path 1 `replayed=true`, returns row 3 | 3→3 | 3 revoke | `unverified` |
*Guidance for A (status/inspect output, descriptive only).* Newest event: ordinal 3, a `revoke` (key shown). Unrevoked grants: exactly one, ordinal 2, recorded digests B; revoked grant: ordinal 1. Effective reader result: `unverified` because the newest event is a revoke (R2); the reader never consults the unrevoked ordinal-2 grant, even though the tool cannot tell and does not claim that it matches the current source (`matches_current=not_evaluated`). Why no repair is prescribed: a re-grant of B is not a repair (A1: dedup, newest event stays the revoke; A2: refused before dedup if the anchor is not fresh); whether to revoke B (A4) and later issue a new grant is an authorization decision of the user that the tool neither makes nor emits as a step (R8), and the grant that would follow depends on current digests the runtime process cannot compute.

**Scenario B: A granted, B granted, B revoked.** Ledger: 1 grant(A), 2 grant(B), 3 revoke(→2). Unrevoked: G1(A). Newest = 3 revoke. Reader: `unverified`.
| ID | src@ | Request | Fresh/replay | 047 result / reason | Rows | Newest after | 048 after |
|---|---|---|---|---|---|---|---|
| B1 | B | grant req=B, anchor ok | fresh | Path 4 insert: G2 is revoked so it is not matched; all gates pass | 3→4 | 4 grant(B) | `verified_trusted` (all other 048 conditions holding) |
| B2 | B | grant req=A | fresh | Path 2 refused `digest_mismatch` although unrevoked G1(A) holds A | 3→3 | 3 revoke | `unverified` |
| B3 | A | grant req=A, anchor ok | fresh | Path 3 dedup against unrevoked G1 | 3→3 | 3 revoke | `unverified` |
| B4 | A | revoke req=A | fresh | inserts revoke(→1) | 3→4 | 4 revoke | `unverified` |

**Scenario C: restore to older digests.** Two ledgers.
C-i (R2 ledger): 1 grant(A), 2 grant(B), 3 revoke(→1); source restored so src@A. Unrevoked: G2(B) (≠ current). Newest 3 revoke. Reader `unverified`.
| ID | src@ | Request | Fresh/replay | 047 result / reason | Rows | Newest after | 048 after |
|---|---|---|---|---|---|---|---|
| Ci1 | A | grant req=A, anchor ok | fresh | Path 4 insert: G1 is revoked, no unrevoked A-grant; restoration does not revive it | 3→4 | 4 grant(A) | `verified_trusted` (other conditions holding) |
| Ci2 | A | grant req=B | fresh | Path 2 refused `digest_mismatch` | 3→3 | 3 revoke | `unverified` |
| Ci3 | A | revoke req=B | fresh | inserts revoke(→2) | 3→4 | 4 revoke | `unverified` |
C-ii (handoff ledger, no revoke): 1 grant(A), 2 grant(B); source restored so src@A. Unrevoked: G1(A) matches current but is not newest; G2(B) is newest. Reader `unverified` (newest grant ≠ current digests).
| ID | src@ | Request | Fresh/replay | 047 result / reason | Rows | Newest after | 048 after |
|---|---|---|---|---|---|---|---|
| Cii1 | A | grant req=A, anchor ok | fresh | Path 3 dedup against G1 (unrevoked, digests equal current) | 2→2 | 2 grant(B) | `unverified` |
| Cii2 | A | grant req=B | fresh | Path 2 refused `digest_mismatch` | 2→2 | 2 grant(B) | `unverified` |
| Cii3 | A | revoke req=B | fresh | inserts revoke(→2) | 2→3 | 3 revoke | `unverified` |

**Scenario D: attempted re-grant of an unrevoked newer grant after an older revoke.** Ledger: 1 grant(A), 2 grant(B), 3 revoke(→1); src@B. Unrevoked G2(B). Newest 3 revoke. Reader `unverified`.
| ID | src@ | Request | Fresh/replay | 047 result / reason | Rows | Newest after | 048 after |
|---|---|---|---|---|---|---|---|
| D1 | B | grant req=B, anchor ok | fresh | Path 3 dedup, `replayed=true`, no row | 3→3 | 3 revoke | `unverified` |
| D2 | B | the identical request again | fresh (dedup wrote no record, so it is not an exact replay) | Path 3 again | 3→3 | 3 revoke | `unverified` |
Inspect output is byte-identical before and after D1/D2.

**Scenario E: several unrevoked grants plus a latest revoke.** Ledger L_E: 1 grant(A), 2 grant(B), 3 grant(C), 4 revoke(→2). Unrevoked: G1(A), G3(C). Revoked: G2(B). Newest 4 revoke. Reader `unverified` in every state of src@. `unrevoked_grant_count`=2, `distinct_unrevoked_digest_pairs`=2.
| ID | Ledger | src@ | Request | Fresh/replay | 047 result / reason | Rows | Newest after | 048 after |
|---|---|---|---|---|---|---|---|---|
| E1 | L_E | B | grant req=A, anchor ok | fresh | Path 2 refused `digest_mismatch` (current is B, not A) although G1(A) is unrevoked; no dedup | 4→4 | 4 revoke | `unverified` |
| E1b | L_E | B | grant req=C | fresh | Path 2 refused `digest_mismatch` | 4→4 | 4 revoke | `unverified` |
| E2 | L_E | C | grant req=C, anchor ok | fresh | Path 3 dedup against G3, no row | 4→4 | 4 revoke | `unverified` |
| E2b | L_E | C | grant req=A | fresh | Path 2 refused `digest_mismatch` | 4→4 | 4 revoke | `unverified` |
| E3 | L_E + row 5 revoke(→1) | A | grant req=A, anchor ok | fresh | Path 4 insert: the only A-grant (G1) is revoked, so it is not matched | 5→6 | 6 grant(A) | `verified_trusted` (other conditions holding) |
| E4 | L_E | C | (read-only observation, no 047 call) | n/a | newest is a revoke while two unrevoked grants exist; tool shows both, no automatic recovery, `situations` per below | 4→4 | 4 revoke | `unverified` |
| E5 | L_E | B | re-submit the authorization that produced row 3 (grant C) | replay | Path 1 `replayed=true`, returns row 3 although req=C ≠ current B (replay precedes `digest_mismatch`) | 4→4 | 4 revoke | `unverified` |

**Scenario F: inactive source with an unrevoked grant.** Ledger: 1 grant(A); source was src@A, then `source_revoke` set `sources.status` to a non-active value. Unrevoked G1(A). Newest 1 grant. Reader `unverified` (R6).
| ID | src@ | Request | Fresh/replay | 047 result / reason | Rows | Newest after | 048 after |
|---|---|---|---|---|---|---|---|
| F1 | A | grant req=A, anchor ok | fresh | Path 5 refused `source_not_active` (step 2, before digest, anchor and dedup) | 1→1 | 1 grant | `unverified` |
| F2 | A | re-submit the authorization that produced row 1 | replay | Path 1 `replayed=true`, returns row 1: replay does not require an active source and does not create or restore trust | 1→1 | 1 grant | `unverified` |
| F3 | A | revoke req=A, anchor ok | fresh | inserts revoke(→1): not gated by source status | 1→2 | 2 revoke | `unverified` |
The lifecycle change itself adds no ledger row (ledger count unchanged); restoring `sources.status` is outside this design.

Normative: the status/inspect response for each ledger state must show exactly the observations implied by the row (5.3) and the situation codes below; guidance text is limited to R1-R8 and the neutral descriptions above. Tool output never contains a request-result column: the 047 columns are fixture oracle content only.

Situation codes (`trust_explanation.situations`, fixed order, zero or more): `no_ledger_events` | `source_not_active` | `newest_event_is_revoke` | `newest_revoke_with_unrevoked_grants_present` (newest is a revoke and `unrevoked_grant_count>0`; R2) | `newest_grant_unrevoked_reader_unverified` (only when the source is active and the newest event is an unrevoked grant, yet the reader declines for a reason it does not expose; the tool names no cause) | `effective`. `trust_explanation` also contains `{newest_event_action, unrevoked_grant_count, distinct_unrevoked_digest_pairs, source_active, reader_result, inventory_complete}`, the `rules` list (R1-R8 fixed one-line texts), `executed:false`, `no_universal_repair_sequence:true`, `production_execution:"disabled_g8_open"`. No `recovered` field.

### 5.3 Inventory interface (bounded, project-scoped, deterministic)
Aggregate S3, over the whole ledger of the source (not limited by `limit`): `ledger_total`, `unrevoked_grant_count`, `distinct_unrevoked_digest_pairs`, and the newest event as exactly the `newest_event` object of Section 2.2 (`ordinal`, `event_key`, `action`, `created_at`; `null` iff `ledger_total==0`). `inventory` object (inspect only, from S4):
```
{ "ordering": "ordinal_descending", "limit": <n>, "returned": <int>, "ledger_total": <int>,
  "truncated": <bool>, "inventory_complete": <bool>,        // complete iff returned == ledger_total
  "events": [ { "ordinal": <int>, "event_key": "STE-...", "action": "grant"|"revoke", "created_at": "<ISO-8601>",
                "content_digest": "<64hex recorded>", "descriptor_digest": "<64hex recorded>",
                "is_newest": <bool>,
                "grant_state": "unrevoked"|"revoked"|null,          // null for revoke events
                "revoked_by_event_key": "STE-..."|null,             // grants only
                "revokes_event_key": "STE-..."|null,                // revokes only (derived supersedes_event_key)
                "matches_current": "verified_by_reader"|"not_evaluated" } ] }
```
The first four fields of each event use the same names, order and value types as `newest_event`; the event with `is_newest=true` is the one whose first four fields equal `newest_event` (it is present in `events` whenever `returned >= 1`, because the page is ordinal-descending). Example (Scenario A, limit 20): `events[0] = {"ordinal":3,"event_key":"STE-...","action":"revoke","created_at":"...","content_digest":"<A>","descriptor_digest":"<A'>","is_newest":true,"grant_state":null,"revoked_by_event_key":null,"revokes_event_key":"<key of ordinal 1>","matches_current":"not_evaluated"}`.
- `ordinal` = `row_number() OVER (ORDER BY id)` over the source's full ledger. The page is `ORDER BY ordinal DESC LIMIT n`; when `truncated`, `inventory_complete=false` and the explanation carries `inventory_complete:false`.
- `revokes_event_key` is derived by `LEFT JOIN source_trust_events t ON t.id = e.supersedes_event_id AND t.project_id = e.project_id AND t.source_id = e.source_id`; `revoked_by_event_key` by a correlated subselect under the same project/source scope. Physical ids are never returned.
- **Fail closed** (value-free `RuntimeError("source trust inventory inconsistent")`, nothing partial returned) when: a revoke has no joined target; a grant has a `supersedes_event_id`; the target is not a grant or has an ordinal not lower than the revoke; a grant has more than one superseding revoke; two events share an ordinal; `ledger_total` differs between S3 and S4's window; the S3 `newest_event` differs from the ordinal-maximum row of S4 when it is on the page.
- Digests in `events` are recorded ledger facts, never labelled as current.

### 5.4 The `matches_current` limitation
Python must not recompute digests (F2). `matches_current` is `verified_by_reader` only for the newest event when it is a grant and the reader returned `verified_trusted`; for every other event, and for all events when the reader returns `unverified`, it is `not_evaluated`. The response never implies a grant does or does not match the current source when it is `not_evaluated`. Broader comparison needs the future protected read-only DB function of Section 4.

## 6. G8 statement carried in every response
Unchanged: `host_authenticated:false`, `g8:"open"` and the `attestation_class` string. A `user_prompt` task event alone is not a G8 solution; a token readable by the same agent process is not an origin proof. A future issuer needs an independently protected host/user channel with separate design and protected review.

## 7. Compatibility, rollback, permissions
Unchanged. No migration, role, grant, policy, 047 or 048 change. Additive: two MCP tools and one service module. Rollback = remove them. `tests/test_runtime_surfaces.py` pin moves 52 to 54, adding exactly the two names.

## 8. Acceptance matrix (RED first; tests written before implementation; nothing is executed in this design round)
Classes: **U** unit (fake connections, no database), **I** integration (isolated PostgreSQL cluster, system id 7694553000872930884, never the control cluster 7685334034094099024; role-split fixture; the privileged owner principal exists only inside the fixture to create ledger events and never reaches the tool), **S** security, **R** registration, **P** privilege. A row passes only when its assertion has run and its output was read. Rows unchanged from R2 keep their R2 wording; changed rows are marked **(R3)**.

| ID | Class | Area | Assertion (exact pass condition) |
|---|---|---|---|
| R1 | R | Registry | `len(registered)==54`; `registered - BASELINE_52 == {source_trust_status, source_trust_inspect}`; both present. |
| R2 | R | Registry | `source_trust_grant`, `source_trust_revoke` absent; no registered name matches `source_trust_(grant|revoke|preview|authorize|issue|bind|enable|mutate)`; no other new name. |
| R3 | R | Registry | Both tools use `@mcp.tool()`; schemas accept only `source_key` (+ `limit` for inspect). |
| V1 | U | Validation | Non-dict, `project_id`, unknown field, missing key, non-str, bytes, blank, 201 chars, NUL, CR/LF/control chars, `limit` of 0/51/-1/True/1.5/"5": each raises `ValueError`; instrumented `connect` and `_trusted_project_id` factories record zero calls and zero SQL. |
| V2 | U | Validation | Error text for every V1 case contains none of the supplied values (sentinel key). |
| V3 | U | Validation | Boundary success: 200-char key; `limit` 1 and 50. |
| T1 | U | Transaction configuration **(R3)** | With a fake connection that records (i) attribute assignments and (ii) statements passed to `execute`, in one shared ordered log: `isolation_level == REPEATABLE_READ` and `read_only == True` are assigned, in that log, **before the first `execute`**; the first `execute` is S0 (the `current_setting` pair); exactly one runtime connection is opened for the snapshot. Fail-closed cases, each with a value-free error and **no S1-S4 executed**: S0 returns any value other than `("repeatable read","on")`; an attribute assignment raises; the fake reports a transaction already started. The test asserts **no** `BEGIN`/`SET TRANSACTION`/`START TRANSACTION` string is passed to `execute` by the service (driver-emitted transaction control is not part of the application log). |
| T1b | I | Transaction state (real login) **(R3, new)** | Real restricted runtime login (never the migrator/owner), real PostgreSQL: through a connection hook that wraps the service's own connection, after S4 and before the transaction ends, a probe on the same connection returns `transaction_read_only='on'`, `transaction_isolation='repeatable read'` and `pg_current_xact_id_if_assigned() IS NULL` (so S0 and S1-S4 ran in that same transaction and no write xid was assigned); the S0 result captured by the service equals that pair. A fixture that makes the attribute configuration ineffective (a connection wrapper that drops the attribute assignment) must make the call fail closed at S0, proving S0 is not a vacuous check. |
| T2 | U | Application SQL classification **(R3)** | The wrapper log of statements passed to `execute` equals, in order, exactly `[S0,S1,S2,S3]` for status, `[S0,S1,S2,S3,S4]` for inspect, `[S0,S1]` for unknown/foreign/company-scope sources, `[S0]` on a transaction-state mismatch and `[]` on validation failure; every entry matches the allowlist of 2.4 (all start with `SELECT`; S2 is the only function call, and it names only `vres.source_effective_trust`); no `INSERT/UPDATE/DELETE/CALL/DO/SET/RESET/COMMIT/ROLLBACK/SAVEPOINT/LOCK/CREATE/DROP`; every ledger SELECT binds both `project_id` and `source_id`. T2 asserts nothing about driver-emitted transaction control; that is T1b's job. T1 (attribute order, no hand-written transaction SQL) and T2 (application log) read the same log and cannot contradict each other: attribute assignments are not statements, and statements are never transaction control. |
| T3 | I | Fail-closed on setup failure **(R3, new)** | On a real connection, if the transaction cannot be configured (attribute assignment refused or S0 mismatch), the call raises a value-free error, zero application SELECTs beyond S0 are executed (T2 log), and the ledger and sources are unchanged. |
| D1 | I | DB read-only | See T1b; additionally at transaction end `pg_current_xact_id_if_assigned() IS NULL` (no xid). |
| D2 | I | DB read-only | Row counts of `source_trust_events`, `sources`, `knowledge_chunks`, `task_events`, `approval_events`, `tasks` unchanged after repeated status/inspect calls; ledger max(id) unchanged; no source mutation (`sources` rows byte-identical). |
| D3 | P | Privilege | Runtime role: INSERT/UPDATE/DELETE on `source_trust_events` denied; EXECUTE on `record_source_trust_decision` and `source_trust_digests` denied; EXECUTE on `source_effective_trust` allowed; the service never uses another role. |
| D4 | I | Snapshot consistency **(R3)** | A concurrent ledger append by the fixture between S2 and S3 (hook) is invisible to S3/S4 of the same call: `ledger_total`, `newest_event` and `events` are mutually consistent and reflect the snapshot taken at S0/S1; the next call sees the append. Claims no more than that. |
| L1 | I | Scenario A **(R3)** | Fixture ledger A. Tool output: `ledger_total` 3, `newest_event` = {3, key, `revoke`, ts}, unrevoked grant ordinal 2 listed, reader `unverified`, `situations` = [`newest_event_is_revoke`, `newest_revoke_with_unrevoked_grants_present`], guidance per 5.2 A. Fixture 047 calls A1-A5 each return exactly the Result/Rows/Newest/048 columns of the table (A1 dedup 3→3; A2 `anchor_stale`; A3 `digest_mismatch`; A4 revoke 3→4; A5 replay 3→3). |
| L2 | I | Scenario B **(R3)** | Fixture ledger B: B1-B4 per table (B1 insert 3→4, then `verified_trusted`; B2 `digest_mismatch`; B3 dedup; B4 revoke). |
| L3 | I | Scenario C **(R3)** | Fixture ledgers C-i and C-ii: Ci1-Ci3 and Cii1-Cii3 per table (Ci1 new event, not dedup; Cii1 dedup, newest remains grant B, `unverified`). |
| L4 | I | Scenario D **(R3)** | D1 and D2 both dedup (rows 3→3, newest revoke, `unverified`); inspect output identical before and after both. |
| L5 | I | Scenario E **(R3, replaces R2 L5)** | Each of E1, E1b, E2, E2b, E3, E4, E5 asserted **individually**, each with its own fixture state, with the fixture setting the source to the stated src@ before the call and asserting the **current digest pair** by reading it from the owner digest function (fixture only) before the request: E1/E1b/E2b `digest_mismatch`, rows unchanged; E2 dedup, rows unchanged, newest revoke; E3 new grant event (rows 5→6) then `verified_trusted`; E4 tool output shows `unrevoked_grant_count`=2, `distinct_unrevoked_digest_pairs`=2, reader `unverified`; E5 replay returns row 3 although req≠current. No assertion anywhere claims dedup of a pair that differs from the source's current pair. |
| L6 | I | Scenario F **(R3)** | F1 `source_not_active`; F2 Path 1 replay with `replayed=true` and reader still `unverified`; F3 revoke succeeds; ledger count unchanged by the lifecycle change itself; `situations`=[`source_not_active`]. |
| L7 | I | Inventory | Ordering ordinal descending; `revokes_event_key`/`revoked_by_event_key` match the fixture's links in A-E; no physical ids in any output (large sentinel ids absent). |
| L8 | I | Truncation | `limit` < `ledger_total`: `truncated=true`, `inventory_complete=false`, counts and `newest_event` from the full ledger; `limit` ≥ total: `inventory_complete=true`. |
| L9 | I | Fail closed | Corrupt rows injected by the fixture owner (revoke with missing/foreign-source target, grant with a target, two revokes for one grant): value-free inconsistency error, nothing partial. A supersedes target in another project/source does not join. |
| L10 | U | matches_current | `verified_by_reader` only on the newest unrevoked grant when the reader says `verified_trusted`; otherwise `not_evaluated`; the module computes no digest (no hashlib/sha use). |
| N1 | U/I | newest_event schema **(R3, new)** | Status and inspect both return `newest_event` with exactly the keys `ordinal, event_key, action, created_at` (this order, no others) or `null` iff `ledger_total==0`; the status and inspect values are equal; in `inventory.events` the `is_newest` entry's first four fields equal it; present even when `limit`=1 and when the page is truncated. |
| C1 | I | Control | CR or LF in `source_type`, `origin` or `version`: reader `unverified` although the newest grant is unrevoked; the tool reports the reader verdict, not a cause. |
| C2 | I | Control **(R3)** | Nullability per F8. `origin` and `version`: NULL and `''` are equivalent normalized absence: the same source content granted under `origin`/`version` NULL and under `''` yields `verified_trusted` in both forms. `source_type` is `NOT NULL` (schema check `information_schema.columns.is_nullable='NO'` for `vres.sources.source_type`), so a NULL `source_type` is not a reachable state and no test fabricates one; the empty string `''` for `source_type` is not tested as a trust equivalence (out of scope); the CR/LF exclusion of C1 covers all three columns. The test does not alter the schema. |
| C3 | I | Control | Ledger revoke vs `source_revoke`: after a ledger revoke `source_status` stays `active`; after `source_revoke` the status is non-active and `ledger_total` unchanged; responses and docstrings call the first "trust revoke" and never invoke or link `source_revoke`. |
| C4 | I | Control | Company-scope source (NULL project), another project's source and unknown key give byte-identical errors. |
| C5 | I | Control | Source with zero chunks after a grant (fixture owner removes chunks): reader `unverified`; status shows it without error. |
| C6 | I | Control | Conflicting labels: `trusted_project_source` with no grant: `unverified`, `label_is_evidence=false`; `external_untrusted_observation` with a valid grant: `unverified`; the label is echoed truncated to 64 chars and flagged non-evidence. |
| C7 | I | Control (positive) | Fixture-granted, active, matching source: `verified_trusted`, newest event that grant, `matches_current=verified_by_reader` for it only. |
| I1 | S | Isolation/privacy | Recursive scan of every response: no key named `project_id`, `project_key`, `project_name`; no value equal to the fixture project's id (large sentinel), key or name; sentinels in title, `path_or_uri`, origin, version, metadata, chunk text, task keys, user event payload, anchor text, subject_key never appear. |
| I2 | S | Isolation | Project P1 caller never sees P2's source, ledger events, counts or labels; identical error as C4. |
| I3 | S | Isolation | Two projects with sources of the same key pattern: each caller sees only its own ledger. |
| X1 | S | Authority | AST/import check of the service module: no import of database_boundary writers, no reference to `record_source_trust_decision`, `source_trust_digests`, `migrator`, owner DSN/credential names, no `user_event_id`/`approval_key` parameters. |
| X2 | S | Authority | Tools accept no `user_event_id`, `approval_key`, `authority_level`, `project_id`; a forged `user_event_id`/approval row cannot make a source `verified_trusted`. |
| X3 | S | Authority | Module public-name allowlist equals the two tools; no alias, helper, dry-run or preview reaches a ledger write. |
| X4 | S | Authority | `mutation` is static `{available:false, reason:"g8_host_ingress_open"}`; no response contains an executable step, `recovered`, or `executed:true`. |
| G1 | U | G8 | Every response carries `host_authenticated:false`, `g8:"open"` and the attestation class string. |
| S1 | I | Policy | Policy version/digest in responses equal `176.g7.v1` / `f20b...cf03` and the ledger rows; 047, 048 and policy files byte-identical (hash check in the gate). |

Fixture-only privileged SQL never runs in unit tests, and no test executes in this design round.

## 9. Obligations unchanged
G8 OPEN; positive production issuance DISABLED; Chunk 3 completion BLOCKED_ON_G8; the e6 and user-event-writer journeys deferred merge gates OPEN; Chunk 4 cross-statement consistency; B4B-v1 flood/varied-poison unresolved; G1/G2 obligations OPEN. No commit/push without separate authorization.

## 10. Change log
See `CHANGES_R2_TO_R3.md` (clause-level ledger with reviewer checks). R1 -> R2 history is in `files/prior/R2_CONTRACT_FAILED_VAL-f49f4752ef064749.md` Section 10.
