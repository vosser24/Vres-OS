# Vres-OS #165 — B2B Trusted Chairman Authority Contract, REVISED DESIGN R1

**Date:** 2026-10-23, Europe/Athens.
**Status:** REVISED DESIGN DRAFT R1 / INDEPENDENT R1 REVIEW NOT_RUN / NO TRUST PROVIDER / NO AUTHORITY ISSUED / NOT IMPLEMENTED.
**Repository:** vosser24/Vres-OS.
**Canonical docs branch:** docs/chatgpt-continuity-20261023.
**Current accepted source foundation:** feature/165-chairman-policy-foundation-20261023 at 32847410952e9d4620bf7046cbee4a41a7ddc73b (B2A R3 offline ACCEPT only).
**Historical reviewed v0:** docs/architecture/VRES-165-B2B-TRUSTED-CHAIRMAN-AUTHORITY-CONTRACT-DRAFT-2026-10-23.md; Git blob 851f5323888bfd3043ba992abc8096834ee356d0; Claude verdict DESIGN_REVISE, marker VRES_165_B2B_DESIGN_REVIEW_COMPLETE.
This is a separate R1 design, not an amendment to the v0 document that Claude originally reviewed. R1 has NOT been independently accepted.

## 1. Scope, hard decisions and non-claims

The central issue F1 is not SHA-256 chain computation. It is trust in the **source** of the expected chain identity and in the separately demonstrated operator intent and protected validation. The accepted B2A method compares canonical history bytes to caller-SUPPLIED expected count/history/latest SHA. A malicious caller can forge both history and expectation and still get equality. B2B must not promote comparison, a locally constructed evidence object, a stored status label, chat text, a rationale, agent-generated output, a model identifier, or telemetry into approval.

R1 decides the dependencies and deny-by-default interfaces required before an authority implementation can exist. No real consent provider, secure monotonic anchor store, user-presence verifier, protected Fable validator, positive authorization issuer, signing key, installer, or model observation exists under this document. Those are B2B-2/B2C/B2D future operations requiring independent design/security review and explicit user permission. **B2B-1 may only define pure in-memory inert descriptors and REFUSED/INDETERMINATE results; no permit variant.**

Current installed Chairman remains Sonnet/high; Opus/medium is the explicit requested *candidate* only. Issue #165 remains OPEN/PARTIAL. No main merge or installation follows from this design.

## 2. Attacker tiers and testable independence requirement (F-02)

- **T1 — input/candidate adversary:** submits or edits chat text, proposal rationale, JSON, digests, manifests, prompts, telemetry and ordinary files; may assert "operator approved" or "Fable PASS".
- **T2 — same-Windows-user code adversary:** an AI coding agent, compromised plugin, hook or subprocess operating with the user's normal OS-user permissions can execute code, write user-controlled files and registry keys, manipulate same-user processes and timestamps, read and write same-user DPAPI-protected data, and spoof UI/text it controls. Treat **Claude Code permission prompts, auto-accept status, project hooks, CLI approval text, and same-user agent logs as UNTRUSTED** for policy authority.
- **T3 — administrator/SYSTEM or fully compromised trusted-provider infrastructure:** beyond the intended B2B-2 T2-resistance guarantee; later implementation must state narrower assumptions, logging, exposure and operational controls rather than pretending T3 cannot attack.

**Positive trusted consent and anchor independence MUST resist T2.** Storage writable by ordinary same-user agents—including a local "protected" JSON file, same-user registry key, ordinary per-user DPAPI ciphertext or a GitHub file whose credential the agent controls—is NOT independently anchored authority. A future trusted provider must enforce a user-presence/consent action the agent cannot script or spoof and hold monotonic anchor updates behind a different security principal or trust boundary inaccessible for write by the T2 adversary. The choice of provider is DEFERRED; candidate options such as Windows Hello/TPM-assisted user presence, a separately permissioned service, or an external independent store require their own security assessment, T2 adversary test and express operator approval. A named vendor or technology is not by itself sufficient.

The trusted provider must also attest which principal/session/channel actually confirmed the displayed action; the operator's normal user SID on its own is not proof of user intent. No mock, toy signing key, self-written local data or read-back from GitHub can satisfy this production requirement.

## 3. Canonical evidence schemas, target identity and digest domains (F-12 to F-14)

Logical contracts are versioned; **no live evidence objects are created here**. Future code must strictly allowlist accepted schemas and fields, reject duplicate/unknown/missing fields, reject obsolete weaker schema versions and refuse cross-type digest substitutions. Never implicitly upgrade an old event or omit required bindings.

