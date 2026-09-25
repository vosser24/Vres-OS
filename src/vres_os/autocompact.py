from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

AUTO_COMPACT_KEY = "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"
AUTO_COMPACT_WINDOW_KEY = "CLAUDE_CODE_AUTO_COMPACT_WINDOW"
DISABLE_KEYS = ("DISABLE_AUTO_COMPACT", "DISABLE_COMPACT")
DESIRED_USED_PERCENT = "15"
LEGACY_MANAGED_USED_PERCENTS = {"85"}


def _out(path: Path, **fields: Any) -> dict[str, Any]:
    return {"settings_path": str(path), **fields}


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.vres-tmp")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _read(path: Path) -> tuple[dict[str, Any] | None, bool]:
    if not path.exists():
        return {}, False
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    try:
        value = json.loads((raw[3:] if bom else raw).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, bom
    return (value, bom) if isinstance(value, dict) else (None, bom)


def _write(path: Path, value: dict[str, Any], *, bom: bool) -> None:
    raw = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    _atomic_write(path, (b"\xef\xbb\xbf" + raw) if bom else raw)


def _env(settings: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    value = settings.get("env")
    if value is None:
        return {}, None
    if not isinstance(value, dict):
        return None, "existing-nondict-env-preserved"
    return dict(value), None


def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _persistent_conflict(settings: dict[str, Any], env: dict[str, Any]) -> str | None:
    window = settings.get("autoCompactWindow")
    if window not in (None, "", "auto") or env.get(AUTO_COMPACT_WINDOW_KEY) not in (None, ""):
        return "existing-custom-auto-compact-window-preserved"
    if settings.get("autoCompactEnabled") is False or any(
        _truthy(env.get(key)) for key in DISABLE_KEYS
    ):
        return "existing-auto-compact-disable-preserved"
    return None


def _process_conflict() -> str | None:
    if os.environ.get(AUTO_COMPACT_WINDOW_KEY):
        return "process-auto-compact-window-present"
    if any(_truthy(os.environ.get(key)) for key in DISABLE_KEYS):
        return "process-auto-compact-disable-present"
    return None


def _save_env(path: Path, settings: dict[str, Any], env: dict[str, Any], *, bom: bool) -> None:
    if env:
        settings["env"] = env
    else:
        settings.pop("env", None)
    _write(path, settings, bom=bom)


def install_autocompact(claude_home: Path, *, owned_before: bool = False) -> dict[str, Any]:
    """Manage Claude native auto-compaction at 15% used (~85% free) of its auto-compact window."""
    path = claude_home.resolve() / "settings.json"
    settings, bom = _read(path)
    if settings is None:
        return _out(
            path,
            configured=False,
            owned=False,
            reason="invalid-settings-json-preserved",
        )

    env, env_error = _env(settings)
    if env is None:
        return _out(path, configured=False, owned=False, reason=env_error)

    existing = env.get(AUTO_COMPACT_KEY)
    persistent = _persistent_conflict(settings, env)
    transient = _process_conflict()

    if owned_before:
        if existing is None:
            return _out(
                path,
                configured=False,
                owned=False,
                reason="managed-autocompact-removed-externally",
            )
        existing_text = str(existing)
        managed_value = (
            existing_text == DESIRED_USED_PERCENT
            or existing_text in LEGACY_MANAGED_USED_PERCENTS
        )
        if not managed_value:
            return _out(
                path,
                configured=False,
                owned=False,
                reason="managed-autocompact-modified-externally",
            )
        if persistent:
            env.pop(AUTO_COMPACT_KEY, None)
            _save_env(path, settings, env, bom=bom)
            return _out(
                path,
                configured=False,
                owned=False,
                updated=True,
                reason=persistent,
            )
        migrated = existing_text != DESIRED_USED_PERCENT
        if migrated:
            env[AUTO_COMPACT_KEY] = DESIRED_USED_PERCENT
            _save_env(path, settings, env, bom=bom)
        result = _out(
            path,
            configured=True,
            owned=True,
            updated=migrated,
            used_percent=int(DESIRED_USED_PERCENT),
        )
        if transient:
            result["warning"] = transient
        return result

    if existing is not None:
        return _out(
            path,
            configured=False,
            owned=False,
            reason="existing-custom-autocompact-preserved",
        )

    conflict = persistent or transient
    if conflict:
        return _out(path, configured=False, owned=False, reason=conflict)

    env[AUTO_COMPACT_KEY] = DESIRED_USED_PERCENT
    _save_env(path, settings, env, bom=bom)
    return _out(
        path,
        configured=True,
        owned=True,
        updated=True,
        used_percent=int(DESIRED_USED_PERCENT),
    )


def remove_autocompact(claude_home: Path, *, owned: bool) -> dict[str, Any]:
    """Remove only a still-owned Vres 15%-used threshold."""
    path = claude_home.resolve() / "settings.json"
    if not owned:
        return _out(path, removed=False, reason="not-vres-owned")

    settings, bom = _read(path)
    if settings is None:
        return _out(path, removed=False, reason="invalid-settings-json-preserved")

    env, env_error = _env(settings)
    if env is None:
        return _out(path, removed=False, reason=env_error)

    existing = env.get(AUTO_COMPACT_KEY)
    if existing is None:
        return _out(path, removed=False, reason="managed-autocompact-already-absent")
    if str(existing) != DESIRED_USED_PERCENT:
        return _out(path, removed=False, reason="managed-autocompact-modified-externally")

    env.pop(AUTO_COMPACT_KEY, None)
    _save_env(path, settings, env, bom=bom)
    return _out(path, removed=True)


def _bool(value: str) -> bool:
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
    install.add_argument("--owned-before", type=_bool, default=False)
    remove = sub.add_parser("remove")
    remove.add_argument("--claude-home", required=True)
    remove.add_argument("--owned", type=_bool, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    result = (
        install_autocompact(Path(args.claude_home), owned_before=args.owned_before)
        if args.command == "install"
        else remove_autocompact(Path(args.claude_home), owned=args.owned)
    )
    sys.stdout.write(json.dumps(result, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
