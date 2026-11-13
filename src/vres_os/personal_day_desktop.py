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
            "acceptance_path", "acceptance_sha")}
        self.with_intake = tk.BooleanVar(value=False)
        self.with_acceptance = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Choose an explicit scratch desk and select Load.")
        self.choices: dict[str, tuple[str, str, str]] = {}
        self.focused: tuple | None = None
        self.decision: dict | None = None
        self._draw()

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
        tasks.rowconfigure(0, weight=1)
        self.listing = ttk.Treeview(
            tasks, columns=("kind", "task", "note"), show="headings",
            selectmode="browse", height=7)
        for name, heading, width in (
                ("kind", "Original kind", 180), ("task", "Task key", 260),
                ("note", "Note SHA-256 (short display)", 280)):
            self.listing.heading(name, text=heading)
            self.listing.column(name, width=width, anchor="w")
        self.listing.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(tasks, orient="vertical", command=self.listing.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listing.configure(yscrollcommand=scrollbar.set)
        self.listing.bind("<<TreeviewSelect>>", lambda _event: self._invalidate())

        context = ttk.LabelFrame(self, text="Explicit project / result (never auto-discovered)")
        context.grid(row=3, column=0, sticky="ew", pady=6)
        context.columnconfigure(1, weight=1)
        self._field(context, 0, "Project root", "project")
        self._field(context, 1, "Original project key", "key")
        self._field(context, 2, "Result file", "result")
        ttk.Checkbutton(
            context, text="Read-only original #168 project/source intake",
            variable=self.with_intake).grid(row=3, column=1, sticky="w")
        self._field(context, 4, "Optional acceptance file in scratch desk", "acceptance_path")
        self._field(context, 5, "Expected acceptance SHA-256", "acceptance_sha")
        ttk.Checkbutton(
            context, text="Explicitly include caller-supplied acceptance self-claims",
            variable=self.with_acceptance).grid(row=6, column=1, sticky="w")

        buttons = ttk.Frame(self)
        buttons.grid(row=4, column=0, sticky="ew", pady=5)
        for column, (label, method) in enumerate((
                ("Focus / inspect", self.focus),
                ("Decision (read only)", self.preview_decision),
                ("Complete (separate approval)", self.complete),
                ("Reopen (approval)", self.reopen),
                ("Verify saved bytes (approval)", self.replay))):
            ttk.Button(buttons, text=label, command=method).grid(
                row=0, column=column, padx=3)

        report = ttk.LabelFrame(self, text="Original owner view · historical is NOT current")
        report.grid(row=5, column=0, sticky="nsew", pady=6)
        report.columnconfigure(0, weight=1)
        report.rowconfigure(0, weight=1)
        self.detail = tk.Text(report, wrap="word", height=11, state="disabled")
        self.detail.grid(row=0, column=0, sticky="nsew")
        ttk.Scrollbar(report, orient="vertical", command=self.detail.yview).grid(
            row=0, column=1, sticky="ns")

        create = ttk.LabelFrame(self, text="Optional NEW scratch start (absent desk + empty project only)")
        create.grid(row=6, column=0, sticky="ew")
        create.columnconfigure(1, weight=1)
        self._field(create, 0, "New task key", "new_task")
        self._field(create, 1, "Existing nonsensitive Markdown note", "note")
        ttk.Button(create, text="Start NEW scratch with separate approval",
                   command=self.start).grid(row=1, column=2, padx=4)
        ttk.Label(self, textvariable=self.status, wraplength=900).grid(
            row=7, column=0, sticky="w", pady=5)

    def _display(self, content: str) -> None:
        self.detail.configure(state="normal")
        self.detail.delete("1.0", tk.END)
        self.detail.insert("1.0", content[:24000])
        self.detail.configure(state="disabled")

    def _invalidate(self) -> None:
        self.focused = None
        self.decision = None

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
                    "project", "key", "result", "acceptance_path", "acceptance_sha")),
                bool(self.with_acceptance.get()), bool(self.with_intake.get()))

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

    def _history_only(self) -> tuple[str, str, str]:
        kind, task, digest = self._selected()
        if kind != "SAVED_COMPLETED_RESULT":
            raise DesktopRefused("Select a saved completed result for this operation.")
        if (any(self.values[n].get().strip() for n in (
                "project", "key", "result", "acceptance_path", "acceptance_sha"))
                or self.with_intake.get() or self.with_acceptance.get()):
            raise DesktopRefused("Clear active context and opt-ins before saved history.")
        return kind, task, digest

    def refresh(self) -> bool:
        self._invalidate()
        self.choices.clear()
        self.listing.delete(*self.listing.get_children())
        self._display("")
        try:
            packet = checked_day(
                owner.review_personal_day(self.values["desk"].get().strip()),
                selected=False)
            for idx, item in enumerate(packet["original_offered_choices"]):
                identity = (item["kind"], item["task_key_claimed"],
                            item["selected_note_sha256"])
                iid = f"choice-{idx}"
                self.choices[iid] = identity
                self.listing.insert("", "end", iid=iid, values=(
                    identity[0], identity[1], identity[2][:16]))
            self.status.set(
                f"Read-only: {packet['active_task_count']} active; "
                f"{packet['saved_completed_snapshot_count']} historical completed snapshots (undated).")
            self._display(owner.render_personal_day(packet))
            return True
        except Exception:
            self._refuse()
            return False

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
                if opts and not context["result_file"]:
                    raise DesktopRefused("Acceptance review requires an explicit result.")
                packet = owner.review_personal_day(
                    desk, task, include_source_context=bool(self.with_intake.get()),
                    **context, **opts)
            checked_day(packet, selected=True)
            journey = packet["selected_original_journey"]
            if journey["selected_note_sha256"] != digest:
                raise DesktopRefused("Selected original note changed.")
            self.focused = (self._binding(), journey)
            self._display(owner.render_personal_day(packet))
            self.status.set("READ ONLY. Focus did not approve or complete anything.")
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
            self.status.set("Decision prepared READ ONLY. Completion requires another action.")
            self._display(
                "READ-ONLY DECISION / NOT QUALITY VALIDATION\n"
                f"Task: {task}\nCheckpoint SHA-256: {preview['checkpoint_sha256']}\n"
                f"Decision SHA-256: {preview['decision_sha256']}\n"
                f"Self-claim state: {preview['acceptance_claims_state']}\n"
                f"Unresolved criterion IDs: {', '.join(preview['unresolved_criterion_ids']) or 'none'}\n"
                f"Separate gap acknowledgement: {preview['extra_known_gap_acknowledgement_required']}\n"
                f"{preview['next_safe_step']}")
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

    def start(self) -> None:
        try:
            context = checked_context(*(self.values[k].get() for k in (
                "project", "key", "result")))
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
