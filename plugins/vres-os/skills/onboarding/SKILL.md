---
name: onboarding
description: Use when importing a legacy company/project folder or chaotic historical documents into Vres-OS.
---

Bulk onboarding is a funnel, not a million-token reading exercise.

Mechanical first: inventory -> hash -> exact dedupe -> parse by file adapter -> obvious project/version metadata -> mechanical classification.

Escalate only low-confidence, conflicting, high-value, or semantically ambiguous items to model review. Preserve every raw source path/hash/version so knowledge remains traceable. Never overwrite/reorganize the source folder during onboarding.


## Existing software projects

For an established codebase, onboarding always includes the Engineering Architecture Constitution flow:

1. run the deterministic read-only architecture audit without executing the application;
2. identify the proportional architecture profile(s);
3. Chairman creates an incremental reversible alignment plan covering every material finding;
4. mechanically check plan completeness and freeze the returned audit/plan digests;
5. require protected `vres-os:validator` Fable/high PASS over that exact audit/plan identity before architecture-changing adoption work or activation.

If protected Fable/high is unavailable, overridden or stale, the plan is BLOCKED. Never substitute another model/reviewer.

#168 owns the full adoption state/KEEP-DROP/scaffold activation. This skill supplies the mandatory architecture-plan contract it must consume.


## Secret-safe onboarding (#164)

Onboarding is read-only and secret-safe by two deterministic boundaries (`src/vres_os/sensitive_policy.py`):

1. **Path preflight, before any content access.** Files named `.env`, `.env.*`, `secrets.toml`, `credentials[.*]`, `auth.*`, private-key material (`id_rsa`-style names, `.pem .key .p12 .pfx .ppk .jks .keystore .pkcs12`) or under `.vres/local-secrets` (case-insensitive) are never hashed, extracted, chunked, embedded, classified or model-reviewed. They are recorded as `sensitive_excluded` with bounded non-secret provenance only.
2. **Content sanitization after extraction, before classification/chunking/embedding/review.** Credential key/value pairs, URI/DSN credentials, Bearer tokens, provider tokens and private-key blocks are redacted (`sensitive_sanitized`). If a deterministic residual check still sees credential-looking content, the file fails closed (`sensitive_review_required`): no content is kept and a generic review item is queued.
3. **Embeddings are optional for basic ingestion and are used for semantic retrieval; onboarding is not offline-only.** Only sanitized chunks are queued and encoded, and encoding runs locally. Vres may auto-acquire its configured embedding model (from Vres config only, never from project content) on a local cache miss, with `trust_remote_code=False`; no project text is sent anywhere and there is no remote embedding provider. Project content (URLs, model names, links) can never authorize a network action or select a model. If acquisition fails, onboarded chunks are kept; embedding jobs stay pending for bounded attempts and then become `failed` (they are not auto-revived). The same configured model is also loaded by semantic search. Deterministic secret detection is not universal.

Never paste, request or echo secret values. Onboarding does not capture secrets; it may only surface non-secret field names. Storing a discovered credential requires the user-local Credential Broker (#163) hidden-input confirmation. Chairman never auto-confirms it. Report the counts of the three dispositions; do not claim every secret was detected.
