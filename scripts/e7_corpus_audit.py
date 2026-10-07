"""Reproducible audit of the committed E7 development and adversarial assets.

Reads manifest.json and the development/adversarial bundles only. It never opens held-out files and
exits non-zero when any check fails. Usage:
    python scripts/e7_corpus_audit.py [--root benchmarks/experience_e7] [--json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from vres_os import experience_benchmark as eb  # noqa: E402

DEFAULT_ROOT = REPO / "benchmarks" / "experience_e7"

# Red-team family -> security assertions that evidence it (any one suffices).
FAMILIES = {
    1: ("no_durable_instruction_from_untrusted_doc",),
    2: ("no_poisoned_trajectory_promotion",),
    3: ("no_injection_after_context_reset",),
    4: ("no_cross_project_retrieval",),
    5: ("no_authority_from_external_claim",),
    6: ("no_poisoned_procedure_accept",),
    7: ("no_secret_persistence",),
    8: ("revoked_source_not_retrieved",),
    9: ("no_lexical_or_embedding_poison_rank",),
    10: ("trusted_outranks_untrusted_conflict",),
    11: ("second_user_isolation",),
    12: ("burst_fails_closed", "frequency_is_not_trust"),
    13: ("varied_poison_single_lineage",),
    14: ("diversity_is_lineage",),
    15: ("recurrence_cannot_raise_authority",),
    16: ("participation_distinct_from_observation",),
    17: ("challenge_flags_without_mutation",),
    18: ("retrieval_no_silent_rewrite",),
}
# Development coverage required by the Chunk 1 authorization.
DEV_CATEGORIES = (
    "static_state",
    "dynamic_state_change",
    "recurring_workflow",
    "gotcha",
    "false_premise",
    "successful_trajectory",
    "failed_trajectory",
    "user_correction",
    "procedure_reuse",
    "capability_precedent",
    "cross_project_trap",
    "noisy_distractor",
    "stale_superseded_challenged",
    "current_vs_historical",
    "source_revocation",
    "participated_vs_observed",
    "abstention",
    "memory_not_needed",
    "temporal_update",
)
SECRET_PATTERNS = {
    "sk_key": re.compile(r"sk-[A-Za-z0-9]{12,}"),
    "aws_key": re.compile(r"AKIA[0-9A-Z]{12,}"),
    "private_key": re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
    "assigned_secret": re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|token)\s*[=:]\s*\S"),
    "bearer": re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{16,}"),
}
CANARY_PLACEHOLDER = "<<CANARY_1>>"
HIDDEN_KEYS = {
    "reasoning",
    "chain_of_thought",
    "cot",
    "thinking",
    "thoughts",
    "scratchpad",
    "rationale",
    "analysis",
}
SCORING_KEYS = {
    "expected",
    "relevant",
    "acceptable",
    "irrelevant",
    "stale",
    "label",
    "labels",
    "score",
    "gold",
    "answer",
    "criteria",
    "assertions",
    "outcome",
    "claims",
    "source_facts",
    "forbidden_actions",
    "success_criteria",
}


def _walk_keys(value, out: set[str]) -> None:
    if isinstance(value, dict):
        for key, sub in value.items():
            out.add(key)
            _walk_keys(sub, out)
    elif isinstance(value, list):
        for sub in value:
            _walk_keys(sub, out)


def _walk_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for sub in value.values():
            yield from _walk_strings(sub)
    elif isinstance(value, list):
        for sub in value:
            yield from _walk_strings(sub)


def audit(root: Path) -> dict:
    checks: dict[str, object] = {}
    problems: list[str] = []

    def check(name: str, ok: bool, detail: object = None) -> None:
        checks[name] = {"ok": bool(ok), **({"detail": detail} if detail is not None else {})}
        if not ok:
            problems.append(f"{name}: {detail}")

    manifest = eb.load_manifest(root)
    scoring = eb.load_scoring(root)  # binds scoring.json to the manifest digest
    check("heldout_status_not_authored", manifest["heldout_status"] == "not_authored")
    check("manifest_has_no_heldout_bundle", "heldout" not in manifest["bundles"])
    check("heldout_directory_absent", not (root / "heldout").exists())
    stray = sorted(p.name for p in root.iterdir() if "held" in p.name.lower())
    check("no_heldout_named_entries", not stray, stray)
    check("no_thresholds_file", not (root / "thresholds.json").exists())

    bundles = {s: eb.load_development_bundle(root, s) for s in eb.DEVELOPMENT_SPLITS}
    report: dict[str, object] = {"bundles": {}}
    all_ids: Counter = Counter()
    split_aliases: dict[str, set[str]] = {}
    within_dupes: list[str] = []
    secret_hits: list[str] = []
    hidden_hits: list[str] = []
    scoring_hits: list[str] = []
    raw_defects: list[str] = []
    placeholder_count = 0
    t_defects: list[str] = []
    for split, bundle in bundles.items():
        cases = bundle["cases"]
        by_cat = Counter(c["category"] for c in cases)
        report["bundles"][split] = {
            "case_count": len(cases),
            "categories": dict(sorted(by_cat.items())),
            "digests": bundle["digests"],
            "manifest_files": manifest["bundles"][split]["files"],
        }
        for case in cases:
            all_ids[case["case_id"]] += 1
            if len(set(case["aliases"])) != len(case["aliases"]):
                within_dupes.append(case["case_id"])
            split_aliases.setdefault(split, set()).update(case["aliases"])
            if not all(a.startswith(eb.ALIAS_PREFIX[split]) for a in case["aliases"]):
                raw_defects.append(f"{case['case_id']}: alias prefix")
            times = [s["t"] for s in case.get("timeline", [])]
            if times != sorted(set(times)):
                t_defects.append(case["case_id"])
            keys: set[str] = set()
            _walk_keys(case, keys)
            hidden_hits += [f"{case['case_id']}:{k}" for k in sorted(keys & HIDDEN_KEYS)]
            scoring_hits += [
                f"{case['case_id']}:{k}"
                for k in sorted(keys & SCORING_KEYS)
                if k in ("expected", "relevant", "irrelevant", "gold", "answer", "label", "score")
            ]
            for text in _walk_strings(case):
                placeholder_count += text.count(CANARY_PLACEHOLDER)
                scrubbed = text.replace(CANARY_PLACEHOLDER, "")
                for name, pattern in SECRET_PATTERNS.items():
                    if pattern.search(scrubbed):
                        secret_hits.append(f"{case['case_id']}:{name}")
        for name in eb.BUNDLE_FILES:
            raw = (root / split / name).read_bytes()
            if raw.startswith(b"\xef\xbb\xbf"):
                raw_defects.append(f"{split}/{name}: BOM")
            if b"\r" in raw:
                raw_defects.append(f"{split}/{name}: CR")
            if not raw.endswith(b"\n"):
                raw_defects.append(f"{split}/{name}: no final LF")
            actual = hashlib.sha256(raw).hexdigest()
            if actual != manifest["bundles"][split]["files"][f"{split}/{name}"]:
                raw_defects.append(f"{split}/{name}: digest")
            lines = raw.decode("utf-8").splitlines() if name == "corpus.jsonl" else [raw.decode()]
            for line in lines:  # a float literal anywhere in an asset is a defect
                json.loads(line, parse_float=_reject_float)
    check("case_ids_unique_across_splits", all(v == 1 for v in all_ids.values()))
    check("aliases_unique_within_case", not within_dupes, within_dupes)
    check(
        "aliases_split_disjoint",
        not (split_aliases["development"] & split_aliases["adversarial"]),
    )
    check("t_strictly_increasing", not t_defects, t_defects)
    check("file_format_and_digests", not raw_defects, raw_defects)
    check("no_real_secret_shapes", not secret_hits, secret_hits)
    check("canary_only_as_placeholder", placeholder_count >= 1, placeholder_count)
    check("no_hidden_reasoning_keys", not hidden_hits, hidden_hits)
    check("no_scoring_material_in_corpus", not scoring_hits, scoring_hits)

    dev_cats = {c["category"] for c in bundles["development"]["cases"]}
    check(
        "development_category_coverage",
        set(DEV_CATEGORIES) <= dev_cats,
        sorted(set(DEV_CATEGORIES) - dev_cats),
    )
    # expected answers must only name aliases (loader enforces); report unmapped counts as zero
    coverage: dict[int, list[str]] = {}
    for case_id, entry in bundles["adversarial"]["expected"].items():
        for assertion in entry.get("security", {}).get("assertions", []):
            for family, wanted in FAMILIES.items():
                if assertion in wanted:
                    coverage.setdefault(family, []).append(case_id)
    missing = sorted(set(FAMILIES) - set(coverage))
    check("all_18_families_covered", not missing, missing)
    report["family_coverage"] = {str(f): sorted(set(coverage.get(f, []))) for f in FAMILIES}
    adv_assertions = {
        a
        for e in bundles["adversarial"]["expected"].values()
        for a in e.get("security", {}).get("assertions", [])
    }
    check(
        "every_security_assertion_used",
        adv_assertions == set(eb.SECURITY_ASSERTIONS),
        sorted(set(eb.SECURITY_ASSERTIONS) - adv_assertions),
    )
    budget_hits = [
        c["case_id"]
        for c in bundles["adversarial"]["cases"]
        if any("max_open" in s.lower() or "budget" in s.lower() for s in _walk_strings(c))
    ]
    check("no_invented_proposal_budget", not budget_hits, budget_hits)

    all_cases = [c for b in bundles.values() for c in b["cases"]]
    ops_used = {s["op"] for c in all_cases for s in c.get("timeline", [])}
    check(
        "owner_map_covers_operations",
        ops_used <= set(eb.OPERATION_OWNERS)
        and all(
            row["owner_gap"] or (row["owner"] and row["method"] and not row["uses_direct_sql"])
            for row in eb.OPERATION_OWNERS.values()
        ),
        sorted(ops_used - set(eb.OPERATION_OWNERS)),
    )
    gap_ops = sorted(op for op, row in eb.OPERATION_OWNERS.items() if row["owner_gap"])
    check("owner_gap_ops_recorded", gap_ops == [], gap_ops)
    observed_wrong = [
        c["case_id"]
        for c in all_cases
        for s in c.get("timeline", [])
        if s["op"] == "episode_capture" and s.get("args", {}).get("participation") == "observed"
    ]
    check("observed_episodes_use_owner_gap_op", not observed_wrong, observed_wrong)
    no_edge, bad_consolidation = [], []
    for c in all_cases:
        edges: set[tuple[str, str]] = set()
        for s in c.get("timeline", []):
            args = s.get("args", {})
            if s["op"] == "knowledge_attach_source":
                edges.add((s["alias"], args["source"]))
            elif s["op"] == "source_revoke" and not any(src == s["alias"] for _, src in edges):
                no_edge.append(c["case_id"])
            elif s["op"] == "experience_consolidate" and not (
                args["trigger"] in eb.CONSOLIDATION_TRIGGERS
                and 1 <= len(args["evidence"]) <= 10
                and all(e["pointer"].startswith("/") and e["quote"] for e in args["evidence"])
            ):
                bad_consolidation.append(c["case_id"])
    check("revocation_has_provenance_edge", not no_edge, no_edge)
    check("consolidations_e2_shaped", not bad_consolidation, bad_consolidation)
    flagged = [
        a
        for e in bundles["adversarial"]["expected"].values()
        for a in e.get("security", {}).get("must_flag_challenged", [])
    ]
    check("challenge_cases_have_lifecycle_challenge", bool(flagged), flagged)
    matrix: dict[str, dict] = {}
    classify_errors: list[str] = []
    for split, bundle in bundles.items():
        rows = {"executable": [], "owner_gap": {}}
        for c in bundle["cases"]:
            try:
                label = eb.classify_case(c)
            except eb.BenchmarkError as exc:
                classify_errors.append(f"{c['case_id']}: {exc}")
                continue
            if label == "EXECUTABLE":
                rows["executable"].append(c["case_id"])
            elif label.startswith("OWNER_GAP:") and label[len("OWNER_GAP:") :]:
                rows["owner_gap"][c["case_id"]] = label[len("OWNER_GAP:") :]
            else:
                classify_errors.append(f"{c['case_id']}: ambiguous state {label!r}")
        rows["executable_count"] = len(rows["executable"])
        rows["owner_gap_count"] = len(rows["owner_gap"])
        matrix[split] = rows
    check("every_case_executable_or_owner_gap", not classify_errors, classify_errors)
    report["execution_matrix"] = matrix
    try:
        eb.validate_metric_semantics(scoring["metric_semantics"])
        semantics_ok = True
    except eb.BenchmarkError as exc:
        semantics_ok = False
        report["metric_semantics_error"] = str(exc)
    check("metric_semantics_frozen", semantics_ok)
    report["metric_semantics_digest"] = eb.sha256_hex(eb.render_json(scoring["metric_semantics"]))
    report["scoring"] = {"digest": eb.scoring_digest(scoring), "config": scoring}
    report["manifest_digest"] = hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest()
    report["checks"] = checks
    report["ok"] = not problems
    report["problems"] = problems
    return report


def _reject_float(text: str):
    raise ValueError(f"float literal {text!r} in asset")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = audit(args.root)
    if args.json:
        sys.stdout.write(eb.render_json(report).decode("utf-8"))
    else:
        for name, result in report["checks"].items():
            print(("PASS " if result["ok"] else "FAIL ") + name)
        for split, info in report["bundles"].items():
            print(split, info["case_count"], info["digests"])
        for split, rows in report["execution_matrix"].items():
            print(
                split, "executable", rows["executable_count"], "owner_gap", rows["owner_gap_count"]
            )
            for cid, reason in rows["owner_gap"].items():
                print("  OWNER_GAP", cid, reason)
        print("manifest", report["manifest_digest"], "ok" if report["ok"] else report["problems"])
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
