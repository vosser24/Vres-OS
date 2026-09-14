# Vres-OS live verification runbook

**Target:** 0.2.0a1 controlled-live-test preview. These tests are NOT recorded as run by this audit.
The local evidence archive records a different, non-Windows gate. Complete this runbook on the exact packaged
commit before describing the Windows experience as verified.

## Safety and execution order

Use a disposable Windows VM/snapshot, synthetic files and a dedicated PostgreSQL database. Never run failure,
kill-process, hostile-document, upgrade or deletion cases on production. No real customer/supplier credentials
belong in screenshots, model prompts or attached logs. Use normal vendor login and the separate secure Vres console.

Proceed in the listed order. Stop on a credential leak, existing-role modification, wrong-task continuation,
cross-project leakage, false validation PASS or unexpected deletion. Save sanitized evidence, restore the snapshot,
and file a defect against the exact commit. Do not quietly bypass a failed gate to finish the checklist.

Required tests must pass before wider evaluation. Optional Codex/embedding tests may be NOT RUN if those features
remain disabled; enabling them later requires those tests. HELD means deliberately unavailable by design, not passed.
Missing native support or model entitlement is a blocker, not a reason to fake the result.

## Evidence record

Copy `docs/live-results-template.csv` outside the source checkout. For each test record:

- exact source commit and archive hash; machine/native CLI/package versions;
- start/end time, commands/actions, expected result, observed result;
- PASS / FAIL / NOT RUN / BLOCKED, sanitized evidence paths, defect IDs and reviewer;
- actual failures/limitations, not an agent's assertion that the test probably works.

Screenshots help with UI/credentials-vault presence, but must hide secrets. SQL evidence should show only synthetic
IDs/rows. Copy the installed release's resolved-dependencies.txt. Preserve vendor transcript metadata necessary to
identify the actual validator, with sensitive content removed.

## PostgreSQL integration helper

The installer does not install development test tools. In a separate developer test venv from the source checkout:

```powershell
py -3.12 -m venv .live-test-venv
.\.live-test-venv\Scripts\python.exe -m pip install ".[full,dev]"
.\.live-test-venv\Scripts\python.exe scripts\run_live_db_tests.py
```

The helper asks for the test DSN using a hidden local prompt and requires explicit DISPOSABLE confirmation.
The database name must end `_test`. It passes the DSN only in the child process environment, clears its temporary
mapping afterwards and never writes a credential file. Same-user process access is not prevented by environment
transport. Test logs must still be inspected/redacted before sharing. Creating that empty test DB is an explicit
administrator action; the helper never guesses an admin credential or creates a production resource.

## Cases

### LV-00 — Release identity and isolated target

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Restore a disposable Windows VM snapshot. Record OS, PowerShell, CPU/RAM, locale and user profile path. Verify source ZIP/bundle/wheel SHA-256 values against the manifest. Record exact source commit. Copy the synthetic fixtures, not company data.

**Pass evidence:** The checksums match the supplied manifest and the directory is the correct version. No production DB/credential/project is in the test scope. A manifest is not a publisher signature.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-01 — Junior-user fresh install

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Open a normal PowerShell in the fully extracted source. Run Set-ExecutionPolicy -Scope Process Bypass, then .\install.ps1. Follow the displayed dependency prompts. Record every consent, native exit code and prerequisite version; never record credential input.

**Pass evidence:** Missing required packages are offered by exact ID. Declining or unavailable package exits clearly. A supported Python is selected even with another newer default. No package failures are ignored; no unrelated plugin is removed.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-02 — Non-default path and native encoding

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Repeat install in a VM/user with spaces and Greek characters in profile/source/project paths. Include supported Python 3.12 alongside a newer unsupported default. Inspect plugin/runtime pointer and launchers.

**Pass evidence:** Quoted paths work, UTF-8 JSON reads correctly, compatible Python is selected and no parent-directory release ID is accepted. No change to unrelated project configuration.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-03 — Plugin discovery and native login

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Open a fresh terminal. Run claude --version and claude plugin list --json. Authenticate Claude natively. Start Claude in a disposable project; inspect the active agent and MCP server. Repeat in a second project. Use the account with the protected validator available.

