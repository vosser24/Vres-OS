# Vres-OS — Pre-Production Build Handoff (2026-09-25)

This is the authoritative continuation handoff after completion of the real-world adoption coverage audit and creation of the pre-production execution ledger.

It supersedes `docs/FINALIZATION-HANDOFF-2026-09-25-POST-141-159.md` **for continuation purposes only**. The prior handoff remains historical evidence for #141/#146/#159 and the completed finalization phase.

Repository: `vosser24/Vres-OS`

Master implementation plan:

`docs/PREPRODUCTION-ADOPTION-BUILD-PLAN-2026-09-25.md`

## 1. Repository state at planning freeze

Planning base main:

`4370e6794a3595696179f3781cfc661edf015e8d`

Commit message:

`Merge pull request #162 from vosser24/docs-preproduction-case-audit-handoff-20260925`

Verified product implementation baseline before docs-only handoff commits:

`acd45f1262979c16b1029ca9241976098cb503e8`

At the start of this planning update:

- open issues: 0;
- open PRs: 0;
- current main CI was green;
- #141, #146 and #159 were complete and must remain closed absent fresh regression evidence.

This planning tranche creates the new work ledger #163–#170. No product source implementation is changed by the planning tranche.

## 2. Audit conclusion

The real-world audit found genuine product gaps, so Vres must not move directly to Production Readiness yet.

Final classified gaps:

| Area | Audit verdict | Result |
|---|---|---|
| Healthy existing Claude preservation | COVERED + PROVEN | historical F-01/F-02 evidence remains valid |
| Dirty/global Claude adoption into clean Vres governance | PARTIALLY COVERED | #166 |
| First-use legacy project adoption | PARTIALLY COVERED | #168 |
| Canonical project Claude/Vres scaffold | PARTIALLY COVERED | #168 |
| Secret-safe legacy ingestion for supplied fixture | NOT COVERED | #164 |
| Current-user reusable credential resources across projects | PARTIALLY COVERED | #163 |
| Prompt-time credential interception | NOT COVERED | #163 |
| Configurable Chairman Opus/medium policy + monitoring | PARTIALLY COVERED | #165 |
| Current-user external data-source registry | NOT COVERED | #167 |
| Read-only structural/semantic database dependency catalog | NOT COVERED | #167 |
| Reusable cross-project DB index with explicit binding | NOT COVERED | #167 |
| Database drift/incremental catalog refresh | NOT COVERED | #167 |
| Integrated actual dirty-global + legacy-project proof | NEEDS NEW LIVE ACCEPTANCE after builds | #169 |
| Production readiness/go-live | intentionally separate | #170 |

## 3. New issue ledger

The authoritative execution order is:

1. **#163 — Credential Broker: current-user reusable secrets and prompt ingress protection**
2. **#164 — Secret-safe onboarding: path exclusion, pre-model sanitization and fail-closed ingestion**
3. **#165 — Chairman model policy: configurable Opus/medium default with host-observed monitoring**
4. **#166 — Global Claude adoption: snapshot, quarantine, Chairman KEEP/DROP migration and rollback**
5. **#167 — Current-user Data Source Registry and read-only semantic database catalog**
6. **#168 — Project adoption and canonical Claude scaffold with credential/data-source linking**
7. **#169 — Integrated Windows live acceptance from Visual Studio: PRISM global adoption + real legacy project**
8. **#170 — Production readiness after adoption live acceptance**

Do not combine dependent issues into one branch/PR.

Each implementation issue must be built, validated, committed/PR'd/merged, post-merge verified and documented before the next dependent issue starts.

## 4. Credential architecture frozen decision

Credentials are scoped to the **current Windows user only**.

Durable values stay in Windows Credential Locker.

Vres may retain only non-secret credential metadata/handles and explicit project bindings.

A credential belongs to a service/account identity, not to the project where it was first encountered.

Example:

```text
website
https://www.example.gr
account: main
fields: username,password
```

If Project A creates this credential and Project B later needs the same login, Vres may offer the current-user saved resource and create a Project B binding after explicit approval. The password is not re-entered or copied to Project B.

Another Windows user must not inherit the resource.

`.env` plaintext is not the Vres durable-storage design.

Environment variables/materialized files are temporary process-local delivery only.

Native Claude/Codex vendor login state remains outside Vres ownership.

## 5. Credential pasted into chat — target behavior

A deterministic `UserPromptSubmit` ingress guard is required.

High-confidence credential input should be stopped before normal Claude processing when the host contract supports it.

The guard must not echo the value.

The desired user experience is:

> Credential detected. I stopped this message before sending the credential to Claude. I can save it securely for the current Windows user as a reusable login. Re-send the request without the password.

A local pending capture may then be confirmed/discarded.

Physical acceptance must determine the exact transcript/debug guarantees of the installed Claude Code host. Do not claim stronger secrecy than the host evidence supports.

## 6. Secret-safe onboarding frozen decision

Secret-bearing paths such as:

