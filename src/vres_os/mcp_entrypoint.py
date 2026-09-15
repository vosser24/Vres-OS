from __future__ import annotations

from .company_mcp import mcp
from .mcp_server import _current_session, _project, _require_node
from .reply_guard import confirm_reply_gate


@mcp.tool()
def task_reply_gate(task_key: str, session_id: str, advances_state: bool) -> dict:
    """Satisfy the turn-scoped pre-reply guard without inferring progress from assistant prose.

    Set advances_state=true only after task_checkpoint when the pending reply itself
    completes, invalidates, or advances persisted next_action/pending_work. Use false
    only for a genuinely non-material reply.
    """
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return confirm_reply_gate(pid, sid, task_key, advances_state=advances_state)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
