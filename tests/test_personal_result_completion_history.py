"""Original #165 acceptance -> separately approved completion -> saved #176 source-prep.

Only disposable nonsensitive scratch fixtures. Historical caller claims are never
quality proof, host user authentication, Fable approval or eligible memory.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from vres_os import personal_portable_desk as desk_owner
from vres_os import personal_task_lifecycle as lifecycle
from vres_os import personal_work_result as result_owner
from vres_os import personal_work_completion as completion
from vres_os import personal_work_session as session
from vres_os import personal_result_acceptance as acceptance
from vres_os import personal_desk_cli as cli


def _scratch(tmp_path, statuses=("CLAIMED_MET", "CLAIMED_MET")):
    d = tmp_path / "Vres-Desk-Completion-Review"
    d.mkdir()
    project = tmp_path / "OrdinaryProject"
    project.mkdir()
    note = tmp_path / "note.md"
    note.write_text("# Task\n\n## Next action\n- Write a local report.\n", encoding="utf-8")
    task = "TASK-REPORT-COMPLETION"
    desk_owner.add_task(d, task, note, approved=True)
    report = project / "report.md"
    report.write_text("# Nonsensitive synthetic report\nDone.\n", encoding="utf-8")
    ctx = (d, task, project, "project:" + "a" * 24, report)
    checkpoint = result_owner.inspect_work_result(*ctx)["checkpoint_sha256"]
    proposed = session.propose_chairman_turn(d)
    active = next(x for x in proposed["choices"] if x["kind"] == "ACTIVE_TASK")
    choice = session.select_chairman_turn(
        d, task=task, proposal_sha256=proposed["proposal_sha256"],
        selected_note_sha256=active["selected_note_sha256"], approved=True,
        project_root=project, project_key=ctx[3], result_file=report,
        expected_checkpoint_sha256=checkpoint)
    continuity = choice["selected_task_result_continuity"]
    data = {
        "schema": acceptance.SCHEMA,
        "selected_task_key": task,
        "selected_note_sha256": continuity["selected_note_sha256"],
        "selected_project_binding_sha256": continuity["selected_project_binding_sha256"],
        "selected_result_sha256": continuity["selected_result_sha256"],
        "selected_result_checkpoint_sha256": continuity["selected_result_checkpoint_sha256"],
        "selected_continuity_receipt_sha256": continuity["continuity_receipt_sha256"],
        "criteria": [{
            "id": f"C{i:02d}",
            "criterion": f"SECRET-CHECK-{i} operator-only detail should never be echoed",
            "status": state,
            "evidence_sha256": "1" * 64 if state == "CLAIMED_MET" else None,
        } for i, state in enumerate(statuses, 1)],
    }
    raw = json.dumps(data, sort_keys=True).encode("utf-8")
    opts = {
        "expected_checkpoint_sha256": checkpoint,
        "approved": True,
        "include_result_acceptance_evidence": True,
        "acceptance_evidence_document": raw,
        "expected_acceptance_evidence_sha256": hashlib.sha256(raw).hexdigest(),
        "expected_chairman_turn_proposal_sha256": proposed["proposal_sha256"],
        "expected_selected_note_sha256": active["selected_note_sha256"],
    }
    return ctx, opts, data


def _saved(ctx):
    rows = lifecycle.list_history(ctx[0])["snapshots"]
    assert len(rows) == 1
    return rows[0]["result_evidence"]


def test_explicit_separate_approval_required_even_when_all_claimed_met(tmp_path):
    ctx, opts, _ = _scratch(tmp_path)
    with pytest.raises(completion.WorkCompletionRefused):
        completion.finish_work(*ctx, **{**opts, "approved": False})
    assert lifecycle.list_history(ctx[0])["count"] == 0
    done = completion.finish_work(*ctx, **opts)
    assert done["status"] == "USER_CONFIRMED_SCRATCH_WORK_RESULT_COMPLETED"
    assert done["saved_acceptance_self_claims_linked"] is True
    assert done["acceptance_claims_independently_validated"] is False
    assert done["original_176_live_experience_eligible_or_promoted"] is False
    assert done["result_quality_validated"] is False
    saved = _saved(ctx)
    claims = saved["saved_acceptance_claims"]
    assert saved["schema"] == lifecycle._RESULT_LINK_ACCEPTANCE_SCHEMA
    assert claims["acceptance_claims_state"] == "ALL_SELF_CLAIMED_MET_NOT_VALIDATED"
    assert claims["claimed_met_count"] == 2
    assert claims["original_176_experience_eligible_or_reused"] is False
    assert claims["independent_quality_or_owner_authentication_proven"] is False
    assert "SECRET-CHECK" not in json.dumps(saved)
    assert str(ctx[2]) not in json.dumps(lifecycle.list_history(ctx[0]))


def test_unresolved_claims_hold_completion_until_extra_acknowledgement(tmp_path):
    ctx, opts, _ = _scratch(tmp_path, ("CLAIMED_MET", "CLAIMED_GAP", "UNREVIEWED"))
    with pytest.raises(completion.WorkCompletionRefused):
        completion.finish_work(*ctx, **opts)
    assert lifecycle.list_history(ctx[0])["count"] == 0
    done = completion.finish_work(*ctx, **{**opts, "accept_unresolved_claims": True})
    assert done["caller_explicitly_acknowledged_unresolved_claims"] is True
    claims = _saved(ctx)["saved_acceptance_claims"]
    assert claims["unresolved_criterion_ids"] == ["C02", "C03"]
    assert claims["acceptance_claims_state"] == "CLAIMED_GAPS_OR_UNREVIEWED_CRITERIA"
    assert claims["original_176_episode_captured"] is False


def test_saved_replay_shows_redacted_claims_but_not_memory_eligibility(tmp_path):
    ctx, opts, _ = _scratch(tmp_path)
    done = completion.finish_work(*ctx, **opts)
    home = session.review_workday(ctx[0])
    saved = next(i for i in home["saved_history"] if i["state"] == "completed")
    assert saved["saved_acceptance_self_claims_linked"] is True
    assert saved["saved_acceptance_claims_state"] == "ALL_SELF_CLAIMED_MET_NOT_VALIDATED"
    note_sha = done["selected_note_sha256"]
    assert session.reopen_saved(ctx[0], ctx[1], note_sha, approved=True)["status"] == (
        "SAVED_WORK_SESSION_TASK_REOPENED")
    replay = session.replay_saved(ctx[0], ctx[1], note_sha, approved=True,
                                  include_experience_provenance=True)
    assert replay["status"] == "SAVED_WORK_SESSION_EXACT_CONTEXT_REPLAY_MATCH"
    claims = replay["selected_saved_acceptance_claims"]
    assert claims["saved_claims_receipt_sha256"] == done[
        "saved_acceptance_claims_receipt_sha256"]
    assert replay["selected_experience_provenance"]["experience_episode_created"] is False
    assert replay["selected_experience_provenance"][
        "original_176_live_trust_scope_revocation_checked"] is False
    assert replay["saved_claims_do_not_validate_quality_or_consent"] is True
    assert "SECRET-CHECK" not in json.dumps(replay)
    assert str(ctx[2]) not in json.dumps(replay)


def test_stale_result_or_stale_chairman_proposal_refuses_before_move(tmp_path):
    ctx, opts, _ = _scratch(tmp_path)
    with pytest.raises(completion.WorkCompletionRefused):
        completion.finish_work(*ctx, **{**opts, "expected_chairman_turn_proposal_sha256": "0" * 64})
    assert lifecycle.list_history(ctx[0])["count"] == 0
    ctx[4].write_text("# Changed while selected\n", encoding="utf-8")
    with pytest.raises(completion.WorkCompletionRefused):
        completion.finish_work(*ctx, **opts)
    assert lifecycle.list_history(ctx[0])["count"] == 0


def test_extra_authority_in_fixture_is_not_promoted(tmp_path):
    ctx, opts, data = _scratch(tmp_path)
    data["independent_approval"] = True
    raw = json.dumps(data).encode("utf-8")
    with pytest.raises(completion.WorkCompletionRefused):
        completion.finish_work(*ctx, **{
            **opts, "acceptance_evidence_document": raw,
            "expected_acceptance_evidence_sha256": hashlib.sha256(raw).hexdigest(),
        })
    assert lifecycle.list_history(ctx[0])["count"] == 0


def test_partial_opt_in_and_gap_override_without_review_refused(tmp_path):
    ctx, opts, _ = _scratch(tmp_path)
    with pytest.raises(completion.WorkCompletionRefused):
        completion.finish_work(*ctx, expected_checkpoint_sha256=opts["expected_checkpoint_sha256"],
                               approved=True, accept_unresolved_claims=True)
    with pytest.raises(completion.WorkCompletionRefused):
        completion.finish_work(*ctx, **{**opts,
            "include_result_acceptance_evidence": False})
    with pytest.raises(completion.WorkCompletionRefused):
        completion.finish_work(*ctx, **{**opts,
            "expected_selected_note_sha256": "0" * 64})
    assert lifecycle.list_history(ctx[0])["count"] == 0


def test_saved_sidecar_count_and_receipt_tampering_fail_closed(tmp_path):
    ctx, opts, _ = _scratch(tmp_path)
    completion.finish_work(*ctx, **opts)
    links = list((ctx[0] / lifecycle._HISTORY / "completed").glob("Vres-Result-H*.json"))
    assert len(links) == 1
    obj = json.loads(links[0].read_text())
    obj["acceptance_claims"]["claimed_met_count"] = 1
    links[0].write_text(json.dumps(obj, separators=(",", ":"), sort_keys=True) + "\n")
    with pytest.raises(lifecycle.LifecycleRefused):
        lifecycle.list_history(ctx[0])
    with pytest.raises((session.WorkSessionRefused, lifecycle.LifecycleRefused)):
        session.review_workday(ctx[0])


def test_historical_helper_refuses_fake_memory_authority(tmp_path):
    ctx, opts, _ = _scratch(tmp_path)
    continuity = session.select_chairman_turn(
        ctx[0], proposal_sha256=opts["expected_chairman_turn_proposal_sha256"],
        task=ctx[1], selected_note_sha256=opts["expected_selected_note_sha256"],
        approved=True, project_root=ctx[2], project_key=ctx[3],
        result_file=ctx[4], expected_checkpoint_sha256=opts["expected_checkpoint_sha256"],
        include_result_acceptance_evidence=True,
        acceptance_evidence_document=opts["acceptance_evidence_document"],
        expected_acceptance_evidence_sha256=opts["expected_acceptance_evidence_sha256"])
    frozen = acceptance.freeze_saved_acceptance_claims(
        continuity=continuity["selected_task_result_continuity"],
        review=continuity["selected_result_acceptance_evidence"])
    base = dict(task=ctx[1], note_sha256=frozen["selected_note_sha256"],
                project_binding_sha256=frozen["selected_project_binding_sha256"],
                result_sha256=frozen["selected_result_sha256"],
                checkpoint_sha256=frozen["selected_result_checkpoint_sha256"])
    acceptance.validate_saved_acceptance_claims(frozen, **base)
    for field, value in (("experience_reuse_eligible", True),
                         ("criteria_count", 200),
                         ("saved_claims_receipt_sha256", "0" * 64)):
        bad = {**frozen, field: value}
        with pytest.raises(acceptance.ResultAcceptanceRefused):
            acceptance.validate_saved_acceptance_claims(bad, **base)


def test_legacy_completion_contract_unchanged(tmp_path):
    ctx, opts, _ = _scratch(tmp_path)
    done = completion.finish_work(*ctx,
          expected_checkpoint_sha256=opts["expected_checkpoint_sha256"], approved=True)
    assert done["saved_acceptance_self_claims_linked"] is False
    assert _saved(ctx)["schema"] == lifecycle._RESULT_LINK_SCHEMA
    assert _saved(ctx).get("saved_acceptance_claims") is None


def test_existing_cli_finish_requires_exact_desk_fixture_and_owner_flags(tmp_path, capsys):
    ctx, opts, _ = _scratch(tmp_path)
    fixture = ctx[0] / "result-acceptance-evidence.json"
    fixture.write_bytes(opts["acceptance_evidence_document"])
    cmd = ["work-session", "finish", "--desk", str(ctx[0]), "--task-key", ctx[1],
           "--project-root", str(ctx[2]), "--project-key", ctx[3],
           "--result-file", str(ctx[4]), "--expected-checkpoint-sha256",
           opts["expected_checkpoint_sha256"], "--yes",
           "--include-result-acceptance-evidence",
           "--result-acceptance-evidence-file", str(fixture),
           "--expected-result-acceptance-evidence-sha256",
           opts["expected_acceptance_evidence_sha256"],
           "--expected-chairman-turn-proposal-sha256",
           opts["expected_chairman_turn_proposal_sha256"],
           "--expected-selected-note-sha256", opts["expected_selected_note_sha256"]]
    assert cli.main(cmd) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["saved_acceptance_self_claims_linked"] is True
    assert str(ctx[2]) not in json.dumps(output)
    assert "SECRET-CHECK" not in json.dumps(output)


def test_two_stage_completion_without_checklist_reuses_history(tmp_path):
    ctx, opts, _ = _scratch(tmp_path)
    decision = session.prepare_completion_decision(
        *ctx, expected_checkpoint_sha256=opts["expected_checkpoint_sha256"])
    assert decision["status"] == "READ_ONLY_EXACT_PERSONAL_COMPLETION_DECISION"
    assert decision["acceptance_claims_state"] == "NO_CHECKLIST_REVIEWED"
    assert decision["task_completion_approved_or_performed"] is False
    assert decision["original_176_episode_or_reuse_eligible"] is False
    assert lifecycle.list_history(ctx[0])["count"] == 0
    done = session.finish_reviewed_decision(
        *ctx, expected_checkpoint_sha256=opts["expected_checkpoint_sha256"],
        expected_decision_sha256=decision["decision_sha256"], approved=True)
    assert done["status"] == "SEPARATELY_APPROVED_PERSONAL_RESULT_SAVED_IN_ORIGINAL_HISTORY"
    assert done["saved_acceptance_self_claims_linked"] is False
    assert done["saved_snapshot_sha256"] == decision["selected_note_sha256"]
    assert _saved(ctx)["schema"] == lifecycle._RESULT_LINK_SCHEMA
    assert done["explicit_reopen_then_replay_required"] is True


def test_reviewed_completion_requires_separate_approval_and_exact_token(tmp_path):
    ctx, opts, _ = _scratch(tmp_path)
    preview = session.prepare_completion_decision(
        *ctx, expected_checkpoint_sha256=opts["expected_checkpoint_sha256"])
    for variations in ({"approved": False},
                       {"approved": True, "expected_decision_sha256": "0" * 64},
                       {"approved": True, "accept_unresolved_claims": True}):
        values = {
            "expected_checkpoint_sha256": opts["expected_checkpoint_sha256"],
            "expected_decision_sha256": preview["decision_sha256"], **variations}
        with pytest.raises(session.WorkSessionRefused):
            session.finish_reviewed_decision(*ctx, **values)
    assert lifecycle.list_history(ctx[0])["count"] == 0


def test_decision_with_self_claims_is_redacted_and_saved_original_v3(tmp_path):
    ctx, opts, _ = _scratch(tmp_path)
    inp = {
        "include_result_acceptance_evidence": True,
        "acceptance_evidence_document": opts["acceptance_evidence_document"],
        "expected_acceptance_evidence_sha256": opts["expected_acceptance_evidence_sha256"],
    }
    preview = session.prepare_completion_decision(
        *ctx, expected_checkpoint_sha256=opts["expected_checkpoint_sha256"], **inp)
    assert preview["acceptance_claims_state"] == "ALL_SELF_CLAIMED_MET_NOT_VALIDATED"
    assert preview["extra_known_gap_acknowledgement_required"] is False
    assert preview["claimed_met_count"] == 2
    assert "SECRET-CHECK" not in json.dumps(preview)
    assert str(ctx[2]) not in json.dumps(preview)
    done = session.finish_reviewed_decision(
        *ctx, expected_checkpoint_sha256=opts["expected_checkpoint_sha256"],
        expected_decision_sha256=preview["decision_sha256"], approved=True, **inp)
    assert done["saved_acceptance_self_claims_linked"] is True
    assert _saved(ctx)["schema"] == lifecycle._RESULT_LINK_ACCEPTANCE_SCHEMA
    home = session.render_workday(session.review_workday(ctx[0]))
    assert "ALL_SELF_CLAIMED_MET_NOT_VALIDATED" in home
    assert "NOT quality validation" in home
    assert "SECRET-CHECK" not in home
    assert str(ctx[2]) not in home
    reopened = session.reopen_saved(ctx[0], ctx[1], done["saved_snapshot_sha256"], approved=True)
    assert reopened["result_replayed"] is False
    replay = session.replay_saved(
        ctx[0], ctx[1], done["saved_snapshot_sha256"], approved=True,
        include_experience_provenance=True)
    assert replay["selected_experience_provenance"]["experience_episode_created"] is False
    assert replay["selected_saved_acceptance_claims"]["historical_caller_self_claims_only"] is True


def test_decision_with_known_gaps_requires_additional_explicit_ack(tmp_path):
    ctx, opts, _ = _scratch(tmp_path, ("CLAIMED_MET", "CLAIMED_GAP", "UNREVIEWED"))
    inp = {
        "include_result_acceptance_evidence": True,
        "acceptance_evidence_document": opts["acceptance_evidence_document"],
        "expected_acceptance_evidence_sha256": opts["expected_acceptance_evidence_sha256"],
    }
    preview = session.prepare_completion_decision(
        *ctx, expected_checkpoint_sha256=opts["expected_checkpoint_sha256"], **inp)
    assert preview["unresolved_criterion_ids"] == ["C02", "C03"]
    assert preview["extra_known_gap_acknowledgement_required"] is True
    values = {"expected_checkpoint_sha256": opts["expected_checkpoint_sha256"],
              "expected_decision_sha256": preview["decision_sha256"], "approved": True, **inp}
    with pytest.raises(session.WorkSessionRefused):
        session.finish_reviewed_decision(*ctx, **values)
    assert lifecycle.list_history(ctx[0])["count"] == 0
    done = session.finish_reviewed_decision(*ctx, **values,
                                            accept_unresolved_claims=True)
    assert done["caller_acknowledged_known_gaps"] is True
    assert _saved(ctx)["saved_acceptance_claims"]["unresolved_criterion_ids"] == ["C02", "C03"]
    assert done["original_176_live_episode_or_reuse_eligible"] is False


def test_decision_stale_result_or_changed_self_claims_refuses_before_move(tmp_path):
    ctx, opts, _ = _scratch(tmp_path)
    kwargs = {
        "include_result_acceptance_evidence": True,
        "acceptance_evidence_document": opts["acceptance_evidence_document"],
        "expected_acceptance_evidence_sha256": opts["expected_acceptance_evidence_sha256"],
    }
    preview = session.prepare_completion_decision(
        *ctx, expected_checkpoint_sha256=opts["expected_checkpoint_sha256"], **kwargs)
    bad = {**kwargs, "acceptance_evidence_document": b"{}"}
    with pytest.raises(session.WorkSessionRefused):
        session.finish_reviewed_decision(
            *ctx, expected_checkpoint_sha256=opts["expected_checkpoint_sha256"],
            expected_decision_sha256=preview["decision_sha256"], approved=True, **bad)
    ctx[4].write_text("# Changed after exact preview\n", encoding="utf-8")
    with pytest.raises((session.WorkSessionRefused, result_owner.WorkResultRefused)):
        session.finish_reviewed_decision(
            *ctx, expected_checkpoint_sha256=opts["expected_checkpoint_sha256"],
            expected_decision_sha256=preview["decision_sha256"], approved=True, **kwargs)
    assert lifecycle.list_history(ctx[0])["count"] == 0


def test_decision_no_implicit_selected_checklist_or_hidden_authority(tmp_path):
    ctx, opts, data = _scratch(tmp_path)
    with pytest.raises(session.WorkSessionRefused):
        session.prepare_completion_decision(
            *ctx, expected_checkpoint_sha256=opts["expected_checkpoint_sha256"],
            acceptance_evidence_document=opts["acceptance_evidence_document"])
    data["independent_fable_approval"] = True
    forged = json.dumps(data, sort_keys=True).encode("utf-8")
    with pytest.raises(session.WorkSessionRefused):
        session.prepare_completion_decision(
            *ctx, expected_checkpoint_sha256=opts["expected_checkpoint_sha256"],
            include_result_acceptance_evidence=True,
            acceptance_evidence_document=forged,
            expected_acceptance_evidence_sha256=hashlib.sha256(forged).hexdigest())
    assert lifecycle.list_history(ctx[0])["count"] == 0


def test_original_desk_cli_two_explicit_completion_commands(tmp_path, capsys):
    ctx, opts, _ = _scratch(tmp_path)
    args = ["--desk", str(ctx[0]), "--task-key", ctx[1],
            "--project-root", str(ctx[2]), "--project-key", ctx[3],
            "--result-file", str(ctx[4]), "--expected-checkpoint-sha256",
            opts["expected_checkpoint_sha256"]]
    assert cli.main(["work-session", "decision", *args]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview["writes_performed"] is False
    assert cli.main(["work-session", "decide", *args,
                     "--expected-decision-sha256", preview["decision_sha256"]]) == 2
    capsys.readouterr()
    assert lifecycle.list_history(ctx[0])["count"] == 0
    assert cli.main(["work-session", "decide", *args, "--yes",
                     "--expected-decision-sha256", preview["decision_sha256"]]) == 0
    done = json.loads(capsys.readouterr().out)
    assert done["saved_snapshot_sha256"] == preview["selected_note_sha256"]
    assert done["original_176_live_episode_or_reuse_eligible"] is False



def test_one_task_briefing_uses_original_workday_decision_no_mutation(tmp_path):
    ctx, opts, _ = _scratch(tmp_path)
    before = lifecycle.list_history(ctx[0])
    brief = session.prepare_completion_briefing(
        *ctx, expected_checkpoint_sha256=opts["expected_checkpoint_sha256"])
    preview = session.prepare_completion_decision(
        *ctx, expected_checkpoint_sha256=opts["expected_checkpoint_sha256"])
    assert brief["status"] == "READ_ONLY_ONE_TASK_COMPLETION_BRIEFING"
    assert brief["decision_sha256"] == preview["decision_sha256"]
    assert brief["current_result_sha256"] == preview["result_sha256"]
    assert brief["selected_project_binding_sha256"] == preview["project_binding_sha256"]
    assert brief["historical_completed_snapshots_for_selected_task"] == 0
    assert brief["selected_next_action_untrusted"] is None
    assert brief["task_completion_approved_or_performed"] is False
    assert brief["original_176_live_episode_or_reuse_eligible"] is False
    assert brief["writes_performed"] is False
    assert lifecycle.list_history(ctx[0]) == before
    rendered = session.render_completion_briefing(brief)
    assert "READ ONLY" in rendered and "DIFFERENT explicit" in rendered
    assert str(ctx[2]) not in rendered


def test_one_task_briefing_redacts_gaps_and_requires_separate_ack(tmp_path):
    ctx, opts, _ = _scratch(tmp_path, statuses=("CLAIMED_GAP", "UNREVIEWED"))
    brief = session.prepare_completion_briefing(
        *ctx, expected_checkpoint_sha256=opts["expected_checkpoint_sha256"],
        include_result_acceptance_evidence=True,
        acceptance_evidence_document=opts["acceptance_evidence_document"],
        expected_acceptance_evidence_sha256=opts["expected_acceptance_evidence_sha256"])
    rendered = session.render_completion_briefing(brief)
    assert brief["extra_known_gap_acknowledgement_required"] is True
    assert brief["unresolved_criterion_ids"] == ["C01", "C02"]
    assert "known-gap acknowledgement required" in rendered
    assert "SECRET-CHECK" not in rendered
    assert "SECRET-CHECK" not in json.dumps(brief)
    assert str(ctx[2]) not in json.dumps(brief)
    assert lifecycle.list_history(ctx[0])["count"] == 0


def test_one_task_briefing_stale_result_refuses_before_history_move(tmp_path):
    ctx, opts, _ = _scratch(tmp_path)
    ctx[4].write_text("Changed result since the checkpoint", encoding="utf-8")
    with pytest.raises((session.WorkSessionRefused, ValueError)):
        session.prepare_completion_briefing(
            *ctx, expected_checkpoint_sha256=opts["expected_checkpoint_sha256"])
    assert lifecycle.list_history(ctx[0])["count"] == 0


def test_one_task_briefing_original_cli_text_json_and_action_optin(tmp_path, capsys):
    ctx, opts, _ = _scratch(tmp_path)
    args = ["--desk", str(ctx[0]), "--task-key", ctx[1],
            "--project-root", str(ctx[2]), "--project-key", ctx[3],
            "--result-file", str(ctx[4]), "--expected-checkpoint-sha256",
            opts["expected_checkpoint_sha256"]]
    assert cli.main(["work-session", "briefing", *args]) == 0
    hidden = capsys.readouterr().out
    assert "PERSONAL COMPLETION BRIEFING" in hidden
    assert "Task action hidden" in hidden
    assert str(ctx[2]) not in hidden
    assert cli.main(["work-session", "briefing", *args, "--format", "json"]) == 0
    packet = json.loads(capsys.readouterr().out)
    assert packet["decision_sha256"] and packet["writes_performed"] is False
    assert packet["selected_next_action_untrusted"] is None
    assert cli.main(["work-session", "briefing", *args, "--show-selected-action"]) == 0
    shown = capsys.readouterr().out
    assert "UNTRUSTED TASK ACTION" in shown
    assert "Write a local report" in shown
    assert lifecycle.list_history(ctx[0])["count"] == 0
