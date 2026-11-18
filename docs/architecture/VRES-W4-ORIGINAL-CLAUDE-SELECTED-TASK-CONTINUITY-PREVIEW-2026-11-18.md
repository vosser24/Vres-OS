# 2026-11-18 — Original Claude CLI/MCP explicit task continuity preview

**SOURCE ONLY. All exact-source Python, AST, pytest, PowerShell, MCP, native Claude/hooks, PostgreSQL even SELECT, Windows and installer operations NOT_RUN/HELD.**

## Integrated personal workday improvement

After the original Chairman presents the original current-project workday_overview, the user may explicitly identify ONE task and inspect it before deciding to resume. The new task_continuity_preview(task_key) tool is registered on the SAME existing mcp_server.mcp FastMCP instance, using the SAME original Repository.inspect_task owner. It does NOT invoke resume_context, create a task, set project focus, bind a session, capture an episode or mutate a result. Project ID comes from _existing_project and lookup includes BOTH the current project ID and exact task key.

One bounded, declared READ ONLY transaction reads the original vres.tasks/vres.task_state state, latest vres.checkpoints record, and (only for completed tasks) most recent vres.task_events TASK_COMPLETED event. This is the original complete_task recorded result, with event ID and timestamp; absence is explicitly null. No new schema, table, result ledger, experience store, migration, CLI application, alternate runtime or GUI.

The MCP response redacts and clips untrusted persisted strings, limits lists and reports overflow. Persisted validation status is NOT current validator authorization. Recorded results are history, not proof of calendar-today, current PASS or approved learning. experience_reference names the ORIGINAL experience_retrieve route without querying or inventing an episode key; governed learning is a separate deliberate operation.

Original Chairman guidance requires explicit task choice before inspection and separately before state-changing task_resume using the genuine current Claude session. Existing configured-only control_preflight inspection classification and exact PreToolUse matcher admit this read-only tool during an established inspection hold; unconfigured access remains limited to vres_status / explicit start_vres. The VresMCP.call_tool native-host hold still precedes tool dispatch. Original synthetic regressions updated and new tests authored but NOT_RUN. No real DB query executed.

## Boundary and next steps

Do not interpret task preview as session binding, current validation, evidence approval or knowledge promotion. Retain original task_resume, task_complete, experience_retrieve and task/event owners; preserve source-only holds and the full original V-01..V-42 roadmap. This is a useful source milestone, NOT first-FULL release/UAT evidence. Independent issue #185 acceptance, closure of BOTH LIVE_SCHEMA_048 and HOST_HOOK_DB_ROUTE incidents, publisher/toolchain/wheelhouse closure and separate owner consent are prerequisites to native execution, Windows install or protected P2 modification.
