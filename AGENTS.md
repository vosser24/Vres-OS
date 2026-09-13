# Vres-OS maintenance contract

Read README.md, constitution/CONSTITUTION.md and docs/KNOWN-LIMITATIONS.md first.
Use the smallest evidence-backed change. Preserve project scope, secret boundaries, typed identity and immutable provenance.
Never let ordinary task edits, agent-supplied booleans or positive telemetry certify independent validation.
The protected validator may not be downgraded. Do not confuse configured model/effort with cryptographic attestation.

Local gate: `python scripts/release_gate.py --output <outside-checkout-directory>`.
Run affected tests first, then the full gate. Migrations 001–006 are recovered released input and must not change.
Commit the tested source; export/recover ZIP, bundle and wheel from that exact commit. Preserve actual evidence,
including skipped live dependencies. Do not use historical chat counts as evidence. Do not claim automatic
optimization/global publishing/arbitrary seamless rollover while the known-limitations document holds them.
Never run integration tests against production or collect credentials through chat. Live verification is a separate gate.
