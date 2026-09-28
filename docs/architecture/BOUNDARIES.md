# Module ownership

| Module | Owns | Must not pretend to own |
|---|---|---|
| Chairman/plugin | Conversation, routing, evidence requests, checkpoint discipline | Database authority or invisible guaranteed context rollover |
| Repository/DB | Tasks, material state, events, explicit session binding, migrations | Raw model reasoning or external business databases |
| Credential Broker | Current-user credential resource metadata, project bindings, pending capture handles and guarded delivery adapters | Plaintext durable storage outside Windows Credential Locker, native Claude/Codex authentication, machine/company-wide credential sharing |
| Validation | Review requests, state/file fingerprints, observed review reports | Cryptographic identity or automatic proof of all criteria |
| Knowledge/source/registry | Scoped records, provenance, typed semantic identities | Recomputed code imports as permanently complete truth |
| Procedures/approvals | Accepted contracts, subject-specific decisions, candidate history | Unmeasured auto-optimization |
| Acquisition | Read-only mechanical parsing and bounded candidate indexing | Truth of document content or macro execution |
| Embeddings | Optional local vectors and leased jobs | Full-corpus recall or general reasoning authority |
| Model policy | Protected registered phase policies and advisory metrics | Actual model entitlement or self-certified quality |
| Windows lifecycle | Versioned runtimes, pointer/plugin staging, owned-path uninstall | OS sandboxing, DB rollback or unattended crash repair |

Credential values are a local OS concern, not repository/knowledge state. See [CREDENTIAL-BROKER.md](CREDENTIAL-BROKER.md) for resource identity, binding, prompt-ingress and delivery contracts.

Compute current code relationships from the repository when needed. Persist non-computable semantic edges
with evidence. Typed identity is `(kind, key)`; unknown identity must not be confused with known/no recorded
edges. An empty graph answer proves only that no registered relationships were found.

Use one product, separate replaceable modules, stable contracts and minimal context packets. Current runtime
limitations override aspirational diagrams in the original planning discussion.
