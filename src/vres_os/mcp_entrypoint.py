from __future__ import annotations

from .company_mcp import mcp
from .mcp_server import _current_session, _project
from .reply_guard import observe_reply_activity


@mcp.tool()
def reply_activity_observe(
    session_id: str,
    tool_name: str,
    tool_use_id: str = "",
    event_name: str = "PostToolUse",
) -> dict:
    """Internal lifecycle hook: record bounded tool activity for reply freshness.

    The Chairman should never call this directly. Claude Code's PostToolUse and
    PostToolUseFailure hooks invoke it automatically with host-observed tool identity.
    Tool inputs and outputs are deliberately not persisted.
    """
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    return observe_reply_activity(
        pid,
        sid,
        tool_name,
        tool_use_id=tool_use_id or None,
        event_name=event_name,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
