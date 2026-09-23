"""Regression matrix for src/vres_os/codex_handoff.py (issue #143, Slice 1).

No MCP wiring, no real Codex execution, no migrations are exercised here.
Git fixtures are built with plain subprocess calls (mirroring the pattern in
tests/test_windows_node_mcp_git.py: no shell, stdin=DEVNULL, bounded timeout)
since fixture setup is not itself the code under test.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import subprocess
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_audit_regressions import ScriptedConnection

from vres_os import codex_handoff as ch
from vres_os.repository import ActiveTask

_GIT_IDENTITY = ["-c", "user.email=test@example.com", "-c", "user.name=Vres Test"]


def run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *_GIT_IDENTITY, "-C", str(cwd), *args],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )


def init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    run_git(path, "init")
    return path


def commit_all(path: Path, message: str) -> str:
    run_git(path, "add", "-A")
    run_git(path, "commit", "-m", message, "--allow-empty")
    return run_git(path, "rev-parse", "HEAD").stdout.strip()


def make_snapshot(
    head="abc123",
    clean=True,
    changed=frozenset(),
    ignored=frozenset(),
    ref="refdigest",
    shared_exists=True,
    shared_digest="shareddigest",
    wt_exists=False,
    wt_digest=None,
    index_digest="indexdigest",
) -> ch.GitSnapshot:
    return ch.GitSnapshot(
        head_sha=head,
        clean=clean,
        changed_paths=changed,
        ignored_paths=ignored,
        ref_digest=ref,
        shared_config=ch.FingerprintResult(exists=shared_exists, digest=shared_digest),
        worktree_config=ch.FingerprintResult(exists=wt_exists, digest=wt_digest),
        index_state_digest=index_digest,
    )


# ---------------------------------------------------------------------------
# 1. Write-scope normalization
# ---------------------------------------------------------------------------


class TestWriteScope:
    def test_rejects_empty_path(self):
        with pytest.raises(ch.WriteScopeError):
            ch.normalize_write_scope_path("")

    def test_rejects_absolute_path(self):
        with pytest.raises(ch.WriteScopeError):
            ch.normalize_write_scope_path("/etc/passwd")

    def test_rejects_drive_qualified_backslash_path(self):
        with pytest.raises(ch.WriteScopeError):
            ch.normalize_write_scope_path("C:\\Windows\\system32\\evil.dll")

    def test_rejects_drive_qualified_forward_slash_path(self):
        with pytest.raises(ch.WriteScopeError):
            ch.normalize_write_scope_path("C:/Windows/system32/evil.dll")

    def test_rejects_dotdot_segment(self):
        with pytest.raises(ch.WriteScopeError):
            ch.normalize_write_scope_path("src/../../../etc/passwd")

    def test_rejects_trailing_slash_directory_style(self):
        with pytest.raises(ch.WriteScopeError):
            ch.normalize_write_scope_path("src/vres_os/")

    def test_converts_backslashes_to_forward_slashes(self):
        assert (
            ch.normalize_write_scope_path("src\\vres_os\\codex_handoff.py")
            == "src/vres_os/codex_handoff.py"
        )

    def test_rejects_more_than_50_entries(self):
        entries = [f"file{i}.txt" for i in range(ch.MAX_WRITE_SCOPE_ENTRIES + 1)]
        with pytest.raises(ch.WriteScopeError):
            ch.build_write_scope(entries)

    def test_accepts_exactly_50_entries(self):
        entries = [f"file{i}.txt" for i in range(ch.MAX_WRITE_SCOPE_ENTRIES)]
        scope = ch.build_write_scope(entries)
        assert len(scope.entries) == ch.MAX_WRITE_SCOPE_ENTRIES

    def test_path_identity_is_platform_sensitive(self):
        if os.name == "nt":
            assert ch.path_identity("Foo.txt") == ch.path_identity("foo.txt")
        else:
            assert ch.path_identity("Foo.txt") != ch.path_identity("foo.txt")

    def test_duplicate_detection_uses_platform_identity(self):
        if os.name == "nt":
            with pytest.raises(ch.WriteScopeError):
                ch.build_write_scope(["Foo.txt", "foo.txt"])
        else:
            scope = ch.build_write_scope(["Foo.txt", "foo.txt"])
            assert set(scope.entries) == {"Foo.txt", "foo.txt"}

    def test_plain_duplicates_rejected(self):
        with pytest.raises(ch.WriteScopeError):
            ch.build_write_scope(["a.txt", "a.txt"])

    def test_required_changed_paths_must_be_subset(self):
        with pytest.raises(ch.WriteScopeError):
            ch.build_write_scope(["a.txt"], required_changed_paths=["b.txt"])

    def test_required_changed_paths_accepted_when_subset(self):
        scope = ch.build_write_scope(["a.txt", "b.txt"], required_changed_paths=["b.txt"])
        assert scope.required_changed_paths == ("b.txt",)


# ---------------------------------------------------------------------------
# 2. NUL-delimited git status parser
# ---------------------------------------------------------------------------


class TestGitStatusParsing:
    def test_tracked_modification_add_delete_untracked(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        (repo / "a.txt").write_text("one\n")
        (repo / "b.txt").write_text("two\n")
        commit_all(repo, "init")
        (repo / "a.txt").write_text("one modified\n")
        (repo / "b.txt").unlink()
        (repo / "c.txt").write_text("new\n")
        (repo / "d.txt").write_text("staged add\n")
        run_git(repo, "add", "d.txt")
        status = ch.get_git_status(repo)
        assert status.changed_paths == {"a.txt", "b.txt", "c.txt", "d.txt"}

    def test_staged_modification(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        (repo / "a.txt").write_text("one\n")
        commit_all(repo, "init")
        (repo / "a.txt").write_text("staged change\n")
        run_git(repo, "add", "a.txt")
        status = ch.get_git_status(repo)
        assert status.changed_paths == {"a.txt"}

    def test_rename_captures_both_old_and_new(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        (repo / "old.txt").write_text("content for rename detection padding\n" * 5)
        commit_all(repo, "init")
        run_git(repo, "mv", "old.txt", "new.txt")
        status = ch.get_git_status(repo)
        assert "old.txt" in status.changed_paths
        assert "new.txt" in status.changed_paths
        assert status.renames == (("old.txt", "new.txt"),)

    def test_spaces_and_unicode_filenames(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        name = "a file with spaces and \u00fc\u00f1\u00ee\u00e7\u00f8d\u00e9 \u540d\u524d.txt"
        (repo / name).write_text("hello\n", encoding="utf-8")
        status = ch.get_git_status(repo)
        assert name in status.changed_paths

    def test_clean_repo_has_no_changed_paths(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        commit_all(repo, "init")
        status = ch.get_git_status(repo)
        assert status.changed_paths == frozenset()

    def test_unknown_record_type_fails_closed(self):
        with pytest.raises(ch.GitStatusParseError):
            ch.parse_porcelain_v2_z("X something\x00")

    def test_malformed_ordinary_record_field_count_fails_closed(self):
        with pytest.raises(ch.GitStatusParseError):
            ch.parse_porcelain_v2_z("1 .M\x00")

    def test_rename_record_missing_orig_path_fails_closed(self):
        with pytest.raises(ch.GitStatusParseError):
            ch.parse_porcelain_v2_z(
                "2 R. N... 100644 100644 100644 abc123 def456 R100 new.txt\x00"
            )

    def test_malformed_untracked_record_fails_closed(self):
        with pytest.raises(ch.GitStatusParseError):
            ch.parse_porcelain_v2_z("?\x00")


# ---------------------------------------------------------------------------
# 3. Git snapshot + comparison helpers
# ---------------------------------------------------------------------------


class TestGitSnapshot:
    def test_clean_snapshot(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        commit_all(repo, "init")
        snap = ch.take_snapshot(repo)
        assert snap.clean
        assert snap.changed_paths == frozenset()
        assert len(snap.head_sha) == 40

    def test_dirty_detection(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        commit_all(repo, "init")
        (repo / "x.txt").write_text("dirty\n")
        snap = ch.take_snapshot(repo)
        assert not snap.clean
        assert "x.txt" in snap.changed_paths

    def test_head_mutation_detected(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        commit_all(repo, "init")
        before = ch.take_snapshot(repo)
        (repo / "y.txt").write_text("y\n")
        commit_all(repo, "second")
        after = ch.take_snapshot(repo)
        diff = ch.compare_snapshots(before, after)
        assert diff.head_changed
        assert diff.mutated

    def test_commit_leaving_status_clean_still_detected(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        commit_all(repo, "init")
        before = ch.take_snapshot(repo)
        (repo / "z.txt").write_text("z\n")
        commit_all(repo, "third")
        after = ch.take_snapshot(repo)
        assert after.clean
        diff = ch.compare_snapshots(before, after)
        assert diff.head_changed

    def test_branch_ref_mutation_detected(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        commit_all(repo, "init")
        before = ch.take_snapshot(repo)
        run_git(repo, "branch", "feature")
        after = ch.take_snapshot(repo)
        diff = ch.compare_snapshots(before, after)
        assert diff.ref_digest_changed
        assert not diff.head_changed

    def test_stash_ref_mutation_detected(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        commit_all(repo, "init")
        (repo / "s.txt").write_text("stash me\n")
        before = ch.take_snapshot(repo)
        run_git(repo, "stash", "push", "-u", "-m", "test stash")
        after = ch.take_snapshot(repo)
        diff = ch.compare_snapshots(before, after)
        assert diff.ref_digest_changed

    def test_shared_config_mutation_detected(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        commit_all(repo, "init")
        before = ch.take_snapshot(repo)
        run_git(repo, "config", "some.testkey", "testvalue")
        after = ch.take_snapshot(repo)
        diff = ch.compare_snapshots(before, after)
        assert diff.shared_config_changed

    def test_worktree_config_appearing_detected(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        commit_all(repo, "init")
        run_git(repo, "config", "extensions.worktreeConfig", "true")
        before = ch.take_snapshot(repo)
        assert not before.worktree_config.exists
        run_git(repo, "config", "--worktree", "some.key", "value")
        after = ch.take_snapshot(repo)
        assert after.worktree_config.exists
        diff = ch.compare_snapshots(before, after)
        assert diff.worktree_config_changed

    def test_worktree_config_content_mutation_detected(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        commit_all(repo, "init")
        run_git(repo, "config", "extensions.worktreeConfig", "true")
        run_git(repo, "config", "--worktree", "some.key", "value1")
        before = ch.take_snapshot(repo)
        run_git(repo, "config", "--worktree", "some.key", "value2")
        after = ch.take_snapshot(repo)
        diff = ch.compare_snapshots(before, after)
        assert diff.worktree_config_changed

    def test_worktree_config_disappearing_detected(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        commit_all(repo, "init")
        run_git(repo, "config", "extensions.worktreeConfig", "true")
        run_git(repo, "config", "--worktree", "some.key", "value")
        before = ch.take_snapshot(repo)
        assert before.worktree_config.exists
        git_dir_out = run_git(repo, "rev-parse", "--git-dir").stdout.strip()
        git_dir = Path(git_dir_out)
        if not git_dir.is_absolute():
            git_dir = repo / git_dir
        (git_dir / "config.worktree").unlink()
        after = ch.take_snapshot(repo)
        assert not after.worktree_config.exists
        diff = ch.compare_snapshots(before, after)
        assert diff.worktree_config_changed

    def test_worktree_starts_at_exact_requested_sha(self, tmp_path):
        source = init_repo(tmp_path / "source")
        sha = commit_all(source, "init")
        dest = tmp_path / "wt"
        snap = ch.create_detached_worktree(source, dest, sha)
        assert snap.head_sha == sha
        assert snap.clean

    def test_preexisting_destination_rejected(self, tmp_path):
        source = init_repo(tmp_path / "source")
        sha = commit_all(source, "init")
        dest = tmp_path / "wt"
        dest.mkdir()
        with pytest.raises(ch.WorktreeError):
            ch.create_detached_worktree(source, dest, sha)

    def test_source_not_a_working_tree_rejected(self, tmp_path):
        not_a_repo = tmp_path / "not_a_repo"
        not_a_repo.mkdir()
        with pytest.raises(ch.WorktreeError):
            ch.create_detached_worktree(not_a_repo, tmp_path / "wt2", "HEAD")

    def test_unresolvable_sha_rejected(self, tmp_path):
        source = init_repo(tmp_path / "source")
        commit_all(source, "init")
        with pytest.raises(ch.WorktreeError):
            ch.create_detached_worktree(source, tmp_path / "wt3", "deadbeef" * 5)


# ---------------------------------------------------------------------------
# project-config detection
# ---------------------------------------------------------------------------


class TestProjectConfigDetection:
    def test_no_config_is_supported(self, tmp_path):
        result = ch.check_codex_project_config(tmp_path)
        assert result.supported

    def test_config_present_is_rejected(self, tmp_path):
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        (codex_dir / "config.toml").write_text("[foo]\nbar = 1\n")
        result = ch.check_codex_project_config(tmp_path)
        assert not result.supported
        assert "config.toml" in result.reason


# ---------------------------------------------------------------------------
# Codex command construction
# ---------------------------------------------------------------------------


class TestCodexCommandBuilder:
    def test_exact_baseline_argv(self):
        argv = ch.build_codex_exec_argv("/usr/local/bin/codex")
        assert argv == [
            "/usr/local/bin/codex",
            "exec",
            "--ephemeral",
            "--json",
            "--sandbox",
            "workspace-write",
            "--ignore-user-config",
            "-",
        ]

    def test_no_prohibited_flags_ever_appear(self):
        argv = ch.build_codex_exec_argv("codex")
        argv_text = " ".join(argv)
        prohibited = [
            "--ask-for-approval",
            "-a",
            "danger-full-access",
            "--dangerously-bypass-approvals-and-sandbox",
            "--yolo",
            "--worktree",
            "--skip-git-repo-check",
            "--add-dir",
        ]
        for flag in prohibited:
            assert flag not in argv
            assert flag not in argv_text

    def test_no_prompt_or_project_text_in_argv(self):
        argv = ch.build_codex_exec_argv("codex")
        assert "prompt" not in " ".join(argv).lower()
        assert not any(os.sep in part for part in argv[1:])

    def test_requires_executable(self):
        with pytest.raises(ValueError):
            ch.build_codex_exec_argv("")


# ---------------------------------------------------------------------------
# 7. Structured JSONL parser
# ---------------------------------------------------------------------------


class TestJsonlParsing:
    def test_valid_single_event(self):
        result = ch.parse_codex_jsonl('{"type": "message", "text": "hi"}\n')
        assert result.ok
        assert len(result.events) == 1
        assert result.diagnostics == ()

    def test_valid_multiple_events(self):
        text = '{"a": 1}\n{"b": 2}\n{"c": 3}\n'
        result = ch.parse_codex_jsonl(text)
        assert result.ok
        assert len(result.events) == 3

    def test_malformed_line_fails(self):
        result = ch.parse_codex_jsonl("not json\n")
        assert not result.ok
        assert len(result.diagnostics) == 1
        assert result.diagnostics[0].error_type == "json_decode_error"
        assert result.diagnostics[0].line_index == 0

    def test_malformed_then_valid_still_fails_overall(self):
        text = 'not json\n{"ok": true}\n'
        result = ch.parse_codex_jsonl(text)
        assert not result.ok

    def test_secret_bearing_event_is_structurally_redacted(self):
        text = json.dumps({"event": "token_issued", "token": "sk-ant-abcdefghijklmnop"}) + "\n"
        result = ch.parse_codex_jsonl(text)
        assert result.ok
        assert result.events[0]["token"] == "[REDACTED]"

    def test_truncated_indicator_forces_fail(self):
        result = ch.parse_codex_jsonl('{"a": 1}\n', truncated=True)
        assert not result.ok
        assert result.truncated

    def test_event_count_bound_enforced(self):
        text = "\n".join(json.dumps({"i": i}) for i in range(ch.MAX_JSONL_EVENTS + 5)) + "\n"
        result = ch.parse_codex_jsonl(text)
        assert not result.ok
        assert any(d.error_type == "event_count_exceeded" for d in result.diagnostics)

    def test_empty_stream_never_reported_as_success(self):
        result = ch.parse_codex_jsonl("")
        assert not result.ok
        assert result.events == ()

    def test_diagnostics_never_carry_raw_line_content(self):
        secret_line = "this is not json but contains sk-ant-testsecrettoken123456"
        result = ch.parse_codex_jsonl(secret_line + "\n")
        assert not result.ok
        for diag in result.diagnostics:
            assert not hasattr(diag, "content")
            assert not hasattr(diag, "line")
            assert diag.length <= ch.MAX_DIAG_LINE_CHARS


# ---------------------------------------------------------------------------
# 8. Write-preflight verifier (simulated inputs only)
# ---------------------------------------------------------------------------


class TestPreflightVerifier:
    def _jsonl_ok(self):
        return ch.JsonlParseResult(
            ok=True, events=({"type": "done"},), diagnostics=(), truncated=False
        )

    def test_exit_zero_but_no_probe_file_created_fails(self, tmp_path):
        probe_file = tmp_path / "probe.txt"
        pre = make_snapshot()
        post = make_snapshot(changed=frozenset({"probe.txt"}))
        result = ch.verify_write_preflight(
            probe_path="probe.txt",
            nonce=b"nonce123",
            exit_code=0,
            jsonl_result=self._jsonl_ok(),
            pre_snapshot=pre,
            post_snapshot=post,
            actual_changed_paths=frozenset({"probe.txt"}),
            probe_file_path=probe_file,
        )
        assert not result.passed

    def test_probe_created_but_extra_unexpected_change_fails(self, tmp_path):
        probe_file = tmp_path / "probe.txt"
        probe_file.write_bytes(b"nonce123")
        pre = make_snapshot()
        post = make_snapshot(changed=frozenset({"probe.txt", "other.txt"}))
        result = ch.verify_write_preflight(
            probe_path="probe.txt",
            nonce=b"nonce123",
            exit_code=0,
            jsonl_result=self._jsonl_ok(),
            pre_snapshot=pre,
            post_snapshot=post,
            actual_changed_paths=frozenset({"probe.txt", "other.txt"}),
            probe_file_path=probe_file,
        )
        assert not result.passed

    def test_exact_probe_passes(self, tmp_path):
        probe_file = tmp_path / "probe.txt"
        probe_file.write_bytes(b"nonce123")
        pre = make_snapshot()
        post = make_snapshot(changed=frozenset({"probe.txt"}))
        result = ch.verify_write_preflight(
            probe_path="probe.txt",
            nonce=b"nonce123",
            exit_code=0,
            jsonl_result=self._jsonl_ok(),
            pre_snapshot=pre,
            post_snapshot=post,
            actual_changed_paths=frozenset({"probe.txt"}),
            probe_file_path=probe_file,
        )
        assert result.passed

    def test_nonzero_exit_code_fails(self, tmp_path):
        probe_file = tmp_path / "probe.txt"
        probe_file.write_bytes(b"nonce123")
        pre = make_snapshot()
        post = make_snapshot(changed=frozenset({"probe.txt"}))
        result = ch.verify_write_preflight(
            probe_path="probe.txt",
            nonce=b"nonce123",
            exit_code=1,
            jsonl_result=self._jsonl_ok(),
            pre_snapshot=pre,
            post_snapshot=post,
            actual_changed_paths=frozenset({"probe.txt"}),
            probe_file_path=probe_file,
        )
        assert not result.passed

    def test_malformed_jsonl_result_fails(self, tmp_path):
        probe_file = tmp_path / "probe.txt"
        probe_file.write_bytes(b"nonce123")
        pre = make_snapshot()
        post = make_snapshot(changed=frozenset({"probe.txt"}))
        bad_jsonl = ch.JsonlParseResult(ok=False, events=(), diagnostics=(), truncated=False)
        result = ch.verify_write_preflight(
            probe_path="probe.txt",
            nonce=b"nonce123",
            exit_code=0,
            jsonl_result=bad_jsonl,
            pre_snapshot=pre,
            post_snapshot=post,
            actual_changed_paths=frozenset({"probe.txt"}),
            probe_file_path=probe_file,
        )
        assert not result.passed

    def test_head_changed_fails(self, tmp_path):
        probe_file = tmp_path / "probe.txt"
        probe_file.write_bytes(b"nonce123")
        pre = make_snapshot(head="abc")
        post = make_snapshot(head="def", changed=frozenset({"probe.txt"}))
        result = ch.verify_write_preflight(
            probe_path="probe.txt",
            nonce=b"nonce123",
            exit_code=0,
            jsonl_result=self._jsonl_ok(),
            pre_snapshot=pre,
            post_snapshot=post,
            actual_changed_paths=frozenset({"probe.txt"}),
            probe_file_path=probe_file,
        )
        assert not result.passed

    def test_content_mismatch_fails(self, tmp_path):
        probe_file = tmp_path / "probe.txt"
        probe_file.write_bytes(b"wrong-content")
        pre = make_snapshot()
        post = make_snapshot(changed=frozenset({"probe.txt"}))
        result = ch.verify_write_preflight(
            probe_path="probe.txt",
            nonce=b"nonce123",
            exit_code=0,
            jsonl_result=self._jsonl_ok(),
            pre_snapshot=pre,
            post_snapshot=post,
            actual_changed_paths=frozenset({"probe.txt"}),
            probe_file_path=probe_file,
        )
        assert not result.passed

    def test_cleanup_verification_passes(self):
        baseline = make_snapshot()
        post_cleanup = make_snapshot()
        result = ch.verify_cleanup(baseline_snapshot=baseline, post_cleanup_snapshot=post_cleanup)
        assert result.passed

    def test_cleanup_verification_fails_on_remaining_changes(self):
        baseline = make_snapshot()
        post_cleanup = make_snapshot(changed=frozenset({"leftover.txt"}))
        result = ch.verify_cleanup(baseline_snapshot=baseline, post_cleanup_snapshot=post_cleanup)
        assert not result.passed

    def test_cleanup_verification_fails_on_snapshot_drift(self):
        baseline = make_snapshot(ref="ref1")
        post_cleanup = make_snapshot(ref="ref2")
        result = ch.verify_cleanup(baseline_snapshot=baseline, post_cleanup_snapshot=post_cleanup)
        assert not result.passed


# ---------------------------------------------------------------------------
# 9. Exact changed-path scope check
# ---------------------------------------------------------------------------


class TestScopeCheck:
    def test_out_of_scope_change_fails(self):
        scope = ch.build_write_scope(["a.txt"])
        result = ch.check_write_scope(write_scope=scope, actual_changed_paths=frozenset({"b.txt"}))
        assert not result.passed

    def test_missing_required_change_fails(self):
        scope = ch.build_write_scope(["a.txt", "b.txt"], required_changed_paths=["b.txt"])
        result = ch.check_write_scope(write_scope=scope, actual_changed_paths=frozenset({"a.txt"}))
        assert not result.passed

    def test_rename_source_outside_scope_fails_even_if_dest_in_scope(self):
        scope = ch.build_write_scope(["new.txt"])
        result = ch.check_write_scope(
            write_scope=scope, actual_changed_paths=frozenset({"old.txt", "new.txt"})
        )
        assert not result.passed

    def test_in_scope_change_with_required_passes(self):
        scope = ch.build_write_scope(["a.txt", "b.txt"], required_changed_paths=["a.txt"])
        result = ch.check_write_scope(write_scope=scope, actual_changed_paths=frozenset({"a.txt"}))
        assert result.passed

    def test_rename_with_both_paths_in_scope_passes(self):
        scope = ch.build_write_scope(["old.txt", "new.txt"])
        result = ch.check_write_scope(
            write_scope=scope, actual_changed_paths=frozenset({"old.txt", "new.txt"})
        )
        assert result.passed


# ---------------------------------------------------------------------------
# 10. Patch/promotion primitives
# ---------------------------------------------------------------------------


class TestPatchPromotion:
    def _make_pair(self, tmp_path):
        primary = init_repo(tmp_path / "primary")
        (primary / "keep.txt").write_text("keep\n")
        (primary / "mod.txt").write_text("original\n")
        (primary / "del.txt").write_text("to delete\n")
        sha = commit_all(primary, "init")
        worktree = tmp_path / "wt"
        ch.create_detached_worktree(primary, worktree, sha)
        return primary, worktree

    def test_text_addition(self, tmp_path):
        primary, worktree = self._make_pair(tmp_path)
        (worktree / "added.txt").write_text("new content\n")
        patch = ch.generate_patch(worktree)
        assert patch.ok
        assert b"added.txt" in patch.patch_bytes
        assert patch.sha256 == hashlib.sha256(patch.patch_bytes).hexdigest()
        assert patch.size_bytes == len(patch.patch_bytes)

    def test_text_modification(self, tmp_path):
        primary, worktree = self._make_pair(tmp_path)
        (worktree / "mod.txt").write_text("modified\n")
        patch = ch.generate_patch(worktree)
        assert patch.ok
        assert b"mod.txt" in patch.patch_bytes

    def test_text_deletion(self, tmp_path):
        primary, worktree = self._make_pair(tmp_path)
        (worktree / "del.txt").unlink()
        patch = ch.generate_patch(worktree)
        assert patch.ok
        assert b"del.txt" in patch.patch_bytes

    def test_untracked_file_included(self, tmp_path):
        primary, worktree = self._make_pair(tmp_path)
        (worktree / "untracked.txt").write_text("brand new\n")
        patch = ch.generate_patch(worktree)
        assert patch.ok
        assert b"untracked.txt" in patch.patch_bytes

    def test_binary_file(self, tmp_path):
        primary, worktree = self._make_pair(tmp_path)
        (worktree / "binary.dat").write_bytes(bytes(range(256)))
        patch = ch.generate_patch(worktree)
        assert patch.ok
        assert b"binary.dat" in patch.patch_bytes
        assert b"GIT binary patch" in patch.patch_bytes

    def test_rename(self, tmp_path):
        primary, worktree = self._make_pair(tmp_path)
        (worktree / "keep.txt").rename(worktree / "renamed.txt")
        patch = ch.generate_patch(worktree)
        assert patch.ok
        assert b"renamed.txt" in patch.patch_bytes

    def test_apply_check_rejects_conflicting_primary_state(self, tmp_path):
        primary, worktree = self._make_pair(tmp_path)
        (worktree / "mod.txt").write_text("worktree change\n")
        patch = ch.generate_patch(worktree)
        assert patch.ok
        (primary / "mod.txt").write_text("conflicting primary change that does not match context\n")
        patch_file = tmp_path / "conflict.patch"
        patch_file.write_bytes(patch.patch_bytes)
        result = ch.apply_check_patch(primary, patch_file)
        assert not result.ok
        ch.remove_temp_patch_file(patch_file)
        assert not patch_file.exists()

    def test_successful_apply_matches_expected_changed_set(self, tmp_path):
        primary, worktree = self._make_pair(tmp_path)
        (worktree / "added.txt").write_text("new content\n")
        (worktree / "mod.txt").write_text("modified\n")
        patch = ch.generate_patch(worktree)
        assert patch.ok
        patch_file = tmp_path / "apply.patch"
        patch_file.write_bytes(patch.patch_bytes)
        check = ch.apply_check_patch(primary, patch_file)
        assert check.ok
        applied = ch.apply_patch(primary, patch_file)
        assert applied.ok
        status = ch.get_git_status(primary)
        assert status.changed_paths == {"added.txt", "mod.txt"}
        ch.remove_temp_patch_file(patch_file)
        assert not patch_file.exists()


# ---------------------------------------------------------------------------
# Remediation regression: Defect 1 -- ref-digest truncation fail-open
# ---------------------------------------------------------------------------


def _create_many_lightweight_tags(repo: Path, count: int, sha: str) -> None:
    """Create `count` lightweight tags via one `update-ref --stdin` batch call.

    Far faster than spawning `count` individual `git tag` processes, and
    produces the same `refs/tags/*` entries `for-each-ref` enumerates.
    """
    # Bytes input with explicit LF only: subprocess.run(text=True) on Windows
    # translates "\n" to os.linesep ("\r\n") on write, which corrupts
    # update-ref --stdin's line-oriented command format ("extra input").
    commands = "".join(f"create refs/tags/tag{i:05d} {sha}\n" for i in range(count))
    subprocess.run(
        ["git", *_GIT_IDENTITY, "-C", str(repo), "update-ref", "--stdin"],
        input=commands.encode("utf-8"),
        capture_output=True,
        timeout=60,
        check=True,
    )


class TestRefDigestIntegrity:
    TAG_COUNT = 1500  # matches the validator's P5 probe scale

    def _large_ref_repo(self, tmp_path: Path) -> tuple[Path, str]:
        repo = init_repo(tmp_path / "repo")
        sha = commit_all(repo, "init")
        _create_many_lightweight_tags(repo, self.TAG_COUNT, sha)
        return repo, sha

    def test_raw_ref_listing_exceeds_old_60000_char_run_bounded_limit(self, tmp_path):
        # Sanity check that this fixture actually reproduces the validator's
        # scale: raw `for-each-ref` output must exceed run_bounded's default
        # 60,000-char MAX_RESULT_CHARS, or this is not the same bug scenario.
        repo, _sha = self._large_ref_repo(tmp_path)
        raw = subprocess.run(
            ["git", *_GIT_IDENTITY, "-C", str(repo), "for-each-ref", "--sort=refname", "refs/"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=30,
            check=True,
        ).stdout
        assert len(raw) > 60_000

    def test_early_sorted_tag_deletion_changes_digest(self, tmp_path):
        # This is the validator's exact P5 repro: with the old run_bounded-backed
        # implementation, `text[-max_result_chars:]` kept only the TAIL of the
        # output, silently dropping the alphabetically-earliest refs (like
        # tag00000). Deleting that ref therefore left the (truncated) digest
        # unchanged -- a real mutation went undetected. The fix must detect it.
        repo, _sha = self._large_ref_repo(tmp_path)
        before = ch.compute_ref_digest(repo)
        subprocess.run(
            ["git", *_GIT_IDENTITY, "-C", str(repo), "tag", "-d", "tag00000"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=15,
            check=True,
        )
        after = ch.compute_ref_digest(repo)
        assert before != after

    def test_digest_deterministic_across_repeated_calls(self, tmp_path):
        repo, _sha = self._large_ref_repo(tmp_path)
        first = ch.compute_ref_digest(repo)
        second = ch.compute_ref_digest(repo)
        assert first == second

    def test_byte_ceiling_overflow_fails_closed(self, tmp_path, monkeypatch):
        repo, _sha = self._large_ref_repo(tmp_path)
        monkeypatch.setattr(ch, "REF_DIGEST_MAX_BYTES", 100)
        with pytest.raises(RuntimeError, match="byte ceiling"):
            ch.compute_ref_digest(repo)

    def test_nonzero_git_exit_fails_closed(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        commit_all(repo, "init")
        with pytest.raises(RuntimeError, match="failed with exit code"):
            ch._run_git_raw_bytes(
                ["for-each-ref", "--this-flag-does-not-exist"],
                cwd=repo,
                timeout=ch.GIT_TIMEOUT,
                max_bytes=ch.REF_DIGEST_MAX_BYTES,
            )


# ---------------------------------------------------------------------------
# Remediation regression: Defect 2 -- patch generation corrupts diff bytes
# ---------------------------------------------------------------------------


def _raw_cached_diff_bytes(worktree: Path) -> bytes:
    """Capture `git diff --cached --binary --find-renames=50%` byte-exact,

    entirely independent of the module under test, for comparison.
    """
    return subprocess.run(
        [
            "git",
            *_GIT_IDENTITY,
            "-C",
            str(worktree),
            "diff",
            "--cached",
            "--binary",
            "--find-renames=50%",
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=30,
        check=True,
    ).stdout


class TestPatchByteIntegrity:
    def _make_pair(self, tmp_path):
        primary = init_repo(tmp_path / "primary")
        (primary / "keep.txt").write_text("keep\n")
        (primary / "mod.txt").write_text("original\n")
        sha = commit_all(primary, "init")
        worktree = tmp_path / "wt"
        ch.create_detached_worktree(primary, worktree, sha)
        return primary, worktree

    def test_trailing_blank_line_patch_is_byte_exact_and_applies(self, tmp_path):
        # Validator's exact repro: a file ending in a legitimate trailing
        # blank (whitespace-only) line, edited in the worktree. The old
        # run_bounded-backed implementation `.strip()`d the diff text and only
        # re-appended a single guessed trailing "\n", which does not restore a
        # stripped trailing whitespace-only context line -- corrupting the
        # patch (135 raw bytes -> 133 stripped-and-patched bytes in their
        # repro) while PatchResult.ok still reported True.
        primary, worktree = self._make_pair(tmp_path)
        (worktree / "keep.txt").write_text("keep\n\n")  # trailing blank line
        run_git(worktree, "add", "-A")
        raw = _raw_cached_diff_bytes(worktree)
        assert raw  # sanity: there is in fact a diff

        patch = ch.generate_patch(worktree)
        assert patch.ok
        assert patch.patch_bytes == raw
        assert patch.size_bytes == len(raw)
        assert patch.sha256 == hashlib.sha256(raw).hexdigest()

        patch_file = tmp_path / "trailing_blank.patch"
        patch_file.write_bytes(patch.patch_bytes)
        check = ch.apply_check_patch(primary, patch_file)
        assert check.ok, check.output
        ch.remove_temp_patch_file(patch_file)

    def test_no_trailing_newline_in_source_content(self, tmp_path):
        primary, worktree = self._make_pair(tmp_path)
        (worktree / "mod.txt").write_bytes(b"modified content with no trailing newline")
        run_git(worktree, "add", "-A")
        raw = _raw_cached_diff_bytes(worktree)
        patch = ch.generate_patch(worktree)
        assert patch.ok
        assert patch.patch_bytes == raw
        patch_file = tmp_path / "no_newline.patch"
        patch_file.write_bytes(patch.patch_bytes)
        check = ch.apply_check_patch(primary, patch_file)
        assert check.ok, check.output
        ch.remove_temp_patch_file(patch_file)

    def test_binary_patch_end_to_end_apply_check(self, tmp_path):
        primary, worktree = self._make_pair(tmp_path)
        (worktree / "binary.dat").write_bytes(bytes(range(256)) * 4)
        patch = ch.generate_patch(worktree)
        assert patch.ok
        assert b"GIT binary patch" in patch.patch_bytes
        patch_file = tmp_path / "binary.patch"
        patch_file.write_bytes(patch.patch_bytes)
        check = ch.apply_check_patch(primary, patch_file)
        assert check.ok, check.output
        ch.remove_temp_patch_file(patch_file)

    def test_rename_patch_end_to_end_apply_check(self, tmp_path):
        primary, worktree = self._make_pair(tmp_path)
        (worktree / "keep.txt").rename(worktree / "renamed.txt")
        patch = ch.generate_patch(worktree)
        assert patch.ok
        assert b"renamed.txt" in patch.patch_bytes
        patch_file = tmp_path / "rename.patch"
        patch_file.write_bytes(patch.patch_bytes)
        check = ch.apply_check_patch(primary, patch_file)
        assert check.ok, check.output
        ch.remove_temp_patch_file(patch_file)

    def test_oversize_patch_fails_closed(self, tmp_path, monkeypatch):
        primary, worktree = self._make_pair(tmp_path)
        (worktree / "mod.txt").write_text("x" * 5000 + "\n")
        monkeypatch.setattr(ch, "PATCH_MAX_BYTES", 100)
        patch = ch.generate_patch(worktree)
        assert not patch.ok
        assert patch.patch_bytes == b""
        assert patch.sha256 == ""
        assert patch.size_bytes == 0
        assert "byte ceiling" in patch.output

    def test_git_nonzero_exit_during_diff_fails_closed(self, tmp_path, monkeypatch):
        primary, worktree = self._make_pair(tmp_path)
        (worktree / "mod.txt").write_text("modified\n")

        def raise_nonzero_exit(*args, **kwargs):
            raise RuntimeError("git diff ... failed with exit code 129")

        monkeypatch.setattr(ch, "_run_git_raw_bytes", raise_nonzero_exit)
        patch = ch.generate_patch(worktree)
        assert not patch.ok
        assert patch.patch_bytes == b""
        assert patch.sha256 == ""
        assert patch.size_bytes == 0

    def test_failure_paths_never_report_ok_true(self, tmp_path, monkeypatch):
        # Both new failure paths (oversize, nonzero git exit) must never
        # report PatchResult.ok=True -- reconfirm both explicitly here.
        primary, worktree = self._make_pair(tmp_path)
        (worktree / "mod.txt").write_text("x" * 1000 + "\n")
        monkeypatch.setattr(ch, "PATCH_MAX_BYTES", 10)
        oversize = ch.generate_patch(worktree)
        assert oversize.ok is False

        primary2, worktree2 = self._make_pair(tmp_path / "second")
        (worktree2 / "mod.txt").write_text("modified\n")
        monkeypatch.setattr(
            ch, "_run_git_raw_bytes", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
        )
        failed_exit = ch.generate_patch(worktree2)
        assert failed_exit.ok is False


# ---------------------------------------------------------------------------
# Hardening round: Gap 1 -- ignored files must not be invisible in the
# disposable worktree
# ---------------------------------------------------------------------------


class TestIgnoredFileVisibility:
    def _repo_with_gitignored_dist(self, tmp_path: Path) -> tuple[Path, str]:
        repo = init_repo(tmp_path / "repo")
        (repo / ".gitignore").write_text("dist/\n")
        (repo / "keep.txt").write_text("keep\n")
        sha = commit_all(repo, "init")
        return repo, sha

    def test_old_style_status_call_misses_ignored_file(self, tmp_path):
        # Discriminating control: the pre-existing parser/status call (no
        # --ignored flags) must NOT see dist/hidden.txt anywhere.
        repo, _sha = self._repo_with_gitignored_dist(tmp_path)
        dist = repo / "dist"
        dist.mkdir()
        (dist / "hidden.txt").write_text("codex output\n")
        old_status = ch.get_git_status(repo)
        assert "dist/hidden.txt" not in old_status.changed_paths
        assert not any("hidden.txt" in p for p in old_status.changed_paths)
        # Parsing the OLD (no --ignored) porcelain text directly, even with
        # recognize_ignored=True, still can't recover it: git never emitted
        # a `!` record for it in that invocation.
        assert old_status.ignored_paths == frozenset()

    def test_new_status_call_sees_ignored_file_in_ignored_paths(self, tmp_path):
        repo, _sha = self._repo_with_gitignored_dist(tmp_path)
        dist = repo / "dist"
        dist.mkdir()
        (dist / "hidden.txt").write_text("codex output\n")
        new_status = ch.get_git_status_including_ignored(repo)
        assert "dist/hidden.txt" in new_status.ignored_paths
        assert "dist/hidden.txt" not in new_status.changed_paths

    def test_disposable_worktree_snapshot_fails_closed_on_ignored_output(self, tmp_path):
        repo, sha = self._repo_with_gitignored_dist(tmp_path)
        worktree = tmp_path / "wt"
        ch.create_detached_worktree(repo, worktree, sha)
        dist = worktree / "dist"
        dist.mkdir()
        (dist / "hidden.txt").write_text("codex output\n")

        # Simulated real-execution verification path: scope check must fail
        # closed because of the ignored path, even though nothing in
        # write_scope references it.
        status = ch.get_git_status_including_ignored(worktree)
        scope = ch.build_write_scope(["dist/hidden.txt"])
        result = ch.check_write_scope(
            write_scope=scope,
            actual_changed_paths=status.changed_paths,
            ignored_paths=status.ignored_paths,
        )
        assert not result.passed
        assert "ignored" in result.reason.lower()

    def test_ignored_path_inside_write_scope_still_fails(self, tmp_path):
        # write_scope membership never rescues an ignored path.
        scope = ch.build_write_scope(["dist/hidden.txt"])
        result = ch.check_write_scope(
            write_scope=scope,
            actual_changed_paths=frozenset(),
            ignored_paths=frozenset({"dist/hidden.txt"}),
        )
        assert not result.passed

    def test_ignored_unicode_filename_parsed_exactly(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        (repo / ".gitignore").write_text("dist/\n")
        commit_all(repo, "init")
        dist = repo / "dist"
        dist.mkdir()
        name = "üñîçødé_名前.txt"
        (dist / name).write_text("hello\n", encoding="utf-8")
        status = ch.get_git_status_including_ignored(repo)
        assert f"dist/{name}" in status.ignored_paths

    def test_ignored_filename_with_spaces_parsed_exactly(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        (repo / ".gitignore").write_text("dist/\n")
        commit_all(repo, "init")
        dist = repo / "dist"
        dist.mkdir()
        name = "a file with spaces.txt"
        (dist / name).write_text("hello\n")
        status = ch.get_git_status_including_ignored(repo)
        assert f"dist/{name}" in status.ignored_paths

    def test_clean_disposable_worktree_has_empty_ignored_paths(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        (repo / ".gitignore").write_text("dist/\n")
        sha = commit_all(repo, "init")
        worktree = tmp_path / "wt"
        snap = ch.create_detached_worktree(repo, worktree, sha)
        assert snap.ignored_paths == frozenset()
        assert snap.clean

    def test_ordinary_untracked_file_unaffected_by_ignored_detection(self, tmp_path):
        repo = init_repo(tmp_path / "repo")
        (repo / ".gitignore").write_text("dist/\n")
        commit_all(repo, "init")
        (repo / "plain_untracked.txt").write_text("hi\n")
        status = ch.get_git_status_including_ignored(repo)
        assert "plain_untracked.txt" in status.changed_paths
        assert "plain_untracked.txt" not in status.ignored_paths
        assert status.ignored_paths == frozenset()

    def test_existing_tracked_and_rename_behavior_unmodified(self, tmp_path):
        # Same fixture as TestGitStatusParsing.test_rename_captures_both_old_and_new,
        # but run through the NEW ignored-aware status call, to confirm
        # tracked/rename behavior is unaffected by --ignored=traditional.
        repo = init_repo(tmp_path / "repo")
        (repo / "old.txt").write_text("content for rename detection padding\n" * 5)
        commit_all(repo, "init")
        run_git(repo, "mv", "old.txt", "new.txt")
        status = ch.get_git_status_including_ignored(repo)
        assert "old.txt" in status.changed_paths
        assert "new.txt" in status.changed_paths
        assert status.renames == (("old.txt", "new.txt"),)
        assert status.ignored_paths == frozenset()

    def test_bang_record_rejected_when_not_recognized(self):
        with pytest.raises(ch.GitStatusParseError):
            ch.parse_porcelain_v2_z("! dist/hidden.txt\x00")

    def test_malformed_ignored_record_fails_closed(self):
        with pytest.raises(ch.GitStatusParseError):
            ch.parse_porcelain_v2_z("!\x00", recognize_ignored=True)

    def test_verify_write_preflight_fails_when_post_snapshot_has_ignored_paths(self, tmp_path):
        probe_file = tmp_path / "probe.txt"
        probe_file.write_bytes(b"nonce123")
        pre = make_snapshot()
        post = make_snapshot(
            changed=frozenset({"probe.txt"}), ignored=frozenset({"dist/hidden.txt"})
        )
        jsonl_ok = ch.JsonlParseResult(
            ok=True, events=({"type": "done"},), diagnostics=(), truncated=False
        )
        result = ch.verify_write_preflight(
            probe_path="probe.txt",
            nonce=b"nonce123",
            exit_code=0,
            jsonl_result=jsonl_ok,
            pre_snapshot=pre,
            post_snapshot=post,
            actual_changed_paths=frozenset({"probe.txt"}),
            probe_file_path=probe_file,
        )
        assert not result.passed
        assert "ignored" in result.reason.lower()

    def test_verify_cleanup_fails_when_ignored_paths_remain(self):
        baseline = make_snapshot()
        post_cleanup = make_snapshot(ignored=frozenset({"dist/hidden.txt"}))
        result = ch.verify_cleanup(baseline_snapshot=baseline, post_cleanup_snapshot=post_cleanup)
        assert not result.passed


# ---------------------------------------------------------------------------
# Hardening round: Gap 2 -- semantic git index-state protection
# ---------------------------------------------------------------------------


class TestIndexStateDigest:
    def _repo(self, tmp_path: Path) -> Path:
        repo = init_repo(tmp_path / "repo")
        (repo / "tracked.txt").write_text("original\n")
        commit_all(repo, "init")
        return repo

    def test_baseline_digest_deterministic(self, tmp_path):
        repo = self._repo(tmp_path)
        first = ch.compute_index_state_digest(repo)
        second = ch.compute_index_state_digest(repo)
        assert first == second

    def test_unstaged_edit_leaves_digest_unchanged(self, tmp_path):
        repo = self._repo(tmp_path)
        before = ch.compute_index_state_digest(repo)
        (repo / "tracked.txt").write_text("codex edited this content directly\n")
        after = ch.compute_index_state_digest(repo)
        assert before == after

    def test_git_add_changes_digest(self, tmp_path):
        repo = self._repo(tmp_path)
        before = ch.compute_index_state_digest(repo)
        (repo / "tracked.txt").write_text("staged change\n")
        run_git(repo, "add", "tracked.txt")
        after = ch.compute_index_state_digest(repo)
        assert before != after
        # And the comparison function used by the real verifiers treats this
        # as a FAIL.
        baseline = make_snapshot(index_digest=before)
        current = make_snapshot(index_digest=after)
        result = ch.verify_worktree_integrity(
            baseline_snapshot=baseline, current_snapshot=current, context="test"
        )
        assert not result.passed

    def test_staged_content_mutation_changes_digest(self, tmp_path):
        repo = self._repo(tmp_path)
        (repo / "tracked.txt").write_text("first staged content\n")
        run_git(repo, "add", "tracked.txt")
        before = ch.compute_index_state_digest(repo)
        (repo / "tracked.txt").write_text("different staged content\n")
        run_git(repo, "add", "tracked.txt")
        after = ch.compute_index_state_digest(repo)
        assert before != after
        baseline = make_snapshot(index_digest=before)
        current = make_snapshot(index_digest=after)
        result = ch.verify_worktree_integrity(
            baseline_snapshot=baseline, current_snapshot=current, context="test"
        )
        assert not result.passed

    def test_assume_unchanged_bit_changes_digest(self, tmp_path):
        repo = self._repo(tmp_path)
        before = ch.compute_index_state_digest(repo)
        run_git(repo, "update-index", "--assume-unchanged", "tracked.txt")
        after = ch.compute_index_state_digest(repo)
        assert before != after
        baseline = make_snapshot(index_digest=before)
        current = make_snapshot(index_digest=after)
        result = ch.verify_worktree_integrity(
            baseline_snapshot=baseline, current_snapshot=current, context="test"
        )
        assert not result.passed

    def test_skip_worktree_bit_changes_digest(self, tmp_path):
        repo = self._repo(tmp_path)
        before = ch.compute_index_state_digest(repo)
        run_git(repo, "update-index", "--skip-worktree", "tracked.txt")
        after = ch.compute_index_state_digest(repo)
        assert before != after
        baseline = make_snapshot(index_digest=before)
        current = make_snapshot(index_digest=after)
        result = ch.verify_worktree_integrity(
            baseline_snapshot=baseline, current_snapshot=current, context="test"
        )
        assert not result.passed

    def test_flag_set_then_reset_would_have_been_caught_by_earlier_capture_point(self, tmp_path):
        # Framing note: resetting a transient mutation back to normal before a
        # LATER verification call does not retroactively excuse it. This test
        # demonstrates the ordering property directly -- it does NOT assert
        # that the final state equals baseline is somehow wrong; it asserts
        # that an EARLIER comparison (baseline vs. the point where the flag
        # was set) fails, which is what the real capture-point sequence relies
        # on to catch a transient mutation before it gets reset.
        repo = self._repo(tmp_path)
        baseline_digest = ch.compute_index_state_digest(repo)
        run_git(repo, "update-index", "--assume-unchanged", "tracked.txt")
        during_digest = ch.compute_index_state_digest(repo)
        run_git(repo, "update-index", "--no-assume-unchanged", "tracked.txt")
        after_reset_digest = ch.compute_index_state_digest(repo)

        # The earlier (during-mutation) capture point would have failed:
        baseline_snap = make_snapshot(index_digest=baseline_digest)
        during_snap = make_snapshot(index_digest=during_digest)
        earlier_result = ch.verify_worktree_integrity(
            baseline_snapshot=baseline_snap, current_snapshot=during_snap, context="during"
        )
        assert not earlier_result.passed

        # The digest returns to the baseline value after reset (sanity check
        # only -- this does not mean the real sequence would have missed the
        # transient mutation, since the real sequence's earlier capture point
        # already caught it above).
        assert after_reset_digest == baseline_digest

    def test_oversized_index_output_fails_closed(self, tmp_path, monkeypatch):
        repo = self._repo(tmp_path)
        monkeypatch.setattr(ch, "INDEX_STATE_MAX_BYTES", 1)
        with pytest.raises(RuntimeError, match="byte ceiling"):
            ch.compute_index_state_digest(repo)

    def test_nonzero_git_exit_during_ls_files_fails_closed(self, tmp_path):
        repo = self._repo(tmp_path)
        with pytest.raises(RuntimeError, match="failed with exit code"):
            ch._run_git_raw_bytes(
                ["ls-files", "--this-flag-does-not-exist"],
                cwd=repo,
                timeout=ch.GIT_TIMEOUT,
                max_bytes=ch.INDEX_STATE_MAX_BYTES,
            )

    def test_git_snapshot_carries_index_state_digest(self, tmp_path):
        repo = self._repo(tmp_path)
        snap = ch.take_snapshot(repo)
        assert snap.index_state_digest == ch.compute_index_state_digest(repo)

    def test_index_state_digest_change_detected_via_take_snapshot_and_compare(self, tmp_path):
        repo = self._repo(tmp_path)
        before = ch.take_snapshot(repo)
        run_git(repo, "add", "tracked.txt")  # no content change, but let's actually stage something
        (repo / "tracked.txt").write_text("changed\n")
        run_git(repo, "add", "tracked.txt")
        after = ch.take_snapshot(repo)
        diff = ch.compare_snapshots(before, after)
        assert diff.index_state_digest_changed
        assert diff.mutated


# ---------------------------------------------------------------------------
# Slice 2 (issue #143): governed two-phase Codex handoff SERVICE
# ---------------------------------------------------------------------------


def make_active_task(**overrides) -> ActiveTask:
    fields = dict(
        task_key="TASK-1",
        title="Improve widget",
        objective="Make the widget faster",
        task_family="general",
        current_phase="build",
        current_step="implement",
        state_summary="Widget is halfway optimized",
        next_action="Optimize the hot loop in a.py",
        latest_user_instruction="Please continue optimizing",
        open_questions=[],
        assumptions=[],
        constraints=["no migrations"],
        decisions=[],
        completed_work=["profiled the widget"],
        pending_work=["optimize hot loop"],
        relevant_objects=["a.py"],
        validation_status="pending",
    )
    fields.update(overrides)
    return ActiveTask(**fields)


class FakeRepository:
    """In-memory double for Repository -- exercises CodexHandoffService without

    a live PostgreSQL database (matching this codebase's existing unit-test
    convention; real-DB integration tests are opt-in under tests/integration/).
    """

    def __init__(self, active: ActiveTask | None):
        self.active = active
        self.events: list[tuple[str, str, str, dict, str | None]] = []
        self.state_updates: list[tuple[str, dict]] = []

    def active_task(self, project_id, provider_session_id=None):
        return self.active

    def record_event(self, task_key, event_type, actor, payload, session_id=None):
        self.events.append((task_key, event_type, actor, payload, session_id))

    def update_state(self, task_key, **fields):
        bad_field = set(fields) - {"validation_status"}
        bad_value = fields.get("validation_status") not in {"pending", "failed"}
        if bad_field or bad_value:
            raise ValueError("only validation_status in {pending,failed} is exercised by this fake")
        self.state_updates.append((task_key, fields))


class FakeDecisions:
    def __init__(self, active: list[dict] | None = None):
        self._active = active or []

    def list_active(self, task_key):
        return list(self._active)


def _rows(reply):
    return SimpleNamespace(fetchone=lambda: reply, fetchall=lambda: reply)


class FakePromotionDB:
    """Transactional in-memory double for the promotion window's SQL.

    Unlike ScriptedConnection (whose transaction() is a no-op), this models
    the three things the #143 remediation depends on: committed vs.
    in-transaction validation_status (a rollback discards the staged write),
    row-lock ownership (a SECOND connection that locks/writes a row held by an
    open promotion transaction fails immediately -- on real PostgreSQL it
    would block forever: the proven self-deadlock), and migration 028's
    passed -> pending guard. It is not PostgreSQL; the live-DB probe remains a
    separate validation gate.
    """

    def __init__(self, active: ActiveTask, decisions=None, *, task_id=1, project_id=7):
        self.row = dataclasses.asdict(active)
        self.committed_validation = active.validation_status
        self.decisions = [dict(d) for d in (decisions or [])]
        self.task_id = task_id
        self.project_id = project_id
        self.connections: list[FakeTxnConnection] = []
        self.opened_while_lock_held: list[bool] = []
        self.lock_owner: FakeTxnConnection | None = None
        self.log: list[tuple[int, str]] = []
        self.fail_sql: dict[str, BaseException] = {}  # SQL substring -> raise once

    def connect(self):
        conn = FakeTxnConnection(self, len(self.connections))
        self.opened_while_lock_held.append(self.lock_owner is not None)
        self.connections.append(conn)
        return conn

    def sql(self, index: int | None = None) -> list[str]:
        return [text for i, text in self.log if index is None or i == index]


class FakeTxnConnection:
    def __init__(self, db: FakePromotionDB, index: int):
        self.db = db
        self.index = index
        self.staged: str | None = None
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.closed = True
        self._release()
        return False

    @contextmanager
    def transaction(self):
        try:
            yield
        except BaseException:
            self.staged = None  # ROLLBACK
            raise
        else:
            if self.staged is not None:  # COMMIT
                self.db.committed_validation = self.staged
            self.staged = None
        finally:
            self._release()

    def view(self) -> str:
        return self.staged if self.staged is not None else self.db.committed_validation

    def _release(self):
        if self.db.lock_owner is self:
            self.db.lock_owner = None

    def _lock(self, text: str):
        owner = self.db.lock_owner
        if owner is not None and owner is not self:
            raise AssertionError(
                f"self-deadlock: connection {self.index} needs a row lock held by open "
                f"connection {owner.index}: {text}"
            )
        self.db.lock_owner = self

    def execute(self, sql, params=None):
        assert not self.closed, "SQL on a closed connection"
        text = " ".join(str(sql).split())
        self.db.log.append((self.index, text))
        for needle in list(self.db.fail_sql):
            if needle in text:
                raise self.db.fail_sql.pop(needle)
        if text.startswith("SET LOCAL"):
            return _rows(None)
        if "FROM vres.tasks WHERE task_key" in text:
            assert "FOR UPDATE" in text
            self._lock(text)
            return _rows({"id": self.db.task_id, "project_id": self.db.project_id,
                          "status": "active"})
        if "FROM vres.sessions" in text:
            return _rows({"task_id": self.db.task_id})
        if "JOIN vres.task_state" in text:
            self._lock(text)
            return _rows({**self.db.row, "validation_status": self.view()})
        if "FROM vres.task_decisions" in text:
            return _rows([dict(d) for d in self.db.decisions])
        if text.startswith("UPDATE vres.task_state"):
            assert "validation_status='pending'" in text, text
            self._lock(text)
            if self.view() == "passed":
                raise RuntimeError("migration 028: Fresh passed validation is protected")
            self.staged = "pending"
            return _rows(None)
        if text.startswith("UPDATE vres.tasks SET updated_at"):
            self._lock(text)
            return _rows(None)
        raise AssertionError(f"unexpected SQL: {text}")


def _repo_with_commit(tmp_path: Path, name: str = "primary") -> Path:
    root = init_repo(tmp_path / name)
    (root / "a.py").write_text("print('hello')\n")
    commit_all(root, "init")
    return root


class TestPrepareAuthority:
    def test_no_active_task_rejects(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        svc = ch.CodexHandoffService(
            repository=FakeRepository(None), task_decisions=FakeDecisions()
        )
        with pytest.raises(ch.HandoffError) as exc:
            svc.prepare(
                project_id=7, project_root=root, task_key="TASK-1", session_id="s",
                write_scope=["a.py"], required_changed_paths=["a.py"],
                acceptance_criteria=None, file_postconditions=None,
            )
        assert exc.value.reason_category == "no_active_task"

    def test_task_key_mismatch_rejects_without_persisting_anything(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        repo = FakeRepository(make_active_task(task_key="TASK-OTHER"))
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        with pytest.raises(ch.HandoffError) as exc:
            svc.prepare(
                project_id=7, project_root=root, task_key="TASK-1", session_id="s",
                write_scope=["a.py"], required_changed_paths=["a.py"],
                acceptance_criteria=None, file_postconditions=None,
            )
        assert exc.value.reason_category == "task_mismatch"
        assert repo.events == []

    def test_dirty_primary_rejects(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        (root / "a.py").write_text("dirty\n")
        repo = FakeRepository(make_active_task())
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        with pytest.raises(ch.HandoffError) as exc:
            svc.prepare(
                project_id=7, project_root=root, task_key="TASK-1", session_id="s",
                write_scope=["a.py"], required_changed_paths=["a.py"],
                acceptance_criteria=None, file_postconditions=None,
            )
        assert exc.value.reason_category == "primary_dirty"
        assert repo.events == []

    def test_codex_project_config_present_rejects(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        (root / ".codex").mkdir()
        (root / ".codex" / "config.toml").write_text("[x]\n")
        commit_all(root, "add codex config")  # tracked+clean, so only the config check fires
        repo = FakeRepository(make_active_task())
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        with pytest.raises(ch.HandoffError) as exc:
            svc.prepare(
                project_id=7, project_root=root, task_key="TASK-1", session_id="s",
                write_scope=["a.py"], required_changed_paths=["a.py"],
                acceptance_criteria=None, file_postconditions=None,
            )
        assert exc.value.reason_category == "codex_config_unsupported"

    def test_empty_write_scope_rejects(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        repo = FakeRepository(make_active_task())
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        with pytest.raises(ch.HandoffError) as exc:
            svc.prepare(
                project_id=7, project_root=root, task_key="TASK-1", session_id="s",
                write_scope=[], required_changed_paths=[],
                acceptance_criteria=None, file_postconditions=None,
            )
        assert exc.value.reason_category == "empty_write_scope"

    def test_empty_required_changed_paths_rejects(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        repo = FakeRepository(make_active_task())
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        with pytest.raises(ch.HandoffError) as exc:
            svc.prepare(
                project_id=7, project_root=root, task_key="TASK-1", session_id="s",
                write_scope=["a.py"], required_changed_paths=[],
                acceptance_criteria=None, file_postconditions=None,
            )
        assert exc.value.reason_category == "empty_required_changed_paths"

    def test_required_path_outside_scope_rejects(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        repo = FakeRepository(make_active_task())
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        with pytest.raises(ch.HandoffError) as exc:
            svc.prepare(
                project_id=7, project_root=root, task_key="TASK-1", session_id="s",
                write_scope=["a.py"], required_changed_paths=["b.py"],
                acceptance_criteria=None, file_postconditions=None,
            )
        assert exc.value.reason_category == "invalid_write_scope"

    def test_missing_next_action_rejects(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        repo = FakeRepository(make_active_task(next_action=""))
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        with pytest.raises(ch.HandoffError) as exc:
            svc.prepare(
                project_id=7, project_root=root, task_key="TASK-1", session_id="s",
                write_scope=["a.py"], required_changed_paths=["a.py"],
                acceptance_criteria=None, file_postconditions=None,
            )
        assert exc.value.reason_category == "missing_next_action"

    def test_malformed_acceptance_criteria_rejects(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        repo = FakeRepository(make_active_task())
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        with pytest.raises(ch.HandoffError) as exc:
            svc.prepare(
                project_id=7, project_root=root, task_key="TASK-1", session_id="s",
                write_scope=["a.py"], required_changed_paths=["a.py"],
                acceptance_criteria=["x" * 501], file_postconditions=None,
            )
        assert exc.value.reason_category == "invalid_acceptance_criteria"

    def test_file_postcondition_outside_scope_rejects(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        repo = FakeRepository(make_active_task())
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        with pytest.raises(ch.HandoffError) as exc:
            svc.prepare(
                project_id=7, project_root=root, task_key="TASK-1", session_id="s",
                write_scope=["a.py"], required_changed_paths=["a.py"],
                acceptance_criteria=None,
                file_postconditions=[{"kind": "file_exists", "path": "b.py"}],
            )
        assert exc.value.reason_category == "invalid_file_postconditions"

    def test_malformed_sha256_postcondition_rejects(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        repo = FakeRepository(make_active_task())
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        with pytest.raises(ch.HandoffError) as exc:
            svc.prepare(
                project_id=7, project_root=root, task_key="TASK-1", session_id="s",
                write_scope=["a.py"], required_changed_paths=["a.py"],
                acceptance_criteria=None,
                file_postconditions=[{"kind": "file_sha256", "path": "a.py", "sha256": "not-hex"}],
            )
        assert exc.value.reason_category == "invalid_file_postconditions"

    def test_secret_like_content_rejects_before_any_event_persisted(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        repo = FakeRepository(make_active_task(state_summary="token=sk-ant-abcdefghijklmnop"))
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        with pytest.raises(ch.HandoffError) as exc:
            svc.prepare(
                project_id=7, project_root=root, task_key="TASK-1", session_id="s",
                write_scope=["a.py"], required_changed_paths=["a.py"],
                acceptance_criteria=None, file_postconditions=None,
            )
        assert exc.value.reason_category == "secret_detected"
        assert repo.events == []

    def test_prompt_exceeding_max_bytes_rejects(self, tmp_path, monkeypatch):
        root = _repo_with_commit(tmp_path)
        repo = FakeRepository(make_active_task())
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        monkeypatch.setattr(ch, "MAX_PROMPT_BYTES", 16)
        with pytest.raises(ch.HandoffError) as exc:
            svc.prepare(
                project_id=7, project_root=root, task_key="TASK-1", session_id="s",
                write_scope=["a.py"], required_changed_paths=["a.py"],
                acceptance_criteria=None, file_postconditions=None,
            )
        assert exc.value.reason_category == "prompt_too_large"
        assert repo.events == []

    def test_payload_contains_no_transcript_shaped_data(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        active = make_active_task()
        repo = FakeRepository(active)
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        result = svc.prepare(
            project_id=7, project_root=root, task_key="TASK-1", session_id="s",
            write_scope=["a.py"], required_changed_paths=["a.py"],
            acceptance_criteria=["a.py runs"], file_postconditions=None,
        )
        assert result["ok"]
        prepared_payload = repo.events[0][3]
        prompt = json.loads(prepared_payload["codex_prompt"])
        forbidden_keys = {
            "recent_turns", "latest_assistant_snapshot", "conversation", "transcript", "messages",
        }
        assert forbidden_keys.isdisjoint(prompt.keys())
        assert prompt["objective"] == active.objective
        assert prompt["next_action"] == active.next_action

    def test_prepare_success_persists_exactly_one_event(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        repo = FakeRepository(make_active_task())
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        result = svc.prepare(
            project_id=7, project_root=root, task_key="TASK-1", session_id="s",
            write_scope=["a.py"], required_changed_paths=["a.py"],
            acceptance_criteria=["a.py runs"], file_postconditions=None,
        )
        assert result["ok"] is True
        assert result["handoff_key"].startswith("HANDOFF-")
        assert len(repo.events) == 1
        assert repo.events[0][1] == "CODEX_HANDOFF_PREPARED"


class TestDecisionsAndFingerprint:
    def test_active_decisions_change_the_fingerprint(self):
        active = make_active_task()
        fields = {f: getattr(active, f) for f in ch.FINGERPRINT_FIELDS}
        fp_none = ch.compute_task_state_fingerprint(fields, [])
        fp_with = ch.compute_task_state_fingerprint(
            fields, [{"decision_key": "DEC-1", "text": "use approach A", "rationale": None}]
        )
        assert fp_none != fp_with

    def test_fingerprint_is_stable_and_repeatable(self):
        active = make_active_task()
        fields = {f: getattr(active, f) for f in ch.FINGERPRINT_FIELDS}
        decisions = [{"decision_key": "DEC-1", "text": "use approach A", "rationale": None}]
        fp1 = ch.compute_task_state_fingerprint(fields, decisions)
        fp2 = ch.compute_task_state_fingerprint(fields, decisions)
        assert fp1 == fp2

    def test_decision_order_does_not_affect_fingerprint(self):
        active = make_active_task()
        fields = {f: getattr(active, f) for f in ch.FINGERPRINT_FIELDS}
        d1 = {"decision_key": "DEC-1", "text": "A", "rationale": None}
        d2 = {"decision_key": "DEC-2", "text": "B", "rationale": None}
        fp_forward = ch.compute_task_state_fingerprint(fields, [d1, d2])
        fp_reversed = ch.compute_task_state_fingerprint(fields, [d2, d1])
        assert fp_forward == fp_reversed

    @pytest.mark.parametrize(
        "field,value",
        [
            ("next_action", "a totally different next action"),
            ("latest_user_instruction", "a totally different instruction"),
            ("validation_status", "failed"),
        ],
    )
    def test_mutating_field_makes_execute_time_fingerprint_stale(self, tmp_path, field, value):
        root = _repo_with_commit(tmp_path)
        active = make_active_task()
        repo = FakeRepository(active)
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        svc.prepare(
            project_id=7, project_root=root, task_key="TASK-1", session_id="s",
            write_scope=["a.py"], required_changed_paths=["a.py"],
            acceptance_criteria=None, file_postconditions=None,
        )
        prepared_payload = repo.events[0][3]

        mutated = make_active_task(**{field: value})
        repo.active = mutated
        current_fp = svc._fingerprint_now("TASK-1", mutated)
        assert current_fp != prepared_payload["task_state_fingerprint"]

    def test_mutating_active_decision_makes_execute_time_fingerprint_stale(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        active = make_active_task()
        decisions_before = [
            {"decision_key": "DEC-1", "text": "use approach A", "rationale": None},
        ]
        repo = FakeRepository(active)
        decisions_svc = FakeDecisions(decisions_before)
        svc = ch.CodexHandoffService(repository=repo, task_decisions=decisions_svc)
        svc.prepare(
            project_id=7, project_root=root, task_key="TASK-1", session_id="s",
            write_scope=["a.py"], required_changed_paths=["a.py"],
            acceptance_criteria=None, file_postconditions=None,
        )
        prepared_payload = repo.events[0][3]

        decisions_svc._active = [
            {"decision_key": "DEC-1", "text": "use approach B", "rationale": None},
        ]
        current_fp = svc._fingerprint_now("TASK-1", active)
        assert current_fp != prepared_payload["task_state_fingerprint"]


class TestOneShotClaim:
    def test_claim_succeeds_once(self):
        repo = FakeRepository(make_active_task())
        conn = ScriptedConnection(
            [
                ("FOR UPDATE", {"id": 1}),
                ("SELECT 1 FROM vres.task_events", None),
                ("INSERT INTO vres.task_events", None),
                ("UPDATE vres.tasks", None),
            ]
        )
        svc = ch.CodexHandoffService(
            repository=repo, task_decisions=FakeDecisions(), connect_fn=lambda: conn
        )
        result = svc._claim_started("TASK-1", "HANDOFF-1")
        assert result.passed

    def test_second_claim_on_same_handoff_key_is_rejected(self):
        repo = FakeRepository(make_active_task())
        conn = ScriptedConnection(
            [
                ("FOR UPDATE", {"id": 1}),
                ("SELECT 1 FROM vres.task_events", {"exists": 1}),
            ]
        )
        svc = ch.CodexHandoffService(
            repository=repo, task_decisions=FakeDecisions(), connect_fn=lambda: conn
        )
        result = svc._claim_started("TASK-1", "HANDOFF-1")
        assert not result.passed

    def test_execute_rejects_when_claim_already_taken(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        active = make_active_task()
        repo = FakeRepository(active)
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        prepared_payload = {
            "handoff_key": "HANDOFF-1", "task_key": "TASK-1", "source_sha": "x",
            "write_scope": ["a.py"], "required_changed_paths": ["a.py"],
            "task_state_fingerprint": "fp", "contract_fingerprint": "cfp",
            "file_postconditions": [], "codex_prompt": "{}",
        }
        svc._locate_prepared_event = lambda pid, hk: {
            "task_id": 1, "task_key": "TASK-1", "payload": prepared_payload,
        }
        svc._claim_started = lambda tk, hk: ch.PreflightResult(
            False, "handoff already claimed/executed/failed"
        )
        with pytest.raises(ch.HandoffError) as exc:
            svc.execute(project_id=7, project_root=root, handoff_key="HANDOFF-1", session_id="s")
        assert exc.value.reason_category == "already_executing"
        assert repo.events == []

    def test_execute_rejects_unknown_handoff_key(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        repo = FakeRepository(make_active_task())
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        svc._locate_prepared_event = lambda pid, hk: None
        with pytest.raises(ch.HandoffError) as exc:
            svc.execute(
                project_id=7, project_root=root, handoff_key="HANDOFF-missing", session_id="s"
            )
        assert exc.value.reason_category == "handoff_not_found"


class TestCliAvailability:
    def _prepared(self, tmp_path, monkeypatch, svc, repo):
        root = _repo_with_commit(tmp_path)
        prep = svc.prepare(
            project_id=7, project_root=root, task_key="TASK-1", session_id="s",
            write_scope=["a.py"], required_changed_paths=["a.py"],
            acceptance_criteria=None, file_postconditions=None,
        )
        prepared_payload = repo.events[0][3]
        svc._locate_prepared_event = lambda pid, hk: {
            "task_id": 1, "task_key": "TASK-1", "payload": prepared_payload
        }
        svc._claim_started = lambda tk, hk: ch.PreflightResult(True, "claimed")
        return root, prep["handoff_key"]

    def test_missing_codex_executable_fails_without_worktree_or_primary_change(
        self, tmp_path, monkeypatch
    ):
        repo = FakeRepository(make_active_task())
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        root, handoff_key = self._prepared(tmp_path, monkeypatch, svc, repo)
        monkeypatch.setattr(ch, "resolve_codex_executable", lambda: None)

        def boom(*a, **k):
            raise AssertionError("worktree must never be created when codex is unavailable")

        monkeypatch.setattr(ch, "create_detached_worktree", boom)
        before = ch.get_git_status(root)
        with pytest.raises(ch.HandoffError) as exc:
            svc.execute(project_id=7, project_root=root, handoff_key=handoff_key, session_id="s")
        assert exc.value.reason_category == "codex_unavailable"
        after = ch.get_git_status(root)
        assert before == after
        failure_events = [e for e in repo.events if e[1] == "CODEX_HANDOFF_FAILED"]
        assert len(failure_events) == 1
        assert failure_events[0][3]["reason_category"] == "codex_unavailable"

    def test_doctor_nonzero_fails_without_worktree(self, tmp_path, monkeypatch):
        repo = FakeRepository(make_active_task())
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        root, handoff_key = self._prepared(tmp_path, monkeypatch, svc, repo)
        monkeypatch.setattr(ch, "resolve_codex_executable", lambda: "/fake/codex")
        real_run_bounded = ch.run_bounded

        def fake_run_bounded(argv, **kwargs):
            if argv[0] == "/fake/codex":
                return ch.ProcessResult(False, "auth error", 1)
            return real_run_bounded(argv, **kwargs)

        monkeypatch.setattr(ch, "run_bounded", fake_run_bounded)

        def boom(*a, **k):
            raise AssertionError("worktree must never be created when doctor check fails")

        monkeypatch.setattr(ch, "create_detached_worktree", boom)
        with pytest.raises(ch.HandoffError) as exc:
            svc.execute(project_id=7, project_root=root, handoff_key=handoff_key, session_id="s")
        assert exc.value.reason_category == "codex_doctor_failed"


class TestStaleSourceOrTask:
    def _prepared(self, tmp_path, svc, repo):
        root = _repo_with_commit(tmp_path)
        prep = svc.prepare(
            project_id=7, project_root=root, task_key="TASK-1", session_id="s",
            write_scope=["a.py"], required_changed_paths=["a.py"],
            acceptance_criteria=None, file_postconditions=None,
        )
        prepared_payload = repo.events[0][3]
        svc._locate_prepared_event = lambda pid, hk: {
            "task_id": 1, "task_key": "TASK-1", "payload": prepared_payload
        }
        svc._claim_started = lambda tk, hk: ch.PreflightResult(True, "claimed")
        return root, prep["handoff_key"]

    def test_source_head_drift_fails_before_codex_invoked(self, tmp_path, monkeypatch):
        repo = FakeRepository(make_active_task())
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        root, handoff_key = self._prepared(tmp_path, svc, repo)
        (root / "b.py").write_text("new file\n")
        commit_all(root, "drift")

        def boom(*a, **k):
            raise AssertionError("codex must never be invoked when source has drifted")

        monkeypatch.setattr(ch, "resolve_codex_executable", boom)
        with pytest.raises(ch.HandoffError) as exc:
            svc.execute(project_id=7, project_root=root, handoff_key=handoff_key, session_id="s")
        assert exc.value.reason_category == "stale_source_sha"

    def test_source_becomes_dirty_fails_before_codex_invoked(self, tmp_path, monkeypatch):
        repo = FakeRepository(make_active_task())
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        root, handoff_key = self._prepared(tmp_path, svc, repo)
        (root / "a.py").write_text("dirty now\n")

        def boom(*a, **k):
            raise AssertionError("codex must never be invoked when primary is dirty")

        monkeypatch.setattr(ch, "resolve_codex_executable", boom)
        with pytest.raises(ch.HandoffError) as exc:
            svc.execute(project_id=7, project_root=root, handoff_key=handoff_key, session_id="s")
        assert exc.value.reason_category == "primary_dirty"

    def test_task_state_drift_fails_before_codex_invoked(self, tmp_path, monkeypatch):
        repo = FakeRepository(make_active_task())
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        root, handoff_key = self._prepared(tmp_path, svc, repo)
        repo.active = make_active_task(next_action="a completely different plan now")

        def boom(*a, **k):
            raise AssertionError("codex must never be invoked when task state has drifted")

        monkeypatch.setattr(ch, "resolve_codex_executable", boom)
        with pytest.raises(ch.HandoffError) as exc:
            svc.execute(project_id=7, project_root=root, handoff_key=handoff_key, session_id="s")
        assert exc.value.reason_category == "stale_task_state"

    def test_session_rebound_to_different_task_fails_before_codex_invoked(
        self, tmp_path, monkeypatch
    ):
        repo = FakeRepository(make_active_task())
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        root, handoff_key = self._prepared(tmp_path, svc, repo)
        repo.active = make_active_task(task_key="TASK-OTHER")

        def boom(*a, **k):
            raise AssertionError("codex must never be invoked when session is rebound elsewhere")

        monkeypatch.setattr(ch, "resolve_codex_executable", boom)
        with pytest.raises(ch.HandoffError) as exc:
            svc.execute(project_id=7, project_root=root, handoff_key=handoff_key, session_id="s")
        assert exc.value.reason_category == "task_mismatch"


# ---------------------------------------------------------------------------
# Full pipeline (fake Codex CLI shim, never a real codex binary)
# ---------------------------------------------------------------------------

_PROBE_RE = re.compile(r"path '([^']+)' containing.*?: '([0-9a-f]{32})'")


class FakeCodexCli:
    """Replaces `ch.run_bounded` module-wide for one test. Delegates every

    non-Codex call (git, via `_run_git`) straight through to the real
    run_bounded so this never breaks any git-status/rev-parse call in the
    module under test -- only calls whose argv[0] is exactly the fake codex
    executable path are intercepted.
    """

    def __init__(self, codex_exe: str, real_run_bounded):
        self.codex_exe = codex_exe
        self._real = real_run_bounded
        self.exec_action = None  # callable(cwd: Path) -> (returncode, jsonl_text)
        self.version_ok = True

    def __call__(self, argv, **kwargs):
        if not argv or argv[0] != self.codex_exe:
            return self._real(argv, **kwargs)
        if len(argv) == 2 and argv[1] == "--version":
            if self.version_ok:
                return ch.ProcessResult(True, "codex-cli 1.2.3 (fake)", 0)
            return ch.ProcessResult(False, "auth error", 1)
        prompt = kwargs.get("prompt", "")
        cwd = kwargs.get("cwd")
        match = _PROBE_RE.search(prompt)
        if match:
            path, nonce_hex = match.group(1), match.group(2)
            # The nonce is the ASCII hex string ITSELF encoded to bytes (see
            # `_run_preflight`'s `nonce = secrets.token_hex(16).encode()`),
            # never the raw bytes you'd get from decoding that hex string.
            (Path(cwd) / path).write_bytes(nonce_hex.encode())
            return ch.ProcessResult(True, json.dumps({"type": "probe.completed"}), 0)
        assert self.exec_action is not None, "test must set exec_action before the real exec call"
        returncode, jsonl_text = self.exec_action(Path(cwd))
        return ch.ProcessResult(returncode == 0, jsonl_text, returncode)


class TestFullPipeline:
    def _svc_and_prep(self, tmp_path, *, write_scope=("a.py",), required=("a.py",)):
        root = _repo_with_commit(tmp_path)
        active = make_active_task()
        repo = FakeRepository(active)
        svc = ch.CodexHandoffService(repository=repo, task_decisions=FakeDecisions())
        prep = svc.prepare(
            project_id=7, project_root=root, task_key="TASK-1", session_id="s",
            write_scope=list(write_scope), required_changed_paths=list(required),
            acceptance_criteria=["a.py behaves correctly"], file_postconditions=None,
        )
        assert prep["ok"]
        prepared_payload = repo.events[0][3]
        svc._locate_prepared_event = lambda pid, hk: {
            "task_id": 1, "task_key": "TASK-1", "payload": prepared_payload
        }
        svc._claim_started = lambda tk, hk: ch.PreflightResult(True, "claimed")
        return root, svc, repo, prep["handoff_key"]

    def test_full_success_promotes_exact_change_and_cleans_up(self, tmp_path, monkeypatch):
        root, svc, repo, handoff_key = self._svc_and_prep(tmp_path)
        real_run_bounded = ch.run_bounded
        cli = FakeCodexCli("/fake/codex", real_run_bounded)

        def do_write(cwd: Path):
            (cwd / "a.py").write_text("print('hello world')\n")
            return 0, json.dumps({"type": "item.completed"})

        cli.exec_action = do_write
        monkeypatch.setattr(ch, "resolve_codex_executable", lambda: "/fake/codex")
        monkeypatch.setattr(ch, "run_bounded", cli)
        db = FakePromotionDB(repo.active)
        svc._connect = db.connect

        result = svc.execute(
            project_id=7, project_root=root, handoff_key=handoff_key, session_id="s"
        )

        assert result["ok"] is True
        assert result["changed_paths"] == ["a.py"]
        assert result["validation_status"] == "pending"
        assert result["task_completed"] is False
        assert (root / "a.py").read_text() == "print('hello world')\n"
        event_types = [e[1] for e in repo.events]
        # Pending is written on the locked promotion connection, never via
        # Repository.update_state (which would open a second connection).
        assert repo.state_updates == []
        assert db.committed_validation == "pending"
        # No real Codex completion/validation authority was ever touched.
        assert "CODEX_HANDOFF_COMPLETED" not in event_types
        # The staged disposable worktree is force-removed after EXECUTED is persisted.
        assert result["worktree_preserved"] is False
        assert result["cleanup_warning"] is None
        assert event_types == ["CODEX_HANDOFF_PREPARED", "CODEX_HANDOFF_EXECUTED"]

    def test_out_of_scope_change_fails_execution_worktree_preserved(self, tmp_path, monkeypatch):
        root, svc, repo, handoff_key = self._svc_and_prep(tmp_path)
        real_run_bounded = ch.run_bounded
        cli = FakeCodexCli("/fake/codex", real_run_bounded)

        def do_write(cwd: Path):
            (cwd / "a.py").write_text("print('hello world')\n")
            (cwd / "unexpected.py").write_text("oops\n")
            return 0, json.dumps({"type": "item.completed"})

        cli.exec_action = do_write
        monkeypatch.setattr(ch, "resolve_codex_executable", lambda: "/fake/codex")
        monkeypatch.setattr(ch, "run_bounded", cli)

        result_error = None
        try:
            svc.execute(project_id=7, project_root=root, handoff_key=handoff_key, session_id="s")
        except ch.HandoffError as exc:
            result_error = exc
        assert result_error is not None
        assert result_error.reason_category == "execution_scope_violation"
        assert result_error.worktree_preserved is True
        assert (root / "a.py").read_text() == "print('hello')\n"  # primary untouched
        failure_events = [e for e in repo.events if e[1] == "CODEX_HANDOFF_FAILED"]
        assert len(failure_events) == 1

    def test_malformed_jsonl_fails_execution(self, tmp_path, monkeypatch):
        root, svc, repo, handoff_key = self._svc_and_prep(tmp_path)
        real_run_bounded = ch.run_bounded
        cli = FakeCodexCli("/fake/codex", real_run_bounded)

        def do_write(cwd: Path):
            (cwd / "a.py").write_text("print('hello world')\n")
            return 0, "not valid json\n"

        cli.exec_action = do_write
        monkeypatch.setattr(ch, "resolve_codex_executable", lambda: "/fake/codex")
        monkeypatch.setattr(ch, "run_bounded", cli)

        with pytest.raises(ch.HandoffError) as exc:
            svc.execute(project_id=7, project_root=root, handoff_key=handoff_key, session_id="s")
        assert exc.value.reason_category == "execution_jsonl_invalid"
        assert (root / "a.py").read_text() == "print('hello')\n"

    def test_nonzero_exit_fails_execution(self, tmp_path, monkeypatch):
        root, svc, repo, handoff_key = self._svc_and_prep(tmp_path)
        real_run_bounded = ch.run_bounded
        cli = FakeCodexCli("/fake/codex", real_run_bounded)
        cli.exec_action = lambda cwd: (1, json.dumps({"type": "error"}))
        monkeypatch.setattr(ch, "resolve_codex_executable", lambda: "/fake/codex")
        monkeypatch.setattr(ch, "run_bounded", cli)

        with pytest.raises(ch.HandoffError) as exc:
            svc.execute(project_id=7, project_root=root, handoff_key=handoff_key, session_id="s")
        assert exc.value.reason_category == "execution_nonzero_exit"

    def test_required_write_never_happening_fails_execution(self, tmp_path, monkeypatch):
        root, svc, repo, handoff_key = self._svc_and_prep(tmp_path)
        real_run_bounded = ch.run_bounded
        cli = FakeCodexCli("/fake/codex", real_run_bounded)
        cli.exec_action = lambda cwd: (0, json.dumps({"type": "item.completed"}))  # no file touched
        monkeypatch.setattr(ch, "resolve_codex_executable", lambda: "/fake/codex")
        monkeypatch.setattr(ch, "run_bounded", cli)

        with pytest.raises(ch.HandoffError) as exc:
            svc.execute(project_id=7, project_root=root, handoff_key=handoff_key, session_id="s")
        # The required write never happened, so the scope check (required_changed_paths
        # not observed) fails before any postcondition is even evaluated.
        assert exc.value.reason_category == "execution_scope_violation"
        assert exc.value.worktree_preserved is True

    def test_prompt_delivered_stdin_only_never_in_argv(self, tmp_path, monkeypatch):
        root, svc, repo, handoff_key = self._svc_and_prep(tmp_path)
        real_run_bounded = ch.run_bounded
        captured_calls = []

        cli = FakeCodexCli("/fake/codex", real_run_bounded)
        cli.exec_action = lambda cwd: (0, json.dumps({"type": "item.completed"}))

        def dispatch(argv, **kwargs):
            captured_calls.append((list(argv), kwargs.get("prompt", "")))
            return cli(argv, **kwargs)

        monkeypatch.setattr(ch, "resolve_codex_executable", lambda: "/fake/codex")
        monkeypatch.setattr(ch, "run_bounded", dispatch)

        # Required write still never happens (no promotion wiring here); only
        # argv/prompt delivery is under test.
        with pytest.raises(ch.HandoffError):
            svc.execute(project_id=7, project_root=root, handoff_key=handoff_key, session_id="s")

        codex_calls = [
            c for c in captured_calls if c[0] and c[0][0] == "/fake/codex" and len(c[0]) > 2
        ]
        assert codex_calls, "expected at least one real Codex exec invocation"
        for argv, _prompt in codex_calls:
            assert argv == [
                "/fake/codex", "exec", "--ephemeral", "--json", "--sandbox",
                "workspace-write", "--ignore-user-config", "-",
            ]
            assert all(
                "hello world" not in part and "Optimize the hot loop" not in part for part in argv
            )

    def test_apply_check_failure_preserves_worktree_and_does_not_apply(self, tmp_path, monkeypatch):
        root, svc, repo, handoff_key = self._svc_and_prep(tmp_path)
        real_run_bounded = ch.run_bounded
        cli = FakeCodexCli("/fake/codex", real_run_bounded)

        def do_write(cwd: Path):
            (cwd / "a.py").write_text("print('hello world')\n")
            return 0, json.dumps({"type": "item.completed"})

        cli.exec_action = do_write
        monkeypatch.setattr(ch, "resolve_codex_executable", lambda: "/fake/codex")
        monkeypatch.setattr(ch, "run_bounded", cli)
        db = FakePromotionDB(repo.active)
        svc._connect = db.connect

        # Make the primary workspace diverge from what the patch expects,
        # so `git apply --check` fails inside the locked promotion window.
        monkeypatch.setattr(
            ch, "apply_check_patch",
            lambda *a, **k: ch.ProcessResult(False, "patch does not apply", 1),
        )

        with pytest.raises(ch.HandoffError) as exc:
            svc.execute(project_id=7, project_root=root, handoff_key=handoff_key, session_id="s")
        assert exc.value.reason_category == "promotion_apply_check_failed"
        assert exc.value.worktree_preserved is True
        assert (root / "a.py").read_text() == "print('hello')\n"
        # validation_status was set (and committed, never rolled back), even
        # though promotion failed -- on the locked connection, not update_state.
        assert db.committed_validation == "pending"
        assert repo.state_updates == []


# ---------------------------------------------------------------------------
# Remediation regression (#143 Slice 2): promotion self-deadlock / pending
# ---------------------------------------------------------------------------


def _promotion_setup(tmp_path, *, prior_validation="failed", decisions=None):
    """Real git primary + real patch; FakePromotionDB for the locked window."""
    root = _repo_with_commit(tmp_path)
    sha = run_git(root, "rev-parse", "HEAD").stdout.strip()
    worktree = tmp_path / "wt"
    ch.create_detached_worktree(root, worktree, sha)
    (worktree / "a.py").write_text("print('hello world')\n")
    patch = ch.generate_patch(worktree)
    assert patch.ok
    patch_file = tmp_path / "promotion.patch"
    patch_file.write_bytes(patch.patch_bytes)

    active = make_active_task(validation_status=prior_validation)
    decisions = decisions or [{"decision_key": "DEC-1", "text": "use A", "rationale": None}]
    repo = FakeRepository(active)
    decision_svc = FakeDecisions(decisions)
    db = FakePromotionDB(active, decisions)
    svc = ch.CodexHandoffService(
        repository=repo, task_decisions=decision_svc, connect_fn=db.connect
    )
    fields = {f: getattr(active, f) for f in ch.FINGERPRINT_FIELDS}
    kwargs = dict(
        project_id=7,
        project_root=root,
        task_key="TASK-1",
        session_id="s",
        prepared_payload={
            "source_sha": sha,
            "task_state_fingerprint": ch.compute_task_state_fingerprint(fields, decisions),
        },
        disposable_changed_paths=frozenset({"a.py"}),
        patch_file=patch_file,
        postconditions=(),
    )
    return SimpleNamespace(root=root, repo=repo, decisions=decision_svc, db=db, svc=svc,
                           kwargs=kwargs)


def _forbid_service_calls_while_locked(env, calls: list[str]):
    """Spy: record every Repository/TaskDecisionService call and whether a lock was held."""

    def spy(name, original):
        def wrapper(*args, **kwargs):
            calls.append(f"{name}(lock_held={env.db.lock_owner is not None})")
            return original(*args, **kwargs)

        return wrapper

    env.repo.update_state = spy("update_state", env.repo.update_state)
    env.repo.active_task = spy("active_task", env.repo.active_task)
    env.repo.record_event = spy("record_event", env.repo.record_event)
    env.decisions.list_active = spy("list_active", env.decisions.list_active)


class TestPromotionTransactionSafety:
    def test_promote_never_calls_update_state_or_other_services_while_locked(self, tmp_path):
        env = _promotion_setup(tmp_path)
        calls: list[str] = []
        _forbid_service_calls_while_locked(env, calls)
        env.svc._promote(**env.kwargs)
        assert calls == []  # no Repository/TaskDecisionService call at all during promotion
        assert env.repo.state_updates == []

    def test_promote_uses_exactly_one_connection_for_locked_window(self, tmp_path):
        env = _promotion_setup(tmp_path)
        env.svc._promote(**env.kwargs)
        assert len(env.db.connections) == 1
        assert env.db.opened_while_lock_held == [False]
        assert {i for i, _ in env.db.log} == {0}
        assert env.db.lock_owner is None  # released at commit

    def test_old_nested_update_state_pattern_is_detected_as_self_deadlock(self, tmp_path):
        """Negative control: the fake really does catch the pre-fix pattern."""
        env = _promotion_setup(tmp_path)
        conn_a = env.db.connect()
        with conn_a, conn_a.transaction():
            conn_a.execute("SELECT id FROM vres.tasks WHERE task_key=%s FOR UPDATE", ("TASK-1",))
            conn_c = env.db.connect()
            with pytest.raises(AssertionError, match="self-deadlock"), conn_c:
                conn_c.execute("UPDATE vres.tasks SET updated_at=now() WHERE id=%s", (1,))

    def test_pending_written_on_same_locked_connection_before_apply(self, tmp_path, monkeypatch):
        env = _promotion_setup(tmp_path, prior_validation="failed")
        seen = {}
        real_check, real_apply = ch.apply_check_patch, ch.apply_patch

        def check(*a, **k):
            conn = env.db.connections[0]
            seen["check"] = (conn.view(), env.db.committed_validation, env.db.lock_owner is conn)
            return real_check(*a, **k)

        def apply(*a, **k):
            conn = env.db.connections[0]
            seen["apply"] = (conn.view(), env.db.committed_validation, env.db.lock_owner is conn)
            return real_apply(*a, **k)

        monkeypatch.setattr(ch, "apply_check_patch", check)
        monkeypatch.setattr(ch, "apply_patch", apply)
        env.svc._promote(**env.kwargs)

        # Staged 'pending' visible on the lock-holding connection, not yet committed.
        assert seen["check"] == ("pending", "failed", True)
        assert seen["apply"] == ("pending", "failed", True)
        sql = env.db.sql(0)
        lock_idx = next(i for i, s in enumerate(sql) if "WHERE task_key" in s)
        state_lock_idx = next(i for i, s in enumerate(sql) if "FOR UPDATE OF s" in s)
        pending_idx = next(
            i for i, s in enumerate(sql) if s.startswith("UPDATE vres.task_state")
        )
        assert lock_idx < state_lock_idx < pending_idx
        assert "validation_status='pending'" in sql[pending_idx]
        assert env.db.committed_validation == "pending"

    def test_apply_check_failure_before_primary_touch(self, tmp_path, monkeypatch):
        # Pinned ordering: pending is written (and committed) BEFORE apply_check,
        # which is read-only on the primary; apply_patch is never reached.
        env = _promotion_setup(tmp_path, prior_validation="failed")
        monkeypatch.setattr(
            ch, "apply_check_patch", lambda *a, **k: ch.ProcessResult(False, "no", 1)
        )

        def boom(*a, **k):
            raise AssertionError("apply_patch must not run after a failed --check")

        monkeypatch.setattr(ch, "apply_patch", boom)
        with pytest.raises(ch.HandoffError) as exc:
            env.svc._promote(**env.kwargs)
        assert exc.value.reason_category == "promotion_apply_check_failed"
        assert (env.root / "a.py").read_text() == "print('hello')\n"
        assert env.db.committed_validation == "pending"
        assert len(env.db.connections) == 1

    def test_successful_apply_leaves_pending(self, tmp_path):
        env = _promotion_setup(tmp_path, prior_validation="failed")
        env.svc._promote(**env.kwargs)
        assert (env.root / "a.py").read_text() == "print('hello world')\n"
        assert env.db.committed_validation == "pending"

    @pytest.mark.parametrize("prior", ["failed", "not_required"])
    def test_post_apply_changed_path_mismatch_keeps_pending(self, tmp_path, prior):
        env = _promotion_setup(tmp_path, prior_validation=prior)
        env.kwargs["disposable_changed_paths"] = frozenset({"a.py", "other.py"})
        with pytest.raises(ch.HandoffError) as exc:
            env.svc._promote(**env.kwargs)
        assert exc.value.reason_category == "promotion_changed_paths_mismatch"
        assert (env.root / "a.py").read_text() == "print('hello world')\n"  # primary touched
        assert env.db.committed_validation == "pending"
        assert len(env.db.connections) == 1  # committed on the locked connection itself

    @pytest.mark.parametrize("prior", ["failed", "not_required"])
    def test_post_apply_postcondition_failure_keeps_pending(self, tmp_path, prior):
        env = _promotion_setup(tmp_path, prior_validation=prior)
        env.kwargs["postconditions"] = (ch.FilePostcondition(kind="file_absent", path="a.py"),)
        with pytest.raises(ch.HandoffError) as exc:
            env.svc._promote(**env.kwargs)
        assert exc.value.reason_category == "promotion_postcondition_failed"
        assert env.db.committed_validation == "pending"

    @pytest.mark.parametrize("prior", ["failed", "not_required", "pending"])
    def test_unexpected_exception_after_primary_touch_repairs_pending(
        self, tmp_path, monkeypatch, prior
    ):
        env = _promotion_setup(tmp_path, prior_validation=prior)

        def infra_failure(*a, **k):
            raise OSError("simulated infrastructure failure after git apply")

        monkeypatch.setattr(ch, "evaluate_file_postconditions", infra_failure)
        with pytest.raises(ch.HandoffError) as exc:
            env.svc._promote(**env.kwargs)
        assert exc.value.reason_category == "promotion_unexpected_error"
        assert "may have been modified" in str(exc.value)
        assert isinstance(exc.value.__cause__, OSError)
        assert (env.root / "a.py").read_text() == "print('hello world')\n"
        # The locked transaction rolled back; the fresh repair transaction ran
        # only after the first connection closed and released its locks.
        assert env.db.committed_validation == "pending"
        assert len(env.db.connections) == 2
        assert env.db.opened_while_lock_held == [False, False]
        assert env.db.connections[0].closed
        repair_sql = env.db.sql(1)
        assert repair_sql[0].startswith("SET LOCAL lock_timeout")
        assert any("validation_status='pending'" in s for s in repair_sql)

    def test_unexpected_failure_at_commit_after_touch_repairs_pending(self, tmp_path):
        env = _promotion_setup(tmp_path, prior_validation="not_required")

        class CommitFailure(FakeTxnConnection):
            @contextmanager
            def transaction(self):
                with FakeTxnConnection.transaction(self):
                    yield
                    raise RuntimeError("simulated connection loss at COMMIT")

        first = CommitFailure(env.db, 0)
        original_connect = env.db.connect

        def connect():
            if not env.db.connections:
                env.db.opened_while_lock_held.append(False)
                env.db.connections.append(first)
                return first
            return original_connect()

        env.svc._connect = connect
        with pytest.raises(ch.HandoffError) as exc:
            env.svc._promote(**env.kwargs)
        assert exc.value.reason_category == "promotion_unexpected_error"
        assert env.db.committed_validation == "pending"
        assert len(env.db.connections) == 2

    def test_failure_before_pending_point_neither_writes_nor_repairs(self, tmp_path):
        env = _promotion_setup(tmp_path, prior_validation="failed")
        env.db.fail_sql["UPDATE vres.task_state"] = RuntimeError("simulated DB error")
        with pytest.raises(RuntimeError, match="simulated DB error"):
            env.svc._promote(**env.kwargs)
        assert env.db.committed_validation == "failed"
        assert len(env.db.connections) == 1
        assert (env.root / "a.py").read_text() == "print('hello')\n"

    def test_prior_pass_is_refused_before_any_write_or_primary_touch(self, tmp_path, monkeypatch):
        # Migration 028 forbids passed -> pending outside validation_invalidate;
        # promotion refuses cleanly instead of self-invalidating a PASS.
        env = _promotion_setup(tmp_path, prior_validation="passed")

        def boom(*a, **k):
            raise AssertionError("no git apply may run against a fresh PASS")

        monkeypatch.setattr(ch, "apply_check_patch", boom)
        monkeypatch.setattr(ch, "apply_patch", boom)
        with pytest.raises(ch.HandoffError) as exc:
            env.svc._promote(**env.kwargs)
        assert exc.value.reason_category == "promotion_validation_passed_protected"
        assert env.db.committed_validation == "passed"  # truthful: primary never touched
        assert (env.root / "a.py").read_text() == "print('hello')\n"
        assert not any(s.startswith("UPDATE") for s in env.db.sql())

    @pytest.mark.parametrize("failure", ["logical", "unexpected"])
    def test_failure_after_touch_never_restores_prior_value(self, tmp_path, monkeypatch, failure):
        # 'not_required' is the PASS-shaped (review-waived) value a rollback
        # could otherwise resurrect; 'passed' itself cannot reach this point.
        env = _promotion_setup(tmp_path, prior_validation="not_required")
        if failure == "logical":
            env.kwargs["disposable_changed_paths"] = frozenset({"elsewhere.py"})
        else:
            monkeypatch.setattr(
                ch, "evaluate_file_postconditions",
                lambda *a, **k: (_ for _ in ()).throw(RuntimeError("infra")),
            )
        with pytest.raises(ch.HandoffError):
            env.svc._promote(**env.kwargs)
        assert (env.root / "a.py").read_text() == "print('hello world')\n"
        assert env.db.committed_validation == "pending"
        assert env.db.committed_validation not in {"not_required", "passed"}

    def test_repair_failure_is_surfaced_not_swallowed(self, tmp_path, monkeypatch):
        env = _promotion_setup(tmp_path, prior_validation="failed")
        monkeypatch.setattr(
            ch, "evaluate_file_postconditions",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("infra")),
        )
        env.db.fail_sql["SET LOCAL lock_timeout"] = RuntimeError("repair connection lost")
        with pytest.raises(ch.HandoffError) as exc:
            env.svc._promote(**env.kwargs)
        assert exc.value.reason_category == "promotion_pending_repair_failed"

    def test_full_success_never_completes_task_or_writes_passed(self, tmp_path):
        env = _promotion_setup(tmp_path)
        env.svc._promote(**env.kwargs)
        sql = " | ".join(env.db.sql())
        assert "'passed'" not in sql
        assert "status='completed'" not in sql and "SET status" not in sql
        assert env.repo.events == []
        assert "validation_status='passed'" not in Path(ch.__file__).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Remediation regression (#143 Slice 2): success-path worktree cleanup
# ---------------------------------------------------------------------------


def _pipeline(tmp_path, monkeypatch, exec_action=None):
    root = _repo_with_commit(tmp_path)
    active = make_active_task()
    repo = FakeRepository(active)
    db = FakePromotionDB(active)
    svc = ch.CodexHandoffService(
        repository=repo, task_decisions=FakeDecisions(), connect_fn=db.connect
    )
    prep = svc.prepare(
        project_id=7, project_root=root, task_key="TASK-1", session_id="s",
        write_scope=["a.py"], required_changed_paths=["a.py"],
        acceptance_criteria=None, file_postconditions=None,
    )
    prepared_payload = repo.events[0][3]
    svc._locate_prepared_event = lambda pid, hk: {
        "task_id": 1, "task_key": "TASK-1", "payload": prepared_payload
    }
    svc._claim_started = lambda tk, hk: ch.PreflightResult(True, "claimed")

    def default_write(cwd: Path):
        (cwd / "a.py").write_text("print('hello world')\n")
        return 0, json.dumps({"type": "item.completed"})

    cli = FakeCodexCli("/fake/codex", ch.run_bounded)
    cli.exec_action = exec_action or default_write
    monkeypatch.setattr(ch, "resolve_codex_executable", lambda: "/fake/codex")
    monkeypatch.setattr(ch, "run_bounded", cli)

    created: list[Path] = []
    original_make = svc._make_worktree_path

    def make_path():
        created.append(original_make())
        return created[-1]

    svc._make_worktree_path = make_path
    return SimpleNamespace(root=root, repo=repo, db=db, svc=svc, created=created,
                           handoff_key=prep["handoff_key"])


def _registered_worktrees(root: Path) -> set[Path]:
    out = run_git(root, "worktree", "list", "--porcelain").stdout
    return {
        ch._path_key(Path(line[len("worktree "):]))
        for line in out.splitlines() if line.startswith("worktree ")
    }


@pytest.fixture
def discard_worktrees():
    """Test-only hygiene: force-remove ONLY worktrees this test itself created."""
    owned: list[tuple[Path, Path]] = []
    yield owned
    for root, path in owned:
        if path.exists():
            subprocess.run(
                ["git", "-C", str(root), "worktree", "remove", "--force", str(path)],
                stdin=subprocess.DEVNULL, capture_output=True, timeout=30, check=False,
            )


class TestSuccessWorktreeCleanup:
    def test_unforced_remove_is_rejected_for_staged_success_worktree(self, tmp_path):
        """'Before' proof of the validator's finding: git refuses the unforced removal."""
        root = _repo_with_commit(tmp_path)
        sha = run_git(root, "rev-parse", "HEAD").stdout.strip()
        worktree = tmp_path / "wt"
        ch.create_detached_worktree(root, worktree, sha)
        (worktree / "a.py").write_text("print('hello world')\n")
        assert ch.generate_patch(worktree).ok  # runs `git add -A`
        with pytest.raises(ch.WorktreeError):
            ch.remove_worktree(root, worktree)
        assert worktree.exists()

    def test_success_force_removes_staged_worktree_end_to_end(
        self, tmp_path, monkeypatch, discard_worktrees
    ):
        env = _pipeline(tmp_path, monkeypatch)
        result = env.svc.execute(
            project_id=7, project_root=env.root, handoff_key=env.handoff_key, session_id="s"
        )
        (path,) = env.created
        discard_worktrees.append((env.root, path))
        assert result["ok"] is True
        assert result["worktree_preserved"] is False
        assert result["cleanup_warning"] is None
        assert not path.exists()
        assert ch._path_key(path) not in _registered_worktrees(env.root)
        assert [e[1] for e in env.repo.events] == [
            "CODEX_HANDOFF_PREPARED", "CODEX_HANDOFF_EXECUTED",
        ]

    def test_forced_cleanup_runs_only_after_executed_evidence(
        self, tmp_path, monkeypatch, discard_worktrees
    ):
        env = _pipeline(tmp_path, monkeypatch)
        order: list[str] = []
        real_record = env.repo.record_event
        real_force = ch._force_remove_worktree_after_success

        def record(task_key, event_type, *a, **k):
            order.append(event_type)
            return real_record(task_key, event_type, *a, **k)

        def force(*a, **k):
            order.append("FORCE_REMOVE")
            assert k["executed_evidence_persisted"] is True
            assert k["promotion_succeeded"] is True
            return real_force(*a, **k)

        env.repo.record_event = record
        monkeypatch.setattr(ch, "_force_remove_worktree_after_success", force)
        env.svc.execute(
            project_id=7, project_root=env.root, handoff_key=env.handoff_key, session_id="s"
        )
        discard_worktrees.append((env.root, env.created[0]))
        assert order == ["CODEX_HANDOFF_EXECUTED", "FORCE_REMOVE"]

    def test_no_forced_cleanup_if_executed_evidence_persistence_fails(
        self, tmp_path, monkeypatch, discard_worktrees
    ):
        env = _pipeline(tmp_path, monkeypatch)
        real_record = env.repo.record_event

        def record(task_key, event_type, *a, **k):
            if event_type == "CODEX_HANDOFF_EXECUTED":
                raise RuntimeError("simulated DB outage persisting EXECUTED")
            return real_record(task_key, event_type, *a, **k)

        def force(*a, **k):
            raise AssertionError("forced cleanup reached before EXECUTED was persisted")

        env.repo.record_event = record
        monkeypatch.setattr(ch, "_force_remove_worktree_after_success", force)
        with pytest.raises(RuntimeError, match="simulated DB outage"):
            env.svc.execute(
                project_id=7, project_root=env.root, handoff_key=env.handoff_key, session_id="s"
            )
        discard_worktrees.append((env.root, env.created[0]))
        assert env.created[0].exists()

    @pytest.mark.parametrize(
        "category",
        ["preflight", "execution", "scope", "promotion_check", "promotion_postcondition"],
    )
    def test_no_forced_cleanup_on_any_failure_path(
        self, tmp_path, monkeypatch, discard_worktrees, category
    ):
        exec_action = None
        if category == "execution":
            def exec_action(cwd):
                return 1, json.dumps({"type": "error"})
        elif category == "scope":
            def exec_action(cwd):
                (cwd / "a.py").write_text("x\n")
                (cwd / "unexpected.py").write_text("oops\n")
                return 0, json.dumps({"type": "item.completed"})
        env = _pipeline(tmp_path, monkeypatch, exec_action)
        if category == "preflight":
            env.svc._run_preflight = lambda *a, **k: (False, "forced preflight failure")
        elif category == "promotion_check":
            monkeypatch.setattr(
                ch, "apply_check_patch", lambda *a, **k: ch.ProcessResult(False, "no", 1)
            )
        elif category == "promotion_postcondition":
            real_apply_and_verify = ch._apply_and_verify_primary

            def apply_then_fail(*a, **k):
                assert real_apply_and_verify(*a, **k) is None  # primary really touched
                return ch.HandoffError("promotion_postcondition_failed", "forced")

            monkeypatch.setattr(ch, "_apply_and_verify_primary", apply_then_fail)

        def force(*a, **k):
            raise AssertionError("forced cleanup must never run on a failure path")

        monkeypatch.setattr(ch, "_force_remove_worktree_after_success", force)
        monkeypatch.setattr(ch, "remove_worktree", force)
        with pytest.raises(ch.HandoffError) as exc:
            env.svc.execute(
                project_id=7, project_root=env.root, handoff_key=env.handoff_key, session_id="s"
            )
        (path,) = env.created
        discard_worktrees.append((env.root, path))
        assert exc.value.worktree_preserved is True
        assert path.exists()
        assert ch._path_key(path) in _registered_worktrees(env.root)
        assert "CODEX_HANDOFF_EXECUTED" not in [e[1] for e in env.repo.events]

    @pytest.mark.parametrize("error", [ch.WorktreeError("git refused"), OSError("fs locked")])
    def test_cleanup_failure_keeps_success_and_records_warning(
        self, tmp_path, monkeypatch, discard_worktrees, error
    ):
        env = _pipeline(tmp_path, monkeypatch)

        def force(*a, **k):
            raise error

        monkeypatch.setattr(ch, "_force_remove_worktree_after_success", force)
        result = env.svc.execute(
            project_id=7, project_root=env.root, handoff_key=env.handoff_key, session_id="s"
        )
        (path,) = env.created
        discard_worktrees.append((env.root, path))
        assert result["ok"] is True
        assert result["worktree_preserved"] is True
        assert str(error) in result["cleanup_warning"]
        assert [e[1] for e in env.repo.events] == [
            "CODEX_HANDOFF_PREPARED", "CODEX_HANDOFF_EXECUTED", "CODEX_HANDOFF_CLEANUP_FAILED",
        ]
        assert (env.root / "a.py").read_text() == "print('hello world')\n"
        assert path.exists()


