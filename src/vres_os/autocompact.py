from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

_AUTO_COMPACT_KEY = "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"
_AUTO_COMPACT_WINDOW_KEY = "CLAUDE_CODE_AUTO_COMPACT_WINDOW"
_DISABLE_KEYS = ("DISABLE_AUTO_COMPACT", "DISABLE_COMPACT")
_DESIRED_USED_PERCENT = "85"


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
    return (value, bom) if isinstance(value, dict) else (None, bom)


def _write_json_file(path: Path, value: dict[str, Any], *, bom: bool) -> None:
    raw = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    _atomic_write(path, (b"\xef\xbb\xbf" + raw) if bom else raw)


def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _settings_env(settings: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    current = settings.get("env")
    if current is None:
        return {}, None
    if not isinstance(current, dict):
        return None, "existing-nondict-env-preserved"
    return dict(current), None


def _settings_conflict(env: dict[str, Any]) -> str | None:
    if env.get(_AUTO_COMPACT_WINDOW_KEY) not in (None, ""):
        return "existing-custom-auto-compact-window-preserved"
    if any(_truthy(env.get(key)) for key in _DISABLE_KEYS):
        return "existing-auto-compact-disable-preserved"
    return None


def _process_conflict() -> str | None:
    if os.environ.get(_AUTO_COMPACT_WINDOW_KEY):
        return "process-auto-compact-window-present"
    if any(_truthy(os.environ.get(key)) for key in _DISABLE_KEYS):
        return "process-auto-compact-disable-present"
    return None


def _store_env(
    settings_path: Path,
    settings: dict[str, Any],
    env: dict[str, Any],
    *,
    bom: bool,
) -> None:
    if env:
        settings["env"] = env
    else:
        settings.pop("env", None)
    _write_json_file(settings_path, settings, bom=bom)


def install_autocompact(claude_home: Path, *, owned_before: bool = False) -> dict[str, Any]:
    """Configure Claude's native auto-compaction at 85% used context conservatively."""
    settings_path = claude_home.resolve() / "settings.json"
    settings, bom = _read_json_file(settings_path)
    if settings is None:
        return {
            "configured": False,
            "owned": False,
            "reason": "invalid-settings-json-preserved",
            "settings_path": str(settings_path),
        }

    env, env_error = _settings_env(settings)
    if env is None:
        return {
            "configured": False,
            "owned": False,
            "reason": env_error,
            "settings_path": str(settings_path),
        }

    existing = env.get(_AUTO_COMPACT_KEY)
    settings_conflict = _settings_conflict(env)
    process_conflict = _process_conflict()

    if owned_before:
        if existing is None:
            return {
                "configured": False,
                "owned": False,
                "reason": "managed-autocompact-removed-externally",
                "settings_path": str(settings_path),
            }
        if str(existing) != _DESIRED_USED_PERCENT:
            return {
                "configured": False,
                "owned": False,
                "reason": "managed-autocompact-modified-externally",
                "settings_path": str(settings_path),
            }
        if settings_conflict:
            env.pop(_AUTO_COMPACT_KEY, None)
            _store_env(settings_path, settings, env, bom=bom)
            return {
                "configured": False,
                "owned": False,
                "updated": True,
                "reason": settings_conflict,
                "settings_path": str(settings_path),
            }
        result = {
            "configured": True,
            "owned": True,
            "updated": False,
            "used_percent": int(_DESIRED_USED_PERCENT),
            "settings_path": str(settings_path),
        }
        if process_conflict:
            result["warning"] = process_conflict
        return result

    if existing is not None:
        return {
            "configured": False,
            "owned": False,
            "reason": "existing-custom-autocompact-preserved",
            "settings_path": str(settings_path),
        }
    conflict = settings_conflict or process_conflict
    if conflict:
        return {
            "configured": False,
            "owned": False,
            "reason": conflict,
            "settings_path": str(settings_path),
        }

    env[_AUTO_COMPACT_KEY] = _DESIRED_USED_PERCENT
    _store_env(settings_path, settings, env, bom=bom)
    return {
        "configured": True,
        "owned": True,
        "updated": True,
        "used_percent": int(_DESIRED_USED_PERCENT),
        "settings_path": str(settings_path),
    }


def remove_autocompact(claude_home: Path, *, owned: bool) -> dict[str, Any]:
    """Remove only an 85% auto-compaction setting that Vres still owns."""
    settings_path = claude_home.resolve() / "settings.json"
    if not owned:
        return {
            "removed": False,
            "reason": "not-vres-owned",
            "settings_path": str(settings_path),
        }

    settings, bom = _read_json_file(settings_path)
    if settings is None:
        return {
            "removed": False,
            "reason": "invalid-settings-json-preserved",
            "settings_path": str(settings_path),
        }

    env, env_error = _settings_env(settings)
    if env is None:
        return {
            "removed": False,
            "reason": env_error,
            "settings_path": str(settings_path),
        }

    existing = env.get(_AUTO_COMPACT_KEY)
    if existing is None:
        return {
            "removed": False,
            "reason": "managed-autocompact-already-absent",
            "settings_path": str(settings_path),
        }
    if str(existing) != _DESIRED_USED_PERCENT:
        return {
            "removed": False,
            "reason": "managed-autocompact-modified-externally",
            "settings_path": str(settings_path),
        }

    env.pop(_AUTO_COMPACT_KEY, None)
    _store_env(settings_path, settings, env, bom=bom)
    return {"removed": True, "settings_path": str(settings_path)}


def _bool_arg(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes"}:
        return True
    if lowered in {"0", "false", "no"}:
        return False
    raise argparse.ArgumentTypeError("expected true/false")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m vres_os.autocompact")
    sub = parser.add_subparsers(dest="command", required=True)

    install = sub.add_parser("install")
    install.add_argument("--claude-home", required=True)
    install.add_argument("--owned-before", type=_bool_arg, default=False)

    remove = sub.add_parser("remove")
    remove.add_argument("--claude-home", required=True)
    remove.add_argument("--owned", type=_bool_arg, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    result = (
        install_autocompact(Path(args.claude_home), owned_before=bool(args.owned_before))
        if args.command == "install"
        else remove_autocompact(Path(args.claude_home), owned=bool(args.owned))
    )
    sys.stdout.write(json.dumps(result, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
