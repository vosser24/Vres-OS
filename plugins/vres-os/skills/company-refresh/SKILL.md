---
name: company-refresh
description: Research material domain changes when requested or overdue, preserving sources, history and validation evidence.
---

Use `refresh_due_domains` to inspect due reviews; a due date is not an automatic background scheduler. On request, begin a scoped task and call `refresh_start` with its task key. Directors research authoritative primary sources, comparing the existing knowledge with the changed evidence. Return a delta: still valid, challenged, newly possible, obsolete, experiments needed. Cite publication/effective dates and company applicability.

Save the exact delta as a project JSON artifact with keys `refresh_key`, `delta_summary`, `knowledge_version`. Persist task state, call `validation_prepare` including that file, and ask `vres-os:validator` for a fresh review. Only after the host-observed PASS call `refresh_complete` with that task, request key, artifact path and the identical JSON values. Another task's PASS or an edited artifact cannot authorize the refresh.

The refresh records research, not automatic company policy changes. Use source/knowledge tools for scoped candidates and approval-backed governance. Company-wide publication is held pending dedicated scope-approval support. An annual due check runs when Vres is used; nothing executes while the application is closed.