**Pass evidence:** The personal vres-os@skills-dir plugin loads once; Chairman is the intended main agent and the Vres MCP starts. Native credentials remain vendor-owned. If policy/other plugins prevent this, record FAIL rather than manually claiming auto-discovery worked.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-04 — Secure first start

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** In Claude say start vres. Enter PostgreSQL details only in the separate local console. Use unused vres_test role/database names. Wait for setup; inspect vres doctor, vres status and vres selftest from a fresh terminal.

**Pass evidence:** Only a separate console receives passwords. Admin password is not stored. Runtime credential is in Windows Credential Manager. Migrations and real selftest complete before configured=true. Doctor does not migrate. Stop on any exception.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-05 — Failed setup and existing-role protection

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Use a VM snapshot. First supply wrong admin credentials, then retry correctly. Separately nominate an existing test role/database used by a dummy client and record its access before/after. Test a previously working Vres config followed by failed reconfiguration.

**Pass evidence:** Failed first setup never marks ready. Existing role password/ownership/grants are not reset. Failed reconfiguration restores the old usable config/credential. Partially created unused resources require explicit operator review, not silent deletion.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-06 — Duplicate setup request and interruption

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Say start vres again while the first secure console is open. Then in an isolated snapshot interrupt setup after a new role exists but before setup finishes; retry with a new unused name or administrator-inspected cleanup.

**Pass evidence:** Only one setup console owns the lock. MCP returns a bounded setup-in-progress response, not an indefinite tool wait. Interrupted setup is reported; it does not overwrite existing objects to recover.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-07 — Real PostgreSQL migration and test journeys

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Create a disposable database whose name ends _test. Install test dependencies in a separate test venv. Run python scripts/run_live_db_tests.py from the source checkout and enter its DSN only in its hidden local prompt. Repeat the migration/selftest; inspect checksums and cleanup of uniquely named test records.

**Pass evidence:** All actual integration tests pass with zero skips. Reapplying migrations is idempotent. Tests never DROP schemas/databases. Tampered applied SQL or a newer unknown migration is rejected in a disposable copy. Save sanitized command logs.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-08 — Material task checkpoint

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Tell Chairman to plan a dummy workflow with an explicit objective, decision, constraint and next action. Ask it to persist the state. Record the task key/session identity and observe DB events through allowed inspection tools.

**Pass evidence:** One real task is bound to the native current session, with structured material state and next action. A chat statement that it saved is insufficient: inspect the durable record.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-09 — Clear and fresh MCP session identity

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** After LV-08 use native /clear, then say continue. Inspect the newly hook-observed session ID and the MCP calls. If selection is ambiguous, request the exact recorded task instead of relying on latest update time.

**Pass evidence:** Correct persisted task resumes. The new hook ID is passed explicitly; the MCP startup environment is not treated as current. It must never bind to an unrelated unfinished task by recency.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-10 — Compaction, exit and abrupt termination

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Checkpoint a fresh material decision. Exercise native /compact, normal exit/restart and an abrupt Claude process kill separately. Restart in the same project and ask for objective/decision/next action. Deliberately leave one unsaved sentence to test truthful recovery claims.

**Pass evidence:** Persisted fields survive. Compaction alone does not alter reviewed content. Unsaved reasoning is identified as unavailable, not invented. No claim that an exit hook saved data without a committed write.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-11 — Two concurrent sessions and tasks

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Open two native Claude windows on the same project and begin different tasks with distinct markers. Alternate updates, complete one, clear the other. Also open a second project with its own task.

**Pass evidence:** Bindings remain session-specific. Completing one task does not jump that session into another. Multiple unbound tasks produce ambiguity. Cross-project state stays isolated. Inspect actual DB concurrency, not mocked expectations.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-12 — Protected validator happy path

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Create a trivial deterministic function/test and a task with exact criteria. Prepare validation with the complete file list, run vres-os:validator with protected Fable/high, inspect the native transcript and SubagentStop event, then complete through task_complete.

