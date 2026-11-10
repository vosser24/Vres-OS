"""#166 PERSONAL global Claude legacy migration review: SYNTHETIC, NOT AUTHORITY.

Every item is derived from a sealed, *simulated* quarantined FixtureTransaction.
A draft and choice sheet are never treated as actual user consent, model review,
validated provenance, installed policy, a live snapshot, or activation permission.
No file/profile/host/credential/network/DB operations; no legacy bytes are rendered.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .global_claude_fixture_transaction import (
    FixtureTransaction,
    GlobalFixtureRefusal,
    inspect_global_fixture, rollback_global_fixture,
)

_SCHEMA = "vres-personal-synthetic-global-legacy-migration-review/1"
_MAX_ITEMS = 96
_MAX_OUTPUT = 17000
_SHA = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_SEGMENT = re.compile(r"(KEEP|DROP)\s+([1-9][0-9]*(?:\s*,\s*[1-9][0-9]*)*)\Z", re.ASCII | re.IGNORECASE)
_DENIED = {
    "real_operator_provenance_verified": False,
    "chairman_semantic_review_verified": False,
    "independent_fable_validation_granted": False,
    "real_global_snapshot_verified": False,
    "real_global_hook_quarantine_verified": False,
    "real_first_claude_launch_authorized": False,
    "activation_authorized": False,
    "keep_drop_effects_applied": False,
}


class MigrationReviewRefusal(GlobalFixtureRefusal):
    """Malformed, stale or potentially authorizing synthetic migration input."""


def _digest(record: Any) -> str:
    raw = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                     allow_nan=False).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


def _classification(path: str) -> tuple[str, str, str, str, str]:
    """Only path-based, non-semantic heuristic advice; never an Opus/Chairman decision."""
    key = path.casefold()
    first = key.split("/")[0]
    if key in ("settings.json", "settings.local.json", ".mcp.json") or first in ("hooks", "scripts", "tools"):
        return (
            "1. Auto-executed governance",
            "Can run old commands or attach tools/servers when an assistant starts",
            "DROP",
            "Default inactive: old automatic execution cannot be trusted as Vres policy",
            "archived-only; any useful behavior needs a fresh protected implementation",
        )
    if first in ("plugins", ".claude-plugin"):
        return (
            "2. Legacy plugins",
            "May carry executable agents, hooks or old permission policies",
            "DROP",
            "A plugin label or previous approval cannot be inherited as Vres authority",
            "archived-only; optional independent capability review",
        )
    if first in ("skills", "agents", "commands"):
        return (
            "3. Skills and specialists",
            "May be a useful workflow or specialist, but may also execute commands",
            "KEEP DISABLED",
            "Keep as an inactive candidate only, pending security and usefulness review",
            "inactive Vres capability candidate; never a live Claude directory",
        )
    if key in ("claude.md", "claude.local.md") or first == "rules":
        return (
            "4. Instructions and rules",
            "Existing assistant instructions may include preferences or conflicts",
            "REVIEW CAREFULLY",
            "Content is untrusted; project-specific meaning cannot be inferred from filename",
            "inactive review queue; explicit project destination required if relevant",
        )
    return (
        "5. Unclassified governance",
        "Unclassified legacy configuration; its purpose is not established",
        "REVIEW CAREFULLY",
        "No deterministic rule establishes safety or a correct destination",
        "manual review required; never automatically installed",
    )


def _source(tx: FixtureTransaction) -> tuple[str, tuple[tuple[str, bytes, str], ...]]:
    """Verify sealed *in-memory* quarantine before any material becomes review data."""
    try:
        details = inspect_global_fixture(tx)
    except (GlobalFixtureRefusal, AttributeError, TypeError, ValueError) as exc:
        raise MigrationReviewRefusal("Synthetic source is not a verified fixture") from exc
    if (type(tx) is not FixtureTransaction or details.get("phase") != "quarantined" or
            details.get("simulated_quarantine_verified") is not True or
            type(details.get("sealed_snapshot_sha256")) is not str or
            not _SHA.fullmatch(details["sealed_snapshot_sha256"])):
        raise MigrationReviewRefusal("Review requires fully simulated quarantined snapshot")
    rows = tx._snapshot
    if len(rows) > _MAX_ITEMS:
        raise MigrationReviewRefusal("Synthetic review inventory exceeds bounded item count")
    return details["sealed_snapshot_sha256"], rows


def draft_legacy_migration_review(tx: FixtureTransaction) -> dict[str, Any]:
    """One stable number per synthetic legacy control FILE; never echo its bytes."""
    seal, rows = _source(tx)
    items: list[dict[str, Any]] = []
    ordered = sorted(rows, key=lambda row: (_classification(row[0])[0], row[0].casefold()))
    for n, (path, _bytes, digest) in enumerate(ordered, 1):
        group, purpose, recommendation, why, destination = _classification(path)
        items.append({
            "number": n,
            "item": path,
            "group": group,
            "what_it_does": purpose,
            "chairman_recommendation": recommendation,
            "recommendation_source": "deterministic_synthetic_heuristic_not_actual_chairman",
            "why": why,
            "destination_if_keep": destination,
            "snapshot_file_sha256": digest,  # synthetic bytes only; never actual credentials
            "active_authority": False,
        })
    basis = {"schema": _SCHEMA, "snapshot_sha256": seal, "items": items}
    return {
        **basis,
        "review_sha256": _digest(basis),
        "status": "synthetic_quarantined_review_pending_untrusted_operator_choices",
        "count": len(items),
        "choice_options": ["KEEP", "DROP"],
        "recommendations_are_not_decisions": True,
        "source_type": "synthetic_quarantined_legacy_configuration",
        **_DENIED,
    }


def _check_review(tx: FixtureTransaction, review: Any) -> dict[str, Any]:
    expected = draft_legacy_migration_review(tx)
    if type(review) is not dict or review != expected:
        raise MigrationReviewRefusal("Review is forged, modified or stale for synthetic snapshot")
    return expected


def _empty_state(review: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": _SCHEMA,
        "review_sha256": review["review_sha256"],
        "snapshot_sha256": review["snapshot_sha256"],
        "choices": [],
        "statement_digests": [],
        "decision_provenance": "synthetic_caller_statement_claim_only_not_real_user_authority",
        "state_sha256": _digest({"review_sha256": review["review_sha256"],
                                 "snapshot_sha256": review["snapshot_sha256"],
                                 "choices": [], "statement_digests": []}),
        **_DENIED,
    }


def _check_state(review: dict[str, Any], state: Any) -> dict[str, Any]:
    if type(state) is not dict or set(state) != set(_empty_state(review)):
        raise MigrationReviewRefusal("Malformed or authority-bearing synthetic decision sheet")
    if any(state[k] is not v for k, v in _DENIED.items()):
        raise MigrationReviewRefusal("Synthetic decision sheet attempted authority escalation")
    if (state["schema"] != _SCHEMA or state["review_sha256"] != review["review_sha256"] or
            state["snapshot_sha256"] != review["snapshot_sha256"] or
            state["decision_provenance"] != "synthetic_caller_statement_claim_only_not_real_user_authority"):
        raise MigrationReviewRefusal("Decision sheet is bound to another or untrusted review")
    choices, digests = state["choices"], state["statement_digests"]
    if type(choices) is not list or type(digests) is not list or len(digests) > _MAX_ITEMS:
        raise MigrationReviewRefusal("Malformed decision record")
    found: set[int] = set()
    for row in choices:
        if (type(row) is not dict or set(row) != {"number", "decision"} or
                type(row["number"]) is not int or not 1 <= row["number"] <= review["count"] or
                type(row["decision"]) is not str or row["decision"] not in ("KEEP", "DROP") or
                row["number"] in found):
            raise MigrationReviewRefusal("Forged, conflicting or duplicate synthetic choice")
        found.add(row["number"])
    if [r["number"] for r in choices] != sorted(found):
        raise MigrationReviewRefusal("Unordered synthetic choice record")
    if any(type(d) is not str or not _SHA.fullmatch(d) for d in digests):
        raise MigrationReviewRefusal("Malformed claimed operator statement fingerprint")
    basis = {"review_sha256": review["review_sha256"],
             "snapshot_sha256": review["snapshot_sha256"],
             "choices": choices, "statement_digests": digests}
    if state["state_sha256"] != _digest(basis):
        raise MigrationReviewRefusal("Decision record changed after synthetic seal")
    return state


def begin_legacy_migration_decisions(tx: FixtureTransaction, review: Any) -> dict[str, Any]:
    """Initialize an unauthorizing choice record tied to the exact synthetic review."""
    current = _check_review(tx, review)
    return _empty_state(current)


def _parse(statement: Any, count: int) -> list[dict[str, Any]]:
    if type(statement) is not str or not 1 <= len(statement) <= 400 or "\n" in statement or "\r" in statement:
        raise MigrationReviewRefusal("Expected a concise single-line KEEP/DROP statement")
    sections = re.split(r"\s*/\s*", statement.strip())
    if not 1 <= len(sections) <= 2:
        raise MigrationReviewRefusal("Use KEEP 1,2 / DROP 3,4 format")
    choices: list[dict[str, Any]] = []
    seen: set[int] = set()
    groups: set[str] = set()
    for section in sections:
        match = _SEGMENT.fullmatch(section.strip())
        if match is None:
            raise MigrationReviewRefusal("Malformed KEEP/DROP numbers or unsupported extra instruction")
        decision, list_text = match.group(1).upper(), match.group(2)
        if decision in groups:
            raise MigrationReviewRefusal("Repeated decision group; choose each once per statement")
        groups.add(decision)
        for token in list_text.split(","):
            number = int(token.strip())
            if number > count or number in seen:
                raise MigrationReviewRefusal("Unknown or duplicate item number")
            seen.add(number)
            choices.append({"number": number, "decision": decision})
    return sorted(choices, key=lambda x: x["number"])


def record_legacy_migration_choices(
    tx: FixtureTransaction, review: Any, sheet: Any, statement: Any,
) -> dict[str, Any]:
    """Record explicitly numbered CLAIMS, not authenticated consent or activation."""
    current = _check_review(tx, review)
    old = _check_state(current, sheet)
    incoming = _parse(statement, current["count"])
    chosen = {r["number"] for r in old["choices"]}
    if any(r["number"] in chosen for r in incoming):
        raise MigrationReviewRefusal("Item already decided; explicit reset/review needed to revise")
    new_choices = sorted([*old["choices"], *incoming], key=lambda x: x["number"])
    digests = [*old["statement_digests"], hashlib.sha256(statement.encode("utf-8")).hexdigest()]
    basis = {"review_sha256": current["review_sha256"],
             "snapshot_sha256": current["snapshot_sha256"],
             "choices": new_choices, "statement_digests": digests}
    return {**old, "choices": new_choices, "statement_digests": digests,
            "state_sha256": _digest(basis)}



def inspect_synthetic_migration_decision_transcript(
    tx: FixtureTransaction, review: Any, sheet: Any,
    statements: Any,
) -> dict[str, Any]:
    """Match exact claimed KEEP/DROP text to an ORIGINAL sealed synthetic sheet.

    This proves only consistency of caller-presented bytes with that sheet.
    A digest or a boolean is NOT proof of a Windows user instruction, a
    Chairman decision, identity, consent, durable journal or Fable authority.
    No original legacy content or statement text is included in the output.
    """
    current = _check_review(tx, review)
    decision = _check_state(current, sheet)
    digests = decision["statement_digests"]
    if (type(statements) is not list or len(statements) != len(digests)
            or len(statements) > _MAX_ITEMS):
        raise MigrationReviewRefusal("Exact ordered synthetic decision statements required")
    rebuilt: list[dict[str, Any]] = []
    for statement, digest in zip(statements, digests):
        parsed = _parse(statement, current["count"])
        if hashlib.sha256(statement.encode("utf-8")).hexdigest() != digest:
            raise MigrationReviewRefusal("Claimed instruction bytes differ from recorded decision")
        rebuilt.extend(parsed)
    numbers = [row["number"] for row in rebuilt]
    if (len(numbers) != len(set(numbers))
            or sorted(rebuilt, key=lambda row: row["number"]) != decision["choices"]):
        raise MigrationReviewRefusal("Transcript choices differ from the sealed synthetic sheet")
    basis = {
        "schema": "vres-personal-synthetic-decision-transcript/1",
        "snapshot_sha256": current["snapshot_sha256"],
        "review_sha256": current["review_sha256"],
        "decision_sheet_sha256": decision["state_sha256"],
        "statement_digests": digests,
        "choices": decision["choices"],
    }
    return {
        "schema": basis["schema"],
        "status": "CLAIMED_SYNTHETIC_DECISION_TRANSCRIPT_MATCH_ONLY",
        "snapshot_sha256": current["snapshot_sha256"],
        "review_sha256": current["review_sha256"],
        "decision_sheet_sha256": decision["state_sha256"],
        "decision_transcript_sha256": _digest(basis),
        "statement_count": len(statements),
        "statement_text_hidden": True,
        "original_legacy_bytes_hidden": True,
        "input_provenance": "caller_claimed_synthetic_text_not_attested",
        "real_user_instruction_provenance_verified": False,
        "real_operator_provenance_verified": False,
        "independent_fable_validation_granted": False,
        "real_global_snapshot_verified": False,
        "activation_authorized": False,
        "files_written": False,
        "native_claude_or_hooks_executed": False,
        "database_contacted": False,
    }


def migration_review_progress(tx: FixtureTransaction, review: Any, sheet: Any) -> dict[str, Any]:
    current = _check_review(tx, review)
    decision = _check_state(current, sheet)
    chosen = {r["number"] for r in decision["choices"]}
    pending = [row["number"] for row in current["items"] if row["number"] not in chosen]
    return {
        "schema": _SCHEMA,
        "review_sha256": current["review_sha256"],
        "snapshot_sha256": current["snapshot_sha256"],
        "chosen": len(chosen), "pending": pending,
        "synthetic_choices_complete": not pending,
        "real_operator_provenance_verified": False,
        "activation_authorized": False,
        "independent_fable_validation_granted": False,
    }


def freeze_synthetic_migration_plan(
    tx: FixtureTransaction, review: Any, sheet: Any, *,
    statement_transcript: Any | None = None,
) -> dict[str, Any]:
    """Produce immutable-looking JSON data only; never activate, validate, or apply."""
    current = _check_review(tx, review)
    decision = _check_state(current, sheet)
    progress = migration_review_progress(tx, current, decision)
    if progress["pending"]:
        raise MigrationReviewRefusal("Unresolved migration choices; cannot freeze review")
    transcript_review = (inspect_synthetic_migration_decision_transcript(
        tx, current, decision, statement_transcript)
        if statement_transcript is not None else None)
    # Pure synthetic rollback from the exact quarantined byte snapshot.
    # The ORIGINAL transaction owner verifies its seal, journal and opaque
    # vendor-state identities. Nothing on the user's Claude profile changes.
    try:
        restored = rollback_global_fixture(tx)
        before = inspect_global_fixture(tx)
        after = inspect_global_fixture(restored)
    except GlobalFixtureRefusal:
        raise MigrationReviewRefusal("Synthetic rollback rehearsal could not verify") from None
    expected_active = tuple((path, data) for path, data, _digest in tx._snapshot)
    if (restored._active != expected_active or restored._quarantine != ()
            or restored._native_ids != tx._native_ids
            or before["sealed_snapshot_sha256"] != current["snapshot_sha256"]
            or after["sealed_snapshot_sha256"] != current["snapshot_sha256"]
            or after["simulated_rollback_verified"] is not True):
        raise MigrationReviewRefusal("Synthetic rollback failed exact restoration checks")
    rehearsal = {
        "status": "SYNTHETIC_EXACT_ROLLBACK_REHEARSAL_ONLY",
        "sealed_snapshot_sha256": current["snapshot_sha256"],
        "governance_file_count": before["governance_file_count"],
        "opaque_vendor_handle_count": before["opaque_native_handle_count"],
        "synthetic_snapshot_bytes_restored": True,
        "opaque_vendor_handles_preserved": True,
        "real_profile_snapshot_verified": False,
        "real_vendor_state_unchanged_verified": False,
        "durable_host_journal_verified": False,
        "native_hook_quarantine_verified": False,
        "independent_fable_validation_granted": False,
        "real_activation_authorized": False,
    }
    mapping = {r["number"]: r["decision"] for r in decision["choices"]}
    items = [{"number": item["number"], "decision": mapping[item["number"]],
              "destination_if_keep": item["destination_if_keep"] if mapping[item["number"]] == "KEEP" else "archived_only_not_destroyed",
              "effect": "inactive_review_candidate_only" if mapping[item["number"]] == "KEEP" else "remain_inactive_unchanged_backup"}
             for item in current["items"]]
    canonical = {"schema": _SCHEMA, "snapshot_sha256": current["snapshot_sha256"],
                 "review_sha256": current["review_sha256"], "decision_sheet_sha256": decision["state_sha256"],
                 "items": items, "rollback_rehearsal": rehearsal}
    if transcript_review is not None:
        # Bind source-claim consistency into the frozen synthetic plan digest.
        # No real-user consent or Fable authority is inferred.
        canonical["decision_transcript_review"] = transcript_review
    return {
        **canonical, "synthetic_plan_sha256": _digest(canonical),
        "status": "synthetic_preview_frozen_no_real_operator_authority",
        "provenance": "claimed_only_not_a_direct_verified_user_instruction",
        "pending": [],
        **_DENIED,
    }


def render_legacy_migration_review(tx: FixtureTransaction, review: Any, sheet: Any) -> str:
    """Human-readable, bounded and escaped; no raw file bytes or vendor state."""
    current = _check_review(tx, review)
    decision = _check_state(current, sheet)
    decisions = {row["number"]: row["decision"] for row in decision["choices"]}
    lines = ["Vres-OS PERSONAL global Claude migration — SYNTHETIC REVIEW ONLY",
             "NOT AUTHORIZED: real user profile, old hooks, first Claude launch, or migration.",
             "The suggestions are deterministic placeholders, NOT actual Chairman reviews.",
             f"Synthetic snapshot: {current['snapshot_sha256']}",
             "Reply format: KEEP 2,3 / DROP 1,4. Missing numbers remain unresolved."]
    current_group = None
    for item in current["items"]:
        if item["group"] != current_group:
            current_group = item["group"]
            lines.append("\n" + current_group)
        n = item["number"]
        name = json.dumps(item["item"], ensure_ascii=True)
        lines.append(f"#{n} {name} | {item['what_it_does']} | Suggested: {item['chairman_recommendation']}")
        lines.append(f"  Why: {item['why']} | If KEEP: {item['destination_if_keep']} | Choice: {decisions.get(n, 'UNRESOLVED')}")
    missing = [item["number"] for item in current["items"] if item["number"] not in decisions]
    lines.append("\nUnresolved item numbers: " + (", ".join(map(str, missing)) if missing else "none (still NOT approved)"))
    rendered = "\n".join(lines)
    if len(rendered) > _MAX_OUTPUT:
        raise MigrationReviewRefusal("Bounded synthetic migration review exceeded output limit")
    return rendered
