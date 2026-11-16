"""Opt-in single-user Personal Day desktop workspace (SOURCE ONLY, NOT ACTIVATED).

A Tkinter view of the ORIGINAL #165 task/session/result/history owners. It never
starts from an installer, profile hook or background process. All project/result
paths must be entered explicitly, and no DB, credentials, native Claude, model,
network or protected Fable/experience authority is contacted or granted.
Do not launch on the owner's Windows installation without separate consent.
"""
from __future__ import annotations

import hashlib
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

if not __package__:
    sys.path.insert(0, str(Path(__file__).absolute().parent.parent))
    from vres_os import personal_work_session as owner
    from vres_os import personal_portable_desk as portable
    from vres_os import personal_task_lifecycle as lifecycle
    from vres_os import personal_day_navigation as navigation
else:
    from . import personal_work_session as owner
    from . import personal_portable_desk as portable
    from . import personal_task_lifecycle as lifecycle
    from . import personal_day_navigation as navigation


class DesktopRefused(ValueError):
    """A UI selection is missing, mixed, stale or outside the original scope."""



# Only transient Desktop input is cleared; none of these are an owner store.
_HISTORY_CONTEXT_FIELDS = (
    "project", "key", "result", "acceptance_path", "acceptance_sha",
    "catalog_root", "catalog_namespace", "catalog_source", "catalog_sha",
    "catalog_revision", "synthetic_file", "synthetic_sha",
)


def guided_action_plan(
    kind: str | None, stage: str | None = None, *,
    focused: bool = False, decision_ready: bool = False,
    history_clear: bool = False,
) -> dict:
    """Presentation ONLY; all original owners still recheck/authorize actions.

    No background reads or automatic task choice; a disabled/enabled button
    never becomes evidence, consent or write authority.
    """
    enabled = {name: False for name in (
        "focus", "briefing", "decision", "complete", "reopen", "replay", "clear_history")}
    if kind == "ACTIVE_TASK":
        enabled["focus"] = True
        if not focused:
            next_step = "Step 2/4: Focus the explicitly selected task and project context."
        elif stage == "TASK_SELECTED_NO_PROJECT":
            next_step = "Step 2/4: Enter an explicit project root and original key; focus again."
        elif stage == "PROJECT_SELECTED_NO_RESULT":
            next_step = "Step 2/4: Enter the exact result file when ready; focus again."
        elif stage == "RESULT_REVIEW_READY_SEPARATE_DECISION":
            enabled["briefing"] = True
            enabled["decision"] = True
            enabled["complete"] = bool(decision_ready)
            if decision_ready:
                next_step = ("Step 4/4: Give separate, explicit completion consent after "
                             "reviewing the exact read-only decision. No result-quality proof.")
            else:
                next_step = ("Step 3/4: Review the exact read-only completion decision "
                             "before requesting separate completion consent.")
        else:
            next_step = "Review the original selected journey; no write is authorized."
    elif kind == "SAVED_COMPLETED_RESULT":
        enabled["clear_history"] = not history_clear
        enabled["focus"] = bool(history_clear)
        enabled["reopen"] = bool(history_clear)
        enabled["replay"] = bool(history_clear)
        if history_clear:
            next_step = ("Historical only: inspect, separately approve Reopen, then "
                         "separately approve saved-byte verification. No auto-replay.")
        else:
            next_step = ("Historical only: explicitly clear active UI inputs before "
                         "inspecting, reopening or checking old saved bytes.")
    else:
        next_step = "Step 1/4: Load the exact scratch desk and select one offered task."
    return {"enabled": enabled, "next_step": next_step}


def checked_context(project_root: str, project_key: str, result_file: str) -> dict:
    """Do not silently select a project or open a result file."""
    root, key, result = (v.strip() for v in (project_root, project_key, result_file))
    if bool(root) != bool(key) or (result and not root):
        raise DesktopRefused("Choose an exact project root/key together with any result.")
    return {"project_root": root or None, "project_key": key or None,
            "result_file": result or None}


def checked_day(packet: dict, *, selected: bool) -> dict:
    """Accept only the original read-only, nonauthoritative day contract."""
    if (type(packet) is not dict
            or packet.get("status") != "READ_ONLY_ONE_ORIGINAL_CHAIRMAN_PERSONAL_DAY"
            or packet.get("schema") != owner.PERSONAL_DAY_SCHEMA
            or packet.get("task_selection_or_completion_performed") is not False
            or packet.get("native_claude_or_hooks_executed") is not False
            or packet.get("database_contacted") is not False
            or packet.get("original_166_168_activation_or_rollback_performed") is not False
            or packet.get("original_167_live_catalog_freshness_verified") is not False
            or packet.get("original_174_protected_fable_granted") is not False
            or packet.get("original_176_live_memory_eligibility_or_promotion") is not False
            or packet.get("writes_performed") is not False
            or packet.get("task_selected_explicitly") is not selected):
        raise DesktopRefused("Original read-only day contract not verified.")
    # Original renderer validates offered identities and the selected journey
    # before any content is allowed into the UI.
    owner.render_personal_day(packet)
    return packet


def _selected_note_input(view) -> tuple[str | None, str | None]:
    """Exactly one explicit source: ordinary file OR transient inline editor.

    Editor bytes are not placed in a temporary file, profile or new store.
    Approval/owner checks must compare a fresh digest of these same bytes.
    """
    note_file = view.values['note'].get().strip()
    editor = getattr(view, 'inline_editor', None)
    inline = editor.get('1.0', 'end-1c') if editor is not None else ''
    if type(inline) is not str or bool(note_file) == bool(inline.strip()):
        raise DesktopRefused('Choose exactly ONE external note or inline Markdown draft.')
    return (note_file or None, inline if inline.strip() else None)


def _clear_inline_editor(view) -> None:
    editor = getattr(view, 'inline_editor', None)
    if editor is not None:
        editor.delete('1.0', tk.END)
        editor.edit_modified(False)


def _source_markdown(root: Path, note_file: str | None,
                     note_markdown: str | None) -> str:
    if (note_file is None) == (note_markdown is None):
        raise DesktopRefused('Choose exactly one original Markdown source.')
    if note_markdown is not None:
        if type(note_markdown) is not str:
            raise DesktopRefused('Inline draft must be exact Markdown text.')
        return note_markdown
    selected_note = Path(note_file)
    if portable.project_draft._under(selected_note, root):
        raise DesktopRefused('Input note must remain outside the existing scratch desk.')
    return portable.project_draft._manual_markdown(note_file)


def preview_existing_desk_task(desk_path: str, task: str,
                               note_file: str | None, *,
                               note_markdown: str | None = None) -> dict:
    """Bounded, read-only ORIGINAL scratch preview; never writes or selects.

    The original #165/#portable owners perform the actual approved write.
    A preview digest is a byte claim, not task quality or user identity proof.
    """
    root = portable._desk(desk_path, must_exist=True)
    target = portable._owned_task(root, task)
    labels = portable._existing_tasks(root)
    if (task in labels or len(labels) >= portable._MAX_CHILDREN
            or portable.workbench._stat(target) is not None):
        raise DesktopRefused("Original desk task already exists or desk is at capacity.")
    markdown = _source_markdown(root, note_file, note_markdown)
    if note_markdown is not None:
        portable.continuity._action(markdown)  # user-authored next action, never executed
    result = portable.workbench.preview_note(task, markdown)
    if (result.get("status") != "DRAFT_PREVIEW_ONLY"
            or result.get("task_key_claimed") != task
            or result.get("writes_performed") is not False
            or result.get("installed_or_project_write_authorized") is not False
            or type(result.get("sha256")) is not str
            or len(result["sha256"]) != 64
            or any(c not in "0123456789abcdef" for c in result["sha256"])):
        raise DesktopRefused("Original scratch note preview did not verify.")
    return result



def checked_revision_inventory(packet: dict, *, task: str, note_sha256: str) -> None:
    """Only a current, explicitly selected ACTIVE original task may be revised."""
    plan = triage_personal_day(packet)
    if plan["manual_recovery_attention_required"]:
        raise DesktopRefused("Original pending revision needs MANUAL recovery review.")
    if ("ACTIVE_TASK", task, note_sha256) not in plan["rows"]:
        raise DesktopRefused("Selected original active note changed; refresh and reselect.")


def preview_selected_task_revision(
    desk_path: str, task: str, note_file: str | None, note_sha256: str, *,
    note_markdown: str | None = None,
) -> dict:
    """Read-only original-owner old/new note receipts; no implicit action disclosure.

    This preview is not authority to write. The original lifecycle owner binds
    BOTH preimage and replacement digest again inside the approved operation.
    """
    if (type(note_sha256) is not str or len(note_sha256) != 64
            or any(c not in "0123456789abcdef" for c in note_sha256)):
        raise DesktopRefused("Exact original active note SHA-256 required.")
    root = portable._desk(desk_path, must_exist=True)
    portable._existing_tasks(root)
    _folder, current = lifecycle._active(root, task)
    if current.get("sha256") != note_sha256:
        raise DesktopRefused("Original active note is no longer the selected version.")
    attention = lifecycle.inspect_pending_revision_attention(root)
    if (type(attention) is not dict
            or attention.get("schema") != lifecycle.SCHEMA
            or attention.get("status") != "READ_ONLY_PENDING_REVISION_ATTENTION"
            or attention.get("manual_recovery_attention_required") is not False
            or attention.get("automatic_recovery_performed") is not False
            or attention.get("pending_contents_opened") is not False
            or attention.get("writes_performed") is not False):
        raise DesktopRefused("Pending revision or unverified recovery state; inspect manually.")
    markdown = _source_markdown(root, note_file, note_markdown)
    portable.continuity._action(markdown)  # original next-action grammar, NOT execution
    preview = portable.workbench.preview_note(task, markdown)
    digest = preview.get("sha256")
    if (preview.get("status") != "DRAFT_PREVIEW_ONLY"
            or preview.get("task_key_claimed") != task
            or preview.get("writes_performed") is not False
            or preview.get("installed_or_project_write_authorized") is not False
            or type(digest) is not str or len(digest) != 64
            or any(c not in "0123456789abcdef" for c in digest)
            or digest == note_sha256):
        raise DesktopRefused("Replacement note preview invalid, identical or not read only.")
    return {
        "task_key_claimed": task,
        "previous_sha256": note_sha256,
        "sha256": digest,
        "writes_performed": False,
    }


