# Knowledge lifecycle

## Ownership and acquisition

PostgreSQL owns task state, approvals, semantic identities/relationships, observations and procedure metadata.
Git/file artifacts own versioned implementation and documentation bytes. Do not maintain two independent
canonical descriptions of the same fact. A DB reference may point to the exact Git/file hash.

External files pass through format-specific parsers. Agent-created structured products can publish their
canonical text directly; the human PDF is an attached rendering, not a reason to parse the same text again.
Both paths retain source/version/scope/hash/location. Source deduplication is scope- and authority-aware:
identical bytes in unrelated projects must not merge their access or trust context.

## Truth is typed

Supported types are fact, observation, finding, hypothesis, lesson, decision, rule, process, requirement and
definition. Unknown types fail. A one-week ice-cube/temperature association is an observation with period,
query/report provenance and limitations. It is not proof of causation or a universal replenishment rule.

Evidence-backed and approval-backed promotions are different. Real source evidence is required where the
contract calls for it. User policy/process decisions require an actual approval event tied to the exact
subject/action and latest unambiguous acceptance. Numeric confidence is a label, not calibrated probability.

Statements are immutable. A changed conclusion creates a new item and an explicit supersession relationship.
Known challenged/rejected/superseded items remain history, but should not surface as current recommendations.
Repeated relation evidence is additive instead of overwriting the original supporting source.

## Scope and review

MCP writes are project-local in this preview. `company_wide=True` fails closed; no model string grants global
publication authority. Cross-project DB access by a trusted local operator is not prevented by this policy.
Review queue resolution records a decision about a queued item; it does not independently promote a claim.

## Procedure memory

User OK freezes the accepted input/method/invariant/validation/output contract and records corrections.
The full version is retrievable, not just a search summary. Repeated acceptance of the exact same payload/event
returns the same version. Reusing an approval for changed content fails. User acceptance establishes the quality
floor; it does not claim an independent validator executed.

Candidate experiments are versioned and retry-safe. Automatic replacement is held until measured paired replay
is implemented. Explicit acceptance/rejection refers to the exact candidate and approval action. Rejected
alternatives and their reason remain retrievable rather than being reinvented.

## Recovery and refresh

Material events/checkpoints are written during work. Fresh sessions receive relevant structured state and
explicit current session identity. There is no promise to recover unpersisted reasoning after a crash.
Domain refreshes are user-triggered records/deltas. Completion requires a reviewed exact JSON artifact and
fresh protected validation, not a `validated_by` string. Due dates are reminders, not a scheduler.
