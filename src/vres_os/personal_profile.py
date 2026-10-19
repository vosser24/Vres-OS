"""Personal-release feature fence: a narrow, versioned capability contract.

The personal release runs only on Windows, so, like the P2-A1 database contact guard,
every Windows process is in the personal profile. That decision depends only on the
interpreter platform: no environment variable, configuration value or file can enable
a fenced capability or leave the profile.

Inside the profile a consequential capability runs only if this contract approves it
by name. The capabilities below are listed explicitly as not approved, and any name
the contract does not list is refused as well (default deny). Callers check at the
real execution boundary, before the associated side effect; a refusal leaves stored
credentials, prepared handoffs and project artifacts untouched.
"""
from __future__ import annotations

import sys

PROFILE_NAME = "vres-personal"
PROFILE_VERSION = 1

CODEX_HANDOFF_EXECUTE = "codex_handoff_execute"
PROCEDURE_AUTO_PROMOTION = "procedure_auto_promotion"
MODEL_EXPERIMENT_EXECUTION = "model_experiment_execution"
LEGACY_SECRET_ALIASES = "legacy_secret_aliases"

# capability -> (approved in the personal profile, why). Only a literal True approves.
CAPABILITIES: dict[str, tuple[bool, str]] = {
    CODEX_HANDOFF_EXECUTE: (False, "launching Codex and promoting its changes into the workspace"),
    PROCEDURE_AUTO_PROMOTION: (False, "unattended project-scoped procedure promotion"),
    MODEL_EXPERIMENT_EXECUTION: (False, "live, paid model-experiment execution"),
    LEGACY_SECRET_ALIASES: (False, "legacy Vres secret-alias commands; use Credential Broker resources"),
}


class CapabilityDisabled(PermissionError):
    """A consequential capability is not approved in the personal profile; nothing was executed."""

    def __init__(self, capability: str, message: str):
        super().__init__(message)
        self.capability = capability


def _personal_platform() -> bool:
    return sys.platform == "win32"


def personal_profile_active() -> bool:
    return _personal_platform()


def capability_enabled(capability: str) -> bool:
    if not personal_profile_active():
        return True
    approved = CAPABILITIES.get(capability, (False, ""))[0]
    return approved is True


def require_capability(capability: str) -> None:
    """Refuse, before any side effect, a capability the personal profile has not approved."""
    if capability_enabled(capability):
        return
    known = CAPABILITIES.get(capability)
    what = known[1] if known else "a capability this profile does not list"
    raise CapabilityDisabled(
        capability,
        f"'{capability}' ({what}) is disabled in the Vres personal release "
        f"({PROFILE_NAME} v{PROFILE_VERSION}). Nothing was executed and no stored data was changed.",
    )


def describe() -> dict:
    return {
        "profile": PROFILE_NAME,
        "version": PROFILE_VERSION,
        "active": personal_profile_active(),
        "capabilities": {
            name: {"approved": approved, "scope": scope} for name, (approved, scope) in CAPABILITIES.items()
        },
        "default": "deny",
    }
