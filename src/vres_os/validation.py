"""Fresh-review evidence. The MCP caller cannot write validation_status='passed'.

Only the lifecycle handler consumes a completed validator subagent report.
This is host-observed provenance, NOT an OS sandbox or cryptographic attestation.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

from .redaction import redact
from .transcript import _text_from_content, transcript_tail

STATE_FIELDS = (
    "objective",
    "current_phase",
    "current_step",
    "state_summary",
    "next_action",
    # latest_user_instruction is continuity/provenance metadata. Material user intent
    # must be reflected in objective/state/constraints before review; otherwise a
    # post-review lifecycle write would spuriously stale an otherwise frozen review.
    "open_questions",
    "assumptions",
    "constraints",
    "decisions",
    "completed_work",
    "pending_work",
    "relevant_objects",
)
MAX_REVIEW_BYTES = 128 * 1024 * 1024


def _connect():
    from .db import connect

    return connect()


def state_digest(state: dict[str, Any]) -> str:
    content = {k: state.get(k) for k in STATE_FIELDS}
    encoded = json.dumps(content, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def artifact_manifest(root: Path, paths: list[str]) -> dict[str, str]:
    root = root.resolve(strict=True)
    if len(paths) > 1000:
        raise ValueError("Review scope exceeds 1000 files; split into complete reviewable slices")
    result: dict[str, str] = {}
    total = 0
    for name in paths:
        raw = root / name
        p = raw.resolve(strict=True)
        if not p.is_relative_to(root) or not p.is_file() or raw.is_symlink():
            raise ValueError("Reviewed artifact must be a regular file inside the project")
        before = p.stat()
        total += before.st_size
        if total > MAX_REVIEW_BYTES:
            raise ValueError("Review artifacts exceed the byte budget")
        digest = hashlib.sha256()
        with p.open("rb") as stream:
            read = 0
            while block := stream.read(1024 * 1024):
                read += len(block)
                if read > before.st_size:
                    raise ValueError("Reviewed file changed during hashing")
                digest.update(block)
        after = p.stat()
        if (before.st_mtime_ns, before.st_size, before.st_ino) != (
            after.st_mtime_ns,
            after.st_size,
            after.st_ino,
        ):
            raise ValueError("Reviewed file changed during hashing")
        result[p.relative_to(root).as_posix()] = digest.hexdigest()
    return result


def parse_validator_report(text: str) -> dict:
    if not isinstance(text, str) or len(text) > 100_000:
        raise ValueError("Validator report is missing or oversized")
    text = text.strip()
    if text.startswith("```json\n") and text.endswith("```"):
        text = text[8:-3].strip()
    report = json.loads(text)
    if not isinstance(report, dict):
        raise ValueError("Validator report must be a JSON object")
    if not report.get("request_key") or report.get("outcome") not in {"passed", "failed"}:
        raise ValueError("Validator must identify its request and outcome")
    checks = report.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("Validator report requires executable/documented checks")
    if any(
        not isinstance(c, dict)
        or not c.get("evidence")
        or c.get("status") not in {"passed", "failed", "not_run"}
        for c in checks
    ):
        raise ValueError("Every check needs a status and concrete evidence")
    if report["outcome"] == "passed" and any(c["status"] != "passed" for c in checks):
        raise ValueError("A skipped or failed check cannot establish PASS")
    return report


def _assistant_handback_messages(value: Any) -> list[str]:
    """Extract only host-recorded SubagentHandback messages from assistant output.

    A validator can hand its canonical report back through Claude Code's
    SubagentHandback tool without repeating the report as a text block. This helper
    deliberately ignores every other tool_use shape and never reads tool results.
    """
    if not isinstance(value, dict):
        return []
    content = value.get("content")
    if not isinstance(content, list):
        return []
    result: list[str] = []
    for block in content[:100]:
        if not isinstance(block, dict) or block.get("type") != "tool_use":
            continue
        if block.get("name") != "SubagentHandback":
            continue
        tool_input = block.get("input")
        if not isinstance(tool_input, dict):
            continue
        message = tool_input.get("message")
        if isinstance(message, str) and message.strip():
            result.append(message)
    return result


def observed_validator_report(final_text: str, records: list[dict[str, Any]]) -> tuple[dict, str]:
    """Return the newest canonical validator report from host-observed assistant output.

    Prefer SubagentStop's final assistant message. If the validator emitted a valid
    canonical report and then a harmless trailing assistant message, recover only
    from assistant-authored transcript text or the message of an assistant-authored
    SubagentHandback tool call. Arbitrary tool calls, tool results, and other
    transcript data are never eligible evidence for the verdict.
    """
    final = final_text.strip() if isinstance(final_text, str) else ""
    if final:
        try:
            return parse_validator_report(final), "last_assistant_message"
        except (ValueError, TypeError, RecursionError):
            pass

    for obj in reversed(records):
        if not isinstance(obj, dict):
            continue
        message = obj.get("message")
        role = message.get("role") if isinstance(message, dict) else obj.get("role")
        if obj.get("type") != "assistant" and role != "assistant":
            continue
        observed = message if isinstance(message, dict) else obj
        texts = _text_from_content(observed)
        handbacks = _assistant_handback_messages(observed)
        candidates: list[str] = []
        if texts:
            candidates.append("\n".join(texts))
            candidates.extend(reversed(texts))
        candidates.extend(reversed(handbacks))
        seen: set[str] = set()
        for candidate in candidates:
            candidate = candidate.strip()
            if not candidate or candidate == final or candidate in seen:
                continue
            seen.add(candidate)
            try:
                return parse_validator_report(candidate), "assistant_transcript"
            except (ValueError, TypeError, RecursionError):
                continue
    raise ValueError(
        "Validator report was not found in the final assistant message or observed assistant transcript"
    )


class ValidationService:
    def prepare(
        self,
        task_key: str,
        project_id: int,
        root: Path,
        paths: list[str],
        *,
        context_type: str | None = None,
        context_key: str | None = None,
        context_payload: dict[str, Any] | None = None,
    ) -> dict:
        if (context_type is None) != (context_key is None):
            raise ValueError("Validation context_type and context_key must be supplied together")
        if context_type is not None and (not context_type.strip() or not context_key.strip()):
            raise ValueError("Validation context must be non-empty")
        manifest = artifact_manifest(root, paths)
        key = f"VAL-{uuid.uuid4().hex[:16]}"
        safe_context = redact(context_payload or {}) if context_type is not None else None
        with _connect() as conn, conn.transaction():
            row = conn.execute(
                "SELECT t.objective,t.project_id,t.status,s.* FROM vres.tasks t "
                "JOIN vres.task_state s ON s.task_id=t.id "
                "WHERE t.task_key=%s FOR UPDATE OF s",
                (task_key,),
            ).fetchone()
            if (
                not row
                or row["project_id"] != project_id
                or row["status"] not in {"active", "blocked", "waiting_user"}
            ):
                raise ValueError("Validation must target an unfinished task in this project")
            routed = conn.execute(
                "SELECT 1 FROM vres.routing_requests "
                "WHERE task_id=%s AND status='routed' LIMIT 1",
                (row["task_id"],),
            ).fetchone()
            if routed:
                final = conn.execute(
                    "SELECT payload FROM vres.task_events "
                    "WHERE task_id=%s AND event_type='ORCHESTRATION_FINAL' "
                    "ORDER BY id DESC LIMIT 1",
                    (row["task_id"],),
                ).fetchone()
                if not final or final["payload"].get("decision_ready") is not True:
                    raise ValueError(
                        "Routed task must have a latest decision-ready orchestration final "
                        "before protected validation can be prepared"
                    )
            conn.execute(
                "UPDATE vres.task_state SET validation_status='pending' WHERE task_id=%s",
                (row["task_id"],),
            )
            conn.execute(
                """
                INSERT INTO vres.validation_requests(
                  request_key,task_id,state_digest,artifact_manifest,
                  context_type,context_key,context_payload
                ) VALUES (%s,%s,%s,%s::jsonb,%s,%s,%s::jsonb)
                """,
                (
                    key,
                    row["task_id"],
                    state_digest(dict(row)),
                    json.dumps(manifest),
                    context_type,
                    context_key,
                    json.dumps(safe_context) if safe_context is not None else None,
                ),
            )
        instruction = (
            "Return ONLY one JSON object. Use lowercase outcome exactly 'passed' or 'failed'. "
            "Each checks item must use lowercase status exactly 'passed', 'failed', or 'not_run' and include evidence. "
            "Shape: {request_key, outcome, checks:[{status,evidence}]}."
        )
        if context_type is not None:
            instruction += " Preserve context_key exactly and return it as context_key."
            if context_type == "procedure_replay":
                instruction += (
                    " Return optimization_replay with replay_key, output_equivalent, "
                    "and protected_regression."
                )
            elif context_type == "model_experiment":
                instruction += (
                    " Return model_experiment with experiment_key, candidate_quality_not_worse, "
                    "and protected_regression."
                )
        return {
            "request_key": key,
            "task_key": task_key,
            "artifacts": manifest,
            "validator": "vres-os:validator",
            "model": "fable",
            "effort": "high",
            "context_type": context_type,
            "context_key": context_key,
            "context": safe_context,
            "instruction": instruction,
        }

    def record_from_hook(self, payload: dict, project_id: int, root: Path) -> dict:
        if (
            payload.get("agent_type") != "vres-os:validator"
            or not payload.get("agent_id")
            or not payload.get("session_id")
        ):
            raise ValueError("Only an observed namespaced validator completion is accepted")
        transcript = payload.get("agent_transcript_path")
        if not transcript:
            raise ValueError("Missing validator transcript; model identity cannot be verified")
        records = transcript_tail(Path(transcript).expanduser())
        models = [
            x["message"].get("model")
            for x in records
            if isinstance(x.get("message"), dict)
            and x.get("type") == "assistant"
            and x["message"].get("model")
        ]
        if not models or not all(
            m == "fable" or m.startswith("claude-fable-") for m in models
        ):
            raise ValueError("Observed validator model is missing or below the protected Fable family")
        report, report_source = observed_validator_report(
            payload.get("last_assistant_message", ""), records
        )
        with _connect() as conn, conn.transaction():
            request = conn.execute(
                "SELECT r.*,t.project_id,t.task_key,t.objective FROM vres.validation_requests r "
                "JOIN vres.tasks t ON t.id=r.task_id "
                "WHERE request_key=%s FOR UPDATE OF r",
                (report["request_key"],),
            ).fetchone()
            if not request or request["project_id"] != project_id:
                raise ValueError("Validator request is unknown or belongs to another project")
            if request.get("context_type"):
                if report.get("context_key") != request["context_key"]:
                    raise ValueError("Validator report does not match the frozen validation context")
                if request["context_type"] == "procedure_replay":
                    replay = report.get("optimization_replay")
                    if not isinstance(replay, dict) or replay.get("replay_key") != request["context_key"]:
                        raise ValueError("Replay validator report does not identify the frozen replay")
                    if type(replay.get("output_equivalent")) is not bool:
                        raise ValueError("Replay report must state output_equivalent as a boolean")
                    if type(replay.get("protected_regression")) is not bool:
                        raise ValueError("Replay report must state protected_regression as a boolean")
                elif request["context_type"] == "model_experiment":
                    experiment = report.get("model_experiment")
                    if (
                        not isinstance(experiment, dict)
                        or experiment.get("experiment_key") != request["context_key"]
                    ):
                        raise ValueError("Model experiment report does not identify the frozen experiment")
                    if type(experiment.get("candidate_quality_not_worse")) is not bool:
                        raise ValueError(
                            "Model experiment report must state candidate_quality_not_worse as a boolean"
                        )
                    if type(experiment.get("protected_regression")) is not bool:
                        raise ValueError(
                            "Model experiment report must state protected_regression as a boolean"
                        )
            session = conn.execute(
                "SELECT task_id FROM vres.sessions WHERE provider='claude' "
                "AND provider_session_id=%s AND project_id=%s AND ended_at IS NULL "
                "ORDER BY started_at DESC LIMIT 1",
                (payload["session_id"], project_id),
            ).fetchone()
            if not session or session["task_id"] != request["task_id"]:
                raise ValueError("Validator session is not bound to this task")
            if request["status"] != "pending":
                return {"recorded": False, "reason": "request already consumed"}
            row = conn.execute(
                "SELECT * FROM vres.task_state WHERE task_id=%s FOR UPDATE",
                (request["task_id"],),
            ).fetchone()
            state = dict(row) | {"objective": request["objective"]}
            if state_digest(state) != request["state_digest"]:
                raise ValueError("Task changed during validation; fresh review required")
            if artifact_manifest(root, list(request["artifact_manifest"])) != request[
                "artifact_manifest"
            ]:
                raise ValueError("Reviewed files changed; fresh review required")
            conn.execute(
                "UPDATE vres.validation_requests SET status=%s,observed_model=%s,"
                "agent_id=%s,session_id=%s,report=%s::jsonb,completed_at=now() WHERE id=%s",
                (
                    report["outcome"],
                    models[-1],
                    payload["agent_id"],
                    payload["session_id"],
                    json.dumps(redact(report)),
                    request["id"],
                ),
            )
            conn.execute(
                "UPDATE vres.task_state SET validation_status=%s WHERE task_id=%s",
                (report["outcome"], request["task_id"]),
            )
        return {
            "recorded": True,
            "request_key": report["request_key"],
            "outcome": report["outcome"],
            "report_source": report_source,
        }

    def assert_current(
        self,
        task_key: str,
        project_id: int,
        root: Path,
        request_key: str | None = None,
    ) -> dict:
        with _connect() as conn:
            if request_key is None:
                request = conn.execute(
                    "SELECT r.*,t.objective,t.project_id FROM vres.validation_requests r "
                    "JOIN vres.tasks t ON t.id=r.task_id "
                    "WHERE t.task_key=%s AND t.project_id=%s "
                    "ORDER BY r.id DESC LIMIT 1",
                    (task_key, project_id),
                ).fetchone()
            else:
                request = conn.execute(
                    "SELECT r.*,t.objective,t.project_id FROM vres.validation_requests r "
                    "JOIN vres.tasks t ON t.id=r.task_id "
                    "WHERE t.task_key=%s AND t.project_id=%s AND r.request_key=%s "
                    "ORDER BY r.id DESC LIMIT 1",
                    (task_key, project_id, request_key),
                ).fetchone()
            if not request or request["status"] != "passed":
                raise ValueError("No current host-observed passing review exists for this task")
            state = conn.execute(
                "SELECT * FROM vres.task_state WHERE task_id=%s", (request["task_id"],)
            ).fetchone()
            if not state or state["validation_status"] != "passed":
                raise ValueError("Task is not currently validated")
            if state_digest(dict(state) | {"objective": request["objective"]}) != request[
                "state_digest"
            ]:
                raise ValueError("Task changed after review; revalidation required")
            if artifact_manifest(root, list(request["artifact_manifest"])) != request[
                "artifact_manifest"
            ]:
                raise ValueError("Reviewed files changed after PASS; revalidation required")
        return dict(request)
