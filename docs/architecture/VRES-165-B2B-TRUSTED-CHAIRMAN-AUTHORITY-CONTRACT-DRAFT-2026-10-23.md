# Vres-OS #165 — B2B Trusted Chairman Policy Authority Contract (DESIGN DRAFT v0)

Date: 2026-10-23, Europe/Athens.
Status: **DESIGN DRAFT / NOT INDEPENDENTLY REVIEWED / NO AUTHORITY ISSUED / NOT IMPLEMENTED**.
Repository: vosser24/Vres-OS.
Document branch: docs/chatgpt-continuity-20261023.
Accepted source foundation: feature/165-chairman-policy-foundation-20261023 at 32847410952e9d4620bf7046cbee4a41a7ddc73b.
Issue: #165 OPEN/PARTIAL; deferred host-physical cases #169.
This document is descriptive architecture, not a live validation result or an instruction to access secrets, PostgreSQL, installed release or native trust keys.

## 1. Decision and scope

The next tranche is **B2B: establish trust in the provenance and permitted use of a Chairman policy decision**. B2A R3 has independently accepted (offline) only a comparison of canonical candidate-history bytes against caller-supplied expected hashes/count. Such equality is necessary but never sufficient: an adversary can replace both the candidate and the expected values.

Keep separate: (a) an ordinary proposal, (b) provenance of a user-intended action, (c) independently anchored history freshness, (d) protected validation result, (e) an authorized release decision, (f) an installed file with verified bytes, and (g) host-observed physical model identity. Never collapse these into a single boolean or SHA-256 digest.

The shipped Windows Chairman remains Sonnet/high; the requested initial Opus/medium model policy is an inactive candidate. No model activation, global Claude mutation, installer, signing, key issuance, actual protected validation or live acceptance occurs in B2B design work. No claim that Opus is empirically superior.

## 2. Existing accepted foundation (exact commits)

- Phase A R2 policy/materialization: 11f2f8689308dfe43e482bca73aa57bb6467c788; 53/53 isolated Windows tests PASS, with prior Phase A R1 REJECT preserved.
- B1 proposal history: f8237bb301dec160f33cab524727e6a0ec79b2c0; 99/99 isolated PASS.
- F2 bounded Unicode history: b77e0eef07976877e7f198a00484f5d13ce36889; 101/101 isolated PASS. F2 test-only follow-up 36a41b6151b7520329ccc0ada0ff827d836ec579, 3/3 PASS.
- B2A expected canonical-history comparison: 32847410952e9d4620bf7046cbee4a41a7ddc73b; independent Windows ACCEPT, 95 reported PASSED lines, exit 0, four individual canonicalization variants PASS. Usual collected/deselected footer suppressed; count of collected=95 inferred. Independent B2A R2 060756b0 REJECT (91/92) and original B2A c01152e3 STATIC_REVIEW_REJECT remain evidence. R3-PROC-01 is the disclosed extra interpreter-version probe.
- P2-A1 R4 database-contact security correction: 3ba41d5ae6b8f2c2abd93d27f82cce0755878237; 183/183 offline PASS; NOT merged/installed, five residual risks preserved.

Source interfaces to reuse: ChairmanPolicy and materialize_chairman (pure candidates), ChairmanPolicyHistory (canonical proposals and digests), ExpectedChairmanHistoryIdentity / require_canonical_history_match (caller-supplied equality check). NONE supplies operator-event authentication, native trust or an installer command.

## 3. Explicit trust boundaries and threat model

Treat as **untrusted**: any pasted chat text or AI-generated confirmation; local proposal rationale; a model's claim it was approved; candidate JSON or manifest; caller-supplied expected hashes; telemetry or claimed model names; a mutable file stored beside its own history; GitHub readback alone; test fixtures and simulated "trusted" flags.

Threats to refuse before a release: forged consent, identity confusion across OS users/projects, replayed approval events, deleted tails, same-parent forks, rollback to earlier anchor, concurrent approvals, altered policy family/effort/version, swapped release template, modified protected validator pin, forged validator PASS, stale/expired approval, changed installation target, unavailable requested model followed by silent downgrade, and installer time-of-check/time-of-use races. Also reject unknown schema or extra fields, wrong source hash and missing evidence.

Trusted **only after a separate real verifier**: a host/UI/operator event authenticated for the current OS user and exact change scope, a persistent independently protected monotonic history anchor, a protected validation outcome bound to exact candidate and release, and a staged installer with verified bytes and rollback. No such trusted verifier or positive native trust issuer is implemented or authorized by this draft. The schema-048 PostgreSQL incident forbids even a read-only database lookup to find one.

## 4. Proposed immutable evidence contracts (logical fields, NOT signed objects)

These are field and invariance requirements for later separate implementation/review, not presently valid authority artifacts. No arbitrary Python dataclass, dict or "approved=True" shall be accepted as trust.

### 4.1 Operator-intent evidence (user-event record)

