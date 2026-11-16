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
else:
    from . import personal_work_session as owner
    from . import personal_portable_desk as portable


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
                next_step = ("Step 4/4: Separately approve completion after reviewing "
                             "the exact read-only decision. No result-quality proof.")
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


def preview_existing_desk_task(desk_path: str, task: str, note_file: str) -> dict:
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
    selected_note = Path(note_file)
    if portable.project_draft._under(selected_note, root):
        raise DesktopRefused("Input note must remain outside the existing scratch desk.")
    markdown = portable.project_draft._manual_markdown(note_file)
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
        self.loaded_desk: str | None = None
        self.inventory_packet: dict | None = None
        self.triage_query = tk.StringVar(value="")
        self.triage_mode = tk.StringVar(value="ALL")
        self.triage_summary = tk.StringVar(value="Load the original day for triage.")
        self.focused: tuple | None = None
        self.decision: dict | None = None
        self.guide = tk.StringVar(value="Step 1/4: Load an exact desk and select a task.")
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
        workspace.grid(row=3, column=0, sticky="ew", pady=6)

        active = ttk.Frame(workspace, padding=5)
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
        for column in range(4):
            buttons.columnconfigure(column, weight=1)
        ttk.Label(buttons, textvariable=self.guide, wraplength=900).grid(
            row=2, column=0, columnspan=4, sticky="w", pady=(7, 0))

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
        self._field(create, 1, "Existing nonsensitive Markdown note", "note")
        task_actions = ttk.Frame(create)
        task_actions.grid(row=2, column=0, columnspan=2, sticky="w", pady=4)
        self.add_button = ttk.Button(
            task_actions, text="Add task to LOADED desk (approve)", command=self.add_existing)
        self.add_button.pack(side="left", padx=4)
        ttk.Button(task_actions, text="Start NEW desk/task (approve)",
                   command=self.start).pack(side="left", padx=4)
        ttk.Label(task_actions, text="No automatic selection or project binding.").pack(
            side="left", padx=10)
        ttk.Label(self, textvariable=self.status, wraplength=900).grid(
            row=6, column=0, sticky="w", pady=5)

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
            return guided_action_plan(None)
        current_focus = self.focused is not None and self.focused[0] == binding
        current_decision = (current_focus and self.decision is not None
                            and self.decision.get("binding") == binding)
        stage = self.focused[1].get("stage") if current_focus else None
        return guided_action_plan(
            kind, stage, focused=current_focus,
            decision_ready=current_decision,
            history_clear=self._history_inputs_clear())

    def _sync_guidance(self) -> None:
        plan = self._ui_plan()
        for name, button in self.action_buttons.items():
            button.configure(
                state="normal" if plan["enabled"][name] else "disabled")
        self.guide.set(plan["next_step"])
        self.add_button.configure(
            state="normal" if self.loaded_desk == self.values["desk"].get().strip()
            and bool(self.loaded_desk) else "disabled")
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
        self._invalidate()
        self._display("")
        if field == "desk":
            self.status.set("Desk changed. Load this desk before selecting a task.")
        else:
            self.status.set("Inputs changed. Focus the exact task again before review.")
        self._sync_guidance()

    def _invalidate(self) -> None:
        self.focused = None
        self.decision = None
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

    def add_existing(self) -> None:
        """Approved one-task addition on a LOADED original desk, not a new store.

        Existing project/result/source form fields are only ephemeral UI state;
        approval explicitly covers clearing them AFTER a confirmed owner write.
        No active or historical choice is automatically focused after refresh.
        """
        try:
            desk = self.values["desk"].get().strip()
            task = self.values["new_task"].get().strip()
            note = self.values["note"].get().strip()
            if not desk or self.loaded_desk != desk:
                raise DesktopRefused("Load the exact existing desk before adding a task.")
            if not task or not note:
                raise DesktopRefused("Explicit task key and ordinary Markdown note required.")
            before = checked_day(owner.review_personal_day(desk), selected=False)
            preview = preview_existing_desk_task(desk, task, note)
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
            if preview_existing_desk_task(desk, task, note) != preview:
                raise DesktopRefused("Selected note or task preview changed during approval.")
            created = portable.add_task(desk, task, note, approved=True)
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

    def start(self) -> None:
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
            note = self.values["note"].get().strip()
            if not task or not note:
                raise DesktopRefused("Explicit new task and existing note required.")
            if not messagebox.askyesno(
                    "Approve new scratch",
                    f"Create a NEW original scratch desk/task {task}?\n"
                    "Only if desk does NOT exist, project is EMPTY and note is nonsensitive. "
                    "No installed Windows Vres modification.",
                    parent=self.master):
                return
            result = owner.start_session(
                self.values["desk"].get().strip(), task, note,
                context["project_root"], context["project_key"], approved=True)
            if result.get("status") != "NEW_ORIGINAL_OWNER_WORK_SESSION_STARTED":
                raise DesktopRefused("Original scratch start not verified.")
            if self.refresh():
                self.status.set("New original scratch task created; no project file was written.")
        except Exception:
            self._refuse()


def main() -> None:
    """Only a manually invoked source entry; never auto-invoked by import."""
    window = tk.Tk()
    PersonalDayDesktop(window)
    window.mainloop()


if __name__ == "__main__":
    main()