Separate domains must include a stable type discriminator, purpose and schema version inside canonical bytes, e.g. a distinct conceptual prefix for operator-event v1, pre-anchor v1, new-anchor v1 and protected-validation v1 before SHA-256 hashing. Never assume two 64-hex digests are interchangeable merely because they have the same format. Preserve the accepted legacy B1/B2A canonical history hashes **unchanged**; new B2B evidence domain hashes refer to separate evidence schemas and must explicitly bind to, not silently redefine, those history identifiers.

The **installation target** must have a canonical identity: machine identity, authenticated OS user SID, resolved real installation root, Vres installation instance ID and release identity. Normalize paths under a trusted OS facility. Windows symlink, junction or reparse-point substitution must be refused at the actual future write boundary. An agent cannot supply an alternative "equivalent" target path or another user's scope. The target fingerprint is included in operator consent, validation, anchor and installer evidence.

Canonical policy fields bind family alias, effort, version and policy digest; the release binding includes source commit, template content digest, rendered content digest and protected worker/validator pre-state pin digest. Requested policy data, resolved-provider identity and installed-byte observation are distinct artifacts and must never be conflated.

## 4. Trusted pre-head and linear event → validation → anchor sequence (F-01, F-06, F-08)

**There is exactly one authority-bearing order.** No circular reference to a "new trusted head" may appear in the event before that head exists.

1. A future independent trusted anchor provider authenticates and reads **H_n**, the actual CURRENT anchor: epoch e_n, type-tagged anchor digest h_n, canonical proposal history count/digest/latest proposal digest, current installed/protected policy and validator pins, target identity, and provider identity. This read must come from a T2-resistant provider, not from the candidate's manifest or a stale local copy. At R1 design stage there is no such provider; therefore this step CANNOT return verified.
2. Untrusted source constructs a proposed candidate **C**, its bounded canonical history H_candidate, policy bytes and intended template/release/target digests. These describe the **proposed successor**, not an already trusted H_(n+1). B2A may compare candidate bytes with a caller-supplied triple but that comparison has no authority. A trusted provider must independently check C extends actual H_n under the history rules before any positive event; invalid prefix, changed prior head, stale counts and same-parent forks are REFUSED.
3. The trusted consent provider constructs a fresh nonce/challenge and **renders from verified canonical fields itself** an unspoofable approval surface showing old → requested family/effort/version, prior anchor epoch/head and proposed successor summary, user/machine/install target, source/release/template identity, permitted resolved-model family rule, and pre-state validator pins. It must NOT display the agent's natural-language summary as the authoritative description. Event E binds H_n (h_n and e_n), the **proposed** C/history/policy digests, exact target and purpose, challenge, authenticated user/session, intended action and expiry. The event NEVER claims H_(n+1) has already been anchored. If the operator declines, cancels or cannot verify the exact provider-rendered details, no positive consent event exists.
4. An independently governed protected validator validates **E and C against H_n** using the protected validator and worker pins selected from the **pre-state H_n or a separate trust root**, NOT by the candidate. Evidence V binds E's digest, H_n, C/history/policy, source/template/release, target, required pin identities and actual validation outcome. A textual model response or agent-chosen route is not evidence. See §6.
5. At the authority commit boundary, the independent provider rechecks event uniqueness, user/session scope, cancellation/revocation, trusted provider-based freshness and exact epoch/head. It performs **atomic compare-and-swap** against unchanged H_n, atomically consumes event/nonce and records H_(n+1) with digest(E), digest(V), predecessor h_n, next epoch and authorized *intent* for C. Concurrent success for a different successor, any mismatch, expired event, forged/missing validation or reused nonce/event is REFUSED. The CAS is protected from T2 writes.
6. **H_(n+1) is an authorized intended head, NOT proof of installed files or provider-side model execution.** It must explicitly indicate pending installation as an *evidence-backed derived condition*, not a stored permission flag. Actual installation is a distinct B2C operation under §9 with byte read-back and recovery rules.

No event obtains an identity by pointing at the future anchor; the **new anchor points back to** the event and validation. A future optional prevalidation step may produce non-authorizing diagnostic output, but it MUST be redone or bound after the actual verified consent E; it cannot serve as protected authorization alone.

## 5. Event freshness, replay, cancellation and revocation (F-07, F-08, F-11)

