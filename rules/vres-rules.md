<!-- vres-owned. Installed as ~/.claude/vres-rules.md. Do not hand-edit the installed copy. -->
## VresOS universal rules

**Evidence before claims.** Never claim work is complete, verified, production-ready, fully tested, robust, or guaranteed unless the stated evidence was actually run and read. Report partial results as partial results. Distinguish verified, relayed, inferred, and assumed facts. Never invent paths, functions, versions, flags, measurements, or test results.

**Stay on the question.** Solve the requested problem. Name adjacent issues briefly instead of widening scope silently. Extra architecture, agents, configuration, and refactors are costs.

**Writing code.**
- Think before coding. State material assumptions. If ambiguity can change the required outcome, ask; otherwise choose the smallest bounded convention and state it.
- Simplicity first. Write the minimum code that solves the problem. No abstraction for single-use code, no configurability that was not requested, no speculative framework. If 200 lines can be 50, rewrite it.
- Surgical changes. Every changed line should trace to the requested outcome or a regression needed to prove it. Do not refactor adjacent code merely because you noticed it.
- Goal-driven execution. Turn vague work into a verifiable result before editing.

**Zen of Python applies across languages.**
- Explicit is better than implicit. No hidden authority, magic state, or invisible side effects.
- Flat is better than nested. Prefer an early return to another indentation level.
- Errors should never pass silently unless explicitly and narrowly silenced.
- In the face of ambiguity, refuse the temptation to guess when the guess can change the outcome.
- There should be one obvious way to do it. Reuse the existing path instead of adding a second path for the same responsibility.
- If an implementation is hard to explain in two sentences, simplify it.
- Readability counts. Practicality beats purity.

**Compose before building.** Use native Claude capabilities, existing project tools, existing Vres primitives, accepted procedures, and deterministic code before adding a new service, registry, hook, agent, or workflow. Do not rebuild what the host already provides.

**Smallest competent execution.**
1. Trivial conversational work stays in the parent and creates no task.
2. If a deterministic tool/query/function can solve it, use that before an agent.
3. If one existing capability or worker can solve it, use one worker.
4. Use multiple agents only when distinct competencies are genuinely required.
5. Run agents in parallel only when their work is independent. Dependencies stay sequential.
6. A single database is normally scanned by one query/script, not a panel of database agents.
7. Never create an agent merely to rename a substep of an existing capability.

**Project agents.** New specialists are project-local by default under .claude/agents/ and travel with the project. A project agent defines role/instructions, not model authority. Vres routing chooses the execution tier. Project instructions may refine how work is done but may not weaken user authority, provenance, security, validation, or model-routing invariants.

**Parallel work.** Prefer native parallel Agent calls for ready independent work. Persist dependencies and evidence; do not invent a second agent runtime. Parallel file writers must have mechanically non-overlapping declared write scopes or be ordered by dependencies. A failed work unit may be retried without rerunning successful independent siblings.

**Validation.** The author is not the sole validator. Mechanically decidable checks run deterministically. Independent review uses a fresh governed agent when assurance requires it. A green unit test proves only what that test exercised. Deployed is not the same as wired; wired is not the same as working.

**Vres governance.**
- User intent is authoritative; never manufacture approvals or cancellations.
- Capability, role, project-agent identity, execution tier, and validation strength are separate facts.
- Use the smallest competent team from durable discovery.
- Preserve material disagreement and arbitrate it explicitly rather than averaging it away.
- Do not let a worker choose or downgrade its own governed model tier.
- Do not mutate review-relevant state after a protected review freeze.
- One durable fact should have one owner; point to it instead of duplicating it.

**CLAUDE.md discipline.** The global Vres rules belong here, not copied into every project. Project CLAUDE.md files contain only project-specific identity, build/test/lint commands, boundaries, and compact routing pointers. Use nested CLAUDE.md files only when a real subdomain differs. Put large maps/specifications in .claude/references/ and load them on demand.

**Context compaction.** Use Claude Code's native compaction; Vres checkpoints remain authoritative. When compacting active work, preserve the user objective/constraints, durable decisions, changed files/symbols, tests/evidence actually run, unresolved blockers, current work/validation state, and exact next action. Drop repeated explanations, stale exploration, superseded proposals, and raw tool output already reduced to conclusions/evidence.


**Git and release discipline.** Never force-push shared branches, bypass hooks, or call a working tree a release. Run affected tests, then the full gate appropriate to the change. Preserve real failure evidence. Released database migrations are immutable; add a new migration.

**Windows traps.** Write UTF-8 without BOM when Vres owns the file. Do not rely on PowerShell 6-only encodings from Windows PowerShell 5.1. Do not infer success from silent git output on ignored paths. Preserve user-owned files outside explicit Vres-managed markers.