**Pass evidence:** A fresh exact request becomes passed only after the observed native report. It identifies the actual supported model family/session/agent and verified checks. No ordinary task mutation supplies its own passed result.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-13 — Stale or forged validation rejection

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** After LV-12 modify a reviewed file or material task state and try completing again. In a separate test omit required live evidence, give a wrong request/session, or request a weaker validator. Do not forge local database rows: test the public application boundary.

**Pass evidence:** Stale/unknown/wrong-model/incomplete review is rejected. A pending/native-unavailable validator cannot become PASS from a caller boolean. Record that same-OS-user forgery remains outside the trust model.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-14 — Approval semantics

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Present one explicit reusable task contract. Respond OK, then test OK for now, no, and fine but change the metric on separate drafts. Attempt reusing the same approval for a different subject or action.

**Pass evidence:** Unambiguous acceptance binds one action/subject to the real user event. Conditional/negative assent is not broadened. Replayed identical approval is idempotent; changed subject/payload requires renewed approval.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-15 — First Excel result and correction

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Give Chairman only tests/fixtures/live/day1_A.xlsx and day1_B.xlsx. Ask to combine first sheets and return top ten products. Resolve ambiguity explicitly: append, sum Net Sales by six-character SKU, preserve Description, sort descending. Do not show expected.json until independently checking the result.

**Pass evidence:** Results match day1_expected exactly: 26 source rows, 12 unique SKUs, all-product Net Sales 10205. Leading zeros, duplicate rows and negative returns survive; the decoy second sheet and Units ranking are ignored.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-16 — Accepted procedure and day-two reuse

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Say OK to the exact LV-15 contract and retain its procedure/version key. Clear/restart. Supply day2_A.xlsx/day2_B.xlsx and ask do the same again. Inspect procedure_match and procedure_get before implementation. Compare against day2_expected afterwards.

**Pass evidence:** The accepted full contract is retrieved and reused; new amounts are calculated, not yesterday's output copied. User corrections remain invariants. No unexplained new ranking method or all-sheet merge appears.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-17 — Procedure retries, candidates and held optimization

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Retry accepting the same baseline and submitting the same optimization experiment; inspect version IDs. Change the payload and reuse the old approval. Supply a proposed faster candidate with only agent-reported token metrics, then try an explicit separately approved candidate decision.

**Pass evidence:** Retries return the same version/experiment; changed approved content is rejected. Automatic promotion remains HELD because paired host-measured replay is absent. A faster claim alone does not replace the baseline. Explicit action/subject approval is recorded.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-18 — Model policy and telemetry

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Ask recommendations for plan, build, summarize, validate, review and an unknown phase. Submit missing, negative and non-finite token/runtime measurements through test tooling; separately record ordinary valid but self-reported metrics.

**Pass evidence:** Validation aliases remain protected Fable/high, unknown phases fail, invalid metrics fail and missing values do not become zero. Valid self-reported telemetry remains advisory; no automatic cheap-model substitution occurs.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-19 — Preference provenance and negation

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Say For this workflow use Net Sales, then ask Chairman to retain the preference with the actual user instruction. Separately say Do not use Units. Attempt recording only the substring use Units as the preference.

**Pass evidence:** Stored preference points to the actual full user instruction in the current project; removing negation is rejected. An agent's invented source=user string cannot substitute for the recorded turn.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-20 — Ice-cube observation with limited evidence

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Supply a small explicitly synthetic report and say hot days appear to coincide with greater ice-cube sales. Ask to remember the finding, with scope, period and limitations. This fixture is not evidence of real Praktiker sales; do not attach production claims.

**Pass evidence:** The item is an observation, not causation/canonical replenishment policy. It retains source/method/period/limits. A future task retrieves the observation and identifies the need for broader validation instead of rediscovering or overstating it.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-21 — Knowledge lifecycle, evidence and supersession

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Create a project-local claim, attach exact source evidence, attempt stronger statuses with and without required evidence, then create an altered statement and explicitly supersede the old item. Test an invented type and reusing an approval for another process.

