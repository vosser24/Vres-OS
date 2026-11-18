# 2026-11-18 — Original Claude CLI/MCP explicit task continuity preview

**SOURCE ONLY. All exact-source Python, AST, pytest, PowerShell, MCP, native Claude/hooks, PostgreSQL even SELECT, Windows and installer operations NOT_RUN/HELD.**

## Integrated personal workday improvement

After the original Chairman presents the original current-project workday_overview, the user may explicitly identify ONE task and inspect it before deciding to resume. The new task_continuity_preview(task_key) tool is registered on the SAME existing mcp_server.mcp FastMCP instance, using the SAME original Repository.inspect_task owner. It does NOT invoke resume_context, create a task, set project focus, bind a session, capture an episode or mutate a result. Project ID comes from _existing_project and lookup includes BOTH the current project ID and exact task key.

One bounded, declared READ ONLY transaction reads the original vres.tasks/vres.task_state state, latest vres.checkpoints record, and (only for completed tasks) most recent vres.task_events TASK_COMPLETED event. This is the original complete_task recorded result, with event ID and timestamp; absence is explicitly null. No new schema, table, result ledger, experience store, migration, CLI application, alternate runtime or GUI.

The MCP response redacts and clips untrusted persisted strings, limits lists and reports overflow. Persisted validation status is NOT current validator authorization. Recorded results are history, not proof of calendar-today, current PASS or approved learning. experience_reference names the ORIGINAL experience_retrieve route without querying or inventing an episode key; governed learning is a separate deliberate operation.

Original Chairman guidance requires explicit task choice before inspection and separately before state-changing task_resume using the genuine current Claude session. Existing configured-only control_preflight inspection classification and exact PreToolUse matcher admit this read-only tool during an established inspection hold; unconfigured access remains limited to vres_status / explicit start_vres. The VresMCP.call_tool native-host hold still precedes tool dispatch. Original synthetic regressions updated and new tests authored but NOT_RUN. No real DB query executed.

## Boundary and next steps

Do not interpret task preview as session binding, current validation, evidence approval or knowledge promotion. Retain original task_resume, task_complete, experience_retrieve and task/event owners; preserve source-only holds and the full original V-01..V-42 roadmap. This is a useful source milestone, NOT first-FULL release/UAT evidence. Independent issue #185 acceptance, closure of BOTH LIVE_SCHEMA_048 and HOST_HOOK_DB_ROUTE incidents, publisher/toolchain/wheelhouse closure and separate owner consent are prerequisites to native execution, Windows install or protected P2 modification.

## Follow-up source correction — structured JSONB continuity hints

The original `task_state` records pending/completed work and relevant objects as JSONB lists, and its `ActiveTask` type permits `list[Any]`. The first preview implementation discarded non-string entries without indicating omission, potentially hiding a concrete work item or reference. The original MCP renderer now shows the first five JSON values as bounded redacted hints (including maps, nested lists and scalars), keeps the original overflow indicator, and never calls a resume, focus, session, database mutation or separate experience owner. The renderer reuses the canonical nested `redact` helper before serialization and the existing text redaction before output clipping. Regression fixtures for structured values, nested credential-like fields, list limits and output flags are AUTHORED/NOT_RUN; no native host, Python, database or Windows execution is implied.

## Additional source-only safety correction — residual credential assignments

The canonical eager nested `redact` does not mask every credential-like key (e.g. `ssh_passphrase` or `db_credential`). Once structured JSONB hints became visible, such values could have appeared in the MCP preview. The SAME original renderer now invokes the existing canonical `sanitize_text` residual-secret postcondition BEFORE text clipping for both string and nested JSON hints, and replaces any unsafe whole hint with `[REDACTED_UNSAFE_HINT]`. It does not edit stored tasks, invoke task_resume, create another store or grant execution. Regression fixtures for raw and nested residual assignments are AUTHORED/NOT_RUN; actual Python/pytest/MCP/DB/Windows execution remains HELD.