- `.env`;
- `.env.*`;
- `secrets.toml`;
- credential/auth/private-key files;
- Vres local-secret material

must be classified before content extraction.

Useful mixed documents containing credential spans must be sanitized before:

- Vres durable chunks;
- embeddings;
- review queue text;
- model prompts;
- validation context;
- logs.

If safe sanitization is uncertain, fail closed for the content.

Credential candidates discovered during onboarding must reuse #163's Credential Broker rather than creating a second secret architecture.

## 7. Chairman model policy frozen decision

Initial target:

```text
Chairman               Opus / medium
Routine governed work  Sonnet
Deep governed work     Opus when routed
Routing arbiter        Fable / high when required
Protected validator    Fable / high
```

The policy uses model families, not hard-coded generation identifiers.

#146 remains complete. Its host-evidence work is reused.

Model telemetry/performance monitoring is evidence only and must not automatically change policy.

Future Chairman policy changes require explicit authority and protected validation.

## 8. Global Claude adoption frozen design

Current preservation behavior is historically correct but insufficient for the new clean-governance target.

New installation/first-start behavior must be:

```text
existing current-user Claude
    ↓
deterministic governance inventory
    ↓
immutable snapshot + hashes
    ↓
quarantine/neutralize active legacy governance
    ↓
install Vres baseline
    ↓
GLOBAL_ADOPTION_PENDING
    ↓
first start vres
    ↓
semantic adoption
    ↓
Chairman recommendations
    ↓
user KEEP/DROP
    ↓
protected validation
    ↓
journaled activation
```

Never bulk-delete `~/.claude`.

Never reset native vendor authentication/session state.

Legacy configuration is historical data during adoption, never active instruction authority.

## 9. Adoption user experience

The migration must be usable by an average user.

Findings are grouped for readability, but every material item has its own number.

Required table:

| # | Item | What it does | Chairman recommendation | Why | Destination if KEEP |
|---:|---|---|---|---|---|

User replies:

```text
KEEP 2,3,7
DROP 1,4,5,6
```

or equivalent natural wording.

Every number is resolved independently.

Unspecified numbers remain pending.

DROP means not activated/promoted; it does not erase the immutable backup.

Chairman is the only user-facing migration adviser. Semantic workers report to Chairman.

## 10. PRISM live fixture

The user intends to deliberately establish a complex current-user Claude environment before the Vres fresh-install acceptance.

Fixture repository:

`vosser24/prism_5`

Planning-time PRISM main:

`44329fdbfbb5a61d409ad202c57237805d56fe9d`

Commit message indicates PRISM v6.7.1 snapshot.

PRISM documentation/install code confirms realistic current-user Claude surfaces including:

- global hooks;
- skills;
- agents;
- tools;
- commands;
- merged `settings.json`;
- status-line behavior;
- preserved PRISM state;
- per-project CLAUDE/project-master/references/bootstrap state.

At #169 test time re-fetch and record the exact PRISM commit actually installed.

Do not change PRISM merely to make Vres acceptance easier.

Vres must adopt the established environment without requiring a PRISM uninstall first.

Expected migration principles:

- PRISM master/control-plane authority: archive/drop as active authority;
- useful capabilities: potential Vres-governed candidates;
- project-specific material accidentally global: move to appropriate project if user keeps it;
- old hooks: inactive unless explicitly justified;
- PRISM telemetry consent: not Vres consent;
- old model selection: historical evidence only, not Vres model-policy provenance.

## 11. Data Source Registry frozen design

The registry/catalog is current-Windows-user local state.

A database/data source is registered once and linked to projects explicitly.

Credential values remain in #163's Credential Broker.

Initial database audit is read-only.

For PostgreSQL, deterministic structural acquisition should map supported:

- schemas;
- tables;
- columns;
- types/defaults/nullability;
- PK/FK/unique/check constraints;
- indexes;
- views/materialized views;
- sequences/types;
- functions/procedures/triggers where readable;
- comments;
- dependency edges;
- safe ownership/size/estimate metadata.

No default raw row sampling.

Metadata itself may be sensitive and needs bounded handling.

Semantic analysis is routed through existing data/PostgreSQL capabilities under Chairman governance.

Persist semantic claims with evidence class. Inference is not canonical truth.

A cheap schema/dependency fingerprint controls reuse:

```text
unchanged → reuse catalog
changed   → incremental refresh
material/unknown drift → reviewed/full audit
```

## 12. Project adoption and scaffold frozen design

Current `start vres` only creates a minimal CLAUDE.md when missing. That is not the target.

New project states:

- fresh;
- legacy;
- adoption pending;
- awaiting user;
- validation pending;
- activating;
- active;
- rollback required/rolled back.

Canonical project directories Vres may create/use:

```text
.claude/
  rules/
  skills/
  agents/
  agent-memory/
```

Project CLAUDE.md stays concise.

Create settings/MCP/worktree/reference files only when a real requirement exists.

Do not manufacture fake agents, empty skills or dummy MCP servers.

Do not create a made-up `.claude/lessons` standard.