**Pass evidence:** Allowlisted types and separate approval/evidence gates apply. Old statements are not overwritten; old/challenged/rejected items remain history but not default current truth. Unknown type cannot bypass governance.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-22 — Cross-project and global scope

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Index the same byte-identical synthetic document in projects A and B with different provenance. Search/read/mutate an A-only object from B. Attempt company_wide=True through public MCP.

**Pass evidence:** Source identity includes scope/authority; A-only content does not leak into B. Cross-project mutation fails. Global publication is explicitly held in this preview rather than silently granted by a Boolean.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-23 — Normal mechanical onboarding

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** In a disposable project, onboard a small folder with text, CSV, DOCX, XLSX, PPTX, searchable PDF, duplicate copies and ignored generated folders. Include the supplied synthetic Excel fixtures. Record hashes, source locations, counts and queue records before/after repeating the run.

**Pass evidence:** Raw files stay untouched. Supported content extracts within bounds; duplicates preserve locations without conflating project authority. Errors/limits are visible. A repeated run may reparse files: do not require a nonexistent full parser cache.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-24 — Hostile and unusual documents

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Use ONLY a disposable resource-limited VM: malformed/encrypted/no-text PDFs; corrupt/overexpanded OOXML; alternate CSV delimiters; large text; permission-denied files; Greek paths; symlink/junctions. Do not create huge attacks on the host workstation.

**Pass evidence:** Known input failures/truncations are reported and queued; path/ZIP limits hold; no macros/links execute. Parser time/output bounds work. Windows hard RAM isolation is NOT claimed. Code/SQL bugs abort rather than becoming bad-document reports.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-25 — Mutable files and review decisions

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Change a test file during acquisition; test one source moved/deleted after indexing. Resolve and dismiss specific review items with reasons, then verify that resolving an item alone does not promote its claim.

**Pass evidence:** Mutation/unavailable evidence is exposed, not certified stable. Review decision history persists and does not become canonical knowledge by itself. Original paths are references, not an archival backup.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-26 — Lexical retrieval without embeddings

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Leave embeddings disabled and ingest a few known text records. Search exact IDs, title words and Greek text. Add outdated/superseded items and verify default results. Record expected-query IDs separately.

**Pass evidence:** Core retrieval works without model downloads. Superseded records are not presented as current. Empty/unknown/incomplete coverage is reported. This is not proof of broad Greeklish semantic accuracy.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-27 — Actual optional embedding runtime

**Applicability:** Optional. **Initial status:** NOT RUN.

**Execute:** Install with -WithEmbeddings in the VM. Configure a supported local multilingual model, allow its real download and process a small queue. Record actual dependency versions, model revision, vector shape, elapsed time and RAM.

**Pass evidence:** Real finite vectors are generated and queried with matching prefixes/dimensions. Missing model/runtime errors stay visible. No claim of successful inference is made from queued jobs alone.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-28 — Worker crash, model change and leases

**Applicability:** Optional. **Initial status:** NOT RUN.

**Execute:** With actual PostgreSQL/embeddings, run two workers; terminate one after claiming a job, let the claim expire, restart, and change the configured model during an old job. Also test missing vectors after a completed job.

**Pass evidence:** Leases/attempts prevent stale writes, jobs recover without infinite retries, compatible model/vector checks hold, and missing completed output can be repaired. Real locking behavior must be observed under PostgreSQL.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-29 — Chairman engineering journey

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** In a new disposable repo ask for a tiny feature with an exact acceptance contract. Observe planning, current impact, code/test changes, protected validation and completion without manually issuing build/save/validator commands.

**Pass evidence:** One coherent end-to-end outcome is delivered and checkpointed. Directors return staffing requests rather than pretending unsupported recursive agents ran. Missing required environments yield incomplete evidence, not production-ready prose.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-30 — Optional Codex adapter

**Applicability:** Optional. **Initial status:** NOT RUN.

**Execute:** Install/authenticate Codex natively; ask for a read-only review of the disposable repo. Test timeout, missing CLI/login and out-of-project path requests. Inspect prompt transport and bounded output.

**Pass evidence:** Adapter invokes the real authenticated CLI with intended permissions; prompts are not command-line secrets, invalid paths fail before execution, time/output limits hold. CWD checks are not called an OS sandbox.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-31 — Semantic graph and provenance

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Register module/process/source nodes, add one typed relationship twice with different evidence, query impact, ask for an unknown key, and create a deliberately ambiguous key under two kinds. Exercise bounded traversal.

