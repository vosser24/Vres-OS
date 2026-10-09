# E7 G7 derived-staleness clarification (additive, 2026-10-09)

Status: **PROPOSED, not accepted** until an independent review accepts it. It amends no earlier document; the source-trust attestation contract and the design-freeze errata stay byte-for-byte unchanged. Policy `176.g7.v1` and its digest `f20b037b00d0a5711666fd6c1d98538101708d99e7f6f32cf5a490ff6b96cf03` are not touched.

Trigger: Chunk 2 review (reader migration 048) found that reverting content byte-for-byte to the granted state makes `vres.source_effective_trust` return `verified_trusted` again. The user decided (Option 1) how the contract is to be read.

## 1. The contradiction in the original contract
Attestation contract section 5 says chunk or descriptor changes after attestation make trust "*stale* at read time with no write needed", i.e. staleness is **derived from current digests**. Section 6 (state machine) says "STALE returns to CURRENT only through a *new* grant for the new digests; an old approval never transfers". Read literally together with a derived read, these disagree for one case: current digests return to the granted digests. Section 5 yields `verified_trusted`; section 6's literal wording yields `unverified`. No frozen test row (matrix G, H, J, N) covers the case.

## 2. Resolution: current-digest identity, not mutation history
G7 v1 effective trust is an authorization bound to the **current exact identity** of a source: `(project_id, source_key)`, the current content digest and the current descriptor digest, as the owner function `vres.source_trust_digests` recomputes them in the same statement as the read. It is not a statement that the source was never modified. G7 v1 has no owner-controlled content-revision or mutation-history record and does not claim one; none is added.

## 3. Exact-current-state re-verification
If content or a bound descriptor changes, the result is `unverified` immediately. If the complete original content and bound descriptor are restored exactly (digest-equal to the granted digests), the **same still-valid grant** may evaluate as `verified_trusted` again with no new grant, provided every other reader condition still holds. The user authorized exactly those digests; the restored state is that state.

## 4. A different identity needs a new grant
An approval for state A never applies to a state with different digests. Any different content or descriptor needs a new exact user authorization for its own subject key. A different source (`source_key` or `project_id`) cannot borrow another source's grant by presenting matching content; the ledger row must match the source identity and re-derive its own subject key.

## 5. Descriptor changes
The policy dict line `descriptor_change=requires_new_authorization` is read as: a descriptor that differs from the one granted needs a new authorization to be trusted. It does **not** require one to re-trust a descriptor that again equals the granted one. Content and descriptor are treated identically: both digests must equal the granted pair.

## 6. Revocation is permanent until a separately authorized re-grant
A ledger `revoke` that supersedes a grant disqualifies that grant for good. Restoring digests never reactivates it. Only a new grant, authorized by the user for the subject key, can restore trust after revocation. A source whose `status` is not `active`, or whose project scope is missing, is `unverified` regardless of digests; source revocation is likewise not undone by content restoration.

## 7. No mutation-history tracking in G7 v1
No security claim of permanent or history-sensitive staleness is made. A consumer that needs "never modified since approval" semantics needs a future, separately designed and reviewed mechanism (owner-controlled revision events and their migration authority). That is out of scope and not implied.

## 8. Policy identity
This is a reading of existing semantics under policy `176.g7.v1`. The policy dictionary and digest are unchanged. If a reviewer finds the reading contradicts the frozen policy identity so that a new policy version is needed, work stops and the exact conflict is returned; the dict is not silently changed.

## 9. Nothing relaxed
Unchanged and still required for `verified_trusted`: active source with project scope; newest ledger event is an unrevoked user-approval grant under the current policy version and digest; ledger/source identity and subject-key consistency; re-verified user-authored authority anchor with whole-message `I authorize <subject_key>`; `chunk_count > 0`; no `external_untrusted_observation` label; any missing, corrupt, contradictory or unknown evidence is `unverified`. `authority_level`, `metadata` and `content_hash` remain non-evidence. Expiry stays `none`; a non-NULL `expires_at` never yields trust.

## 10. Recorded limitations and obligations
- **Older-grant revoke (accepted fail closed).** A revoke of an older grant issued after a newer grant becomes the newest event and suppresses the newer grant. The 047 issuer returns the existing active grant rather than writing a new row, so a plain re-grant does not help. Recovery today: an explicitly authorized revoke of the active grant, then a new authorized grant. Append-only history and exact authorization are preserved. **Chunk 3 obligation:** a usable recovery path with deterministic regression evidence, without changing event ordering or migration 047.
- **Chunk 4 obligation.** The reader is consistent within its own single statement. Atomicity of a later E5 operation that reads trust and chunk content in separate statements is not claimed and must be specified and tested in Chunk 4.
- G8 (host ingress authenticity) remains **OPEN**; the ledger anchor is a user-authored event in the database, not a host-authenticated one. Positive-trust production issuance stays disabled.