Epoch freshness is primary: E is valid only for the currently protected H_n and e_n; any advance makes an event against old H_n stale. A nonce is issued and tracked by the trusted provider, not selected by the candidate or agent. An event is consumed exactly once in the same atomic CAS transaction that advances the protected head; reuse under another user, project, target or anchor epoch is refused. Expiration and cancellation/revocation must be checked both before authorization CAS and before any B2C install commit.

**Proposed maximum consent validity: 300 seconds** measured by the trusted provider's own non-rollback-capable clock/freshness evidence. Untrusted local OS wall-clock time is never authoritative under T2. If the future provider cannot make this guarantee, no positive event may be accepted; B2B-1 returns INDETERMINATE/REFUSED. The 300-second policy is a draft upper bound subject to separate security and operator approval, not a running timer or an issued event.

Cancellation/refusal/expiry BEFORE CAS invalidates E; no advancement. Revocation or cancellation after H_(n+1) has advanced but before installation requires a separately verified **forward** anchor/evidence transition that blocks staging/installation; never delete or roll back the protected epoch, and never automatically install an earlier policy. Revocation after installation triggers an explicit separately authorized remediation request and cannot itself silently demote the Chairman. Any policy demotion, reapplication of an older model or rollback requires the SAME full new consent/validation/evidence chain and a FORWARD anchor epoch, never replay of old valid approval.

If an installation has already begun and a consent event expires or is revoked, the trusted install boundary must re-read independent evidence and fail closed. A newer revoke/refuse for the same prior head or event, if authentically anchored, outranks an uncommitted approval. No agent-local "allow" cache is authoritative.

## 6. Protected validator independence and exact evidence binding (F-04)

The validator identity/version and protected worker/validator model pins used for approval MUST derive from H_n, the existing installed governing policy or a separately held protected trust root. **A candidate cannot nominate, weaken, or route around its own validator.** A candidate proposing changes to a validator or its pins is reviewed under PREVIOUS pins and needs explicitly rendered consent including that pin change; positive protected trust issuance is still disabled.

