# E7 G7 Chunk 3A: R3 contract acceptance decision (2026-10-12)

Status: **R3 design ACCEPTED** by independent protected review. Additive; amends no frozen G7 document, migration 047/048 or policy.

## Accepted artifact
- File: `EXPERIENCE-INTELLIGENCE-E7-G7-CHUNK3A-SOURCE-TRUST-INTERFACE-CONTRACT-R3-2026-10-12.md` in this directory, a **byte-identical** copy of the reviewed `CONTRACT.md`.
- Raw SHA-256 of the contract: `ce6ef7c40f1263367c1202aa8e795ca41384810e62582899a3fca2adaf208c38`.
- The contract's own heading still reads "PROPOSED / NOT ACCEPTED" because those were the exact bytes reviewed. This decision record supersedes that historical status; the bytes were deliberately not edited.
- Source bundle (local, ignored, immutable): `.vres/local-tools/g7-chunk3a-contract-review-r3-20261012`; `SHA256SUMS.txt` SHA-256 `1ea68c5758064c09bfa206f5f57e452214c8feb1a9a2869dacd07e951d142ff6` (22 records, excluding itself). `README.md` SHA-256 `9e81075258c8dd3bc92701327f005f4bc66d456bac144da8a1d5325621ebfd5c`; `CHANGES_R2_TO_R3.md` SHA-256 `4cb57f6180d6a26ce011a26bfa8a6453d7822b822e2a86e3927cb0d2ca663ac4`.
- Product base: `ac45967f63690b76d41b7303ad43248afed8751f`, tree `7a95990fb4413ddf387e90e9cfad5266f266c643`.

## Validation record
- Accepting review: `VAL-86c382ece1b34e02`, host-observed model `claude-fable-5-1`, agent `a280b7b869c1d36ad`, 15/15 checks passed, 0 failed, 0 not_run, persisted in Vres `validation_evidence`.
- Prior failed design reviews (immutable history): R1 `VAL-397fb4037e9546df` (9/11), R2 `VAL-f49f4752ef064749` (22/26). Their contracts are preserved in the local bundle `files/prior/`.
- Non-blocking reviewer notes carried into implementation proof: (1) when the REPEATABLE READ snapshot is established (first statement, S0); (2) proof that all application statements share one transaction, beyond an xid check; (3) the pre-existing `_trusted_project_id()` lookup connection is not configured read-only and must not be described as such.

## Frozen invariants
Policy `176.g7.v1`, digest `f20b037b00d0a5711666fd6c1d98538101708d99e7f6f32cf5a490ff6b96cf03`. Migrations 047/048 unchanged. `vres.source_effective_trust` is the only positive-trust authority. Exactly two read-only MCP tools (`source_trust_status`, `source_trust_inspect`); `source_trust_grant` and `source_trust_revoke` are not registered. Project id comes only from trusted context and is never echoed.

## Boundary and remaining obligations
This record accepts the design only. It authorizes no production issuance. Open: G8 host-authenticated ingress; positive production issuance DISABLED; full grant/revoke execution; E5 v6; legacy source audit; G1/G2; original B4B-v1 obligations; the e6 observability and user-event-writer boundary journeys (merge gates); Chunk 6; held-out acceptance; final release ladder. Implementation is performed separately and is validated separately.