Semantic placement:

```text
always-on convention → CLAUDE.md / rules
repeatable workflow  → skill + Vres procedure
specialist           → agent only after governed capability need
agent memory         → agent-memory
facts/decisions      → Vres knowledge/decision
user preference      → Vres preference
```

Legacy projects receive the same grouped numbered KEEP/DROP experience as global adoption.

## 13. Legacy project fixture

The user supplied `wizzard_9` as a realistic legacy project example.

Observed characteristics include:

- Python application code;
- large JSON business configuration;
- handover documentation;
- project `.claude`;
- bundled `.venv`;
- runtime/log/junk files;
- `.streamlit/secrets.toml`;
- credential material embedded in handover content.

Do not commit the real secret values into Vres fixtures/evidence.

Development should use a sanitized/synthetic equivalent.

#169 will later onboard an actual legacy project under controlled conditions.

During adoption, Vres must not execute:

- browser login;
- OTP;
- voucher reservation;
- production mutation;
- deployment;
- arbitrary application actions.

## 14. Visual Studio live-test decision

After #163–#168 are merged, #169 will run the whole-system acceptance from the user's actual Windows development workflow using Visual Studio / its integrated terminal rather than the earlier PowerShell-only guided acceptance style.

This does not mean PowerShell stops being a product dependency where Windows scripts require it.

The distinction is operator workflow: the user will work from the real Visual Studio environment and onboard a real legacy project instead of only executing isolated acceptance command blocks.

The acceptance must use the actual packaged/release candidate.

## 15. Historical evidence reuse

Do not rerun everything.

Continue using `docs/FINAL-VERIFICATION.md` surface-triggered regression rules.

Historical #141 F-05/F-06/F-15, #146 host-evidence and #159 auto-compaction evidence remain reusable unless a changed owned surface invalidates them.

Never reopen #141/#146/#159 simply because a new issue touches adjacent concepts.

## 16. Per-tranche build/validation/commit rule

For every issue #163–#168:

1. verify exact current `origin/main`;
2. verify dependency issue merged/post-merge green;
3. read issue + master build plan + this handoff;
4. create dedicated branch/worktree;
5. impact/design before source edit;
6. implement smallest viable contract;
7. add targeted automated tests;
8. run PostgreSQL/integration checks where applicable;
9. freeze the tranche's physical Windows/live criteria for #169; do not run the final live acceptance yet;
10. checkpoint final review state;
11. run protected Fable validation;
12. commit;
13. PR;
14. exact-head CI;
15. merge;
16. post-merge main CI;
17. update handoff/evidence and #169's carried live criteria if needed;
18. close the implementation issue without claiming deferred live PASS;
19. stop before next dependent issue unless explicitly continuing.

No dependent tranche is developed on an unmerged predecessor.

## 17. Production boundary

#169 is the consolidated physical Windows live acceptance. Issues #163–#168 build and validate their implementation contracts first; their real host/Windows acceptance is intentionally deferred to #169 and run from the Visual Studio workflow.

#170 is Production Readiness / Go-Live.

Green repository finalization and green #169 do not by themselves equal production-ready.

#170 must cover:

- exact release artifact/manifest/hashes;
- target Windows install;
- PostgreSQL least privilege;
- credential/security/storage/logging review;
- backup/restore;
- update/rollback/interrupted recovery;
- adoption rollback/recovery;
- monitoring/health/operator escalation;
- enabled vs held inventory;
- low-risk pilot;
- final launch decision.

## 18. Next-session exact action

The next session starts with **#163 only**.

Do not start #164–#170 until #163's dependency contract is accepted/merged according to the build program.

Starter prompt:

> Resume Vres-OS from `docs/PREPRODUCTION-BUILD-HANDOFF-2026-09-25.md` and `docs/PREPRODUCTION-ADOPTION-BUILD-PLAN-2026-09-25.md`. Fetch and verify current `origin/main` first. #141, #146 and #159 remain complete. The new pre-production issue ledger is #163–#170. Start only #163 Credential Broker. Read #163 completely and inspect the existing `SecretStore`, `LocalSecretManager`, UserPromptSubmit lifecycle hooks, Windows credential handling and current tests before creating a branch/worktree. Build the current-Windows-user credential-resource layer with explicit per-project bindings, secure prompt-ingress handling, exact-value redaction and no plaintext persistence. Validate the exact issue contract, run protected Fable validation, commit/PR/merge, verify post-merge main CI, update the handoff, and stop before #164 unless I explicitly tell you to continue.

## 19. Planning-closeout verdict

The audit phase is complete.

The build plan is frozen.

The new development program begins with #163.

No product-code implementation was performed in the planning session.

The intended path is:

```text
#163 build/validate/merge
→ #164 build/validate/merge
→ #165 build/validate/merge
→ #166 build/validate/merge
→ #167 build/validate/merge
→ #168 build/validate/merge
→ #169 real Windows/Visual Studio live acceptance
→ #170 Production Readiness / Go-Live
```
