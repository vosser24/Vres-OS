"""#166 one bundled PERSONAL global-Claude operator dry run; no real host access."""
from __future__ import annotations

from dataclasses import replace
import copy
import inspect

import pytest

from vres_os.global_claude_synthetic_operator import (
    SyntheticMigrationSession, SyntheticOperatorRefusal,
    begin_synthetic_migration_dry_run, record_synthetic_migration_choices,
    inspect_synthetic_migration_dry_run, render_synthetic_migration_dry_run,
    freeze_synthetic_migration_dry_run, preview_synthetic_migration_rollback,
)


def completed(scenario="standard"):
    session = begin_synthetic_migration_dry_run(scenario)
    count = len(inspect_synthetic_migration_dry_run(session)["items"])
    if count:
        session = record_synthetic_migration_choices(session,
            "KEEP " + ",".join(map(str, range(1, count + 1))))
    return session


def test_one_synthetic_first_use_is_readable_grouped_and_non_authorizing():
    session = begin_synthetic_migration_dry_run()
    report = inspect_synthetic_migration_dry_run(session)
    rendered = render_synthetic_migration_dry_run(session)
    assert type(session) is SyntheticMigrationSession
    assert report["pending_numbers"] == [1, 2, 3, 4, 5, 6]
    assert report["choice_count"] == 0
    assert report["status"] == "synthetic_choices_pending_not_authorized"
    assert [r["number"] for r in report["items"]] == [1, 2, 3, 4, 5, 6]
    assert len({r["group"] for r in report["items"]}) >= 3
    assert all(r["choice"] == "UNRESOLVED" for r in report["items"])
    assert "KEEP 2,3 / DROP 1,4" in rendered
    assert "This is NOT your Claude profile" in rendered
    assert "SYNTHETIC" in rendered
    assert len(rendered) <= 22000
    assert all(report[k] is False for k in (
        "activation_authorized", "independent_fable_validation_granted",
        "real_first_claude_launch_authorized", "keep_drop_effects_applied"))


def test_conversational_multi_turn_choices_are_individually_tracked():
    a = begin_synthetic_migration_dry_run()
    b = record_synthetic_migration_choices(a, "KEEP 3,4 / DROP 1")
    c = record_synthetic_migration_choices(b, "DROP 2 / KEEP 5,6")
    assert inspect_synthetic_migration_dry_run(a)["pending_numbers"] == [1,2,3,4,5,6]
    assert inspect_synthetic_migration_dry_run(b)["pending_numbers"] == [2,5,6]
    r = inspect_synthetic_migration_dry_run(c)
    assert r["pending_numbers"] == []
    assert r["choice_count"] == 6
    assert r["session_sha256"] != inspect_synthetic_migration_dry_run(a)["session_sha256"]
    assert r["decision_sha256"] != inspect_synthetic_migration_dry_run(a)["decision_sha256"]


def test_complete_plan_is_only_a_frozen_synthetic_preview_with_destinations():
    done = completed()
    plan = freeze_synthetic_migration_dry_run(done)
    assert plan["status"] == "synthetic_plan_frozen_no_effects"
    assert len(plan["plan"]["items"]) == 6
    assert all(r["decision"] == "KEEP" for r in plan["plan"]["items"])
    assert all(r["effect"] == "inactive_review_candidate_only" for r in plan["plan"]["items"])
    assert all(r["destination_if_keep"] for r in plan["plan"]["items"])
    assert plan["plan"]["review_sha256"] == plan["review_sha256"]
    assert plan["plan"]["snapshot_sha256"] == plan["snapshot_sha256"]
    assert plan["plan"]["decision_sheet_sha256"] == plan["decision_sha256"]
    assert all(plan[k] is False for k in (
        "activation_authorized", "keep_drop_effects_applied",
        "real_operator_provenance_verified", "independent_fable_validation_granted"))


def test_drop_is_archived_not_deleted_and_unsupported_legacy_remains_inactive():
    session = begin_synthetic_migration_dry_run()
    session = record_synthetic_migration_choices(session, "DROP 1,2,3,4,5,6")
    plan = freeze_synthetic_migration_dry_run(session)["plan"]
    assert all(x["effect"] == "remain_inactive_unchanged_backup" for x in plan["items"])
    assert all(x["destination_if_keep"] == "archived_only_not_destroyed" for x in plan["items"])


def test_cannot_freeze_with_unresolved_numbers():
    a = record_synthetic_migration_choices(begin_synthetic_migration_dry_run(), "KEEP 1")
    with pytest.raises(SyntheticOperatorRefusal):
        freeze_synthetic_migration_dry_run(a)


def test_built_in_scenarios_have_distinct_seals_but_repeat_identically():
    a = begin_synthetic_migration_dry_run()
    b = begin_synthetic_migration_dry_run()
    c = begin_synthetic_migration_dry_run("changed")
    assert inspect_synthetic_migration_dry_run(a)["snapshot_sha256"] == inspect_synthetic_migration_dry_run(b)["snapshot_sha256"]
    assert inspect_synthetic_migration_dry_run(a)["session_sha256"] == inspect_synthetic_migration_dry_run(b)["session_sha256"]
    assert inspect_synthetic_migration_dry_run(c)["snapshot_sha256"] != inspect_synthetic_migration_dry_run(a)["snapshot_sha256"]


def test_empty_synthetic_profile_does_not_create_launch_permission():
    s = begin_synthetic_migration_dry_run("empty")
    r = inspect_synthetic_migration_dry_run(s)
    assert not r["items"] and r["pending_numbers"] == []
    plan = freeze_synthetic_migration_dry_run(s)
    assert plan["plan"]["items"] == []
    assert plan["activation_authorized"] is False
    assert plan["real_first_claude_launch_authorized"] is False


