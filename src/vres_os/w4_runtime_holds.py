"""Independent P0 source-only holds for original runtime and native Claude routes.

NOT trusted source attestation, OS isolation, incident clearance or execution approval.
"""

W4_ORIGINAL_RUNTIME_SOURCE_INTERLOCK = "HELD_NO_ORIGINAL_PYTHON_RUNTIME"
W4_NATIVE_CLAUDE_SOURCE_INTERLOCK = "HELD_HOST_HOOK_DB_ROUTE_INCIDENT"


class W4OriginalRouteRefused(RuntimeError):
    """Refuse direct original routes while independent P0 holds remain open."""


def require_w4_original_runtime_clearance() -> None:
    if W4_ORIGINAL_RUNTIME_SOURCE_INTERLOCK != "INDEPENDENT_RUNTIME_REVIEW_AND_OWNER_APPROVED":
        raise W4OriginalRouteRefused(
            "VRES_W4_HELD_ORIGINAL_RUNTIME: direct Python execution is blocked; "
            "first-FULL runtime and release authority are not granted."
        )

def require_w4_native_host_clearance() -> None:
    require_w4_original_runtime_clearance()
    if W4_NATIVE_CLAUDE_SOURCE_INTERLOCK != "INDEPENDENT_HOST_INCIDENT_CLEARANCE_AND_OWNER_APPROVED":
        raise W4OriginalRouteRefused(
            "VRES_W4_HELD_NATIVE_CLAUDE: ordinary Claude Code, MCP and hooks "
            "remain blocked under HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED."
        )
    # R13O native entrypoint check AFTER P0 refusal. Non-DB installer
    # doctor preflight may still execute inside the installer's exclusive lock
    # after independent operational clearance; installed CLI and DB are fenced separately.
    from .install_transaction import require_install_transaction_ready

    require_install_transaction_ready()
