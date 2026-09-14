import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


@pytest.mark.skipif(os.name != "nt", reason="Node/libuv inherited-stdin Git hang is Windows-specific")
def test_project_discovery_returns_under_node_libuv_mcp_stdin_pipe(tmp_path: Path):
    if not shutil.which("node") or not shutil.which("git"):
        pytest.skip("Windows live regression needs node and git on PATH")

    project = tmp_path / "project"
    project.mkdir()
    subprocess.run(
        ["git", "-C", str(project), "init"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
        timeout=10,
    )

    child = tmp_path / "mcp_style_child.py"
    child.write_text(
        textwrap.dedent(
            """
            import sys
            import threading
            from vres_os.project import discover_project

            threading.Thread(target=lambda: sys.stdin.buffer.read(1), daemon=True).start()
            print(discover_project(sys.argv[1]).root, flush=True)
            """
        ),
        encoding="utf-8",
    )
    parent = tmp_path / "node_parent.js"
    parent.write_text(
        textwrap.dedent(
            r"""
            const { spawn, execFileSync } = require("child_process");
            const p = spawn(process.env.VRES_TEST_PY, [process.env.VRES_TEST_CHILD, process.env.VRES_TEST_PROJECT], {
              stdio: ["pipe", "pipe", "pipe"], windowsHide: true
            });
            let out = "", err = "";
            p.stdout.on("data", d => out += d);
            p.stderr.on("data", d => err += d);
            const timer = setTimeout(() => {
              try { execFileSync("taskkill.exe", ["/PID", String(p.pid), "/T", "/F"], {stdio: "ignore"}); } catch (_) {}
              console.error("Vres project discovery hung under Node/libuv piped stdin");
              process.exit(124);
            }, 10000);
            p.on("exit", code => {
              clearTimeout(timer);
              process.stdout.write(out);
              process.stderr.write(err);
              process.exit(code === 0 ? 0 : (code || 1));
            });
            """
        ),
        encoding="utf-8",
    )

    env = os.environ.copy()
    env.update(
        VRES_TEST_PY=sys.executable,
        VRES_TEST_CHILD=str(child),
        VRES_TEST_PROJECT=str(project),
    )
    result = subprocess.run(
        ["node", str(parent)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=15,
        check=False,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert str(project.resolve()) in result.stdout
