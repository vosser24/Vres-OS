from __future__ import annotations

import os
import subprocess
import sys

from .paths import logs_dir


def launch_embedding_worker() -> dict:
    from .processes import worker_command
    args = worker_command("vres_os.cli", "embedding-worker")
    log_path = logs_dir() / "embedding-worker.log"
    log = log_path.open("ab")
    kwargs = {"stdin": subprocess.DEVNULL, "stdout": log, "stderr": subprocess.STDOUT}
    try:
        if os.name == "nt":
            flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
            proc = subprocess.Popen(args, creationflags=flags, **kwargs)
        else:
            proc = subprocess.Popen(args, start_new_session=True, **kwargs)
    finally:
        log.close()
    return {"launched": True, "pid": proc.pid, "log": str(log_path)}
