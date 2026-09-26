from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CONSTITUTION_VERSION = "1.0"
PLAN_VERSION = 1

IGNORED_DIRS = {
    ".git", ".hg", ".svn", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".tox", ".venv", "venv", "__pycache__", "build", "coverage", "dist", "node_modules",
}
SOURCE_SUFFIXES = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".java", ".go", ".rs", ".cs",
}
JS_TS_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
STANDARD_LAYERS = {"app", "modules", "domains", "shared", "platform"}
MAX_FILES = 10_000
MAX_PARSE_BYTES = 2 * 1024 * 1024
OVERSIZED_LINES = 800

RULES: dict[str, dict[str, Any]] = {
    "ARCH-001": {
        "title": "No circular architectural dependencies",
        "severity": "error",
        "material": True,
    },
    "ARCH-002": {
        "title": "shared must not depend on domains",
        "severity": "error",
        "material": True,
    },
    "ARCH-003": {
        "title": "shared must not depend on feature modules",
        "severity": "error",
        "material": True,
    },
    "ARCH-004": {
        "title": "domains must not depend on feature modules",
        "severity": "error",
        "material": True,
    },
    "ARCH-005": {
        "title": "feature modules must not depend on sibling module internals",
        "severity": "error",
        "material": True,
    },
    "ARCH-006": {
        "title": "cross-boundary imports must not use explicit private/internal paths",
        "severity": "error",
        "material": True,
    },
    "ARCH-007": {
        "title": "substantive modules should carry local ownership instructions",
        "severity": "warning",
        "material": True,
    },
    "ARCH-008": {
        "title": "substantive modules should expose an intentional public API",
        "severity": "warning",
        "material": True,
    },
    "ARCH-009": {
        "title": "large files are responsibility-split warning signals",
        "severity": "warning",
        "material": False,
    },
    "ARCH-010": {
        "title": "established applications require an architecture alignment plan",
        "severity": "error",
        "material": False,
    },
}

PROFILES: dict[str, dict[str, Any]] = {
    "minimal": {
        "description": "Small application or utility; add layers only when responsibilities justify them.",
        "required_principles": [
            "ownership",
            "tests",
            "secret-safety",
            "dependency-discipline",
        ],
    },
    "frontend-web": {
        "description": "Browser application with app composition, feature modules, domains and shared foundations as complexity warrants.",
        "required_principles": [
            "route-ownership",
            "public-apis",
            "failure-isolation",
            "data-access-layer",
        ],
    },
    "full-stack-web": {
        "description": "Frontend plus backend application using modular-monolith boundaries by default.",
        "required_principles": [
            "frontend-layers",
            "backend-layers",
            "typed-contracts",
            "failure-isolation",
        ],
    },
    "python-service": {
        "description": "Python service/API with route/feature modules, domain services and platform/infrastructure boundaries.",
        "required_principles": [
            "domain-services",
            "central-db-access",
            "public-apis",
            "tests",
        ],
    },
    "data-analytics": {
        "description": "Analytical/data application with explicit data contracts and honest missing-data semantics.",
        "required_principles": [
            "data-contracts",
            "source-truth",
            "honest-missing-data",
            "query-discipline",
        ],
    },
    "pipeline-jobs": {
        "description": "Scheduled/orchestrated workflows with explicit dependency graphs and bounded job contracts.",
        "required_principles": [
            "job-dependencies",
            "retry-contracts",
            "freshness-sla",
            "thin-entrypoints",
        ],
    },
    "cli-library": {
        "description": "CLI tool or reusable library with thin entrypoints and reusable logic in importable packages.",
        "required_principles": [
            "thin-entrypoints",
            "public-api",
            "tests",
            "dependency-discipline",
        ],
    },
}


@dataclass(frozen=True, slots=True)
class DependencyEdge:
    source: str
    target: str
    source_path: str
    target_ref: str
    language: str
    private_path: bool = False


@dataclass(frozen=True, slots=True)
class ArchitectureFinding:
    finding_id: str
    rule_id: str
    severity: str
    material: bool
    title: str
    evidence: str
    paths: tuple[str, ...] = ()
    recommendation: str = ""
