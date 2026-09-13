from __future__ import annotations

import shutil
from pathlib import Path

from .redaction import redact_text
from .processes import ProcessResult as CodexResult, run_bounded, MAX_PROMPT_BYTES


class CodexAdapter:
    """Read-only review adapter. CWD confinement is not an OS security boundary.

    Vendor authentication stays with the native client. Never retry with a weaker
    sandbox if read-only execution is unavailable on the destination machine.
    """
    def available(self) -> bool:
        return shutil.which("codex") is not None

    def doctor(self, timeout: int = 30) -> CodexResult:
        executable = shutil.which("codex")
        if not executable:
            return CodexResult(False, "Codex CLI not installed", 127)
        return run_bounded([executable, "--version"], timeout=timeout)

    def exec(self, prompt: str, *, cwd: Path, timeout: int = 900, project_root: Path | None = None) -> CodexResult:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("A non-empty Codex review prompt is required")
        if len(prompt.encode("utf-8")) > MAX_PROMPT_BYTES:
            raise ValueError("Codex input exceeds the prompt budget")
        if redact_text(prompt) != prompt:
            raise ValueError("Remove credentials from the prompt before invoking Codex")
        root = (project_root or cwd).resolve()
        target = cwd.resolve()
        if not target.is_dir() or not target.is_relative_to(root):
            raise ValueError("Codex working directory must be inside the intended existing project")
        executable = shutil.which("codex")
        if not executable:
            return CodexResult(False, "Codex CLI not installed", 127)
        return run_bounded([executable, "exec", "--sandbox", "read-only", "-"],
                           cwd=target, prompt=prompt, timeout=timeout)
