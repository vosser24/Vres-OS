"""Personal-release input validation (stdlib only; the installer runs this file directly).

The personal release ships exactly the accepted migrations 001-041, pinned below by the
same canonical text digest the runtime migrator records (UTF-8 text with universal
newlines), and none of the C2B/R0/F2 experimental inputs. Any unpinned, renamed,
changed or newer (above 041) migration, and any experimental file, makes the source
tree an invalid release input. Migration contents are only read, never edited.

Run: python -I src/vres_os/release_inputs.py --root <source tree>   (exit 0 = valid)
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

PERSONAL_RELEASE_MAX_MIGRATION = 41
MIGRATIONS_DIR = Path("src/vres_os/migrations")
PERSONAL_MIGRATION_PINS = {
    "001_initial.sql": "0bfac431940459f7cef45735fd89e88093e2db99065225ec7cfedc7cfb9d2af1",
    "002_operational_memory.sql": "3e2457a1d410711ad8420eae98592e73c99db790dfa83f5f53b6b62870375f15",
    "003_capability_seed.sql": "3cc8af2d1afdf2a67524a7791a7d0611f69ef2a48afe28bc1ac432962bf232d8",
    "004_source_locations.sql": "24256171f76daeda78c9d12c0732afa324200666b4f1bca66107640aecac01e2",
    "005_procedure_decisions_and_model_bootstrap.sql": "becceb28b746feb4c8c9da4bac595f96b465b9ef46b189d696d211c1b4281c35",
    "006_governance_hardening.sql": "bef54f0dd0495e086e225a1f73dd02297c46218b481c0fb1b52d5b5c6c42d02f",
    "007_audit_validation_and_provenance.sql": "9dc07b50738a82504dd6d4afe4ea9e7ce4579d34a9ff610c4013e54c893588a8",
    "008_scope_provenance.sql": "182f41fdc2b3b1fa4b4889904f64ea886600243229faffc65c8011652201f598",
    "009_retry_contracts.sql": "7356cf2e791e2acf1b4ce06380f0bb71af0f411e378d0678a2b4125fd55e562b",
    "010_company_authority.sql": "1c035d2f006c7e8112a9b75a330b95ba3999335e67f58a12269c13c8e4ffbf37",
    "011_optimization_attestation.sql": "d4b8589bcbf420ed3ac5ef6abf914edd0de4362c1ec29fe0d1eeaec763af51d3",
    "012_model_run_provenance.sql": "ad673ef8516280860a28164b25d26ead449fc6fdae3fd327ca3381d0b103f56c",
    "013_company_optimization_authority.sql": "3828c47d2c635c4fdcd304eca3c99c5cb65dfa5b8b5f7308855dedfb6fcb528f",
    "014_model_experiment_attestation.sql": "4042d99b550a0c554e0561a3564e84a6d103b94697366c4d488aef8ae547d557",
    "015_validation_ingestion_audit.sql": "4acb6fd6e181a2bf509aa6767ab37f3e97111aa011e5a3d448b8c34ba0a0e95c",
    "016_task_decisions.sql": "d721c74042b2b9899632c3276e264d9bf48ade855dbe4d52eb6023a6ce30ee1e",
    "017_validation_status_contract.sql": "d95dae31a3d307e26c1eed06683f6ff66af95c5fb6a8cf6a84f09ba1387943ea",
    "018_task_status_contract.sql": "8953a497b7ace8baf7fb91169ba8f370e5a48094477201a4a7901e9ee6c854df",
    "019_remove_dead_task_project_metadata.sql": "8c1e07af0ecf457c2fdcd00311751ed6156ae790f0d6df6df3c8ab7da4a5d38f",
    "020_task_decision_provenance.sql": "52d444e89826d1d4805b0d263074855c9bb4051b851726569e58706b7da956a0",
    "021_decision_immutability_and_completion_sessions.sql": "69adacb2964dbf80ed3748a27fc99af26b775eaf8e7ef59bb48bb63250b34de1",
    "022_task_decision_insert_provenance.sql": "220e7af4c3f5a70645c8029dba8297d6c10f3d2d04f3693a50cee121a18d9ae3",
    "023_user_event_writer_boundary.sql": "f0857b1ef2d2d87b2b5fed13c7b10d4525c3d322a200009e2579d7fa3dd2b8b8",
    "024_user_event_immutability.sql": "138a8371d0be5c753ee1a3369520e2b3ac6784b1ac463a5e746e3cafd1fdf1ee",
    "025_aigo_orchestration.sql": "4f9abc72062a2f2783b60198d6220c3e5f69c3fb76b17bd652e68e69d0261aca",
    "026_capability_retrieval_aliases.sql": "49c93b0066aeba7ace0fa70bf4cb4b061828810d90be0c47260afe23998f8b82",
    "027_routing_governor.sql": "156cc003f7de1abd635e144da697e976e251d6db658b9bc5b6bcbaa02415cc1b",
    "028_validation_pass_checkpoint_guard.sql": "10515a42202c85cbb84d3c2c14d1b7e74dbf928ae01edd93b32e280e019fe7a8",
    "029_user_read_only_hold.sql": "729cd64913e6faf2e324e044fe22d62bc96dac1aae9a59acf785f46da4d30128",
    "030_protected_governance_freshness.sql": "5a7801a7637c0ae1258f5c0f2fdc78bf21b0a264c4f412b7e48f91e9bfb1781f",
    "031_software_architecture_routing_calibration.sql": "77279b2eefe8f197701287e169ee9d7857c9facb7c244fa60f1fa051f3b74f4d",
    "032_latest_observed_user_instruction.sql": "2f6f6d572b0e27d1668ae9dd3a69577eefa1d552a806457231c5982e64f86673",
    "033_project_agent_work_units.sql": "a66da56bd059f5093a0ff31afb28451fcd52f6295f19f957c924a59bff02d079",
    "034_work_unit_acceptance_contract.sql": "0df928c8d8c23d0605e3cc8d6c27720e0611b613bc69c720175f18db3503916e",
    "035_validation_ingestion_deferred_disposition.sql": "bfff30f215a8ed576e9c15cf7fc70ef600e07f7ddb3cb269dff31f6cf7c40428",
    "036_protected_pass_supersedes_routine_route.sql": "9f817f5c14038f733efd3f68d2d0634116d5974ec3d4ace595a05b04f71e6e06",
    "037_experience_episode_ledger.sql": "9dab01de3faf76611e2147c78c1b6c3378ebb4fd61b42dc8c17e98536ecc7e07",
    "038_experience_transitions.sql": "e420d9191e96464ae1cf54afc1bc5c06f79e64bbc4adaa0fe2665a635d018362",
    "039_experience_lifecycle_ledger.sql": "a8dd95f0f80d86c3b38b281748388a970fdca10e04eb38227c015ff50f750fc9",
    "040_context_refresh_attestation.sql": "73dd705e8b5ec9984c5e6829ef38591d3b09aac5a3562fb01187497085fbb48d",
    "041_experience_retrieval_observability.sql": "45dcf5e3cf3afad15f42d10eacdfb8eab8699f5f0400c0dfebf9720647b92786",
}
_SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", "build", "dist", ".venv", "venv", "htmlcov", ".live-test-venv"}
# C2B shadow-guard / R0 reader files carry a c2b name component; F2 is the quarantined
# E7 benchmark and PostgreSQL CI driver work; C2A is the schema-048 compatibility probe.
_EXPERIMENTAL = (
    ("C2B/R0", re.compile(r"(?:^|/)(?:test_)?c2b[-_.][^/]*$|(?:^|/)c2b[-_][^/]*/")),
    ("F2", re.compile(r"^benchmarks/experience_e7/")),
    ("F2", re.compile(r"^scripts/(?:ci_pg_integration|e7_corpus_audit)\.py$")),
    ("F2", re.compile(r"^src/vres_os/(?:experience_benchmark[^/]*|source_trust_policy|source_trust_read)\.py$")),
    ("F2", re.compile(r"^tests/integration/(?:e7_[^/]*|pg_fixture_safety\.py|pg_run_guard\.py)$")),
    ("F2", re.compile(r"^tests/(?:[^/]+/)*test_(?:e7_|experience_benchmark_)[^/]*$")),
    ("F2", re.compile(r"^docs/architecture/experience-intelligence-e7-[^/]*$")),
    ("C2A", re.compile(r"^tests/test_control_compat_048[^/]*$")),
)


def migration_digest(path: Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def _files(root: Path):
    for directory, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in _SKIP_DIRS and not d.endswith(".egg-info"))
        for name in sorted(names):
            yield Path(directory, name).relative_to(root).as_posix()


def release_input_problems(root: Path) -> list[str]:
    """Every reason the tree at root is not a valid personal-release input; empty when valid."""
    root = Path(root)
    problems: list[str] = []
    migrations = root / MIGRATIONS_DIR
    present = {p.name: p for p in migrations.glob("*.sql")} if migrations.is_dir() else {}
    for name in sorted(present):
        number = re.match(r"(\d+)_", name)
        if number and int(number.group(1)) > PERSONAL_RELEASE_MAX_MIGRATION:
            problems.append(
                f"migration {name} is above {PERSONAL_RELEASE_MAX_MIGRATION:03d} "
                "and is not part of the personal release"
            )
        elif name not in PERSONAL_MIGRATION_PINS:
            problems.append(f"migration {name} is not one of the pinned personal-release migrations")
        elif migration_digest(present[name]) != PERSONAL_MIGRATION_PINS[name]:
            problems.append(f"migration {name} differs from its pinned personal-release identity")
    for name in sorted(set(PERSONAL_MIGRATION_PINS) - set(present)):
        problems.append(f"pinned migration {name} is missing")
    for rel in _files(root):
        for label, pattern in _EXPERIMENTAL:
            if pattern.search(rel.casefold()):
                problems.append(f"{label} experimental file {rel} must not be part of the personal release")
                break
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Vres personal-release source tree.")
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args(argv)
    problems = release_input_problems(args.root)
    for problem in problems:
        print(f"personal-release input refused: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(
        f"personal-release inputs valid: migrations 001-{PERSONAL_RELEASE_MAX_MIGRATION:03d} pinned, "
        "no experimental files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
