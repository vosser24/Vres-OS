"""One integrated W2 disposable-first-use journey; not native Claude/DB UAT."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vres_os.project import ProjectIdentity
from vres_os import project_adoption
from vres_os.global_claude_synthetic_operator import (
    SyntheticOperatorRefusal,
    begin_synthetic_migration_dry_run,
    preview_synthetic_migration_rollback,
)
from vres_os.personal_w2_onboarding import (
    PersonalW2Refusal,
    freeze_personal_w2_synthetic_review,
    preview_personal_w2_onboarding,
    record_personal_w2_synthetic_choices,
    require_current_personal_w2_onboarding,
)


def _project(root: Path, key: str) -> ProjectIdentity:
    root.mkdir(parents=True, exist_ok=True)
    return ProjectIdentity(
        root=root.resolve(), key=key, name=root.name, remote_url=None, branch=None,
    )


def _files(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def _synthetic_operator(statement: str) -> dict:
    return {"kind": "test_operator", "confirmed": True, "statement": statement}


def test_one_integrated_w2_fresh_legacy_global_stale_and_exact_rollback(tmp_path):
    # Fresh one-file project: read-only preflight first, then existing #168
    # scaffold ONLY in a disposable tmp_path with a separate data root.
    fresh = _project(tmp_path / "fresh", "project:w2:fresh")
    (fresh.root / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
    original_fresh = _files(fresh.root)
    # A parent-traversal spelling must not be silently canonicalized.
    aliased = ProjectIdentity(
        root=fresh.root / ".." / fresh.root.name,
        key=fresh.key, name=fresh.name, remote_url=None, branch=None,
    )
    with pytest.raises(PersonalW2Refusal, match="unlinked"):
        preview_personal_w2_onboarding(aliased)
    # When the host permits creating a directory symlink, reject it too.
    linked_root = tmp_path / "linked-fresh"
    try:
        linked_root.symlink_to(fresh.root, target_is_directory=True)
    except (OSError, NotImplementedError):
        print("W2_ROOT_SYMLINK_CASE=NOT_RUN_HOST_CREATION_REFUSED")
    else:
        linked = ProjectIdentity(
            root=linked_root, key=fresh.key, name=fresh.name,
            remote_url=None, branch=None,
        )
        with pytest.raises(PersonalW2Refusal, match="unlinked"):
            preview_personal_w2_onboarding(linked)
        print("W2_ROOT_SYMLINK_CASE=PASS")
    fresh_report = preview_personal_w2_onboarding(fresh)
    assert fresh_report == require_current_personal_w2_onboarding(fresh, fresh_report)
    assert fresh_report["project_preview"]["preview_status"] == "FRESH_SCAFFOLD_CANDIDATE"
    assert fresh_report["actual_global_claude_profile"] == "NOT_READ_OR_INSPECTED"
    assert fresh_report["activation_authorized"] is False
    assert _files(fresh.root) == original_fresh
    fresh_state = tmp_path / "fresh-state"
    created = project_adoption.start(fresh, data_root=fresh_state)
    assert created["state"] == "active" and created["changed"] is True
    assert set(_files(fresh.root)) - set(original_fresh) == {"CLAUDE.md"}
    assert not (fresh.root / ".claude").exists()  # no fake agents/skills/hooks
    assert project_adoption.start(fresh, data_root=fresh_state)["changed"] is False
    with pytest.raises(PersonalW2Refusal, match="stale"):
        require_current_personal_w2_onboarding(fresh, fresh_report)

    # Established legacy: existing #168 inventory/snapshot and #174 hold.
    # A synthetic hostile hook is never invoked or accepted as KEEP.
    legacy = _project(tmp_path / "legacy", "project:w2:legacy")
    (legacy.root / "CLAUDE.md").write_text("# Historical notes only\n", encoding="utf-8")
    settings = legacy.root / ".claude" / "settings.json"
    settings.parent.mkdir()
    settings.write_text(json.dumps({"hooks": {"PreToolUse": [
        {"hooks": [{"command": "NEVER_EXECUTE_SYNTHETIC_HOOK"}]}
    ]}}), encoding="utf-8")
    src = legacy.root / "src" / "modules" / "orders"
    src.mkdir(parents=True)
    for n in ("a.py", "b.py", "c.py"):
        (src / n).write_text("raise RuntimeError('PROJECT_CODE_EXECUTED')\n", encoding="utf-8")
    (legacy.root / "pyproject.toml").write_text(
        "[project]\nname='synthetic-orders'\nversion='1.0'\n", encoding="utf-8",
    )
    original_legacy = _files(legacy.root)
    global_demo = begin_synthetic_migration_dry_run(interrupt_after=2)
    combined = preview_personal_w2_onboarding(
        legacy, synthetic_global_session=global_demo,
    )
    assert combined["project_preview"]["preview_status"] == "LEGACY_KEEP_DROP_REVIEW_REQUIRED"
    assert "ARCHITECTURE_ALIGNMENT_PLAN" in combined["project_preview"]["required_review_gates"]
    assert combined["project_preview"]["architecture_plan_required"] is True
    assert combined["synthetic_global_review"]["pending_numbers"] == [1, 2, 3, 4, 5, 6]
    assert combined["synthetic_global_review"]["disposable_disk_evidence"]["synthetic_interruption_tested"]
    assert all(combined[k] is False for k in (
        "activation_authorized", "real_claude_launch_authorized",
        "independent_fable_validation_granted", "project_write_permitted",
        "profile_write_permitted",
    ))
    assert _files(legacy.root) == original_legacy

    old = combined.copy()
    old["activation_authorized"] = True  # edited packet cannot grant authority
    with pytest.raises(PersonalW2Refusal):
        require_current_personal_w2_onboarding(
            legacy, old, synthetic_global_session=global_demo,
        )
    # Python's False == 0 must not let a modified packet pass equality.
    type_tampered = combined.copy()
    type_tampered["activation_authorized"] = 0
    with pytest.raises(PersonalW2Refusal, match="modified"):
        require_current_personal_w2_onboarding(
            legacy, type_tampered, synthetic_global_session=global_demo,
        )
    other = _project(tmp_path / "other", "project:w2:legacy")  # same key, different root
    with pytest.raises(PersonalW2Refusal):
        require_current_personal_w2_onboarding(
            other, combined, synthetic_global_session=global_demo,
        )

    # Real owner state/journal API is used only on disposable test inputs.
    legacy_state = tmp_path / "legacy-state"
    waiting = project_adoption.start(legacy, data_root=legacy_state)
    assert waiting["state"] == "awaiting_operator"
    assert waiting["architecture_review_required"] is True
    assert _files(legacy.root) == original_legacy
    items = project_adoption.status(legacy, data_root=legacy_state)["items"]
    executable = next(row for row in items if row["path"] == ".claude/settings.json")
    assert set(executable["options"]) == {"DROP"}
    with pytest.raises(project_adoption.AdoptionError):
        project_adoption.decide(legacy, executable["number"], "KEEP",
                                authority=_synthetic_operator, data_root=legacy_state)
    project_adoption.decide(legacy, executable["number"], "DROP",
                            authority=_synthetic_operator, data_root=legacy_state)

    # A rewritten Claude surface invalidates both the W2 preview and saved #168 decisions.
    settings.write_bytes(original_legacy[".claude/settings.json"] + b" \n")
    with pytest.raises(PersonalW2Refusal, match="stale"):
        require_current_personal_w2_onboarding(
            legacy, combined, synthetic_global_session=global_demo,
        )
    remaining = next(x for x in items if x["number"] != executable["number"])
    with pytest.raises(project_adoption.AdoptionError, match="changed since"):
        project_adoption.decide(legacy, remaining["number"], "KEEP",
                                authority=_synthetic_operator, data_root=legacy_state)
    settings.write_bytes(original_legacy[".claude/settings.json"])
    require_current_personal_w2_onboarding(
        legacy, combined, synthetic_global_session=global_demo,
    )
    for row in items:
        if row["number"] != executable["number"]:
            choice = "KEEP" if "KEEP" in row["options"] else "DROP"
            project_adoption.decide(legacy, row["number"], choice,
                                    authority=_synthetic_operator, data_root=legacy_state)
    assert project_adoption.status(legacy, data_root=legacy_state)["pending"] == []
    called = []
    with pytest.raises(project_adoption.AdoptionError, match="protected Fable/high"):
        project_adoption.activate(
            legacy, authority=lambda statement: called.append(statement), data_root=legacy_state,
        )
    assert not called
    assert _files(legacy.root) == original_legacy
    assert not list(legacy_state.rglob("journal.json"))

    # Global current-user Claude config is *not* inspected. Only an already
    # sealed built-in synthetic session receives individually numbered choices.
    with pytest.raises(SyntheticOperatorRefusal):
        freeze_personal_w2_synthetic_review(legacy, combined, global_demo)
    session, updated = record_personal_w2_synthetic_choices(
        legacy, combined, global_demo, "DROP 1,2 / KEEP 3",
    )
    with pytest.raises(PersonalW2Refusal):
        freeze_personal_w2_synthetic_review(legacy, combined, session)
    session, updated = record_personal_w2_synthetic_choices(
        legacy, updated, session, "DROP 4,5,6",
    )
    frozen = freeze_personal_w2_synthetic_review(legacy, updated, session)
    assert frozen["status"] == "SYNTHETIC_REVIEW_FROZEN_NO_ACTIVATION"
    assert frozen["activation_authorized"] is False
    assert frozen["project_architecture_gates"]
    assert all(row["effect"].startswith(("inactive_", "remain_inactive"))
               for row in frozen["synthetic_global_plan"]["plan"]["items"])
    restored = preview_synthetic_migration_rollback(session)
    assert restored["in_memory_exact_restore_verified"] is True
    assert restored["disposable_disk_exact_restore_verified"] is True
    assert _files(legacy.root) == original_legacy

    # Small legacy may exercise the EXISTING #168 exact rollback contract in
    # disposable-only test state. This is not permission on an actual project.
    small = _project(tmp_path / "small-legacy", "project:w2:small")
    (small.root / "CLAUDE.md").write_text("# Useful simple rule\n", encoding="utf-8")
    unsafe = small.root / ".claude" / "settings.json"
    unsafe.parent.mkdir()
    unsafe.write_text(json.dumps({"hooks": {"Stop": [{"command": "NEVER_RUN"}]}}),
                      encoding="utf-8")
    baseline = _files(small.root)
    small_state = tmp_path / "small-state"
    waiting = project_adoption.start(small, data_root=small_state)
    assert waiting["state"] == "awaiting_operator"
    assert waiting.get("architecture_review_required") is not True
    for row in project_adoption.status(small, data_root=small_state)["items"]:
        choice = "KEEP" if "KEEP" in row["options"] else "DROP"
        project_adoption.decide(small, row["number"], choice,
                                authority=_synthetic_operator, data_root=small_state)
    applied = project_adoption.activate(small, authority=_synthetic_operator,
                                        data_root=small_state)
    assert applied["state"] == "active"
    assert not unsafe.exists()
    recovered = project_adoption.rollback(small, authority=_synthetic_operator,
                                           data_root=small_state)
    assert recovered["state"] == "awaiting_operator"
    assert _files(small.root) == baseline
