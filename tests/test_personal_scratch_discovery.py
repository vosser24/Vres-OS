"""One focused bounded real-directory discovery test with author-only parent stand-ins.

The published full Windows integration must use the actual pinned workbench and
personal_daily_focus parent modules; these stubs are NOT source acceptance.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from vres_os import personal_scratch_discovery as discovery


def write_draft(parent: Path, task: str, label: str, action: str) -> tuple[str, str, Path]:
    folder = parent / f"Vres-Workbench-{label}"
    notes = folder / "notes"
    notes.mkdir(parents=True)
    raw = ("# My task\n\n## Next action\n- " + action + "\n").encode("utf-8")
    (notes / "next-step.md").write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    (folder / "draft-receipt.json").write_text(json.dumps({"task_key_claimed":task,"sha256":digest}),encoding="utf-8")
    return task,digest,folder


@pytest.fixture
def pair(tmp_path):
    parent = tmp_path / "Vres-Desk-MyDay"
    parent.mkdir()
    a = write_draft(parent,"TASK-WORK-A","A","Read the first document.")
    b = write_draft(parent,"TASK-WORK-B","B","Review the second task.")
    unrelated = parent / "README-unrelated.txt"
    unrelated.write_bytes(b"PRESERVE")
    return parent,a,b,unrelated


def test_daily_view_from_exact_parent_is_readonly_and_hidden(pair):
    parent,a,b,unrelated = pair
    before = [(x[2]/"notes"/"next-step.md").read_bytes() for x in (a,b)]
    report = discovery.daily_focus_from_scratch_parent(parent,"TASK-WORK-B")
    assert report["task_count"] == 2 and report["selected_task_key_claimed"] == "TASK-WORK-B"
    assert report["selected_action_disclosed"] is False and "selected_next_action" not in report
    assert report["writes_performed"] is False and unrelated.read_bytes() == b"PRESERVE"
    assert [(x[2]/"notes"/"next-step.md").read_bytes() for x in (a,b)] == before
    assert all(str(parent) not in str(x) for x in report["items"])


def test_explicitly_selected_action_only_when_opted_in(pair):
    parent,_,_,_ = pair
    report = discovery.daily_focus_from_scratch_parent(parent,"TASK-WORK-B",show_selected_action=True)
    assert report["selected_next_action"] == "Review the second task."
    assert "Read the first document." not in json.dumps(report)


def test_unknown_task_refused_no_auto_substitution(pair):
    parent,_,_,_ = pair
    with pytest.raises(ValueError): discovery.daily_focus_from_scratch_parent(parent,"TASK-MISSING",show_selected_action=True)


def test_duplicate_claimed_task_refused(pair):
    parent,_,_,_ = pair
    write_draft(parent,"TASK-WORK-B","C","Wrong duplicate task.")
    with pytest.raises(ValueError): discovery.daily_focus_from_scratch_parent(parent,"TASK-WORK-B")


def test_tampered_receipt_refuses_whole_view(pair):
    parent,a,_,_ = pair
    record=a[2]/"draft-receipt.json"
    record.write_text(json.dumps({"task_key_claimed":"TASK-WORK-A","sha256":"f"*64}))
    with pytest.raises(ValueError): discovery.daily_focus_from_scratch_parent(parent,"TASK-WORK-B")


def test_extra_file_in_unchosen_workspace_refuses(pair):
    parent,a,_,_ = pair
    (a[2]/"unexpected.txt").write_text("extra")
    with pytest.raises(ValueError): discovery.daily_focus_from_scratch_parent(parent,"TASK-WORK-B")


def test_symlinked_scratch_workspace_is_not_followed(pair):
    parent,_,_,_ = pair
    outside=parent.parent / "foreign"
    outside.mkdir()
    link=parent / "Vres-Workbench-malicious-link"
    try: link.symlink_to(outside, target_is_directory=True)
    except (PermissionError, OSError, NotImplementedError): pytest.skip("symlinks unavailable")
    with pytest.raises(ValueError): discovery.daily_focus_from_scratch_parent(parent,"TASK-WORK-B")
    assert list(outside.iterdir()) == []


def test_redirected_parent_refused(pair):
    parent,_,_,_ = pair
    link=parent.parent / "Vres-Desk-redirected"
    try: link.symlink_to(parent, target_is_directory=True)
    except (PermissionError, OSError, NotImplementedError): pytest.skip("symlinks unavailable")
    with pytest.raises(ValueError): discovery.daily_focus_from_scratch_parent(link,"TASK-WORK-B")


def test_scratch_prefix_special_file_refuses(pair):
    parent,_,_,_ = pair
    (parent / "Vres-Workbench-not-a-directory").write_text("unsafe")
    with pytest.raises(ValueError): discovery.daily_focus_from_scratch_parent(parent,"TASK-WORK-B")


def test_more_than_six_scratch_drafts_refuses(pair):
    parent,_,_,_ = pair
    for i in range(5): write_draft(parent,f"TASK-EXTRA-{i}",f"EXTRA{i}","Other draft.")
    with pytest.raises(discovery.ScratchDiscoveryRefused): discovery.daily_focus_from_scratch_parent(parent,"TASK-WORK-B")


def test_more_than_128_parent_entries_refuses(pair):
    parent,_,_,_ = pair
    for i in range(128): (parent / f"unrelated-{i:03d}").write_text("never read")
    with pytest.raises(discovery.ScratchDiscoveryRefused): discovery.daily_focus_from_scratch_parent(parent,"TASK-WORK-B")


@pytest.mark.parametrize("wrong",[".","../Vres-Desk-escape","Vres-Desk-relative", "", "\x00bad"])
def test_nonabsolute_or_ambiguous_parent_refused(wrong):
    with pytest.raises(discovery.ScratchDiscoveryRefused):
        discovery.daily_focus_from_scratch_parent(wrong,"TASK-WORK-B")


def test_no_scratch_drafts_is_not_a_pass(tmp_path):
    parent=tmp_path / "Vres-Desk-Empty"
    parent.mkdir()
    (parent / "unrelated.txt").write_text("do not open")
    with pytest.raises(discovery.ScratchDiscoveryRefused): discovery.daily_focus_from_scratch_parent(parent,"TASK-WORK-B")


def test_unrelated_symlink_name_never_read(pair):
    parent,_,_,_ = pair
    link=parent / "OTHER-PROJECT-LINK"
    try: link.symlink_to(parent.parent, target_is_directory=True)
    except (PermissionError, OSError, NotImplementedError): pytest.skip("symlinks unavailable")
    assert discovery.daily_focus_from_scratch_parent(parent,"TASK-WORK-B")["task_count"] == 2


def test_cli_standalone_new_python_process_with_no_action_echo(pair):
    parent,_,_,_ = pair
    cmd=[sys.executable,"-I","-S","-B",str(discovery.__file__),"--scratch-parent",str(parent),"--select","TASK-WORK-A","--format","json"]
    hidden=subprocess.run(cmd,capture_output=True,text=True,check=True)
    assert "selected_next_action" not in json.loads(hidden.stdout)
    assert not hidden.stderr
    shown=subprocess.run(cmd+["--show-selected-action"],capture_output=True,text=True,check=True)
    assert json.loads(shown.stdout)["selected_next_action"] == "Read the first document."
    wrong=subprocess.run(cmd[:-3]+["TASK-UNKNOWN","--format","json"],capture_output=True,text=True)
    assert wrong.returncode == 2 and not wrong.stdout
    assert "VRES_DESK_AUTOFOCUS_REFUSED" in wrong.stderr
    assert str(parent) not in wrong.stderr


def test_exact_desk_entrypoint_routes_real_discovery_in_new_process(pair):
    from vres_os import personal_desk_cli as desk
    parent,_,_,_ = pair
    help_result=subprocess.run([sys.executable,"-I","-S","-B",desk.__file__,"help"],capture_output=True,text=True,check=True)
    assert "today-here" in help_result.stdout
    command=[sys.executable,"-I","-S","-B",desk.__file__,"today-here","--scratch-parent",str(parent),"--select","TASK-WORK-B","--format","json"]
    hidden=subprocess.run(command,capture_output=True,text=True,check=True)
    assert json.loads(hidden.stdout)["task_count"] == 2
    shown=subprocess.run(command+["--show-selected-action"],capture_output=True,text=True,check=True)
    assert json.loads(shown.stdout)["selected_next_action"] == "Review the second task."
    assert "Read the first document." not in shown.stdout