def triage_personal_day(packet: dict, *, query: str = "", mode: str = "ALL") -> dict:
    """Search only verified original offered task KEYS, with history still historical.

    Never open notes or guess projects/results. Snapshot is not fresh by
    default; every subsequent owner action independently revalidates.
    """
    checked_day(packet, selected=False)
    if (type(query) is not str or len(query) > 64
            or any(not c.isprintable() for c in query)
            or type(mode) is not str or mode not in {"ALL", "ACTIVE", "HISTORY"}):
        raise DesktopRefused("Triage requires a short printable key query and known view.")
    offered = packet.get("original_offered_choices")
    if type(offered) is not list or len(offered) > 54:
        raise DesktopRefused("Original offered choices unavailable.")
    fields = ("active_task_count", "linked_historical_result_choice_count",
              "saved_completed_snapshot_count", "archived_snapshot_count",
              "revision_snapshot_count")
    if any(type(packet.get(k)) is not int or packet[k] < 0 for k in fields):
        raise DesktopRefused("Original task/history counts unavailable.")
    attention = packet.get("manual_revision_recovery_attention_required")
    if type(attention) is not bool:
        raise DesktopRefused("Original recovery attention state unavailable.")
    rows, seen = [], set()
    active = history = 0
    term = query.strip().casefold()
    for item in offered:
        if type(item) is not dict:
            raise DesktopRefused("Malformed original offered choice.")
        kind, task, sha = (item.get("kind"), item.get("task_key_claimed"),
                           item.get("selected_note_sha256"))
        if (type(kind) is not str
                or kind not in {"ACTIVE_TASK", "SAVED_COMPLETED_RESULT"}
                or type(task) is not str or not task.startswith("TASK-")
                or type(sha) is not str or len(sha) != 64
                or any(c not in "0123456789abcdef" for c in sha)):
            raise DesktopRefused("Original task identity invalid.")
        identity = (kind, task, sha)
        if identity in seen:
            raise DesktopRefused("Duplicate original task/snapshot choice.")
        seen.add(identity)
        active += kind == "ACTIVE_TASK"
        history += kind == "SAVED_COMPLETED_RESULT"
        if term in task.casefold() and (
                mode == "ALL" or
                (mode == "ACTIVE" and kind == "ACTIVE_TASK") or
                (mode == "HISTORY" and kind == "SAVED_COMPLETED_RESULT")):
            rows.append(identity)
    if (active != packet["active_task_count"]
            or history != packet["linked_historical_result_choice_count"]):
        raise DesktopRefused("Original offered day counts mismatch.")
    summary = (
        f"Showing {len(rows)}/{len(offered)} choices · {active} active · "
        f"{history} historical offered · "
        f"{packet['saved_completed_snapshot_count']} completed snapshots · "
        f"{packet['archived_snapshot_count']} archived · "
        f"{packet['revision_snapshot_count']} revisions. "
        "Historical is NEVER current by default.")
    if attention:
        summary += " MANUAL RECOVERY ATTENTION: original revisions need review."
    return {"rows": rows, "summary": summary,
            "manual_recovery_attention_required": attention}



def render_verified_workday_home(day: dict, home: dict) -> str:
    """One read-only original Workday Home, reconciled to the Personal Day.

    Never choose a task, disclose unselected actions, repair interrupted writes,
    or treat saved results as current. This is a cooperative snapshot, not an
    atomic filesystem or user/host authentication guarantee.
    """
    offered = triage_personal_day(day)
    fields = (
        ("active_count", "active_task_count"),
        ("completed_snapshot_count", "saved_completed_snapshot_count"),
        ("archived_snapshot_count", "archived_snapshot_count"),
        ("revision_snapshot_count", "revision_snapshot_count"),
    )
    false_fields = (
        "automatic_revision_recovery_performed", "automatic_task_selection_performed",
        "history_has_timestamps", "historical_document_current_bytes_verified",
        "result_quality_validated", "task_reopened_or_completed",
        "native_chairman_task_bound", "native_claude_or_hooks_executed",
        "database_contacted", "writes_performed", "new_store_created",
        "installed_vres_modified",
    )
    if (type(home) is not dict
            or home.get("schema") != owner.WORKDAY_SCHEMA
            or home.get("status") != "READ_ONLY_INTEGRATED_PERSONAL_WORKDAY_HOME"
            or home.get("selected_review") is not None
            or type(home.get("manual_revision_recovery_attention_required")) is not bool
            or home["manual_revision_recovery_attention_required"]
               is not offered["manual_recovery_attention_required"]
            or any(home.get(name) is not False for name in false_fields)
            or any(type(home.get(name)) is not int
                   or home[name] != day[day_name] for name, day_name in fields)):
        raise DesktopRefused("Original workday home identity, counts or holds changed.")
    active = home.get("active_tasks")
    history = home.get("saved_history")
    expected_history = (day["saved_completed_snapshot_count"]
                        + day["archived_snapshot_count"]
                        + day["revision_snapshot_count"])
    if (type(active) is not list or len(active) != day["active_task_count"]
            or type(history) is not list or len(history) != expected_history
            or len(history) > 48):
        raise DesktopRefused("Original workday inventory is not bounded.")
    observed_active = []
    for row in active:
        if (type(row) is not dict
                or type(row.get("task_key_claimed")) is not str
                or not portable.workbench._TASK_KEY.fullmatch(row["task_key_claimed"])
                or type(row.get("note_sha256")) is not str
                or not portable.workbench._SHA.fullmatch(row["note_sha256"])
                or type(row.get("note_bytes")) is not int
                or not 0 < row["note_bytes"] <= 32768):
            raise DesktopRefused("Original workday active task receipt invalid.")
        observed_active.append((row["task_key_claimed"], row["note_sha256"]))
    expected_active = [
        (task, digest) for kind, task, digest in offered["rows"]
        if kind == "ACTIVE_TASK"
    ]
    if sorted(observed_active) != sorted(expected_active):
        raise DesktopRefused("Original active task inventory changed between owners.")
    counts = {"completed": 0, "archived": 0, "revisions": 0}
    linked = []
    for row in history:
        if (type(row) is not dict or row.get("state") not in counts
                or type(row.get("task_key_claimed")) is not str
                or not portable.workbench._TASK_KEY.fullmatch(row["task_key_claimed"])
                or type(row.get("note_sha256")) is not str
                or not portable.workbench._SHA.fullmatch(row["note_sha256"])
                or type(row.get("saved_result_linked")) is not bool
                or row.get("current_result_bytes_verified") is not False
                or row["state"] != "completed" and row["saved_result_linked"]):
            raise DesktopRefused("Historical snapshot cannot become a current result.")
        counts[row["state"]] += 1
        if row["saved_result_linked"]:
            linked.append((row["task_key_claimed"], row["note_sha256"]))
    expected_linked = [
        (task, digest) for kind, task, digest in offered["rows"]
        if kind == "SAVED_COMPLETED_RESULT"
    ]
    if (counts != {
            "completed": day["saved_completed_snapshot_count"],
            "archived": day["archived_snapshot_count"],
            "revisions": day["revision_snapshot_count"]}
            or sorted(linked) != sorted(expected_linked)):
        raise DesktopRefused("Original completed-result history and offered choices differ.")
    rendered = owner.render_workday(home)
    if (type(rendered) is not str
            or not rendered.startswith("Vres-OS PERSONAL WORKDAY HOME -- READ ONLY")
            or len(rendered) > 24000):
        raise DesktopRefused("Original read-only workday renderer refused.")
    return rendered


def checked_archived_history(history: dict, day: dict) -> list[tuple[str, str]]:
    """Validate ONLY existing original-owner, undated archived task receipts.

    No archived snapshot becomes active, current, replayable or trusted by this
    view. All later operations re-attest exact owner state and require consent.
    """
    checked_day(day, selected=False)
    if (type(history) is not dict
            or history.get("schema") != lifecycle.SCHEMA
            or history.get("status") != "READ_ONLY_PERSONAL_HISTORY"
            or history.get("writes_performed") is not False
            or history.get("authoritative_task_store") is not False
            or history.get("document_current_bytes_verified") is not False):
        raise DesktopRefused("Original immutable history contract not verified.")
    snapshots = history.get("snapshots")
    if (type(snapshots) is not list or len(snapshots) > 48
            or type(history.get("count")) is not int
            or history["count"] != len(snapshots)):
        raise DesktopRefused("Original history inventory is missing or unbounded.")
    counts = {"completed": 0, "archived": 0, "revisions": 0}
    archived = []
    seen = set()
    for row in snapshots:
        if (type(row) is not dict or row.get("state") not in counts
                or type(row.get("task_key_claimed")) is not str
                or not portable.workbench._TASK_KEY.fullmatch(row["task_key_claimed"])
                or type(row.get("sha256")) is not str
                or not portable.workbench._SHA.fullmatch(row["sha256"])
                or type(row.get("bytes")) is not int
                or not 0 < row["bytes"] <= 32768):
            raise DesktopRefused("Original archived history identity invalid.")
        identity = (row["state"], row["task_key_claimed"], row["sha256"])
        if identity in seen:
            raise DesktopRefused("Duplicate original history snapshot.")
        seen.add(identity)
        counts[row["state"]] += 1
        if row["state"] == "archived":
            archived.append((row["task_key_claimed"], row["sha256"]))
    if (counts["completed"] != day["saved_completed_snapshot_count"]
            or counts["archived"] != day["archived_snapshot_count"]
            or counts["revisions"] != day["revision_snapshot_count"]):
        raise DesktopRefused("Original Personal Day and archive inventory differ.")
    return sorted(archived)


