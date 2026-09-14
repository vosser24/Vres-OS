from vres_os.redaction import redact, redact_text


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
