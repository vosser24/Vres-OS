from pathlib import Path

import pytest

from vres_os.sensitive_policy import (
    SENSITIVE_REVIEW_REQUIRED,
    SENSITIVE_SANITIZED,
    sanitize_extracted_text,
    sensitive_path_reason,
)


@pytest.mark.parametrize("name,rule", [
    (".env", "env_file"), (".ENV", "env_file"), (".env.local", "env_file"), (".env.production", "env_file"),
    ("secrets.toml", "secrets_toml"), ("Secrets.TOML", "secrets_toml"),
    ("credentials.json", "credentials_file"), ("CREDENTIALS.txt", "credentials_file"), ("credentials", "credentials_file"),
    ("auth.json", "auth_file"), ("Auth.yaml", "auth_file"),
    ("id_rsa", "private_key_file"), ("id_ed25519", "private_key_file"), ("server.PEM", "private_key_file"),
    ("client.key", "private_key_file"), ("store.pfx", "private_key_file"),
])
def test_sensitive_names_are_excluded_case_insensitively(tmp_path, name, rule):
    assert sensitive_path_reason(tmp_path / "proj" / name) == rule


def test_vres_local_secrets_tree_is_excluded_whatever_the_file(tmp_path):
    assert sensitive_path_reason(tmp_path / ".vres" / "local-secrets" / "db" / "notes.md") == "vres_local_secrets"
    assert sensitive_path_reason(tmp_path / ".VRES" / "Local-Secrets" / "x.py") == "vres_local_secrets"
    assert sensitive_path_reason(tmp_path / ".vres" / "other" / "notes.md") is None


@pytest.mark.parametrize("name", ["readme.md", "id_rsa.pub", "authors.txt", "credentials_policy.md",
                                  "environment.md", "secrets_management.md", "idea.txt"])
def test_ordinary_names_are_not_excluded(tmp_path, name):
    assert sensitive_path_reason(tmp_path / name) is None


def test_path_policy_never_opens_the_file(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("content access during path preflight")
    monkeypatch.setattr(Path, "open", boom)
    monkeypatch.setattr(Path, "read_text", boom)
    monkeypatch.setattr(Path, "read_bytes", boom)
    assert sensitive_path_reason(tmp_path / ".env") == "env_file"


def test_disposition_sanitized_keeps_useful_text_and_only_safe_metadata():
    d = sanitize_extracted_text("Billing process\nDATABASE_PASSWORD=synthetic-value-1\n")
    assert d.status == SENSITIVE_SANITIZED
    assert "Billing process" in d.text and "synthetic-value-1" not in d.text
    assert "synthetic" not in str(d.metadata)
    assert d.metadata["sanitized_field_names"] == ["password"]


def test_disposition_review_required_retains_no_text():
    d = sanitize_extracted_text('Billing process\nsecret_key = "synthetic-ambiguous-value"\n')
    assert d.status == SENSITIVE_REVIEW_REQUIRED
    assert d.text == "" and "synthetic" not in (d.reason + str(d.metadata))


def test_disposition_ordinary_is_untouched():
    d = sanitize_extracted_text("plain runbook text")
    assert d.status is None and d.text == "plain runbook text"


@pytest.mark.parametrize("name", [
    "secrets.yaml", "Secret.JSON", "prod.env", "kubeconfig", "kubeconfig-prod", ".envrc", ".netrc", ".pgpass", "prod.tfstate",
])
def test_additional_credential_bearing_paths_are_excluded(name):
    assert sensitive_path_reason(Path("proj") / name)


def test_docker_config_excluded_but_plain_config_json_is_not():
    assert sensitive_path_reason(Path("h") / ".docker" / "config.json")
    assert sensitive_path_reason(Path("h") / "app" / "config.json") is None
    assert sensitive_path_reason(Path("docs") / "secrets.md") is None