class PersonalDayDesktop(ttk.Frame):
    """Ephemeral view state ONLY; original owners own all task/history writes."""

    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=12)
        self.master = master
        self.master.title("Vres-OS | Personal Day (source-only preview)")
        self.master.minsize(940, 680)
        self.grid(sticky="nsew")
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(5, weight=2)
        self.values = {name: tk.StringVar() for name in (
            "desk", "new_task", "note", "project", "key", "result",
            "acceptance_path", "acceptance_sha",
            "catalog_root", "catalog_namespace", "catalog_source",
            "catalog_sha", "catalog_revision", "synthetic_file", "synthetic_sha")}
        self.with_intake = tk.BooleanVar(value=False)
        self.with_acceptance = tk.BooleanVar(value=False)
        self.with_catalog = tk.BooleanVar(value=False)
        self.with_synthetic = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Choose an explicit scratch desk and select Load.")
        self.choices: dict[str, tuple[str, str, str]] = {}
        self.archive_choices: dict[str, tuple[str, str]] = {}
        self.archive_packet: dict | None = None
        self.archive_summary = tk.StringVar(value="Load original archived history explicitly.")
        self.loaded_desk: str | None = None
        self.inventory_packet: dict | None = None
        self.triage_query = tk.StringVar(value="")
        self.triage_mode = tk.StringVar(value="ALL")
        self.triage_summary = tk.StringVar(value="Load the original day for triage.")
        self.focused: tuple | None = None
        self.decision: dict | None = None
        self.guide = tk.StringVar(value="Step 1/4: Load an exact desk and select a task.")
        self.safe_next_label = tk.StringVar(value="Enter an exact scratch desk path first")
        self.action_seen_binding: tuple | None = None
        self.briefing_seen_binding: tuple | None = None
        self.action_buttons = {}
        self._draw()
        # Editing any path, SHA, opt-in or desk invalidates prior focused claims.
        for field, variable in self.values.items():
            variable.trace_add(
                "write", lambda *_ignored, name=field: self._edited(name))
        for variable in (self.with_intake, self.with_acceptance,
                         self.with_catalog, self.with_synthetic):
            variable.trace_add("write", lambda *_ignored: self._edited(None))
        for variable in (self.triage_query, self.triage_mode):
            variable.trace_add("write", lambda *_ignored: self._triage_changed())
        self._sync_guidance()

    def _field(self, parent, row: int, label: str, key: str) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=4, pady=3)
        ttk.Entry(parent, textvariable=self.values[key]).grid(
            row=row, column=1, sticky="ew", padx=4, pady=3)

    def _draw(self) -> None:
        ttk.Label(
            self, text="ONE original Chairman · personal scratch workspace · NOT installed",
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))
        desk = ttk.Frame(self)
        desk.grid(row=1, column=0, sticky="ew")
        desk.columnconfigure(1, weight=1)
        self._field(desk, 0, "Scratch desk (absolute path)", "desk")
        ttk.Button(desk, text="Load / refresh day", command=self.refresh).grid(
            row=0, column=2, padx=4)

        tasks = ttk.LabelFrame(self, text="Choose one original task or historical result")
        tasks.grid(row=2, column=0, sticky="nsew", pady=6)
        tasks.columnconfigure(0, weight=1)
        tasks.rowconfigure(1, weight=1)
        triage = ttk.Frame(tasks)
        triage.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        triage.columnconfigure(1, weight=1)
        ttk.Label(triage, text="Find task key").grid(row=0, column=0, padx=4)
        ttk.Entry(triage, textvariable=self.triage_query).grid(
            row=0, column=1, sticky="ew", padx=4)
        ttk.Label(triage, text="View").grid(row=0, column=2, padx=4)
        ttk.Combobox(triage, textvariable=self.triage_mode, state="readonly",
                     values=("ALL", "ACTIVE", "HISTORY"), width=11).grid(
                         row=0, column=3, padx=4)
        self.action_preview_button = ttk.Button(
            triage, text="View NEXT ACTION (read only)",
            command=self.inspect_next_action)
        self.action_preview_button.grid(row=0, column=4, padx=4)
        self.listing = ttk.Treeview(
            tasks, columns=("kind", "task", "note"), show="headings",
            selectmode="browse", height=7)
        for name, heading, width in (
                ("kind", "Original kind", 180), ("task", "Task key", 260),
                ("note", "Note SHA-256 (short display)", 280)):
            self.listing.heading(name, text=heading)
            self.listing.column(name, width=width, anchor="w")
        self.listing.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(tasks, orient="vertical", command=self.listing.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.listing.configure(yscrollcommand=scrollbar.set)
        self.listing.bind("<<TreeviewSelect>>", lambda _event: self._selection_changed())
        ttk.Label(tasks, textvariable=self.triage_summary, wraplength=900).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(5, 0))

        workspace = ttk.Notebook(self)
        self.workspace = workspace
        workspace.grid(row=3, column=0, sticky="ew", pady=6)

        active = ttk.Frame(workspace, padding=5)
        self.project_tab = active
        active.columnconfigure(1, weight=1)
        workspace.add(active, text="Project / result")
        self._field(active, 0, "Project root (explicit)", "project")
        self._field(active, 1, "Original project key", "key")
        self._field(active, 2, "Result file (explicit)", "result")
        ttk.Checkbutton(
            active, text="Opt in: original #168 read-only project/source preview",
            variable=self.with_intake).grid(row=3, column=1, sticky="w")

        claims = ttk.Frame(workspace, padding=5)
        claims.columnconfigure(1, weight=1)
        workspace.add(claims, text="Acceptance self-claims")
        self._field(claims, 0, "Scratch acceptance file", "acceptance_path")
        self._field(claims, 1, "Exact acceptance SHA-256", "acceptance_sha")
        ttk.Checkbutton(
            claims, text="Opt in: caller self-claims, NOT result-quality proof",
            variable=self.with_acceptance).grid(row=2, column=1, sticky="w")

        sources = ttk.Frame(workspace, padding=5)
        sources.columnconfigure(0, weight=1)
        sources.columnconfigure(1, weight=1)
        workspace.add(sources, text="Optional source context (held)")
        catalog = ttk.LabelFrame(sources, text="Original #167 saved catalog · NOT live freshness")
        catalog.grid(row=0, column=0, sticky="nsew", padx=4)
        catalog.columnconfigure(1, weight=1)
        self._field(catalog, 0, "Explicit saved root", "catalog_root")
        self._field(catalog, 1, "Namespace", "catalog_namespace")
        self._field(catalog, 2, "Source ID", "catalog_source")
        self._field(catalog, 3, "Saved document SHA-256", "catalog_sha")
        self._field(catalog, 4, "Saved revision", "catalog_revision")
        ttk.Checkbutton(
            catalog, text="Opt in: read one existing offline #167 snapshot",
            variable=self.with_catalog).grid(row=5, column=0, columnspan=2, sticky="w")

        synthetic = ttk.LabelFrame(
            sources, text="Original #166/#168 · SYNTHETIC preparation ONLY")
        synthetic.grid(row=0, column=1, sticky="nsew", padx=4)
        synthetic.columnconfigure(1, weight=1)
        self._field(synthetic, 0, "Scratch-only inventory file", "synthetic_file")
        self._field(synthetic, 1, "Synthetic file SHA-256", "synthetic_sha")
        ttk.Checkbutton(
            synthetic, text="Opt in: HELD synthetic preview; no adoption",
            variable=self.with_synthetic).grid(row=2, column=0, columnspan=2, sticky="w")
        ttk.Label(
            synthetic, text="Both previews require Project / result tab #168 opt-in.\n"
            "No real profile scan, DB, credentials, native hooks, or F1/Fable.",
            justify="left").grid(row=3, column=0, columnspan=2, sticky="w", pady=8)

        buttons = ttk.Frame(self)
        buttons.grid(row=4, column=0, sticky="ew", pady=5)
        # Short task/history rows reduce button overflow at minimum desktop size.
        for line, controls in enumerate((
                (("focus", "Focus / inspect", self.focus),
                 ("briefing", "Evidence & gaps (read only)", self.preview_briefing),
                 ("decision", "Review decision", self.preview_decision),
                 ("complete", "Complete (approve)", self.complete)),
                (("clear_history", "Clear history inputs", self.clear_history_context),
                 ("reopen", "Reopen (approve)", self.reopen),
                 ("replay", "Verify saved bytes", self.replay)))):
            for column, (name, label, method) in enumerate(controls):
                button = ttk.Button(buttons, text=label, command=method)
                button.grid(row=line, column=column, sticky="ew", padx=3, pady=2)
                self.action_buttons[name] = button
        self.home_button = ttk.Button(
            buttons, text="Workday / recovery (read only)", command=self.review_home)
        self.home_button.grid(row=1, column=3, sticky="ew", padx=3, pady=2)
        for column in range(4):
            buttons.columnconfigure(column, weight=1)
        self.safe_next_button = ttk.Button(
            buttons, textvariable=self.safe_next_label,
            command=self.follow_read_only_step)
        self.safe_next_button.grid(
            row=2, column=0, columnspan=4, sticky="ew", padx=3, pady=4)
        ttk.Label(buttons, textvariable=self.guide, wraplength=900).grid(
            row=3, column=0, columnspan=4, sticky="w", pady=(5, 0))

        report = ttk.LabelFrame(self, text="Original owner view · historical is NOT current")
        report.grid(row=5, column=0, sticky="nsew", pady=6)
        report.columnconfigure(0, weight=1)
        report.rowconfigure(0, weight=1)
        self.detail = tk.Text(report, wrap="word", height=11, state="disabled")
        self.detail.grid(row=0, column=0, sticky="nsew")
        report_scroll = ttk.Scrollbar(report, orient="vertical", command=self.detail.yview)
        report_scroll.grid(row=0, column=1, sticky="ns")
        self.detail.configure(yscrollcommand=report_scroll.set)

        create = ttk.Frame(workspace, padding=5)
        create.columnconfigure(1, weight=1)
        workspace.add(create, text="Add scratch task")
        self._field(create, 0, "New task key", "new_task")
        self._field(create, 1, "Optional external Markdown file (instead of editor)", "note")
        ttk.Label(create, text=(
            "Write the task and ## Next action directly here, OR choose an external "
            "file above. Only one source is accepted; editing is not saved until "
            "a separately approved original-owner write.")).grid(
                row=2, column=0, columnspan=2, sticky="w", padx=4, pady=3)
        self.inline_editor = tk.Text(create, wrap="word", height=5, undo=True)
        self.inline_editor.grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=3)
        self.inline_editor.bind("<<Modified>>", self._inline_edited)
        self.inline_editor.edit_modified(False)
        task_actions = ttk.Frame(create)
        task_actions.grid(row=4, column=0, columnspan=2, sticky="ew", pady=4)
        self.add_button = ttk.Button(
            task_actions, text="Add task to LOADED desk (approve)", command=self.add_existing)
        self.add_button.grid(row=0, column=0, sticky="w", padx=4, pady=3)
        ttk.Button(task_actions, text="Start NEW desk/task (approve)",
                   command=self.start).grid(row=0, column=1, sticky="w", padx=4, pady=3)
        self.revise_button = ttk.Button(
            task_actions, text="Revise SELECTED ACTIVE task (approve)",
            command=self.revise_selected)
        self.revise_button.grid(row=1, column=0, columnspan=2, sticky="w", padx=4, pady=3)
        ttk.Label(task_actions,
                  text="Original revision history preserves the old note. "
                       "No automatic selection, completion or project binding.").grid(
                       row=2, column=0, columnspan=2, sticky="w", padx=4, pady=3)
        ttk.Button(task_actions, text="Insert editable task starter (no save)",
                   command=self.insert_starter).grid(
                       row=3, column=0, columnspan=2, sticky="w", padx=4, pady=3)
        archive_tab = ttk.Frame(workspace, padding=5)
        archive_tab.columnconfigure(0, weight=1)
        archive_tab.rowconfigure(1, weight=1)
        workspace.add(archive_tab, text="Archive / restore")
        ttk.Label(
            archive_tab, text="ARCHIVED only · verified immutable snapshots · no dates or auto-restore"
        ).grid(row=0, column=0, sticky="w")
        self.archive_listing = ttk.Treeview(
            archive_tab, columns=("task", "sha"), show="headings",
            selectmode="browse", height=4)
        self.archive_listing.heading("task", text="Archived task")
        self.archive_listing.heading("sha", text="Verified note SHA-256 (short display)")
        self.archive_listing.column("task", width=260, anchor="w")
        self.archive_listing.column("sha", width=340, anchor="w")
        self.archive_listing.grid(row=1, column=0, sticky="nsew")
        archive_scroll = ttk.Scrollbar(
            archive_tab, orient="vertical", command=self.archive_listing.yview)
        archive_scroll.grid(row=1, column=1, sticky="ns")
        self.archive_listing.configure(yscrollcommand=archive_scroll.set)
        self.archive_listing.bind(
            "<<TreeviewSelect>>", lambda _event: self._archive_selection_changed())
        archive_buttons = ttk.Frame(archive_tab)
        archive_buttons.grid(row=2, column=0, sticky="ew", pady=4)
        self.archive_button = ttk.Button(
            archive_buttons, text="Archive selected ACTIVE (approve)",
            command=self.archive_selected)
        self.archive_button.grid(row=0, column=0, padx=4)
        self.load_archive_button = ttk.Button(
            archive_buttons, text="Read archived history",
            command=self.load_archived)
        self.load_archive_button.grid(row=0, column=1, padx=4)
        self.restore_archive_button = ttk.Button(
            archive_buttons, text="Restore selected ARCHIVED (approve)",
            command=self.restore_archived)
        self.restore_archive_button.grid(row=0, column=2, padx=4)
        ttk.Label(archive_tab, textvariable=self.archive_summary,
                  wraplength=900).grid(row=3, column=0, sticky="w")

        ttk.Label(self, textvariable=self.status, wraplength=900).grid(
            row=6, column=0, sticky="w", pady=5)

    def _clear_archive_view(self) -> None:
        """Clear transient archive selection; original saved history is untouched."""
        self.archive_choices.clear()
        self.archive_packet = None
        self.archive_listing.delete(*self.archive_listing.get_children())
        self.archive_summary.set("Load original archived history explicitly.")

    def _archive_selection_changed(self) -> None:
        """Archive selection never keeps an old completion decision alive."""
        self._invalidate()
        self._display("")
        self.status.set("Archive selection changed. Reattest before any approved restore.")
        self._sync_guidance()

    def _render_triage(self) -> None:
        """Pure presentation of current read-only inventory; no auto-selection."""
        self.choices.clear()
        self.listing.delete(*self.listing.get_children())
        if self.inventory_packet is None:
            self.triage_summary.set("Load the original day for triage.")
            return
        plan = triage_personal_day(
            self.inventory_packet, query=self.triage_query.get(),
            mode=self.triage_mode.get())
        for index, identity in enumerate(plan["rows"]):
            iid = f"choice-{index}"
            self.choices[iid] = identity
            label = ("ACTIVE TASK" if identity[0] == "ACTIVE_TASK"
                     else "SAVED · HISTORICAL")
            self.listing.insert("", "end", iid=iid, values=(
                label, identity[1], identity[2][:16]))
        self.triage_summary.set(plan["summary"])

    def _triage_changed(self) -> None:
        """Changed filters invalidate prior focus, decision and selected row."""
        self.choices.clear()
        self.listing.delete(*self.listing.get_children())
        self._invalidate()
        self._display("")
        try:
            self._render_triage()
            if self.inventory_packet is not None:
                self._display(owner.render_personal_day(self.inventory_packet))
                self.status.set(
                    "Read-only task-key filter. Select one visible row and focus; "
                    "refresh for a new original-owner snapshot.")
        except Exception:
            self.choices.clear()
            self.listing.delete(*self.listing.get_children())
            self.triage_summary.set("Invalid filter or original snapshot; refresh required.")
            self.status.set("No task selected; use <=64 printable filter characters.")
        self._sync_guidance()

    def _display(self, content: str) -> None:
        self.detail.configure(state="normal")
        self.detail.delete("1.0", tk.END)
        self.detail.insert("1.0", content[:24000])
        self.detail.configure(state="disabled")

    def _selection_changed(self) -> None:
        """Never display the previous task's decision under a new selection."""
        self._invalidate()
        self._display("")
        self.status.set("Selection changed. Focus the exact offered row before reviewing.")

    def _history_inputs_clear(self) -> bool:
        return (not any(self.values[name].get().strip()
                        for name in _HISTORY_CONTEXT_FIELDS)
                and not any(variable.get() for variable in (
                    self.with_intake, self.with_acceptance,
                    self.with_catalog, self.with_synthetic)))

    def _ui_plan(self) -> dict:
        try:
            kind, _task, _sha = self._selected()
            binding = self._binding()
        except DesktopRefused:
            plan = guided_action_plan(None)
            if (getattr(self, "inventory_packet", None) is not None
                    and self.inventory_packet.get(
                        "manual_revision_recovery_attention_required") is True):
                plan["next_step"] = (
                    "MANUAL RECOVERY HOLD: inspect original pending revision staging. "
                    "No task write or automatic repair.")
            return plan
        current_focus = self.focused is not None and self.focused[0] == binding
        current_decision = (current_focus and self.decision is not None
                            and self.decision.get("binding") == binding)
        stage = self.focused[1].get("stage") if current_focus else None
        plan = guided_action_plan(
            kind, stage, focused=current_focus,
            decision_ready=current_decision,
            history_clear=self._history_inputs_clear())
        if (getattr(self, "inventory_packet", None) is not None
                and self.inventory_packet.get(
                    "manual_revision_recovery_attention_required") is True):
            plan["enabled"]["complete"] = False
            plan["enabled"]["reopen"] = False
            plan["next_step"] = (
                "MANUAL RECOVERY HOLD: inspect original pending revision staging. "
                "Only read-only inspection; no automatic repair or task write.")
        return plan

    def _recommended_read(self) -> dict:
        """Ephemeral hint from the current explicit UI selection; no owner writes."""
        desk = self.values["desk"].get().strip()
        loaded = bool(desk) and self.loaded_desk == desk and self.inventory_packet is not None
        if not desk:
            return {"route": None, "label": "Enter an exact scratch desk path first"}
        kind, binding = None, None
        if loaded:
            try:
                kind, _task, _sha = self._selected()
                binding = self._binding()
            except DesktopRefused:
                pass
        focused = bool(binding is not None and self.focused is not None
                       and self.focused[0] == binding)
        decision_ready = bool(focused and self.decision is not None
                              and self.decision.get("binding") == binding)
        stage = (self.focused[1].get("stage")
                 if focused and type(self.focused[1]) is dict else None)
        return navigation.next_read_only_step(
            day_loaded=loaded, selected_kind=kind, focused=focused, stage=stage,
            action_seen=bool(binding is not None and self.action_seen_binding == binding),
            briefing_seen=bool(binding is not None and self.briefing_seen_binding == binding),
            decision_ready=decision_ready,
            history_clear=self._history_inputs_clear(),
            manual_recovery_hold=bool(loaded and self.inventory_packet.get(
                "manual_revision_recovery_attention_required") is True))

    def follow_read_only_step(self) -> None:
        """Explicit operator click; ONLY pre-existing READ or notebook navigation."""
        route = self._recommended_read()["route"]
        if route == "project_tab":
            self.workspace.select(self.project_tab)
            self.status.set("Enter exact project/result fields, then focus again. No write.")
            return
        reads = {
            "refresh": self.refresh,
            "home": self.review_home,
            "next_action": self.inspect_next_action,
            "focus": self.focus,
            "briefing": self.preview_briefing,
            "decision": self.preview_decision,
        }
        if route not in reads:
            self.status.set("No read shortcut now. Use the separate explicit approval "
                            "or manually inspect the original owner state.")
            return
        reads[route]()

    def _sync_guidance(self) -> None:
        plan = self._ui_plan()
        for name, button in self.action_buttons.items():
            button.configure(
                state="normal" if plan["enabled"][name] else "disabled")
        self.guide.set(plan["next_step"])
        hint = self._recommended_read()
        self.safe_next_label.set(hint["label"])
        self.safe_next_button.configure(
            state="normal" if hint["route"] is not None else "disabled")
        self.add_button.configure(
            state="normal" if self.loaded_desk == self.values["desk"].get().strip()
            and bool(self.loaded_desk)
            and self.inventory_packet is not None
            and self.inventory_packet.get(
                "manual_revision_recovery_attention_required") is False
            else "disabled")
        if hasattr(self, "home_button"):
            self.home_button.configure(
                state="normal" if self.loaded_desk == self.values["desk"].get().strip()
                and bool(self.loaded_desk) and self.inventory_packet is not None
                else "disabled")
        try:
            kind, _task, _sha = self._selected()
        except DesktopRefused:
            kind = None
        self.action_preview_button.configure(
            state="normal" if kind == "ACTIVE_TASK"
            and self.inventory_packet is not None
            and bool(self.loaded_desk)
            and self.loaded_desk == self.values["desk"].get().strip()
            else "disabled")
        if hasattr(self, "revise_button"):
            self.revise_button.configure(
                state="normal" if kind == "ACTIVE_TASK"
                and self.inventory_packet is not None
                and self.inventory_packet.get(
                    "manual_revision_recovery_attention_required") is False
                and bool(self.loaded_desk)
                and self.loaded_desk == self.values["desk"].get().strip()
                else "disabled")
        if hasattr(self, "archive_button"):
            loaded_ready = (self.inventory_packet is not None
                            and bool(self.loaded_desk)
                            and self.loaded_desk == self.values["desk"].get().strip())
            write_ready = (loaded_ready and self.inventory_packet.get(
                "manual_revision_recovery_attention_required") is False)
            self.archive_button.configure(
                state="normal" if write_ready and kind == "ACTIVE_TASK"
                else "disabled")
            # Manual-recovery holds never suppress an explicitly chosen READ.
            self.load_archive_button.configure(
                state="normal" if loaded_ready else "disabled")
            selected = self.archive_listing.selection()
            self.restore_archive_button.configure(
                state="normal" if write_ready
                and self.archive_packet is not None and len(selected) == 1
                and selected[0] in self.archive_choices else "disabled")

    def _edited(self, field: str | None) -> None:
        """A changed UI selection cannot retain a ready decision or preview."""
        if field == "desk":
            self.loaded_desk = None
            self.inventory_packet = None
            self.choices.clear()
            self.listing.delete(*self.listing.get_children())
            self.triage_query.set("")
            self.triage_mode.set("ALL")
            self.triage_summary.set("Desk changed; load a verified owner snapshot.")
            if hasattr(self, "archive_listing"):
                self._clear_archive_view()
        self._invalidate()
        self._display("")
        if field == "desk":
            self.status.set("Desk changed. Load this desk before selecting a task.")
        else:
            self.status.set("Inputs changed. Focus the exact task again before review.")
        self._sync_guidance()

    def _inline_edited(self, _event=None) -> None:
        """Drop stale task focus/decision when the ephemeral editor changes."""
        if self.inline_editor.edit_modified():
            self.inline_editor.edit_modified(False)
            self._edited("note")

    def _invalidate(self) -> None:
        self.focused = None
        self.decision = None
        self.action_seen_binding = None
        self.briefing_seen_binding = None
        self._sync_guidance()

    def _refuse(self) -> None:
        self._invalidate()
        self.status.set(
            "REFUSED / state may have changed. Inspect original desk/history; never retry writes blindly.")
        self._display("No current claim, completion or replay may be inferred from a refusal.")

    def _selected(self) -> tuple[str, str, str]:
        selected = self.listing.selection()
        if len(selected) != 1 or selected[0] not in self.choices:
            raise DesktopRefused("Select exactly one original offered row first.")
        return self.choices[selected[0]]

    def _binding(self) -> tuple:
        selected = self._selected()
        return (self.values["desk"].get().strip(), *selected,
                *(self.values[name].get().strip() for name in (
                    "project", "key", "result", "acceptance_path", "acceptance_sha",
                    "catalog_root", "catalog_namespace", "catalog_source",
                    "catalog_sha", "catalog_revision", "synthetic_file", "synthetic_sha")),
                bool(self.with_acceptance.get()), bool(self.with_intake.get()),
                bool(self.with_catalog.get()), bool(self.with_synthetic.get()))

    def _acceptance(self, desk_path: str) -> dict:
        file = self.values["acceptance_path"].get().strip()
        sha = self.values["acceptance_sha"].get().strip()
        if not self.with_acceptance.get():
            if file or sha:
                raise DesktopRefused("Acceptance inputs require explicit opt-in.")
            return {}
        if not file or not sha:
            raise DesktopRefused("Select one scratch acceptance file and exact SHA.")
        root = portable._desk(desk_path, must_exist=True)
        candidate = Path(file)
        if candidate.name != "result-acceptance-evidence.json" or candidate.parent != root:
            raise DesktopRefused("Acceptance file must be inside the selected scratch desk.")
        raw = owner._read_selected_chairman_source(file, maximum=32 * 1024)
        if hashlib.sha256(raw).hexdigest() != sha:
            raise DesktopRefused("Acceptance SHA-256 did not match.")
        return {
            "include_result_acceptance_evidence": True,
            "acceptance_evidence_document": raw,
            "expected_acceptance_evidence_sha256": sha,
        }

    def _sources(self, desk_path: str) -> dict:
        """Opt-in ORIGINAL offline #167 snapshot and HELD scratch-only #166 plan.

        Never opens the broker, a live database, a native host or a profile scan.
        The existing owner rechecks all original digest/identity boundaries.
        """
        keys = ("catalog_root", "catalog_namespace", "catalog_source",
                "catalog_sha", "catalog_revision")
        catalog = {name: self.values[name].get().strip() for name in keys}
        file = self.values["synthetic_file"].get().strip()
        sha = self.values["synthetic_sha"].get().strip()
        if not self.with_catalog.get() and any(catalog.values()):
            raise DesktopRefused("Clear saved catalog fields or explicitly opt in.")
        if not self.with_synthetic.get() and (file or sha):
            raise DesktopRefused("Clear synthetic inputs or explicitly opt in.")
        if (self.with_catalog.get() or self.with_synthetic.get()) and not self.with_intake.get():
            raise DesktopRefused("Saved/synthetic previews require selected #168 intake.")
        result = {}
        if self.with_catalog.get():
            if not all(catalog.values()):
                raise DesktopRefused("All five original saved catalog fields are required.")
            revision_text = catalog["catalog_revision"]
            if (not revision_text.isascii() or not revision_text.isdecimal()
                    or (len(revision_text) > 1 and revision_text.startswith("0"))
                    or len(revision_text) > 7 or int(revision_text) > 1000000):
                raise DesktopRefused("Exact nonnegative saved catalog revision required.")
            digest = catalog["catalog_sha"]
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise DesktopRefused("Expected saved catalog SHA-256 must be lowercase hex.")
            # ORIGINAL #167 store, loaded ONLY on explicit user-selected focus.
            # No broker is ever constructed; the original callback refuses lookup.
            from vres_os.personal_data_source_store import CurrentUserDataSourceStore
            result.update({
                "include_saved_catalog": True,
                "saved_catalog_store": CurrentUserDataSourceStore(
                    Path(catalog["catalog_root"]), catalog["catalog_namespace"],
                    owner._reject_catalog_credential_lookup),
                "saved_catalog_source_id": catalog["catalog_source"],
                "expected_saved_catalog_sha256": digest,
                "expected_saved_catalog_revision": int(revision_text),
            })
        if self.with_synthetic.get():
            if not file or not sha:
                raise DesktopRefused("One exact scratch synthetic file and SHA are required.")
            root = portable._desk(desk_path, must_exist=True)
            selected = Path(file)
            if selected.name != "synthetic-global-inventory.json" or selected.parent != root:
                raise DesktopRefused("Synthetic inventory must stay in selected scratch desk.")
            raw = owner._read_selected_chairman_source(file, maximum=64 * 1024)
            if hashlib.sha256(raw).hexdigest() != sha:
                raise DesktopRefused("Synthetic inventory SHA-256 mismatch.")
            result.update({
                "include_adoption_preparation": True,
                "synthetic_global_inventory_document": raw,
                "expected_synthetic_global_inventory_sha256": sha,
            })
        return result

    def _recheck_original_source(self, task: str) -> None:
        """Re-attest optional original owner context before a completion decision.

        This is an opt-in, bounded, read-only recheck of #168/#167/#166/#176,
        NOT an atomic read, host identity proof, quality proof or new owner.
        The original completion owner still checks its own exact write boundary.
        """
        if self.focused is None or self.focused[0] != self._binding():
            raise DesktopRefused("Refocus the exact unchanged original task first.")
        source_sha = self.focused[2]
        if not self.with_intake.get():
            if source_sha is not None:
                raise DesktopRefused("Previously selected project source context changed.")
            return
        if (type(source_sha) is not str or len(source_sha) != 64
                or any(c not in "0123456789abcdef" for c in source_sha)):
            raise DesktopRefused("Original source focus digest unavailable.")
        desk = self.values["desk"].get().strip()
        context = checked_context(*(self.values[k].get() for k in (
            "project", "key", "result")))
        opts = self._acceptance(desk)
        sources = self._sources(desk)
        current = checked_day(owner.review_personal_day(
            desk, task, include_source_context=True, **context, **opts, **sources),
            selected=True)
        selected = current.get("selected_original_journey")
        original_context = current.get("selected_original_source_context")
        if (current.get("selected_choice_kind") != "ACTIVE_TASK"
                or selected != self.focused[1]
                or type(original_context) is not dict
                or original_context.get("integrated_source_context_sha256") != source_sha):
            raise DesktopRefused(
                "Original project/catalog/synthetic source context changed; refocus.")

    def clear_history_context(self) -> None:
        """Clear UI-only fields AFTER explicit request; never touch saved history."""
        try:
            kind, _task, _sha = self._selected()
            if kind != "SAVED_COMPLETED_RESULT":
                raise DesktopRefused("Select a saved completed result first.")
            if self._history_inputs_clear():
                self.status.set("History fields already clear. Inspect or reopen separately.")
                return
            if not messagebox.askyesno(
                    "Clear transient history inputs",
                    "Clear only the visible project/result/acceptance/source fields "
                    "and opt-ins to inspect this historical result?\n"
                    "No task, project, saved result or history file is changed.",
                    parent=self.master):
                return
            for field in _HISTORY_CONTEXT_FIELDS:
                self.values[field].set("")
            for variable in (self.with_intake, self.with_acceptance,
                             self.with_catalog, self.with_synthetic):
                variable.set(False)
            self._invalidate()
            self._display("")
            self.status.set(
                "Transient UI fields cleared only. Reopen and saved-byte replay "
                "still need separate approvals.")
        except Exception:
            self._refuse()

    def _history_only(self) -> tuple[str, str, str]:
        kind, task, digest = self._selected()
        if kind != "SAVED_COMPLETED_RESULT":
            raise DesktopRefused("Select a saved completed result for this operation.")
        if not self._history_inputs_clear():
            raise DesktopRefused("Clear active context and opt-ins before saved history.")
        return kind, task, digest

    def refresh(self) -> bool:
        self._invalidate()
        if hasattr(self, "archive_listing"):
            self._clear_archive_view()
        self.loaded_desk = None
        self.inventory_packet = None
        self.choices.clear()
        self.listing.delete(*self.listing.get_children())
        self.triage_summary.set("Loading original read-only day.")
        self._display("")
        try:
            packet = checked_day(
                owner.review_personal_day(self.values["desk"].get().strip()),
                selected=False)
            self.inventory_packet = packet
            self._render_triage()
            self.status.set(
                f"Read-only: {packet['active_task_count']} active; "
                f"{packet['saved_completed_snapshot_count']} completed snapshots (undated). "
                "Select an original row explicitly; refresh for a fresh snapshot.")
            self._display(owner.render_personal_day(packet))
            self.loaded_desk = self.values["desk"].get().strip()
            self._sync_guidance()
            return True
        except Exception:
            self.inventory_packet = None
            self.choices.clear()
            self.listing.delete(*self.listing.get_children())
            self.triage_summary.set("Original snapshot unavailable; inspect desk before retry.")
            self._refuse()
            return False

    def review_home(self) -> None:
        """Show existing ORIGINAL #165 Workday Home plus manual recovery attention.

        No task automatically selected, action disclosed, or saved bytes promoted.
        Existing focused decisions are cleared even when the read is refused.
        """
        self._invalidate()
        self._display("")
        try:
            desk = self.values["desk"].get().strip()
            if (not desk or self.loaded_desk != desk
                    or self.inventory_packet is None):
                raise DesktopRefused("Load the exact original desk before Workday Home.")
            before = checked_day(owner.review_personal_day(desk), selected=False)
            if before != self.inventory_packet:
                raise DesktopRefused("Original inventory changed; reload the day first.")
            rendered = render_verified_workday_home(
                before, owner.review_workday(desk))
            after = checked_day(owner.review_personal_day(desk), selected=False)
            if after != before:
                raise DesktopRefused("Original workday changed during read-only review.")
            self._display(rendered)
            if before["manual_revision_recovery_attention_required"]:
                self.status.set(
                    "MANUAL RECOVERY ATTENTION: interrupted original revision staging. "
                    "No write/repair; inspect original files independently.")
            else:
                self.status.set(
                    "Original read-only Workday Home: active, saved completed, archived "
                    "and revision inventory. No task automatically selected, saved bytes rechecked or "
                    "result quality certified.")
            self._sync_guidance()
        except Exception:
            self._refuse()

    def inspect_next_action(self) -> None:
        """Show one explicitly selected original task's next step as DATA only.

        This is a separate opt-in, read-only ORIGINAL #165/handoff request.
        No result, project, command, task selection or approval is inferred.
        """
        self._invalidate()
        self._display("")
        try:
            kind, task, digest = self._selected()
            desk = self.values["desk"].get().strip()
            if (kind != "ACTIVE_TASK" or not desk or self.loaded_desk != desk
                    or self.inventory_packet is None):
                raise DesktopRefused("Load the desk and select a current active task.")
            packet = checked_day(
                owner.review_personal_day(desk, task, show_selected_action=True),
                selected=True)
            journey = packet.get("selected_original_journey")
            if type(journey) is not dict:
                raise DesktopRefused("Original selected task action unavailable.")
            action = journey.get("selected_next_action_untrusted")
            if (packet.get("selected_choice_kind") != "ACTIVE_TASK"
                    or packet.get("selected_task_key_claimed") != task
                    or packet.get("source_context_selected_explicitly") is not False
                    or journey.get("selected_note_sha256") != digest
                    or journey.get("selected_next_action_disclosed") is not True
                    or type(action) is not str or not 0 < len(action) <= 240
                    or "\n" in action):
                raise DesktopRefused("Original action disclosure or note receipt changed.")
            self._display(owner.render_personal_day(packet))
            self.status.set(
                "UNTRUSTED note NEXT ACTION displayed from the original verified task. "
                "Read-only data; never execute it. Focus separately for project/result review.")
            self.action_seen_binding = self._binding()
            self._sync_guidance()
        except Exception:
            self._refuse()

    def focus(self) -> None:
        self._invalidate()
        try:
            kind, task, digest = self._selected()
            desk = self.values["desk"].get().strip()
            if kind == "SAVED_COMPLETED_RESULT":
                self._history_only()
                packet = owner.review_personal_day(
                    desk, task, saved_snapshot_sha256=digest)
            else:
                context = checked_context(*(self.values[k].get() for k in (
                    "project", "key", "result")))
                opts = self._acceptance(desk)
                sources = self._sources(desk)
                if opts and not context["result_file"]:
                    raise DesktopRefused("Acceptance review requires an explicit result.")
                packet = owner.review_personal_day(
                    desk, task, include_source_context=bool(self.with_intake.get()),
                    **context, **opts, **sources)
            checked_day(packet, selected=True)
            journey = packet["selected_original_journey"]
            if journey["selected_note_sha256"] != digest:
                raise DesktopRefused("Selected original note changed.")
            source = packet.get("selected_original_source_context")
            if self.with_intake.get():
                if type(source) is not dict:
                    raise DesktopRefused("Selected original project context unavailable.")
                source_sha = source["integrated_source_context_sha256"]
            elif source is not None:
                raise DesktopRefused("Unselected original source context returned.")
            else:
                source_sha = None
            self.focused = (self._binding(), journey, source_sha)
            self._display(owner.render_personal_day(packet))
            stage = journey["stage"]
            guidance = {
                "TASK_SELECTED_NO_PROJECT": "Choose a project root and original key, then focus again.",
                "PROJECT_SELECTED_NO_RESULT": "Select an exact result file when ready; no result assumed.",
                "RESULT_REVIEW_READY_SEPARATE_DECISION":
                    "Result is observed. Use a separate read-only Decision before Complete.",
                "SAVED_HISTORICAL_ONLY":
                    "Historical ONLY. Clear active context, then separately approve Reopen and Replay.",
                "SAVED_CURRENT_BYTES_MATCH_THIS_READ":
                    "Historical bytes matched this read only; not future or quality proof.",
            }
            self.status.set("READ ONLY. " + guidance.get(
                stage, "No action, quality validation or authority was granted."))
            self._sync_guidance()
        except Exception:
            self._refuse()

    def preview_briefing(self) -> None:
        """Show ORIGINAL #165 task/result/history evidence without approval.

        The selected action is ALWAYS hidden. A briefing never retains a
        completion decision, creates a store or upgrades a historical result.
        """
        self.decision = None
        self._sync_guidance()
        self._display("")
        try:
            kind, task, digest = self._selected()
            desk = self.values["desk"].get().strip()
            if (kind != "ACTIVE_TASK" or not desk or self.loaded_desk != desk
                    or self.focused is None or self.focused[0] != self._binding()):
                raise DesktopRefused("Focus one unchanged ACTIVE task in the loaded desk.")
            journey = self.focused[1]
            if (type(journey) is not dict
                    or journey.get("stage") != "RESULT_REVIEW_READY_SEPARATE_DECISION"
                    or journey.get("task_key_claimed") != task
                    or journey.get("selected_note_sha256") != digest):
                raise DesktopRefused("Exact original result focus is required for briefing.")
            context = checked_context(*(self.values[k].get() for k in (
                "project", "key", "result")))
            if not all(context.values()):
                raise DesktopRefused("Explicit original project and result are required.")
            self._recheck_original_source(task)
            opts = self._acceptance(desk)
            packet = owner.prepare_completion_briefing(
                desk, task, context["project_root"], context["project_key"],
                context["result_file"],
                expected_checkpoint_sha256=journey["checkpoint_sha256"],
                show_selected_action=False, **opts)
            exact = {
                "task_key_claimed": task,
                "selected_note_sha256": digest,
                "selected_project_binding_sha256": journey.get("selected_project_binding_sha256"),
                "checkpoint_sha256": journey.get("checkpoint_sha256"),
                "current_result_sha256": journey.get("current_result_sha256"),
                "decision_sha256": journey.get("decision_sha256"),
                "acceptance_claims_state": journey.get("acceptance_claims_state"),
                "unresolved_criterion_ids": journey.get("unresolved_criterion_ids"),
                "extra_known_gap_acknowledgement_required":
                    journey.get("extra_known_gap_acknowledgement_required"),
                "selected_next_action_disclosed": False,
                "selected_next_action_untrusted": None,
                "historical_result_current_bytes_verified": False,
                "separate_exact_decide_with_yes_required": True,
                "digest_authenticates_user_or_host": False,
                "result_quality_validated": False,
                "original_174_protected_fable_granted": False,
                "original_176_live_episode_or_reuse_eligible": False,
                "task_completion_approved_or_performed": False,
                "native_claude_or_hooks_executed": False,
                "database_contacted": False,
                "writes_performed": False,
                "new_store_created": False,
            }
            if (type(packet) is not dict
                    or packet.get("schema") != owner.COMPLETION_BRIEFING_SCHEMA
                    or packet.get("status") != "READ_ONLY_ONE_TASK_COMPLETION_BRIEFING"
                    or any((packet.get(name) is not value if type(value) is bool
                            or value is None else packet.get(name) != value)
                           for name, value in exact.items())):
                raise DesktopRefused("Original briefing identity or safety receipt changed.")
            # Recheck optional #168/#167/#166 sources AFTER the briefing as well.
            # Neither read nor digest is an atomic or host-identity proof.
            self._recheck_original_source(task)
            rendered = owner.render_completion_briefing(packet)
            if (type(rendered) is not str
                    or not rendered.startswith(
                        "Vres-OS PERSONAL COMPLETION BRIEFING -- READ ONLY")
                    or len(rendered) > 24000):
                raise DesktopRefused("Original briefing renderer refused.")
            self._display(rendered)
            self.status.set(
                "READ ONLY: original task, result, history counts and known gaps. "
                "No action disclosed or approval retained. Review decision separately.")
            self.briefing_seen_binding = self._binding()
            self._sync_guidance()
        except Exception:
            self._refuse()

    def preview_decision(self) -> None:
        self.decision = None
        try:
            if self.focused is None or self.focused[0] != self._binding():
                raise DesktopRefused("Re-focus the exact unchanged selected task/context.")
            kind, task, _ = self._selected()
            journey = self.focused[1]
            if kind != "ACTIVE_TASK" or journey["stage"] != "RESULT_REVIEW_READY_SEPARATE_DECISION":
                raise DesktopRefused("Select an active task with an exact observed result.")
            self._recheck_original_source(task)
            context = checked_context(*(self.values[k].get() for k in (
                "project", "key", "result")))
            opts = self._acceptance(self.values["desk"].get().strip())
            preview = owner.prepare_completion_decision(
                self.values["desk"].get().strip(), task,
                context["project_root"], context["project_key"], context["result_file"],
                expected_checkpoint_sha256=journey["checkpoint_sha256"], **opts)
            if (preview.get("status") != "READ_ONLY_EXACT_PERSONAL_COMPLETION_DECISION"
                    or preview.get("decision_sha256") != journey["decision_sha256"]
                    or preview.get("checkpoint_sha256") != journey["checkpoint_sha256"]
                    or preview.get("writes_performed") is not False
                    or preview.get("result_quality_validated") is not False):
                raise DesktopRefused("Original exact decision changed.")
            self.decision = {"binding": self._binding(), "packet": preview}
            self.status.set(
                "Read-only decision ready. Optional source context rechecked; "
                "complete only after separate approval, never as quality/host proof.")
            self._display(
                "READ-ONLY DECISION / NOT QUALITY VALIDATION\n"
                f"Task: {task}\nCheckpoint SHA-256: {preview['checkpoint_sha256']}\n"
                f"Decision SHA-256: {preview['decision_sha256']}\n"
                f"Self-claim state: {preview['acceptance_claims_state']}\n"
                f"Unresolved criterion IDs: {', '.join(preview['unresolved_criterion_ids']) or 'none'}\n"
                f"Separate gap acknowledgement: {preview['extra_known_gap_acknowledgement_required']}\n"
                f"{preview['next_safe_step']}")
            self._sync_guidance()
        except Exception:
            self._refuse()

    def complete(self) -> None:
        try:
            if self.decision is None or self.decision["binding"] != self._binding():
                raise DesktopRefused("Review the exact decision separately before completion.")
            kind, task, _ = self._selected()
            if kind != "ACTIVE_TASK":
                raise DesktopRefused("Only one current active task may be completed.")
            preview = self.decision["packet"]
            context = checked_context(*(self.values[k].get() for k in (
                "project", "key", "result")))
            opts = self._acceptance(self.values["desk"].get().strip())
            self._recheck_original_source(task)
            approved = messagebox.askyesno(
                "Separate completion approval",
                f"Complete task {task} into ORIGINAL immutable history?\n"
                f"Checkpoint: {preview['checkpoint_sha256']}\n"
                f"Decision: {preview['decision_sha256']}\n"
                "This is NOT proof of result quality.", parent=self.master)
            if not approved:
                self.status.set("Completion cancelled. No completion requested.")
                return
            known_gaps = preview["extra_known_gap_acknowledgement_required"]
            if known_gaps and not messagebox.askyesno(
                    "Separate known-gap acknowledgement",
                    "Explicitly accept the displayed unresolved criterion IDs? "
                    "These are caller claims, NOT validated quality.",
                    parent=self.master):
                self.status.set("Completion cancelled: known gaps not acknowledged.")
                return
            # Check again AFTER both consents; exact original completion digests
            # are independently re-attested by finish_reviewed_decision.
            self._recheck_original_source(task)
            result = owner.finish_reviewed_decision(
                self.values["desk"].get().strip(), task,
                context["project_root"], context["project_key"], context["result_file"],
                expected_checkpoint_sha256=preview["checkpoint_sha256"],
                expected_decision_sha256=preview["decision_sha256"],
                approved=True, accept_unresolved_claims=bool(known_gaps), **opts)
            if result.get("status") != "SEPARATELY_APPROVED_PERSONAL_RESULT_SAVED_IN_ORIGINAL_HISTORY":
                raise DesktopRefused("Original completion owner did not confirm.")
            if self.refresh():
                self.status.set(
                    "Original history saved. Historical only; reopen and replay need SEPARATE approvals.")
        except Exception:
            self._refuse()

    def reopen(self) -> None:
        try:
            _kind, task, sha = self._history_only()
            if not messagebox.askyesno(
                    "Separate reopen approval",
                    f"Reopen exact original saved task {task}?\nSnapshot SHA-256: {sha}\n"
                    "No saved result bytes will be replayed automatically.",
                    parent=self.master):
                return
            result = owner.reopen_saved(
                self.values["desk"].get().strip(), task, sha, approved=True)
            if result.get("status") != "SAVED_WORK_SESSION_TASK_REOPENED":
                raise DesktopRefused("Original reopen not confirmed.")
            if self.refresh():
                self.status.set("Reopened by original owner. Saved bytes NOT checked; replay separately.")
        except Exception:
            self._refuse()

    def replay(self) -> None:
        try:
            _kind, task, sha = self._history_only()
            if not messagebox.askyesno(
                    "Separate exact-byte replay approval",
                    f"After a separate reopen, read the original saved result for {task}?\n"
                    f"Historical snapshot SHA-256: {sha}\n"
                    "This only checks the document at the time of this read.",
                    parent=self.master):
                return
            result = owner.replay_saved(
                self.values["desk"].get().strip(), task, sha, approved=True)
            if (result.get("status") != "SAVED_WORK_SESSION_EXACT_CONTEXT_REPLAY_MATCH"
                    or result.get("current_result_bytes_matched_in_this_read") is not True
                    or result.get("future_document_bytes_guaranteed_unchanged") is not False
                    or result.get("writes_performed") is not False):
                raise DesktopRefused("Saved original bytes did not revalidate.")
            self._invalidate()
            self.status.set("Exact saved bytes matched THIS READ only. No future or quality claim.")
            self._display(
                "ORIGINAL SAVED REPLAY: CURRENT BYTES MATCHED THIS READ ONLY\n"
                f"Task: {task}\nHistorical snapshot SHA-256: {sha}\n"
                f"Result SHA-256: {result['result_sha256']}\n"
                f"Checkpoint SHA-256: {result['checkpoint_sha256']}\n"
                "No F1/Fable, memory, host, database or future-byte authority.")
        except Exception:
            self._refuse()

    def insert_starter(self) -> None:
        """User-triggered transient Markdown only; never overwrite either source."""
        if (self.values["note"].get().strip()
                or self.inline_editor.get("1.0", "end-1c").strip()):
            self.status.set("Starter NOT inserted: preserve the existing Markdown "
                            "or external note selection.")
            return
        self._edited("note")  # drop focused decisions BEFORE editing the draft
        self.inline_editor.insert("1.0", "# My task\n\n## Next action\n- \n")
        self.status.set("Transient starter only. Write a real manual next action "
                        "before separately approving an original-owner save.")

    def add_existing(self) -> None:
        """Approved one-task addition on a LOADED original desk, not a new store.

        Existing project/result/source form fields are only ephemeral UI state;
        approval explicitly covers clearing them AFTER a confirmed owner write.
        No active or historical choice is automatically focused after refresh.
        """
        try:
            desk = self.values["desk"].get().strip()
            task = self.values["new_task"].get().strip()
            note, inline = _selected_note_input(self)
            if not desk or self.loaded_desk != desk:
                raise DesktopRefused("Load the exact existing desk before adding a task.")
            if not task:
                raise DesktopRefused("Explicit task key required.")
            before = checked_day(owner.review_personal_day(desk), selected=False)
            if before.get("manual_revision_recovery_attention_required") is True:
                raise DesktopRefused(
                    "Manual revision recovery needed before adding another task.")
            input_options = {"note_markdown": inline} if inline is not None else {}
            preview = preview_existing_desk_task(desk, task, note, **input_options)
            if not messagebox.askyesno(
                    "Approve one existing-desk task",
                    f"Add NEW original scratch task {task} to this LOADED desk?\n"
                    f"Exact note SHA-256: {preview['sha256']}\n"
                    "Maximum six current tasks; no project binding, code execution, "
                    "installed change or result-quality proof.\n"
                    "On success, clear temporary project/result/source inputs and "
                    "reload without selecting a task.",
                    parent=self.master):
                self.status.set("Add task cancelled. No owner write requested.")
                return
            # Re-attest original day and selected input AFTER consent. No blind
            # retry, and no inferred consent for changed notes or desk state.
            if checked_day(owner.review_personal_day(desk), selected=False) != before:
                raise DesktopRefused("Original desk changed during approval.")
            if (_selected_note_input(self) != (note, inline)
                    or preview_existing_desk_task(
                        desk, task, note, **input_options) != preview):
                raise DesktopRefused("Selected note or task preview changed during approval.")
            created = portable.add_task(
                desk, task, note, approved=True,
                **({"note_markdown": inline, "expected_sha256": preview["sha256"]}
                   if inline is not None else {}))
            if (created.get("status") != "USER_AUTHORED_SCRATCH_DRAFT_NOT_VALIDATED"
                    or created.get("task_key_claimed") != task
                    or created.get("sha256") != preview["sha256"]
                    or created.get("installed_or_project_write_authorized") is not False):
                raise DesktopRefused("Original task creation was not confirmed; inspect desk.")
            for field in _HISTORY_CONTEXT_FIELDS:
                self.values[field].set("")
            for variable in (self.with_intake, self.with_acceptance,
                             self.with_catalog, self.with_synthetic):
                variable.set(False)
            self.values["new_task"].set("")
            self.values["note"].set("")
            _clear_inline_editor(self)
            if not self.refresh():
                raise DesktopRefused("Task may exist; original desk refresh failed.")
            if (self.inventory_packet is None
                    or not any(
                        item["kind"] == "ACTIVE_TASK"
                        and item["task_key_claimed"] == task
                        and item["selected_note_sha256"] == preview["sha256"]
                        for item in self.inventory_packet["original_offered_choices"])):
                raise DesktopRefused(
                    "New original task absent from unfiltered owner inventory; inspect desk.")
            self.status.set(
                "Task added to original desk; no project bound or row selected. "
                "Switch to ALL/ACTIVE, then explicitly select and focus it.")
        except Exception:
            self._refuse()

    def revise_selected(self) -> None:
        """Separately approved original revision: exact old/new digest, preserved history.

        No invented task store, implicit new-action execution, completion or
        recovery. A refused/partial original write is UNKNOWN: never auto-retry.
        """
        self._invalidate()
        self._display("")
        try:
            kind, task, digest = self._selected()
            desk = self.values["desk"].get().strip()
            note, inline = _selected_note_input(self)
            if (kind != "ACTIVE_TASK" or not desk or self.loaded_desk != desk
                    or self.inventory_packet is None):
                raise DesktopRefused("Load and select an active task and one Markdown source.")
            before = checked_day(owner.review_personal_day(desk), selected=False)
            checked_revision_inventory(before, task=task, note_sha256=digest)
            input_options = {"note_markdown": inline} if inline is not None else {}
            preview = preview_selected_task_revision(
                desk, task, note, digest, **input_options)
            if not messagebox.askyesno(
                    "Separate original task revision approval",
                    f"REVISE this explicitly selected ACTIVE task {task}?\n"
                    f"Existing note SHA-256: {digest}\n"
                    f"Replacement SHA-256: {preview['sha256']}\n"
                    "The ORIGINAL owner preserves the previous note in revision history.\n"
                    "The current project/result/acceptance/source inputs will be cleared.\n"
                    "No execution, completion or result-quality proof. If interrupted, "
                    "inspect the original desk manually; do not retry blindly.",
                    parent=self.master):
                self.status.set("Revision cancelled. No original revision requested.")
                return
            fresh = checked_day(owner.review_personal_day(desk), selected=False)
            if fresh != before:
                raise DesktopRefused("Original task/history changed during approval.")
            checked_revision_inventory(fresh, task=task, note_sha256=digest)
            if (_selected_note_input(self) != (note, inline)
                    or preview_selected_task_revision(
                        desk, task, note, digest, **input_options) != preview):
                raise DesktopRefused("Selected old or replacement note changed during consent.")
            result = lifecycle.revise(
                desk, task, note, approved=True,
                expected_sha256=digest, expected_new_sha256=preview["sha256"],
                **input_options)
            if (type(result) is not dict
                    or result.get("schema") != lifecycle.SCHEMA
                    or result.get("status") != "OWN_TASK_REVISED"
                    or result.get("task_key_claimed") != task
                    or result.get("previous_sha256") != digest
                    or result.get("sha256") != preview["sha256"]
                    or result.get("previous_snapshot_preserved") is not True
                    or result.get("installed_vres_modified") is not False):
                raise DesktopRefused("Revision owner receipt ambiguous; inspect before retry.")
            for field in _HISTORY_CONTEXT_FIELDS:
                self.values[field].set("")
            for variable in (self.with_intake, self.with_acceptance,
                             self.with_catalog, self.with_synthetic):
                variable.set(False)
            self.values["note"].set("")
            self.values["new_task"].set("")
            _clear_inline_editor(self)
            if not self.refresh():
                raise DesktopRefused("Revision may have occurred; original refresh failed.")
            current = self.inventory_packet
            if (current is None
                    or current["revision_snapshot_count"] != before["revision_snapshot_count"] + 1
                    or current["active_task_count"] != before["active_task_count"]
                    or current["manual_revision_recovery_attention_required"] is not False
                    or ("ACTIVE_TASK", task, preview["sha256"])
                       not in triage_personal_day(current)["rows"]):
                raise DesktopRefused("Revision readback differs; manually inspect history.")
            self.status.set(
                "Original task revised; previous note preserved in revisions. "
                "No active task auto-selected. Select and focus the new note explicitly.")
        except Exception:
            self._refuse()

    def load_archived(self) -> None:
        """Opt-in immutable original archived-snapshot inventory; no task action."""
        self._invalidate()
        self._display("")
        try:
            desk = self.values["desk"].get().strip()
            if (not desk or self.loaded_desk != desk
                    or self.inventory_packet is None):
                raise DesktopRefused("Load exact desk before inspecting archived tasks.")
            before = checked_day(owner.review_personal_day(desk), selected=False)
            if before != self.inventory_packet:
                raise DesktopRefused("Original day changed; refresh before archive inspection.")
            history = lifecycle.list_history(desk)
            archived = checked_archived_history(history, before)
            if checked_day(owner.review_personal_day(desk), selected=False) != before:
                raise DesktopRefused("Original history changed during archive inspection.")
            self._clear_archive_view()
            self.archive_packet = history
            for i, identity in enumerate(archived):
                iid = f"archived-{i}"
                self.archive_choices[iid] = identity
                self.archive_listing.insert(
                    "", "end", iid=iid, values=(identity[0], identity[1][:16]))
            self.archive_summary.set(
                f"{len(archived)} archived snapshot(s), UNDATED. "
                "Select exactly one; restoration requires separate approval.")
            self.status.set(
                "READ ONLY: original immutable archive inventory verified. "
                "Historical results were NOT opened or promoted to current.")
            self._sync_guidance()
        except Exception:
            self._clear_archive_view()
            self._refuse()

    def archive_selected(self) -> None:
        """Explicit selected active → original archived history, preserving bytes."""
        self._invalidate()
        self._display("")
        try:
            kind, task, digest = self._selected()
            desk = self.values["desk"].get().strip()
            if (kind != "ACTIVE_TASK" or not desk or self.loaded_desk != desk
                    or self.inventory_packet is None):
                raise DesktopRefused("Select one active task in the loaded original desk.")
            before = checked_day(owner.review_personal_day(desk), selected=False)
            if before != self.inventory_packet:
                raise DesktopRefused("Original day changed; refresh before archiving.")
            checked_revision_inventory(before, task=task, note_sha256=digest)
            history = lifecycle.list_history(desk)
            checked_archived_history(history, before)
            if not messagebox.askyesno(
                    "Separate archive approval",
                    f"ARCHIVE selected ACTIVE task {task}?\n"
                    f"Exact note SHA-256: {digest}\n"
                    "The original note moves into immutable ARCHIVED history. "
                    "It is NOT completed and cannot be replayed as a saved result.\n"
                    "Restoring requires separate approval. No automatic focus.",
                    parent=self.master):
                self.status.set("Archive cancelled. No original task write requested.")
                return
            if (checked_day(owner.review_personal_day(desk), selected=False) != before
                    or lifecycle.list_history(desk) != history):
                raise DesktopRefused("Original day/history changed during archive approval.")
            checked_revision_inventory(before, task=task, note_sha256=digest)
            moved = lifecycle.move_out(
                desk, task, state="archived", approved=True, expected_sha256=digest)
            if (type(moved) is not dict or moved.get("schema") != lifecycle.SCHEMA
                    or moved.get("status") != "OWN_TASK_ARCHIVED"
                    or moved.get("task_key_claimed") != task
                    or moved.get("sha256") != digest
                    or moved.get("archived_bytes_preserved") is not True
                    or moved.get("installed_vres_modified") is not False):
                raise DesktopRefused("Archive write uncertain; inspect original history.")
            if not self.refresh():
                raise DesktopRefused("Archive may exist; original day refresh failed.")
            day = self.inventory_packet
            if (day is None
                    or day["archived_snapshot_count"] != before["archived_snapshot_count"] + 1
                    or day["active_task_count"] != before["active_task_count"] - 1
                    or ("ACTIVE_TASK", task, digest) in triage_personal_day(day)["rows"]):
                raise DesktopRefused("Archive readback differs; manually inspect history.")
            # Independently re-query the COMPLETE original history after the write.
            # Uncertain readback requires inspection, never a blind retry.
            updated_history = lifecycle.list_history(desk)
            checked_archived_history(updated_history, day)
            previous_rows = history["snapshots"]
            current_rows = updated_history["snapshots"]
            added_rows = [row for row in current_rows if row not in previous_rows]
            if (len(current_rows) != len(previous_rows) + 1
                    or any(row not in current_rows for row in previous_rows)
                    or len(added_rows) != 1
                    or added_rows[0]["state"] != "archived"
                    or added_rows[0]["task_key_claimed"] != task
                    or added_rows[0]["sha256"] != digest):
                raise DesktopRefused("Archive history identity changed; inspect history.")
            self.status.set(
                "Original task archived, NOT completed. No task auto-selected. "
                "Read archived history separately to restore with new consent.")
        except Exception:
            self._refuse()

    def restore_archived(self) -> None:
        """Explicit original archived snapshot → new active task, no overwrite."""
        self._invalidate()
        self._display("")
        try:
            desk = self.values["desk"].get().strip()
            selected = self.archive_listing.selection()
            if (not desk or self.loaded_desk != desk
                    or self.inventory_packet is None or self.archive_packet is None
                    or len(selected) != 1 or selected[0] not in self.archive_choices):
                raise DesktopRefused("Load and select exactly one original archived snapshot.")
            task, digest = self.archive_choices[selected[0]]
            before = checked_day(owner.review_personal_day(desk), selected=False)
            if (before != self.inventory_packet
                    or before["manual_revision_recovery_attention_required"] is not False):
                raise DesktopRefused("Original day changed or pending revision needs review.")
            history = lifecycle.list_history(desk)
            if (history != self.archive_packet
                    or (task, digest) not in checked_archived_history(history, before)):
                raise DesktopRefused("Original archived snapshot changed; reload history.")
            if (before["active_task_count"] >= portable._MAX_CHILDREN
                    or any(item["kind"] == "ACTIVE_TASK"
                           and item["task_key_claimed"] == task
                           for item in before["original_offered_choices"])):
                raise DesktopRefused("Original active task slot unavailable for restore.")
            if not messagebox.askyesno(
                    "Separate archived-task restore approval",
                    f"RESTORE original archived task {task} into an ABSENT active slot?\n"
                    f"Historical note SHA-256: {digest}\n"
                    "Original archived snapshot stays preserved. This does not "
                    "complete or replay a result; no automatic focus or execution.",
                    parent=self.master):
                self.status.set("Restore cancelled. No original task write requested.")
                return
            if (checked_day(owner.review_personal_day(desk), selected=False) != before
                    or lifecycle.list_history(desk) != history):
                raise DesktopRefused("Original day or archived history changed during approval.")
            reopened = lifecycle.reopen(
                desk, task, state="archived", expected_sha256=digest, approved=True)
            if (type(reopened) is not dict
                    or reopened.get("schema") != lifecycle.SCHEMA
                    or reopened.get("status") != "OWN_TASK_REOPENED"
                    or reopened.get("task_key_claimed") != task
                    or reopened.get("sha256") != digest
                    or reopened.get("archived_snapshot_preserved") is not True
                    or reopened.get("installed_vres_modified") is not False):
                raise DesktopRefused("Archive restore uncertain; inspect original desk.")
            if not self.refresh():
                raise DesktopRefused("Restore may exist; original day refresh failed.")
            day = self.inventory_packet
            if (day is None
                    or day["archived_snapshot_count"] != before["archived_snapshot_count"]
                    or day["active_task_count"] != before["active_task_count"] + 1
                    or ("ACTIVE_TASK", task, digest) not in triage_personal_day(day)["rows"]):
                raise DesktopRefused("Restored active task readback differs; inspect desk.")
            # Restore must preserve every existing original history identity.
            updated_history = lifecycle.list_history(desk)
            checked_archived_history(updated_history, day)
            if updated_history != history:
                raise DesktopRefused("Restore changed original history; inspect desk.")
            self.status.set(
                "Original archived note restored to an ACTIVE slot. "
                "Archived copy preserved; manually reselect and focus the active task.")
        except Exception:
            self._refuse()

    def start(self) -> None:
        """Start NEW original desk from one separately approved note source.

        Inline editor contents remain ephemeral until the original owner has
        created and independently read back exactly one digest-bound note.
        """
        try:
            context = checked_context(*(self.values[k].get() for k in (
                "project", "key", "result")))
            if (self.with_acceptance.get() or self.with_intake.get()
                    or self.with_catalog.get() or self.with_synthetic.get()
                    or any(self.values[k].get().strip() for k in (
                        "acceptance_path", "acceptance_sha", "catalog_root",
                        "catalog_namespace", "catalog_source", "catalog_sha",
                        "catalog_revision", "synthetic_file", "synthetic_sha"))):
                raise DesktopRefused("Clear read-only source and review inputs before NEW scratch.")
            if not context["project_root"] or context["result_file"]:
                raise DesktopRefused("New scratch requires explicit empty project; no result yet.")
            task = self.values["new_task"].get().strip()
            note, inline = _selected_note_input(self)
            if not task:
                raise DesktopRefused("Explicit new task required.")
            desk = self.values["desk"].get().strip()
            root = portable._desk(desk, must_exist=False)
            project = owner.intake._plain_project_root(context["project_root"])
            under = portable.project_draft._under
            if under(root, project) or under(project, root):
                raise DesktopRefused("Project and new desk must be separate.")
            owner._require_empty_new_project(project)
            if note is not None and under(Path(note), project):
                raise DesktopRefused("Markdown input must be outside the project.")
            markdown = _source_markdown(root, note, inline)
            if inline is not None:
                portable.continuity._action(markdown)  # read only; no execution
            preview = portable.workbench.preview_note(task, markdown)
            if not messagebox.askyesno(
                    "Approve new scratch",
                    f"Create a NEW original scratch desk/task {task}?\n"
                    f"Exact note SHA-256: {preview['sha256']}\n"
                    "Desk must NOT exist; separate project must be EMPTY. "
                    "Only user-authored nonsensitive notes; no installation or execution. "
                    "If interrupted, inspect the desk before any retry.",
                    parent=self.master):
                self.status.set("New scratch cancelled. No original-owner write requested.")
                return
            # The note and exact selected fields must remain unchanged across
            # consent; the original owner still verifies all paths before write.
            if (_selected_note_input(self) != (note, inline)
                    or _source_markdown(root, note, inline) != markdown
                    or portable.workbench.preview_note(task, markdown) != preview
                    or self.values["desk"].get().strip() != desk
                    or self.values["new_task"].get().strip() != task
                    or checked_context(*(self.values[k].get() for k in (
                        "project", "key", "result"))) != context):
                raise DesktopRefused("New scratch source or selection changed during consent.")
            result = owner.start_session(
                desk, task, note, context["project_root"], context["project_key"],
                approved=True, **({"note_markdown": inline,
                                   "expected_sha256": preview['sha256']}
                                  if inline is not None else {}))
            if (result.get("status") != "NEW_ORIGINAL_OWNER_WORK_SESSION_STARTED"
                    or result.get("task_key_claimed") != task
                    or result.get("selected_note_sha256") != preview['sha256']
                    or result.get("installed_vres_modified") is not False):
                raise DesktopRefused("Original scratch start not verified.")
            if (not self.refresh() or self.inventory_packet is None
                    or ("ACTIVE_TASK", task, preview['sha256'])
                       not in triage_personal_day(self.inventory_packet)['rows']):
                raise DesktopRefused("New scratch may exist; inspect original desk before retry.")
            _clear_inline_editor(self)
            self.status.set(
                "New original task saved and verified; no automatic selection. "
                "Choose its ACTIVE row, view next action, then focus. No project file written.")
        except Exception:
            self._refuse()


def main() -> None:
    """Only a manually invoked source entry; never auto-invoked by import."""
    window = tk.Tk()
    PersonalDayDesktop(window)
    window.mainloop()


if __name__ == "__main__":
    main()