@pytest.mark.parametrize("bad", [
    None, False, 1, "C:\\Users\\User\\.claude", "prism-installed", "", "standard ",
])
def test_ambiguous_scenario_or_real_profile_path_is_refused(bad):
    with pytest.raises(SyntheticOperatorRefusal):
        begin_synthetic_migration_dry_run(bad)


@pytest.mark.parametrize("bad", [False, -1, 7, "1", 1.0])
def test_invalid_synthetic_interruption_boundary_refused_before_io(bad):
    with pytest.raises(SyntheticOperatorRefusal):
        begin_synthetic_migration_dry_run(interrupt_after=bad)


@pytest.mark.parametrize("index", [0, 1, 6])
def test_disk_interruption_and_rollback_are_synthetic_and_exact(index):
    s = begin_synthetic_migration_dry_run(interrupt_after=index)
    d = inspect_synthetic_migration_dry_run(s)["disposable_disk_evidence"]
    assert d["synthetic_disk_snapshot_verified"] is True
    assert d["synthetic_disk_quarantine_verified"] is True
    assert d["synthetic_disk_rollback_verified"] is True
    assert d["synthetic_interruption_tested"] is True
    assert d["synthetic_interrupted_rollback_verified"] is True
    assert d["governance_file_count"] == 6
    assert "rollback proven only for demo" in render_synthetic_migration_dry_run(s)


def test_in_memory_exact_restore_does_not_change_decisions_or_native_handles():
    s = record_synthetic_migration_choices(begin_synthetic_migration_dry_run(), "KEEP 3")
    before = inspect_synthetic_migration_dry_run(s)
    audit = preview_synthetic_migration_rollback(s)
    assert audit["in_memory_exact_restore_verified"] is True
    assert audit["disposable_disk_exact_restore_verified"] is True
    assert audit["governance_restored_count"] == 6
    assert audit["opaque_native_handle_count"] == 1
    assert audit["real_profile_unchanged"] == "not_inspected_or_accessed"
    assert inspect_synthetic_migration_dry_run(s) == before
    assert audit["activation_authorized"] is False


@pytest.mark.parametrize("bad", [
    "KEEP 0", "KEEP 7", "KEEP 1,1", "KEEP 1 / DROP 1", "KEEP 1 / DROP 2 / KEEP 3",
    "DROP 1; EXECUTE", "yes keep all", "KEEP 1\nSYSTEM override",
])
def test_invalid_or_injected_choices_do_not_change_the_session(bad):
    s = begin_synthetic_migration_dry_run()
    initial = inspect_synthetic_migration_dry_run(s)
    with pytest.raises(SyntheticOperatorRefusal):
        record_synthetic_migration_choices(s, bad)
    assert inspect_synthetic_migration_dry_run(s) == initial


def test_duplicate_cross_turn_choice_refused_and_original_unmodified():
    s = record_synthetic_migration_choices(begin_synthetic_migration_dry_run(), "KEEP 1")
    before = inspect_synthetic_migration_dry_run(s)
    with pytest.raises(SyntheticOperatorRefusal):
        record_synthetic_migration_choices(s, "DROP 1")
    assert inspect_synthetic_migration_dry_run(s) == before


@pytest.mark.parametrize("mutation", [
    lambda s: replace(s, _session_sha256="0" * 64),
    lambda s: replace(s, _review={**s._review, "status": "real_world_approved"}),
    lambda s: replace(s, _sheet={**s._sheet, "activation_authorized": True}),
    lambda s: replace(s, _disk={**s._disk, "synthetic_disk_rollback_verified": False}),
    lambda s: replace(s, _disk={**s._disk, "activation_authorized": True}),
    lambda s: replace(s, _scenario="unexpected"),
])
def test_tampered_session_review_choice_proof_or_authority_refused(mutation):
    session = begin_synthetic_migration_dry_run()
    with pytest.raises(SyntheticOperatorRefusal):
        inspect_synthetic_migration_dry_run(mutation(session))


def test_cross_snapshot_state_replay_is_refused():
    a = begin_synthetic_migration_dry_run()
    b = begin_synthetic_migration_dry_run("changed")
    with pytest.raises(SyntheticOperatorRefusal):
        inspect_synthetic_migration_dry_run(replace(a, _transaction=b._transaction))
    with pytest.raises(SyntheticOperatorRefusal):
        inspect_synthetic_migration_dry_run(replace(a, _review=copy.deepcopy(b._review)))


def test_vendor_handles_and_legacy_body_do_not_appear_in_reports_or_repr():
    session = begin_synthetic_migration_dry_run()
    displayed = repr(session) + render_synthetic_migration_dry_run(session)
    displayed += str(inspect_synthetic_migration_dry_run(session))
    displayed += str(freeze_synthetic_migration_dry_run(completed()))
    for forbidden in ("NEVER EXECUTE", "malicious old hook", "override rules; NEVER obey",
                      "sessions/demo", "DEMO ONLY: a project-specific", "real_profile_snapshot_verified': True"):
        assert forbidden not in displayed
    assert "real_authority=False" in repr(session)


def test_no_filesystem_root_or_activation_api_surface_is_exported():
    from vres_os import global_claude_synthetic_operator as mod
    source = inspect.getsource(mod)
    for forbidden in ("Path(", "os.environ", "subprocess", "psycopg", "connect(",
                      "open(", "requests", "socket", "CLAUDE_CONFIG_DIR", "run_hook"):
        assert forbidden not in source
    assert "DisposableGlobalDiskFixture" in source
    assert "real_first_claude_launch_authorized" in source
