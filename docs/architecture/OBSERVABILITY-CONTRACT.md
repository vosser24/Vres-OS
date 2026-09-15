# Observability and evidence contract

Vres keeps review provenance, artifact catalog entries, and model telemetry as separate evidence classes. Empty tables are not defects by themselves, and runtime code must not manufacture rows merely to make an audit surface non-empty.

## Validation is not artifact registration

`validation_prepare` freezes the exact files in scope by relative path and SHA-256 in `validation_requests.artifact_manifest`. That manifest answers one question: **which bytes were independently reviewed for this validation request?**

It does not create `vres.artifacts` rows automatically. Artifact registration is a separate lifecycle action through `artifact_register` / `ArtifactService.register` when an output needs a durable catalog identity, path/source provenance, media type, and task linkage.

This separation is intentional:

- review inputs may include temporary evidence files that should never become catalog objects;
- a file may be reviewed more than once without creating duplicate artifact identities;
- registering every validator input would turn review bookkeeping into a misleading asset registry.

A validated file is therefore **reviewed evidence**, not implicitly a **registered artifact**.

## Validator identity is not model-run telemetry

Protected validator ingestion records the host-observed validator model in `validation_requests.observed_model`. That field proves the model family that actually produced the accepted review transcript.

It does not create `vres.model_runs` automatically. A validator transcript does not currently provide a complete host-measured set of runtime, token, cost, retry, and quality values suitable for model telemetry.

`model_record_run` / `ModelPolicyService.record_run` is an explicit audit surface for metrics supplied by a caller. Those rows are marked `measurement_source='reported'` and remain advisory. They are not host-attested optimization evidence and cannot auto-promote a model policy.

Host-measured comparison evidence belongs in the dedicated experiment/replay attestation flows. Missing host measurements remain missing; they are never inferred from assistant prose or filled with zeroes.

## Metadata surfaces

Opaque JSON metadata is retained only where it has a concrete runtime contract. Session metadata is used for bounded lifecycle state such as staged user-prompt attribution, host/session reconciliation, and the reply guard.

The original `vres.projects.metadata` and `vres.tasks.metadata` columns had no writer, reader, or defined diagnostic contract. Migration 019 removes those two dead extension bags. Project and task diagnostics must use typed columns or event/provenance tables instead of accumulating undocumented JSON.

Other domain metadata columns are not covered by this removal; they are owned by their explicit source/artifact/registry/knowledge contracts.

## Audit interpretation

For DB-AUDIT-012/013:

- ordinary validation is expected to leave `vres.artifacts` and `vres.model_runs` unchanged unless an explicit artifact or telemetry action is performed;
- `validation_requests.artifact_manifest` and `observed_model` remain the authoritative review-provenance fields for validation;
- empty artifact/model telemetry tables must not be populated synthetically for acceptance;
- task/project opaque metadata is removed rather than wired to invented diagnostics;
- live acceptance should verify these contracts by observing real workflows, not by inserting synthetic rows into the production acceptance database merely to make tables non-empty.
