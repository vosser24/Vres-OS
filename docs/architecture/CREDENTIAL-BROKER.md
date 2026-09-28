# Credential Broker architecture

Issue: #163 — current-user reusable secrets and prompt ingress protection.

This document defines the implementation contract introduced by #163. It does **not** claim that the deferred physical Windows/Claude host acceptance has passed; those criteria are executed with the integrated release candidate in #169.

## Security boundary

Vres credential resources are scoped to the current Windows user.

- Durable credential **values** live only in Windows Credential Locker through `SecretStore`; the broker refuses its default durable backend off Windows.
- Vres local metadata stores resource identity, field names, timestamps, pending-capture metadata and explicit project bindings. It never stores credential values.
- PostgreSQL is not a credential vault. Credential-resource values and pending-capture values are not written to Vres PostgreSQL.
- `.env` and other project configuration files are not durable Vres credential storage.
- Environment variables and materialized files are temporary delivery adapters only.
- Native Claude/Codex login, OAuth and vendor session state remain outside Vres ownership.

The metadata registry records a current-user namespace derived from the current user/profile context and fails closed if copied into a different namespace. This is an additional catalog boundary; Windows Credential Locker and the per-user Vres data directory remain the durable OS boundaries.

## Resource identity

A credential resource belongs to a normalized service/account identity, not to the project that first captured it.

Examples of non-secret identities:

```text
website | https://www.example.gr | main
postgres | db.example.gr:5432/sales | readonly
service | github.com | work
```

Normalization is deterministic:

- website resources retain only normalized `http`/`https` origin (scheme, IDNA/lower-case host and non-default port);
- PostgreSQL resources normalize to `host:port/database`, defaulting the port to 5432;
- generic service identifiers are normalized without treating a project as part of the resource identity;
- account labels and credential field names are normalized;
- embedded URI usernames/passwords are refused as resource metadata.

The resource id is a stable digest of normalized service type, origin and account label. Saving the same identity again updates the same resource rather than creating a project-specific copy.

## Project authorization

Resource discovery and metadata lookup are current-user operations and never resolve values.

A project receives an explicit binding to a resource. The binding is authorization; it is not a copy of the secret.

- Project A and Project B can bind independently to one resource.
- Project C cannot resolve, inject or materialize it merely by knowing the resource id.
- Unlink removes one project's authorization and leaves the underlying current-user credential intact.
- Deleting the underlying resource is a separate explicit operation and removes all bindings.

## Prompt ingress

The `UserPromptSubmit` hook performs deterministic credential classification before Vres configuration, session lifecycle, task binding or user-instruction persistence.

High-confidence shapes include bounded credential assignments, known token forms, bearer tokens, private-key blocks and credential-bearing URIs. Placeholders and ordinary discussion such as “explain password rotation” are not silently captured.

When high-confidence credential material is detected:

1. normal prompt processing is blocked by the host hook decision;
2. the value is never echoed in the hook response;
3. when the detection is unambiguous and bounded, its values are written to temporary pending keys in Windows Credential Locker;
4. Vres writes only non-secret pending metadata locally;
5. the user confirms or discards the pending capture from a local terminal.

Ambiguous/conflicting detections block the prompt but do not create a pending credential. If secure capture fails, the prompt still blocks and the hook logs only a fixed diagnostic, never the provider exception text.

The installed Claude Code host's exact transcript/debug persistence behavior is a physical acceptance question. #163 intentionally makes no stronger claim before #169 proves it on the target Windows workflow.

## Pending capture

A pending capture is not yet a reusable credential resource.

```powershell
vres credential pending
vres credential confirm <capture-id> --service-type website --origin https://www.example.gr --account main
vres credential discard <capture-id>
```

Use `--bind` during confirmation only when the current project should be explicitly authorized.

Confirmation resolves pending values locally from Credential Locker, writes them under the normalized resource handles, updates non-secret metadata, and removes the pending values. Discard removes the pending values without creating a resource.

## Local-terminal capture and reuse

Do not ask users to provide credential values in normal Claude conversation. Capture directly from hidden terminal input:

```powershell
vres credential save --service-type website --origin https://www.example.gr --account main --field username --field password
vres credential list
vres credential bind <resource-id>
```

The same saved resource can later be bound from another project without re-entering the value.

There is deliberately no plaintext `credential get` command and no normal MCP surface that returns credential values.

## Delivery adapters

Prefer passing a resource handle plus field mapping to a bounded child process:

```powershell
vres credential run <resource-id> --env APP_PASSWORD=password -- <command>
```

Vres resolves fields only after checking the current-project binding. Values are added only to a copied child environment. The parent environment is not modified. Child output is scrubbed for the exact resolved values before it is printed.

If a tool genuinely requires a file:

```powershell
vres credential materialize <resource-id> password --path app/password.txt
vres credential cleanup
```

Materialized plaintext is restricted to `.vres/local-secrets/`, Git-excluded locally, owner-restricted and refused for tracked or symlinked paths. Cleanup refuses to delete tracked or symlinked content instead of treating Git exclusion as ownership proof.

Materialized files are plaintext while they exist. Use them only when environment/adapter delivery is impossible and clean them up immediately.

## Legacy local-secret aliases

The existing `vres secret` project-scoped alias commands remain supported for backward compatibility. They continue to use Windows Credential Locker on supported Windows installs.

New cross-project adoption work should use the Credential Broker resource/binding API rather than creating additional project-scoped credential copies. Later onboarding work (#164/#168) must call this broker instead of inventing a second secret architecture.

## Deferred physical acceptance in #169

The following are explicitly **not** marked PASS by #163 implementation tests:

1. store a synthetic `www.example.gr` login under Windows User A;
2. bind/reuse it from Projects A and B without re-entry;
3. prove unbound Project C cannot consume it;
4. prove child-only delivery leaves the real parent environment clean;
5. paste a synthetic credential in a disposable Claude session and inspect actual transcript/debug behavior;
6. prove a second Windows account cannot see/reuse User A's resource;
7. uninstall/reinstall Vres without deleting native Claude/Codex vendor login sessions.

These are carried into #169 and run from the user's Visual Studio workflow against the integrated release candidate.
