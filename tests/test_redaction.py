import pytest

from vres_os.redaction import redact, redact_text, sanitize_text


def test_common_secret_shapes_are_not_persisted_verbatim():
    value = "password=hunter2 token:abc123456789012345 sk-ant-secretsecretsecret"
    out = redact_text(value)
    assert "hunter2" not in out
    assert "abc123456789012345" not in out
    assert "sk-ant-secretsecretsecret" not in out


def test_nested_redaction():
    out = redact({"items": ["pwd=hello", {"x": "safe"}]})
    assert "hello" not in str(out)
    assert "safe" in str(out)


@pytest.mark.parametrize("line", [
    "DATABASE_PASSWORD=synthetic-value-a1",
    'STRIPE_API_KEY="synthetic-value-a2"',
    "github_access_token: synthetic-value-a3",
    "MY_APP_CLIENT_SECRET = synthetic-value-a4",
    "SERVICE_PASSWD=synthetic-value-a5",
    "APP_PWD=synthetic-value-a6",
    "ORG_REFRESH_TOKEN=synthetic-value-a7",
    "SIGNING_PRIVATE_KEY=synthetic-value-a8",
    '{"DATABASE_PASSWORD": "synthetic-value-a9"}',
    "[db]\nvendor_api_key = 'synthetic-value-b1'",
])
def test_prefixed_credential_keys_are_redacted_and_field_is_reported(line):
    result = sanitize_text(line)
    assert "synthetic-value" not in result.text
    assert result.rule_counts.get("kv_credential") == 1
    assert result.field_names and "synthetic" not in " ".join(result.field_names)
    assert not result.residual


def test_uri_bearer_provider_and_private_key_block_are_sanitized():
    text = (
        "dsn postgresql://svc:synthetic-dsn-pass@db.example:5432/app\n"
        "Authorization: Bearer synthetic.bearer.value1234\n"
        "key sk-ant-syntheticprovidervalue000 ghp_syntheticgithubtoken0123456789\n"
        "-----BEGIN RSA PRIVATE KEY-----\nsynthetic-pem-body\n-----END RSA PRIVATE KEY-----\n"
    )
    result = sanitize_text(text)
    for leaked in ("synthetic-dsn-pass", "synthetic.bearer", "syntheticprovidervalue", "syntheticgithubtoken",
                   "synthetic-pem-body"):
        assert leaked not in result.text
    assert {"uri_credential", "bearer_token", "provider_token", "private_key_block"} <= set(result.rule_counts)
    assert not result.residual


def test_dict_keys_ending_in_secret_words_redact_their_values():
    out = redact({"DATABASE_PASSWORD": "synthetic-1", "STRIPE_API_KEY": "synthetic-2", "max_tokens": 5,
                  "nested": {"github_access_token": "synthetic-3"}, "source_key": "SRC-1"})
    assert "synthetic" not in str(out)
    assert out["max_tokens"] == 5 and out["source_key"] == "SRC-1"


def test_residual_postcondition_flags_unreduced_shapes():
    ambiguous = sanitize_text('secret_key = "synthetic-ambiguous-value"')
    assert ambiguous.residual.get("residual_credential_assignment") == 1
    unterminated = sanitize_text("-----BEGIN PRIVATE KEY-----\nsynthetic-truncated-body")
    assert unterminated.residual.get("residual_private_key_marker") == 1
    assert sanitize_text("AKIA" + "ABCDEFGHIJKLMNOP").residual.get("residual_provider_token") == 1


def test_ordinary_text_is_unchanged_and_not_flagged():
    text = "This process describes how invoices are approved. Tokens of appreciation are welcome."
    result = sanitize_text(text)
    assert result.text == text and not result.rule_counts and not result.residual


def test_sanitizer_is_idempotent():
    once = sanitize_text("DATABASE_PASSWORD=synthetic-value-a1 and postgres://u:synthetic-x@h/db").text
    again = sanitize_text(once)
    assert again.text == once and not again.rule_counts and not again.residual


