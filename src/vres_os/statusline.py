from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

_MAX_INPUT_BYTES = 256 * 1024
_VRES_COMMAND_MARKER = "vres_os.statusline"


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.vres-tmp")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def _read_json_file(path: Path) -> tuple[dict[str, Any] | None, bool]:
    if not path.exists():
        return {}, False
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    body = raw[3:] if bom else raw
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, bom
    if not isinstance(value, dict):
        return None, bom
    return value, bom


def _write_json_file(path: Path, value: dict[str, Any], *, bom: bool) -> None:
    raw = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if bom:
        raw = b"\xef\xbb\xbf" + raw
    _atomic_write(path, raw)


def _vres_owned_status_line(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and str(value.get("type") or "") == "command"
        and _VRES_COMMAND_MARKER in str(value.get("command") or "")
    )


def _status_line_command(runtime_python: Path) -> str:
    python = runtime_python.resolve(strict=True)
    command_path = str(python).replace("\\", "/")
    return subprocess.list2cmdline(
        [command_path, "-I", "-X", "utf8", "-m", "vres_os.statusline"]
    )


def install_statusline(claude_home: Path, runtime_python: Path) -> dict[str, Any]:
    """Install/update only a Vres-owned Claude statusLine; preserve any custom one."""
    home = claude_home.resolve()
    settings_path = home / "settings.json"
    settings, bom = _read_json_file(settings_path)
    if settings is None:
        return {
            "configured": False,
            "reason": "invalid-settings-json-preserved",
            "settings_path": str(settings_path),
        }

    existing = settings.get("statusLine")
    if existing is not None and not _vres_owned_status_line(existing):
        return {
            "configured": False,
            "reason": "existing-custom-status-line-preserved",
            "settings_path": str(settings_path),
        }

    desired = {
        "type": "command",
        "command": _status_line_command(runtime_python),
        "padding": 0,
    }
    if existing == desired:
        return {
            "configured": True,
            "updated": False,
            "settings_path": str(settings_path),
        }

    settings["statusLine"] = desired
    _write_json_file(settings_path, settings, bom=bom)
    return {
        "configured": True,
        "updated": existing is not None,
        "settings_path": str(settings_path),
    }


def remove_statusline(claude_home: Path) -> dict[str, Any]:
    """Remove only a Vres-owned statusLine entry; preserve all other settings."""
    home = claude_home.resolve()
    settings_path = home / "settings.json"
    settings, bom = _read_json_file(settings_path)
    if settings is None:
        return {
            "removed": False,
            "reason": "invalid-settings-json-preserved",
            "settings_path": str(settings_path),
        }
    existing = settings.get("statusLine")
    if not _vres_owned_status_line(existing):
        return {
            "removed": False,
            "reason": (
                "existing-custom-status-line-preserved"
                if existing is not None
                else "no-vres-status-line"
            ),
            "settings_path": str(settings_path),
        }
    settings.pop("statusLine", None)
    _write_json_file(settings_path, settings, bom=bom)
    return {"removed": True, "settings_path": str(settings_path)}


def _text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _percent(value: Any) -> str | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    return f"{number:.0f}%"


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def render_statusline(payload: dict[str, Any]) -> str:
    """Render only telemetry Claude Code supplied in this refresh payload."""
    model = _dict(payload.get("model"))
    model_name = _text(model.get("display_name")) or _text(model.get("id"))
    if model_name and model_name.lower().startswith("claude "):
        model_name = model_name[7:].strip()
    model_name = model_name or "model ?"

    effort = _text(_dict(payload.get("effort")).get("level"))
    identity = f"{model_name} · {effort}" if effort else model_name

    parts = [identity]
    context = _percent(_dict(payload.get("context_window")).get("used_percentage"))
    if context is not None:
        parts.append(f"ctx {context}")

    limits = _dict(payload.get("rate_limits"))
    five_hour = _percent(_dict(limits.get("five_hour")).get("used_percentage"))
    seven_day = _percent(_dict(limits.get("seven_day")).get("used_percentage"))
    if five_hour is not None:
        parts.append(f"5h {five_hour}")
    if seven_day is not None:
        parts.append(f"7d {seven_day}")
    return " | ".join(parts)


def render_bytes(raw: bytes) -> str:
    if len(raw) > _MAX_INPUT_BYTES:
        return ""
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ""
    if not isinstance(payload, dict):
        return ""
    return render_statusline(payload)


def _print_result(result: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(result, separators=(",", ":")) + "\n")


def main() -> int:
    args = sys.argv[1:]
    if args:
        if args[0] not in {"install", "remove"}:
            return 0
        if len(args) < 3 or args[1] != "--claude-home":
            return 2
        home = Path(args[2])
        if args[0] == "remove":
            _print_result(remove_statusline(home))
            return 0
        if len(args) != 5 or args[3] != "--runtime-python":
            return 2
        _print_result(install_statusline(home, Path(args[4])))
        return 0

    raw = sys.stdin.buffer.read(_MAX_INPUT_BYTES + 1)
    rendered = render_bytes(raw)
    if rendered:
        sys.stdout.write(rendered + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