def _staged_vres_worktree(tmp_path, discard_worktrees) -> tuple[Path, Path]:
    root = _repo_with_commit(tmp_path)
    sha = run_git(root, "rev-parse", "HEAD").stdout.strip()
    path = ch.CodexHandoffService._make_worktree_path()
    ch.create_detached_worktree(root, path, sha)
    discard_worktrees.append((root, path))
    (path / "a.py").write_text("changed\n")
    assert ch.generate_patch(path).ok
    return root, path


class TestForcedCleanupPreconditions:
    def _call(self, root, path, **overrides):
        kwargs = dict(
            created_worktree_path=path, promotion_succeeded=True, executed_evidence_persisted=True
        )
        kwargs.update(overrides)
        ch._force_remove_worktree_after_success(root, path, **kwargs)

    def test_primary_project_root_is_rejected(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        with pytest.raises(ch.WorktreeError, match="primary project root"):
            self._call(root, root, created_worktree_path=root)
        assert (root / "a.py").read_text() == "print('hello')\n"
        assert (root / ".git").exists()

    def test_path_outside_vres_worktree_area_is_rejected(self, tmp_path, discard_worktrees):
        root = _repo_with_commit(tmp_path)
        sha = run_git(root, "rev-parse", "HEAD").stdout.strip()
        outside = tmp_path / "handoff-outside"
        ch.create_detached_worktree(root, outside, sha)  # registered, but not Vres-owned area
        discard_worktrees.append((root, outside))
        with pytest.raises(ch.WorktreeError, match="outside the Vres-owned"):
            self._call(root, outside)
        assert outside.exists()

    def test_path_not_created_by_this_handoff_is_rejected(self, tmp_path, discard_worktrees):
        root, path = _staged_vres_worktree(tmp_path, discard_worktrees)
        other = ch.codex_worktree_base() / "handoff-someone-else"
        with pytest.raises(ch.WorktreeError, match="not this handoff's own"):
            self._call(root, path, created_worktree_path=other)
        assert path.exists()

    def test_unregistered_directory_in_vres_area_is_rejected(self, tmp_path):
        root = _repo_with_commit(tmp_path)
        stray = ch.CodexHandoffService._make_worktree_path()
        stray.mkdir()
        try:
            with pytest.raises(ch.WorktreeError, match="not a registered git worktree"):
                self._call(root, stray)
            assert stray.exists()
        finally:
            stray.rmdir()

    @pytest.mark.parametrize(
        "flag", ["promotion_succeeded", "executed_evidence_persisted"]
    )
    def test_missing_success_evidence_is_rejected(self, tmp_path, discard_worktrees, flag):
        root, path = _staged_vres_worktree(tmp_path, discard_worktrees)
        with pytest.raises(ch.WorktreeError, match="refused"):
            self._call(root, path, **{flag: False})
        assert path.exists()

    def test_all_preconditions_met_removes_staged_worktree(self, tmp_path, discard_worktrees):
        root, path = _staged_vres_worktree(tmp_path, discard_worktrees)
        self._call(root, path)
        assert not path.exists()
        assert ch._path_key(path) not in _registered_worktrees(root)