The validator must be independent of the agent/proposer supplying C. Its provenance verifier (not merely a model's text) binds the exact authenticated event digest, h_n/e_n, C/history/count/head, requested policy bytes and digest, source/template/release/render digests, canonical target, old protected pins and exact validation outcome. It must reject stale, cross-event, cross-target, cross-policy, replayed or forged outcomes. Ordinary "Fable PASS" text, a free-form chat result, an agent-chosen validator identity or self-generated signature is never positive evidence.

Actual protected Fable validation, its routing infrastructure, authenticated provenance and trust issuance are **NOT AVAILABLE OR AUTHORIZED** in B2B-0/B2B-1. A future adapter must be independently inspected before any positive result is possible.

## 7. Derived state machine, terminal outcomes and deny-only B2B-1 (F-05, F-06, F-11)

**State labels are derived observations, never trusted inputs.** Never accept a stored "AUTHORIZED_FOR_PREPARATION", "approved=True", "trusted=True" or "INSTALLED" string/object as evidence. At every future authorization or install boundary, recompute the condition from current independently verified records; refuse extra trust fields or an attempted request to force a transition. A state snapshot for display is not a capability token.

Logical derived conditions: PROPOSED; B2A_HISTORY_BYTES_MATCH (untrusted comparison only); OPERATOR_EVENT_VERIFIED; ANCHOR_H_N_VERIFIED; PROTECTED_VALIDATION_VERIFIED; PREPARATION_ALLOWED; INSTALL_PREPARED; INSTALLED_HASH_VERIFIED; HOST_PHYSICAL_MODEL_OBSERVED. Do not assume this list is one unconditional linear order: the dependency edges are exactly §4, and a claim about a later condition needs every protected preceding proof bound to the same action/target.

Failure/terminal observations must include **REFUSED, INDETERMINATE, CANCELLED, REVOKED, EXPIRED, FAILED, BLOCKED**; runtime fallback or model mismatch is explicitly **DEGRADED** or **FAILED** (never "Opus active"). Missing provider, missing trusted clock, incomparable anchors, unverified event, invalid schema, unexpected exception, conflicting epoch/CAS and missing protected validation can never turn into an implicit permit or "success".

**B2B-1 public decision result is exactly REFUSED(reason) or INDETERMINATE(reason), with no PERMIT/APPROVED/AUTHORIZED variant.** It may define inert strict descriptor types, canonical domain-separated serializers and denial validation; it cannot create, return, persist or simulate trusted consent/approval tokens, anchor-write capabilities or installed policy changes. A function claiming "true means approved" is disallowed, even if tests use a toy signature or fixture. Unknown/malformed evidence is REFUSED; absent trusted real verifier is INDETERMINATE or REFUSED, NEVER permitted.

## 8. Requested alias, resolved physical model and fallback controls (F-09)

A consent event must bind BOTH the generation-tolerant requested family alias (e.g. opus) and an explicit approved family-matching rule or acceptable resolved-model set. Do not silently narrow it to a dated hard-coded model version, and do not assume any provider-advertised alias maps to an approved physical model without independent host observation. If the host supplies a different resolved model/family or automatically falls back due to model unavailability, quota or restrictions, record the mismatch as DEGRADED or FAILED and do NOT claim that Opus/medium ran.

Installed configuration, requested policy, runtime host-reported physical identity and independently assessed validation quality are separate. Later B2D/#169 collects host-observed evidence and bounded performance metrics where mechanically supported. Such telemetry NEVER promotes/demotes a policy automatically. A provider alias rule/pin update is a separate policy decision with the same authority chain.

A refusal to install Opus/medium may leave the last known installed Sonnet/high bytes intact **without falsely claiming the requested switch occurred**. Returning "success" because an earlier installation still works is prohibited.

## 9. B2C crash consistency, installer boundary, recovery and rollback (F-10, F-11, F-13)

This section is a DEFERRED DESIGN CONTRACT, NOT an installer implementation.

Future protected B2C must define one durable evidence-backed intent/recovery journal under an independently reviewed write boundary. A suggested ordering (subject to separate review) is:
1. Revalidate source/release/template/render bytes and target realpath/reparse safety; prepare staged bytes and a crash-consistent PREPARED journal referencing H_n/C without changing active model bytes.
2. Read back current protected head, event validity/revocation and validator record. The trusted authority advances CAS from H_n to H_(n+1) as an **authorized pending-install intent**, atomically consuming E and recording V. If the CAS fails, abort stage; no installed switch.
3. Before installing, re-verify newest protected head, event/revocation/target/policy bindings, release bytes and staged content. B2C applies an independently reviewed atomic file replacement and verifies the installed content digest; it records an independently authenticated installation observation separately from the authorization anchor.
4. If a process crashes after CAS but before file change, the head may be "authorized pending install" while old Sonnet/high bytes remain. This is NOT a successful install. Do not automatically resume or change models; mark BLOCKED pending an operator-approved recovery with fresh protected checks.
5. If a crash occurs after file change but before read-back, the installed bytes and trusted head must be reconciled by an explicitly authorized recovery. Treat mismatches as BLOCKED; do not silently rewrite the anchor, self-attest install success, roll back to a previous model or auto-repair toward the attacker-controlled side.

Installer and protected anchor shall never derive each other's truth from a mutable agent-written manifest. No source code, journal or physical install action is authorized by this plan. A verified rollback/remediation of a model policy is a new authorized FORWARD-epoch operation under §5; merely cleaning an unactivated staging area is different and may be handled by a future separately reviewed harmless cleanup policy.

## 10. Offline negative security test matrix (updated F-01..F-16)

B2B-1 will implement negative contracts only. Tests may construct fake request bytes for rejection but NEVER a positive authority, toy key or "trusted=True" approval.

| Priority | ID | Negative scenario | Required offline result |
| --- | --- | --- | --- |
| P0 | N-01 | Forged history plus self-derived matching expected triple, no independently authenticated anchor | INDETERMINATE/REFUSED, NEVER permit |
| P0 | N-02 | Caller supplies approved, trusted, AUTHORIZED state, signing outcome or unverifiable provider text | REFUSED unknown/trust fields |
| P0 | N-03 | No permit/approval class, enum, return variant, callback or installer API in B2B-1 | Structural negative assertion |
| P0 | N-04 | Chat "AUTHORIZE", AI rationale, Fable PASS string or agent-supplied UI display | REFUSED, not consent |
| P0 | N-05 | Candidate chooses protected validator identity/pins or proposer acts as validator | REFUSED |
| P0 | N-06 | Event binds post-head as previous anchor, or CAS without independently read H_n | REFUSED |
| P0 | N-07 | Same-user writable anchor, DPAPI blob or registry/file presented as T2-resistant trust | INDETERMINATE/REFUSED |
| P0 | N-08 | Trust UI shows agent-written summary instead of provider-rendered canonical requested fields | REFUSED |
| P0 | N-09 | Stored "AUTHORIZED" state, unverified or expired consent, no verifier | REFUSED/INDETERMINATE |
| P1 | N-10 | Wrong current SID, machine/install target, provider purpose, event scope, channel, or release | REFUSED |
| P1 | N-11 | Replay event/nonce, expired 300s provider freshness, stale epoch, duplicate CAS | REFUSED |
| P1 | N-12 | Forked/truncated/rolled-back history anchor, conflicting writer or missing protected prior head | REFUSED |
| P1 | N-13 | Policy/template/source/render/validator-pin digest mismatch or tampered protected validation | REFUSED |
| P1 | N-14 | Revoked/cancelled/expired event before CAS or prior to install; demotion/rollback with old approval | REFUSED/BLOCKED |
| P1 | N-15 | Wrong alias family rule, unavailable Opus, provider runtime fallback to another physical family | FAILED/DEGRADED; NEVER "active" |
| P1 | N-16 | CAS-before-install crash, install-before-readback crash, unresolved trusted head/install mismatch | BLOCKED, no auto repair |
| P2 | N-17 | Telemetry request for promotion or demotion without new full consent/validation | REFUSED |
| P2 | N-18 | Proposal digest reused as event digest; wrong schema, obsolete version, unknown fields or replay | REFUSED |
| P2 | N-19 | Malformed JSON, duplicate keys, Unicode control, BOM, oversized input and exception propagation | REFUSED bounded exception |
| P2 | N-20 | Target junction/reparse point, unresolved realpath, wrong OS SID or install instance | REFUSED |
| P2 | N-21 | Frozen-object mutation, missing expected fields and unexpected validator exception | REFUSED/INDETERMINATE, never permit |

The deferred T2-resistance property cannot be proven by an in-memory Python mock. Future B2B-2 requires an independently reviewed real trust provider, genuine OS separation and operator consent to those concrete operational permissions. The schema-048 hold rules out PostgreSQL contact (including SELECT) in any test, review or implementation now.

## 11. Reviewer finding disposition and outstanding decisions

| Claude finding | R1 design location | Resolution |
| --- | --- | --- |
| F-01 HIGH circular event/anchor | §4 | Explicit verified H_n → proposal C → trusted E → pre-state protected V → atomic CAS H_(n+1) order |
| F-02 HIGH adversary powers | §2 | T1 text, T2 same-user agent code, T3 privileged compromise out-of-scope; trust must resist T2 |
| F-03 HIGH approval UI source | §4 step 3 | Trusted provider itself renders exact bound policy, target, prior/successor from canonical fields |
| F-04 HIGH validator self-selection | §6 | Protected pre-state pins/root; no candidate-selected validator; proposer/validator independence |
| F-05 HIGH stored status trust | §7 | Labels derived from fresh verified evidence only; B2B-1 no permit variant |
| F-06 MEDIUM ordering/dependency | §4, §7 | Bind validation after real event; optional prevalidation is non-authorizing |
| F-07 MEDIUM trusted freshness | §5 | Epoch primary, provider time max 300s proposed, recheck at CAS/install |
| F-08 MEDIUM one-time consumption | §4–§5 | Nonce from trusted provider, atomic CAS consumes event and records reference |
| F-09 MEDIUM alias/fallback | §8 | Approved family rule, distinguish configuration and observed physical model, fail on substitution |
| F-10 MEDIUM crash consistency | §9 | Pending-install anchor separate from installed readback; journal and BLOCKED mismatch/recovery |
| F-11 MEDIUM revocation/demotion | §5, §7, §9 | Terminal states, explicit revoke, forward epoch for rollback/demotion |
| F-12 MEDIUM digest domain | §3 | Type/purpose/version domain separation for new evidence, unchanged legacy history SHA |
| F-13 LOW target canonicalization | §3, §9 | Machine + SID + resolved root + install/release identity, reparse refusal |
| F-14 LOW downgrade schema | §3 | Explicit schema-version allowlist, reject weaker/obsolete evidence |
| F-15 INFO verdict vocabulary | §12 | Exactly DESIGN_ACCEPT / DESIGN_REVISE / DESIGN_BLOCKED |
| F-16 INFO future providers | §2, §12 | Provider choices deferred; no implied trust from a product name |

The important remaining **provider-selection question is intentionally UNRESOLVED**: what independent trust service/consent ceremony actually resists a T2 agent and protects the history anchor? R1 describes minimum requirements, not a concrete chosen authority. No real signatures, validator proofs, anchors or actor consent have been created. A separate positive-provider design and security gate is required before B2B-2 or B2C can be authorized. F1 therefore remains OPEN.

## 12. Delivery stages, review rules and STOP boundaries

- **B2B-0 R1:** this revised architecture; initial v0 independent verdict DESIGN_REVISE, R1 independent review NOT_RUN. Review focus F-01 through F-16 and remaining provider ambiguity. For static review, allowed tools Read/Glob/Grep only, no Bash, Git, Python, pytest, MCP, files writes or agent runtime.
- **B2B-1:** only after R1 DESIGN_ACCEPT or an explicit narrowly accepted conditional design boundary; create inert frozen descriptors, strict serialization and denial-only decision outputs REFUSED/INDETERMINATE, no positive trust. Exact source SHA and independently isolated Windows review later.
- **B2B-2:** real T2-resistant operator consent, anchor storage and protected validation adapters must be separately selected, permissioned, security-reviewed and approved by user. **STOP** while source of trust is unresolved, schema-048 is OPEN or K0 positive trust issuance blocked.
- **B2C:** separate installer and rollback work, no current active change. Last installed Sonnet/high remains until explicitly authorized exact-byte installation and physical acceptance.
- **B2D/#169:** host physical model observation, acceptable Opus family alias/rule, worker/validator pins and performance evidence; no inferred physical results and no telemetry policy autoselection.
- **Issue/main release gate:** #165 OPEN/PARTIAL; no PR/main merge, installer release, native signing or activation by this design.

**Exact review vocabulary:** reviewer must return DESIGN_ACCEPT, DESIGN_REVISE or DESIGN_BLOCKED; not "production PASS". Every review report explicitly declares DESIGN_ONLY, TESTS_NOT_RUN, NO_AUTHORITY_ISSUED and NO_MODEL_ACTIVATION.

## 13. Current program and release state (holds)

Feature source: 32847410952e9d4620bf7046cbee4a41a7ddc73b; B2A R3 independently accepted offline (95 PASS lines; exit 0; R3-PROC-01 extra interpreter-only call preserved). Original B2A R2 060756b02786c146b87a5262ba2b3b2cc6bf2784 REJECT (91/92); initial B2A static REJECT. Earlier F2 follow-up 36a41b6 3/3, F2 b77e0ee 101/101, B1 f8237bb 99/99, Phase A R2 11f2f868 53/53, P2-A1 R4 3ba41d5 183/183 independently accepted strictly offline, original R1/R2/R3 REJECTs preserved.

Product main last verified 9a8acc5d464b96432a93cb95daa9581412fb07ee. Original personal source 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c, installed Windows personal Vres release 20261022172833-4d82147b unchanged, Chairman still Sonnet/high, requested Opus/medium only an in-memory candidate. All V-01–V-42 development backlog retained.

LIVE_SCHEMA_048_INCIDENT=OPEN; PostgreSQL last reported STOPPED; **no contact even read-only SELECT**, migrations, Vres startup/bootstrap/setup/selftest. D2 OPEN; F2 quarantined; R0 NOT_RUN; K0-T1 blocked; L-04 OPEN; PA-01..PA-08 incomplete; native trust approval NOT_GRANTED, positive production trust issuance DISABLED. No real credentials/vault, global Claude settings/hooks/plugins mutation, native signing, main merge, installed release/model provider/host physical action.

## 14. New-session continuity and immediate next

Resume Vres-OS from latest docs/chatgpt-continuity-20261023 HEAD. Read docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md, then this B2B R1 revision and the companion design-review checkpoint. Original B2B v0 independently DESIGN_REVISE with F-01..F-16 findings; R1 corrects sequencing/T2 threats/provider-rendered consent/old-pins validator/derived states, plus replay/freshness/schema/alias/recovery. R1 remains NOT INDEPENDENTLY REVIEWED and F1 full authority remains OPEN. Source feature SHA 32847410952e9d4620bf7046cbee4a41a7ddc73b unchanged. NEXT: Claude read-only independent static DESIGN review of R1 in a NEW guarded docs checkout; no Python/pytest/Bash/MCP/DB/credential/vault/provider. Return DESIGN_ACCEPT/REVISE/BLOCKED; no B2B-1 implementation before review. Persist future design changes through docs-only SHA-verified commits, preserving all incident/release and review evidence.
