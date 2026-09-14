from __future__ import annotations

import os
import signal
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from .redaction import redact_text

MAX_PROMPT_BYTES = 64 * 1024
MAX_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_RESULT_CHARS = 60_000


@dataclass(slots=True, frozen=True)
class ProcessResult:
    ok: bool
    output: str
    returncode: int


def _terminate(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill.exe", "/PID", str(proc.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def run_bounded(
    args: list[str],
    *,
    cwd: Path | None = None,
    prompt: str = "",
    timeout: float = 30,
    max_output_bytes: int = MAX_OUTPUT_BYTES,
    max_result_chars: int = MAX_RESULT_CHARS,
    redact_output: bool = True,
) -> ProcessResult:
    """No shell, no prompt in argv, finite retained output, and bounded process lifetime."""
    if not 0 < timeout <= 3600:
        raise ValueError("Subprocess timeout must be in (0, 3600] seconds")
    if (
        type(max_output_bytes) is not int
        or type(max_result_chars) is not int
        or not 1 <= max_output_bytes <= 64 * 1024 * 1024
        or not 1 <= max_result_chars <= 64 * 1024 * 1024
    ):
        raise ValueError("Worker output limits must be positive bounded integers")
    if len(prompt.encode("utf-8")) > MAX_PROMPT_BYTES:
        raise ValueError("Worker input exceeds the prompt budget")
    with tempfile.TemporaryFile() as source, tempfile.TemporaryFile() as output:
        source.write(prompt.encode("utf-8"))
        source.seek(0)
        options = (
            {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
            if os.name == "nt"
            else {"start_new_session": True}
        )
        proc = subprocess.Popen(
            args,
            cwd=cwd,
            stdin=source,
            stdout=output,
            stderr=subprocess.STDOUT,
            **options,
        )
        started, forced, reason = time.monotonic(), None, ""
        try:
            while proc.poll() is None:
                if os.fstat(output.fileno()).st_size > max_output_bytes:
                    forced, reason = 125, "Worker exceeded its output budget; execution terminated.\n"
                    _terminate(proc)
                    break
                if time.monotonic() - started >= timeout:
                    forced, reason = 124, "Worker timed out; execution terminated.\n"
                    _terminate(proc)
                    break
                time.sleep(0.02)
            size = os.fstat(output.fileno()).st_size
            if size > max_output_bytes and forced is None:
                forced, reason = 125, "Worker exceeded its output budget.\n"
            output.seek(max(0, size - max_output_bytes))
            text = output.read(max_output_bytes).decode("utf-8", errors="replace")
            if redact_output:
                text = redact_text(text)
            if len(text) > max_result_chars:
                text = "[earlier output omitted]\n" + text[-max_result_chars:]
            code = forced if forced is not None else proc.returncode
            return ProcessResult(code == 0, reason + text.strip(), code)
        finally:
            _terminate(proc)


def worker_command(module: str, *arguments: str) -> list[str]:
    """Import only this installed/source distribution, never a project shadow package."""
    import sys

    if module not in {"vres_os.cli", "vres_os.parse_worker", "vres_os.procedure_worker"}:
        raise ValueError("Unapproved Vres worker module")
    loader = (
        "import runpy,sys; sys.path.insert(0,sys.argv.pop(1)); "
        "runpy.run_module(sys.argv.pop(1),run_name='__main__')"
    )
    return [
        sys.executable,
        "-I",
        "-X",
        "utf8",
        "-c",
        loader,
        str(Path(__file__).resolve().parent.parent),
        module,
        *arguments,
    ]