Required logical fields:
- schema_version and unique event identifier from trusted event source (not user-supplied rationale);
- authenticated current-user principal binding, trusted session/channel handle, explicit interactive action and event-purpose identifier "chairman_policy_change";
- exact requested policy family alias, effort and policy version; exact canonical policy_sha256;
- target Vres instance/current-user scope and intended release/template digest, so approval for one installation cannot be replayed for another;
- expected proposal_count, canonical history_sha256 and latest_proposal_sha256 from an independently authenticated anchor (NOT from the candidate's own manifest);
- nonce/challenge, trusted observation time/expiry, anchor epoch/sequence and previously anchored head;
- explicit disposition (approval versus refusal/cancellation), event provenance verifier identity and immutable evidence reference.

Never treat mere conversation text, a copied credential, prompted "AUTHORIZE" words, free-form rationale or a model's self-report as this event. Time, actor and channel fields are meaningless unless verified by the originating trust boundary. Do not create a fake operator-event provider for the installed runtime.

### 4.2 Independent history anchor

A separate protected authority owns a monotonic {epoch, proposal_count, canonical history digest, latest proposal digest, previous-anchor digest, authorizing event digest, target identity} record. It must not be writable through the same untrusted history file or client-provided request. Advancing the head requires compare-and-swap (CAS) against the last independently anchored epoch/digest, plus event replay checks. A stale epoch, forked head, deleted tail, conflicting writer or missing previous anchor is a refusal, never a silent replacement.

An append-only record alone does not guarantee tamper or rollback resistance if the attacker also controls its storage. A credible protected store or trust verifier must be independently identified and reviewed before it becomes authoritative. Do NOT choose PostgreSQL as an immediate implementation mechanism while LIVE_SCHEMA_048_INCIDENT=OPEN.

### 4.3 Protected validation evidence

A distinct protected validator must attest to what it actually validated:
- versioned validation schema and pinned protected validator routing identity;
- exact request/consent reference, proposal count/history/head hashes, canonical policy hash, template and source release hashes, requested family/effort, protected worker/validator pin identities, target and validation purpose;
- bounded validation result and failure rationale with trustworthy provenance, freshness and non-replay semantics;
- evidence bound to the same anchor epoch and event scope as the operator action.

A free-form text "Fable PASS" is not validation. The protected validator must not merely repeat the operator's desired verdict; it independently verifies governing policy, pins and acceptance. Do not fabricate Fable execution or host-observed physical model identity; actual evidence is deferred until authorized and physically observed. No positive protected trust issuance in this design stage.

### 4.4 Release/install request and observation

A later install request must reference a **verified** operator event, externally anchored accepted history, protected-validation evidence, exact template content hash, rendered content hash, source commit and target user/installation identity. Execution is separate: lock/CAS the expected head, verify all source/rendered bytes at the write boundary, prepare an atomic stage/rollback record, fail without fallback on unsupported/unavailable requested family, then independently read back installed bytes.

An installed hash or release manifest is not proof of provider-side observed model. Host-observed requested-vs-physical model, tasks, validation, token/cache/cost/timing where actually trustworthy belong to later B2D/#169; telemetry may never automatically change policy.

## 5. State machine and authority gates

- PROPOSED — untrusted candidate from accepted B1; may be serialized but is not active.
- HISTORY_INTEGRITY_MATCHED — B2A canonical match to supplied expectation; comparison only, never a trust state.
- OPERATOR_EVENT_VERIFIED — requires real independently authenticated consent provider (NOT AVAILABLE).
- ANCHOR_FRESHNESS_VERIFIED — requires independent protected monotonic head and replay/CAS check (NOT AVAILABLE).
- PROTECTED_VALIDATION_VERIFIED — requires independently proven protected Fable contract (NOT AVAILABLE).
- AUTHORIZED_FOR_PREPARATION — requires ALL three verified positive gates bound to same policy/history/target; **POSITIVE TRUST ISSUANCE DISABLED**.
- INSTALL_PREPARED / INSTALLED_HASH_VERIFIED — later B2C physical installer, not provided by B2B.
- HOST_PHYSICAL_MODEL_OBSERVED — later B2D/#169, distinct from all earlier software claims.

Deny any transition skipping prerequisites. A successful hash equality, docstring, CLI flag, test assertion, locally constructed evidence object or synthesized actor handle cannot transition to OPERATOR_EVENT_VERIFIED or AUTHORIZED. Expired evidence, absent host verifier, changing history, target mismatch, tampered template, policy mismatch and unavailable requested family all result in BLOCKED/REFUSED with no installed change. Refusal is not permission to continue with an older Sonnet/High policy if the user specifically authorized Opus/Medium; preserve last known installed state while returning an explicit failure, without silently claiming the requested switch succeeded.

## 6. Negative-path acceptance matrix and future tests

Future **offline-only** tests must demonstrate refusal for:
1. Matching history and expected digest obtained from the same forged candidate; no trusted-event verifier; no authorization.
2. Missing consent, text-only "approval", wrong principal, cross-user/cross-project target, wrong action purpose, expired event and replayed event ID.
3. Forked, truncated or rolled-back anchor; stale/missing monotonic epoch; competing CAS advancement and conflicting history head.
4. Wrong policy version/family/effort; altered canonical policy digest; changed template/release hashes or protected worker/validator pins.
5. Forged/unbound/missing protected validation; a text assertion of PASS; wrong validator identity; stale or mismatched validation result.
6. Installer target mismatch, staging/checkpoint inconsistency, unavailable Opus alias, changed bytes and silent downgrade.
7. Telemetry suggesting policy change without separately authorized explicit operator event.
8. Wrong schema, duplicate keys, too-large or untrusted input, mutated frozen objects, and exception-type leakage.

A mock can exercise pure "reject" branches, but a toy test key, self-issued signature or \`trusted=True\` fixture cannot be interpreted as positive production authority. A positive end-to-end authorization/installation requires a separately reviewed real trust provider and explicit user approval of its operational permissions; it is NOT part of the next offline design commit. Tests remain subject to tests/conftest.py protected roots, child process and PostgreSQL connection tripwires. No new tests may contact the held live database.

## 7. Delivery decomposition and explicit stop gates

- **B2B-0 — this document:** design/threat model, field and state-machine requirements, independent security review. CURRENT STATUS: DRAFT, NOT REVIEWED. No source changes.
- **B2B-1 — pure offline types and rejection contracts:** separate source commit(s) defining inert request/evidence descriptors and negative-path validators that return INDETERMINATE/REFUSED without an authenticated provider. No approval objects, no installer, no persistence. Independent Windows review on exact SHA; preserve all prior REJECTs.
- **B2B-2 — real trust-provider and protected validator adapter:** requires operator approval of provider, user identity boundaries, secure anchor storage, signing/trust handling and schema-048 separation. STOP: no implementation/positive trust issuance until those gates are expressly authorized and independently reviewed.
- **B2C — deterministic installed materialization, release manifest and rollback:** only after trusted authority exists; exact source/template/policy/render digests, atomic fail-closed activation and provider-unavailable policy.
- **B2D / #169 — trusted host-observed model and performance tests:** physical Chairman Opus/medium plus protected worker/model pins and generation-tolerant alias behavior, independently observed; cannot be inferred from templates or unit tests.
- **Main release gate:** controlled PR, protected checks/CI and explicit approval. No merge or release is authorized by this design.

## 8. Release holds and current program state

#165 OPEN/PARTIAL. Product main 9a8acc5d464b96432a93cb95daa9581412fb07ee (last verified); feature source 32847410952e9d4620bf7046cbee4a41a7ddc73b, independently B2A R3 offline ACCEPT. Installed personal source original P2 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c and release 20261022172833-4d82147b, unchanged; Chairman still Sonnet/high. Requested Opus/medium remains candidate only. Full V-01..V-42 vision stays active development backlog.

LIVE_SCHEMA_048_INCIDENT=OPEN; PostgreSQL service last reported STOPPED; NO contact even SELECT/health query. D2 OPEN, F2 quarantined, R0 NOT_RUN, K0-T1 BLOCKED, L-04 OPEN, PA-01..PA-08 incomplete, positive native trust issuance DISABLED. No real vault/credentials, global Claude configuration/plugin changes, installer, signing, production host probe or main merge without separately explicit operator approval.

## 9. Proposed independent design-review gate

Ask Claude to STATIC REVIEW this DRAFT only after its GitHub docs SHA is sealed: validate the actor/provenance separation, anchor location and monotonicity, binding of protected validation to policy/release/user and target, replay/race/rollback refusal, state-machine non-jump, no silent downgrade and absolute no-DB/vault/installed-release restrictions. No Python, pytest, Vres startup, signing, credentials, MCP or database touch. Reviewer returns ACCEPT/REJECT/REQUEST_CHANGES for **DESIGN ONLY** and exact current documentation SHA. Only then choose B2B-1 source contract work.

## 10. New-session resume

Resume Vres-OS from current HEAD docs/chatgpt-continuity-20261023. Read docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md, then this B2B design draft and its next-step handoff, followed by B2A R3 independent acceptance. The source feature SHA remains 32847410952e9d4620bf7046cbee4a41a7ddc73b, with 95 PASSED lines/pytest exit 0 bound to R3 offline only; R3-PROC-01 extra interpreter version probe retained. B2B design draft is NOT REVIEWED, does not authenticate or authorize anything. Next independent Claude static design review, then narrow offline-only B2B-1 rejection contracts if accepted. F1 full trusted source-of-expectation remains OPEN; schema-048 PostgreSQL no-contact, Sonnet/high installed, all K0/PA/vault/trust/merge restrictions unchanged. ChatGPT owns code/GitHub docs, Claude independent evaluator, user Windows operator.