**Pass evidence:** Both evidence records survive, kind identity is preserved, unknown differs from known/no recorded edges, ambiguity requires kind, and a bounded/incomplete traversal never claims exhaustive no impact.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-32 — Manual refresh with exact reviewed delta

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Start a project-owned refresh task. Save a JSON delta including refresh_key, delta_summary and knowledge_version. Checkpoint the final state, prepare validation including that exact file, run protected validation, then complete refresh. Edit the file and retry. Inspect due dates.

**Pass evidence:** Only the fresh exact reviewed delta can complete. Another task's review/string flag is insufficient. Due dates exist but no unattended annual scheduler is claimed. External practice remains a candidate until supported/adopted.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-33 — Staged update and source independence

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** After a working VM snapshot, remove/move only the source extraction directory and verify installed Vres still starts. Restore the source and run .\update.ps1 with native sessions/workers closed. Observe new release paths, plugin backup and active pointer.

**Pass evidence:** Installed runtime is independent of the ZIP directory. New venv is built at its permanent path, checked before pointer publication, and old release retained. Actual resolved dependencies are recorded; DB backup is separate.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-34 — Caught update failure and abrupt journal recovery

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** In a VM only, induce an installation failure before and after staging, and separately interrupt near publication. Inspect old pointer/plugin/bin and pending-install.json. Follow manual journal recovery rather than deleting it blindly.

**Pass evidence:** Caught failure restores the prior usable selection where promised. Abrupt interruption blocks unattended retry and leaves recoverable evidence. No claim that binary rollback undoes schema migrations. Escalate to snapshot restore if uncertain.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-35 — Uninstall/reinstall data preservation

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Close sessions/workers; run .\uninstall.ps1 without RemoveLocalData. Inspect native vendor logins, DB, source repo, config/vault and PATH. Reinstall the same source and recover the known task after setup/status checks.

**Pass evidence:** Only owned runtime/plugin/bin are removed. DB/project/vendor credentials remain untouched; local Vres config/runtime credential are preserved. Reinstall works without re-creating or resetting existing provisioned DB roles.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-36 — Explicit local cleanup and owned paths

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Use a separate disposable snapshot. Attempt uninstall with a pending journal or reparse-point install root; it should refuse. Then run valid uninstall -RemoveLocalData and inspect only Vres-owned config/logs/runtime credential.

**Pass evidence:** Cleanup honors explicit consent and owned boundaries. It never deletes PostgreSQL databases, company source files or Claude/Codex login. A wrong plugin/runtime path or running worker blocks destructive removal.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

### LV-37 — One realistic day and final verdict

**Applicability:** Required. **Initial status:** NOT RUN.

**Execute:** Combine accepted Excel reuse, limited observation capture, a tiny code task, protected review, compaction/restart and project switching. Have the junior tester operate the normal conversation without an engineer coaching each tool invocation. Preserve sanitized records and exact artifact hashes.

**Pass evidence:** Every applicable required case has recorded evidence and no unresolved critical failure. Optional cases are NOT RUN when unused, never counted as pass. Held features stay held. Only then approve wider live evaluation; production is a separate decision.

**Record:** actual result, sanitized evidence path, native versions, defect/reviewer.

## Final release decision

Sign the actual matrix, not this blank plan. Record remaining defects and held functions. The decision can be
“eligible for limited use on these tested projects”, not necessarily production-ready. Keep the old working
AIGO environment and tested VM snapshot available until rollback/recovery have themselves passed.

## Primary interface references

Checked 2026-09-13; recheck when native dependencies change. Documentation describes capabilities, not proof
of the Vres integration on your machine.

- https://code.claude.com/docs/en/plugins-reference
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/env-vars
- https://code.claude.com/docs/en/setup
- https://developers.openai.com/codex/noninteractive
- https://www.postgresql.org/docs/17/
- https://www.psycopg.org/psycopg3/docs/
- https://keyring.readthedocs.io/en/stable/