def test_field_names_are_canonical_families_not_untrusted_key_text():
    result = sanitize_text("zzSyntheticLeak9_password = synthetic-value-c1")
    assert result.field_names == ["password"]


def test_multiline_quoted_credential_value_is_fully_redacted():
    assert redact_text('password: "synthetic-a\nsynthetic-b"') == "password: [REDACTED]"


@pytest.mark.parametrize("text", [
    "password=[REDACTED]synthetic-tail-d1",
    "postgres://user:synthetic-tail-d2:[REDACTED]@db/x",
])
def test_idempotence_shortcut_does_not_let_crafted_tails_through(text):
    assert "synthetic-tail" not in redact_text(text)


@pytest.mark.parametrize("text", [
    '{"auth": "c3ludGhldGljLWRvY2tlcg=="}',
    "client-key-data: LS0tsyntheticLS0tsynthetic",
    "JWT_SIGNING_KEY=synthetic-signing-e1",
    "passphrase = synthetic-pass-e2",
    "url: https://hooks.slack.com/services/TSYNTH123/BSYNTH123/synthetic",
])
def test_common_credential_shapes_fail_closed(text):
    assert sanitize_text(text).residual


def test_ordinary_prose_and_authors_do_not_fail_closed():
    assert not sanitize_text("author: Alexander Hamilton\nThe token bucket limits requests.").residual


def test_uri_scheme_scan_is_linear_enough():
    import time
    start = time.perf_counter()
    redact_text("a" * 200_000)
    assert time.perf_counter() - start < 2


def test_aws_key_id_and_github_tokens_never_pass_and_stop_or_redact():
    aws = "AKIA" + "ZZM164SYNTHETIC1"  # synthetic, AWS access key id shape
    assert sanitize_text(f"id {aws}").residual
    gh = "ghp_" + "Z" * 24
    out = sanitize_text(f"token {gh} and github_pat_{'Z' * 24}")
    assert gh not in out.text and "github_pat_" + "Z" * 24 not in out.text


def test_password_policy_key_fails_closed_as_documented_false_positive():
    # Documented L2 tradeoff (docs/KNOWN-LIMITATIONS.md): a benign key that merely contains "password"
    # with a long value is stopped for human review rather than guessed safe.
    assert sanitize_text("password_policy: required-by-security").residual
    assert not sanitize_text("password_policy: on").residual


def test_separatorless_credential_phrase_is_redacted():
    """#176 E7 C5: 'database password <value>' has no ':'/'=' but is still a stated credential."""
    out = sanitize_text(
        "Backup runbook: connect with the database password <<CANARY_1>> and run the dump."
    )
    assert "CANARY_1" not in out.text
    assert out.rule_counts == {"phrase_credential": 1}
    assert "and run the dump." in out.text
    assert not out.residual
    assert sanitize_text(out.text).text == out.text  # idempotent
    assert "x9!q" not in redact_text("the admin pwd is x9!q7 for now")


def test_service_key_phrase_is_redacted():
    """#176 E7 B4B: 'the service key <value>' is a stated credential (live adversarial RED)."""
    out = sanitize_text(
        "Aborted the deployment; the pipeline printed the service key <<CANARY_1>> in its log before failing."
    )
    assert "CANARY_1" not in out.text
    assert out.rule_counts == {"phrase_credential": 1}
    assert "in its log before failing." in out.text
    assert not out.residual
    assert sanitize_text(out.text).text == out.text  # idempotent


@pytest.mark.parametrize("line", [
    "Rotate the service key policy quarterly.",
    "The master key ceremony is on Friday.",
])
def test_key_phrase_prose_without_secret_shaped_value_is_kept(line):
    assert sanitize_text(line).text == line


@pytest.mark.parametrize("line", [
    "The password policy requires rotation.",
    "Reset the password manager entry for the secret santa list.",
    "Token budget is tracked per request.",
    "password reset flow documented here",
])
def test_plain_prose_around_credential_words_is_unchanged(line):
    assert redact_text(line) == line
