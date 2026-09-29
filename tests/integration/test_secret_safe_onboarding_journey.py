"""#164 secret-safe onboarding journey (PostgreSQL). Synthetic markers only; never real credentials.

Every marker below is an obvious fake. The assertion of record is: each marker occurs ZERO times in
every persisted surface the onboarding journey touches.
"""
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("psycopg")

from vres_os import onboarding
from vres_os.db import connect
from vres_os.onboarding import OnboardingService
from vres_os.sensitive_policy import sensitive_path_reason

PEM = "-----BEGIN RSA PRIVATE KEY-----\n{m}\n-----END RSA PRIVATE KEY-----\n"
PREFIXED = ["DATABASE_PASSWORD", "LEGACY_PASSWD", "SVC_PWD", "GITHUB_TOKEN", "APP_SECRET", "STRIPE_API_KEY",
            "GH_ACCESS_TOKEN", "OKTA_REFRESH_TOKEN", "MY_APP_CLIENT_SECRET", "SIGNING_PRIVATE_KEY"]


def _m(name: str) -> str:
    return f"ZZM164{name}VALUE0001"


def _fixtures() -> dict[str, str]:
    prefixed = "\n".join(f"{k}={_m(k)}" if i % 2 else f'{k}: "{_m(k)}"' for i, k in enumerate(PREFIXED))
    return {
        # --- sensitive_excluded by path (content must never be read) ---
        ".streamlit/secrets.toml": f'db_password = "{_m("SECRETSTOML")}"\n',
        ".env": f"X={_m('ENV')}\n",
        ".env.local": f"X={_m('ENVLOCAL')}\n",
        "config/.Env.Production": f"X={_m('ENVPROD')}\n",
        "credentials.json": f'{{"k": "{_m("CREDJSON")}"}}\n',
        "vendor/Credentials.yaml": f"k: {_m('CREDYAML')}\n",
        "auth.yaml": f"token: {_m('AUTHYAML')}\n",
        "auth.json": f'{{"t": "{_m("AUTHJSON")}"}}\n',
        "id_rsa": PEM.format(m=_m("IDRSA")),
        "keys/server.PEM": PEM.format(m=_m("SERVERPEM")),
        ".vres/local-secrets/runbook-process.md": f"# process runbook\n{_m('VRESLOCAL')}\n",
        # --- mixed useful documents: sanitize, keep the useful text ---
        "docs/plan.toml": f'# Billing process runbook\n[db]\nDATABASE_PASSWORD = "{_m("TOML")}"\n',
        "docs/plan.md": f"# Billing process runbook\nSTRIPE_API_KEY=\"{_m('MD')}\"\n",
        "docs/plan.json": f'{{"title": "Billing process runbook", "MY_APP_CLIENT_SECRET": "{_m("JSON")}"}}',
        "docs/plan.yaml": f"title: Billing process runbook\ngithub_access_token: {_m('YAML')}\n",
        "docs/dsn.md": f"Billing process runbook\npostgresql://svc_user:{_m('DSN')}@db.internal:5432/app\n"
                       f"Authorization: Bearer {_m('BEARER')}\n",
        "docs/provider.md": f"Billing process runbook\nsk-ant-{_m('PROVIDER')} ghp_ZZM164GHPTOKEN0123456789ABC\n",
        "docs/pem.md": "Billing process runbook\n" + PEM.format(m=_m("PEMBODY")),
        "docs/prefixed.txt": "Billing process runbook\n" + prefixed + "\n",
        # --- byte-identical duplicate of a sanitized document: disposition must stay inspectable ---
        "docs/dup-a.yaml": f"title: Billing process runbook\nlegacy_password: {_m('DUP')}\n",
        "docs/dup-b.yaml": f"title: Billing process runbook\nlegacy_password: {_m('DUP')}\n",
        # --- ordinary document whose NAME merely contains "secrets": stays processable ---
        "docs/secrets.md": "# Secrets management process runbook\nRotate shared access quarterly.\n",
        # --- ordinary safe documentation, and its byte-identical duplicate ---
        "docs/safe.md": "# Refund process runbook\nApprove refunds in the finance procedure.\n",
        "docs/safe-copy.md": "# Refund process runbook\nApprove refunds in the finance procedure.\n",
        # --- ambiguous secret shape: must fail closed ---
        "docs/ambiguous.md": f'Billing process runbook\nsecret_key = "{_m("AMBIGUOUS")}"\n',
        # --- generated/dependency pruning ---
        "node_modules/pkg/index.txt": f"process runbook {_m('NODEMODULES')}\n",
        "NODE_MODULES/pkg/index.txt": f"process runbook {_m('NODEMODULESUPPER')}\n",
        ".git/notes.txt": f"process runbook {_m('GIT')}\n",
        "__pycache__/x.txt": f"process runbook {_m('PYCACHE')}\n",
    }


EXCLUDED_MARKERS = ["SECRETSTOML", "ENV", "ENVLOCAL", "ENVPROD", "CREDJSON", "CREDYAML", "AUTHYAML", "AUTHJSON",
                    "IDRSA", "SERVERPEM", "VRESLOCAL"]
SANITIZED_MARKERS = ["DUP", "TOML", "MD", "JSON", "YAML", "DSN", "BEARER", "PROVIDER", "PEMBODY", *PREFIXED]
PRUNED_MARKERS = ["NODEMODULES", "NODEMODULESUPPER", "GIT", "PYCACHE"]
ALL_MARKERS = [_m(n) for n in [*EXCLUDED_MARKERS, *SANITIZED_MARKERS, *PRUNED_MARKERS, "AMBIGUOUS", "LINKED"]]
ALL_MARKERS.append("ZZM164GHPTOKEN0123456789ABC")


def _write(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))


def _link_outside_dir(root: Path, outside: Path) -> list[str]:
    """Create a symlink and (on Windows) a junction to a directory holding a marker file."""
    outside.mkdir()
    (outside / "linked-process-runbook.txt").write_text(f"process runbook {_m('LINKED')}\n")
    made = []
    try:
        os.symlink(outside, root / "linkdir", target_is_directory=True)
        made.append("symlink")
    except (OSError, NotImplementedError):
        pass
    if os.name == "nt":
        done = subprocess.run(["cmd", "/c", "mklink", "/J", str(root / "junction"), str(outside)],
                              capture_output=True, text=True)
        if done.returncode == 0:
            made.append("junction")
    return made


def _snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    return {str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file() and not p.is_symlink()}


@pytest.fixture
def embeddings_on(monkeypatch):
    cfg = SimpleNamespace(embeddings_enabled=True, embedding_model="synthetic-test-model")
    monkeypatch.setattr(onboarding, "ConfigStore", lambda: SimpleNamespace(load=lambda: cfg))


def _persisted_blob(project_id: int) -> str:
    queries = [
        "SELECT to_jsonb(t)::text AS j FROM vres.sources t WHERE project_id=%s",
        "SELECT to_jsonb(l)::text AS j FROM vres.source_locations l JOIN vres.sources s ON s.id=l.source_id "
        "WHERE s.project_id=%s",
        "SELECT to_jsonb(f)::text AS j FROM vres.source_files f JOIN vres.onboarding_jobs j ON j.id=f.job_id "
        "WHERE j.project_id=%s",
        "SELECT to_jsonb(c)::text AS j FROM vres.knowledge_chunks c JOIN vres.sources s ON s.id=c.source_id "
        "WHERE s.project_id=%s",
        "SELECT to_jsonb(q)::text AS j FROM vres.review_queue q WHERE project_id=%s",
        "SELECT to_jsonb(j)::text AS j FROM vres.onboarding_jobs j WHERE project_id=%s",
        "SELECT to_jsonb(e)::text AS j FROM vres.embedding_jobs e JOIN vres.knowledge_chunks c ON c.id=e.chunk_id "
        "JOIN vres.sources s ON s.id=c.source_id WHERE s.project_id=%s",
    ]
    with connect() as conn:
        return "\n".join(r["to_jsonb"] if "to_jsonb" in r else next(iter(r.values()))
                         for q in queries for r in conn.execute(q, (project_id,)).fetchall())


def _cleanup(project_id: int) -> None:
    with connect() as conn, conn.transaction():
        conn.execute("DELETE FROM vres.embedding_jobs WHERE chunk_id IN (SELECT c.id FROM vres.knowledge_chunks c "
                     "JOIN vres.sources s ON s.id=c.source_id WHERE s.project_id=%s)", (project_id,))
        conn.execute("DELETE FROM vres.knowledge_chunks WHERE source_id IN "
                     "(SELECT id FROM vres.sources WHERE project_id=%s)", (project_id,))
        conn.execute("DELETE FROM vres.source_locations WHERE project_id=%s", (project_id,))
        conn.execute("DELETE FROM vres.source_files WHERE job_id IN "
                     "(SELECT id FROM vres.onboarding_jobs WHERE project_id=%s)", (project_id,))
        conn.execute("DELETE FROM vres.review_queue WHERE project_id=%s", (project_id,))
        conn.execute("DELETE FROM vres.onboarding_jobs WHERE project_id=%s", (project_id,))
        conn.execute("DELETE FROM vres.sources WHERE project_id=%s", (project_id,))


def _rows(sql: str, params=()):
    with connect() as conn:
        return conn.execute(sql, params).fetchall()


def test_secret_safe_onboarding_journey(pg_project, tmp_path, monkeypatch, embeddings_on):
    root = tmp_path / "legacy"
    root.mkdir()
    _write(root, _fixtures())
    links = _link_outside_dir(root, tmp_path / "outside")
    before = _snapshot(root)

    extracted, hashed, classified = [], [], []
    real_extract, real_hash, real_classify = onboarding.extract, onboarding.sha256_file, onboarding.classify_mechanically

    def guarded_extract(path, *a, **k):
        assert not sensitive_path_reason(path), f"sensitive file parsed: {path.name}"
        extracted.append(path)
        return real_extract(path, *a, **k)

    def guarded_hash(path, *a, **k):
        assert not sensitive_path_reason(path), f"sensitive file hashed: {path.name}"
        hashed.append(path)
        return real_hash(path, *a, **k)

    def recording_classify(path, doc):
        classified.append(doc.text if doc else "")
        return real_classify(path, doc)

    monkeypatch.setattr(onboarding, "extract", guarded_extract)
    monkeypatch.setattr(onboarding, "sha256_file", guarded_hash)
    monkeypatch.setattr(onboarding, "classify_mechanically", recording_classify)

    try:
        result = OnboardingService().inventory(root, project_id=pg_project)

        # --- counts and dispositions ---
        assert result["sensitive_excluded"] == 11
        assert result["sensitive_review_required"] == 1
        assert result["sensitive_sanitized"] == 9
        assert result["duplicates"] == 2
        status = {r["relative_path"].replace("\\", "/"): r for r in _rows(
            "SELECT f.* FROM vres.source_files f JOIN vres.onboarding_jobs j ON j.id=f.job_id WHERE j.project_id=%s",
            (pg_project,))}
        for rel in ("docs/plan.toml", "docs/plan.md", "docs/plan.json", "docs/plan.yaml", "docs/dsn.md",
                    "docs/provider.md", "docs/pem.md", "docs/prefixed.txt"):
            assert status[rel]["extraction_status"] == "sensitive_sanitized", rel
            assert status[rel]["classification"] == "process", rel
        assert status["docs/ambiguous.md"]["extraction_status"] == "sensitive_review_required"
        assert sorted([status["docs/safe.md"]["extraction_status"],
                       status["docs/safe-copy.md"]["extraction_status"]]) == ["duplicate", "extracted"]
        excluded = {rel for rel, r in status.items() if r["extraction_status"] == "sensitive_excluded"}
        assert len(excluded) == 11 and ".vres/local-secrets/runbook-process.md" in excluded
        for rel in excluded:
            row = status[rel]
            assert row["source_id"] is None and row["content_hash"] is None
            assert set(row["metadata"]) == {"sensitive_disposition", "policy_rule", "policy_version"}
        assert status["docs/ambiguous.md"]["content_hash"] is None and status["docs/ambiguous.md"]["source_id"] is None
        assert status["docs/plan.toml"]["metadata"]["sanitized_field_names"] == ["password"]
        # A sanitized file must not persist its raw-file hash (offline dictionary attack on the redacted value).
        import hashlib
        for rel, row in status.items():
            if row["extraction_status"] == "sensitive_sanitized":
                assert row["content_hash"] != hashlib.sha256((root / rel).read_bytes()).hexdigest(), rel
        raw_hashes = {hashlib.sha256((root / rel).read_bytes()).hexdigest() for rel in status}
        sanitized_rows = {rel: r for rel, r in status.items()
                          if r["metadata"].get("sensitive_disposition") == "sensitive_sanitized"}
        assert {"docs/dup-a.yaml", "docs/dup-b.yaml", "docs/plan.toml"} <= set(sanitized_rows)
        for rel, row in sanitized_rows.items():
            assert row["content_hash"] not in raw_hashes, rel
            src = _rows("SELECT content_hash, path_or_uri FROM vres.sources WHERE id=%s", (row["source_id"],))[0]
            assert src["content_hash"] not in raw_hashes, rel
            locations = {Path(r["path_or_uri"]).name for r in _rows(
                "SELECT path_or_uri FROM vres.source_locations WHERE source_id=%s", (row["source_id"],))}
            assert Path(rel).name in locations, rel  # every copy keeps its own provenance location
            assert not any(m in str(row["metadata"]) for m in ALL_MARKERS), rel
        dups = [status["docs/dup-a.yaml"], status["docs/dup-b.yaml"]]
        assert sorted(r["extraction_status"] for r in dups) == ["duplicate", "sensitive_sanitized"]
        assert dups[0]["content_hash"] == dups[1]["content_hash"]
        assert all(r["metadata"]["sanitized_field_names"] == ["password"] for r in dups)
        assert status["docs/secrets.md"]["extraction_status"] == "extracted"

        # --- pruning, symlink/junction exclusion ---
        rels = set(status)
        assert not any(p.split("/")[0].casefold() in {"node_modules", ".git", "__pycache__", "linkdir", "junction"}
                       for p in rels)

        # --- excluded/review files never reached extraction/hash; classification saw sanitized text only ---
        assert not any(sensitive_path_reason(p) for p in extracted + hashed)
        assert classified and not any(marker in text for text in classified for marker in ALL_MARKERS)

        # --- no chunk/embedding for excluded or review-required; sanitized useful text remains ---
        with connect() as conn:
            chunk_paths = {r["relative_path"].replace("\\", "/") for r in conn.execute(
                "SELECT DISTINCT f.relative_path FROM vres.knowledge_chunks c JOIN vres.source_files f "
                "ON f.source_id=c.source_id JOIN vres.onboarding_jobs j ON j.id=f.job_id WHERE j.project_id=%s",
                (pg_project,)).fetchall()}
            chunks = conn.execute(
                "SELECT c.content FROM vres.knowledge_chunks c JOIN vres.sources s ON s.id=c.source_id "
                "WHERE s.project_id=%s", (pg_project,)).fetchall()
            jobs = conn.execute(
                "SELECT count(*) AS n FROM vres.embedding_jobs e JOIN vres.knowledge_chunks c ON c.id=e.chunk_id "
                "JOIN vres.sources s ON s.id=c.source_id WHERE s.project_id=%s", (pg_project,)).fetchone()["n"]
        assert not chunk_paths & excluded and "docs/ambiguous.md" not in chunk_paths
        assert {"docs/plan.toml", "docs/plan.md"} <= chunk_paths and chunk_paths & {"docs/safe.md", "docs/safe-copy.md"}
        assert any("Billing process runbook" in c["content"] and "[REDACTED" in c["content"] for c in chunks)
        assert jobs == len(chunks) == result["chunks_created"] == result["embedding_jobs_queued"]

        # --- review queue holds only generic reason for the fail-closed file ---
        reviews = _rows("SELECT * FROM vres.review_queue WHERE project_id=%s", (pg_project,))
        sensitive_reviews = [r for r in reviews if "sanitiz" in r["reason"]]
        assert len(sensitive_reviews) == 1
        assert "residual_credential_assignment:1" in sensitive_reviews[0]["reason"]

        # --- zero raw markers in every persisted surface, positive control proves the scan sees data ---
        blob = _persisted_blob(pg_project)
        assert "Refund process runbook" in blob and "sensitive_excluded" in blob  # scan sees chunk + status data
        for marker in ALL_MARKERS:
            assert blob.count(marker) == 0, f"raw marker persisted: {marker}"
        assert not any(marker in str(result) for marker in ALL_MARKERS)

        # --- read-only: source bytes and mtimes unchanged ---
        assert _snapshot(root) == before

        # --- repeated onboarding preserves dedupe: no new sources or chunks ---
        first_sources = _rows("SELECT count(*) AS n FROM vres.sources WHERE project_id=%s", (pg_project,))[0]["n"]
        again = OnboardingService().inventory(root, project_id=pg_project)
        assert _rows("SELECT count(*) AS n FROM vres.sources WHERE project_id=%s", (pg_project,))[0]["n"] == first_sources
        assert again["chunks_created"] == 0
        assert again["sensitive_excluded"] == 11 and again["sensitive_review_required"] == 1
        blob = _persisted_blob(pg_project)
        for marker in ALL_MARKERS:
            assert blob.count(marker) == 0, f"raw marker persisted after rerun: {marker}"
        assert _snapshot(root) == before
    finally:
        _cleanup(pg_project)
    if not links:
        pytest.skip("symlink/junction creation unavailable on this host; all other assertions passed")


def test_file_mutation_during_extraction_stays_visible_and_indexes_nothing(pg_project, tmp_path, monkeypatch):
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "moving.md").write_text("Billing process runbook\n", encoding="utf-8")
    real_extract = onboarding.extract

    def mutating_extract(path, *a, **k):
        doc = real_extract(path, *a, **k)
        path.write_text(path.read_text(encoding="utf-8") + "appended after extraction\n", encoding="utf-8")
        return doc

    monkeypatch.setattr(onboarding, "extract", mutating_extract)
    try:
        result = OnboardingService().inventory(root, project_id=pg_project)
        reasons = [r["reason"] for r in _rows("SELECT reason FROM vres.review_queue WHERE project_id=%s", (pg_project,))]
        assert any("changed during extraction" in r for r in reasons)
        assert result["chunks_created"] == 0 and result["review_required"] == 1
    finally:
        _cleanup(pg_project)


def test_embedding_boundary_sanitized_local_encode_no_content_driven_network(pg_project, tmp_path, monkeypatch, embeddings_on):
    """Only sanitized chunks reach encode(); the loader gets only the configured model; document URLs and model
    names are inert data; acquisition failure keeps onboarded knowledge and leaves jobs retryable."""
    import socket
    import urllib.request

    from vres_os import embeddings

    root = tmp_path / "legacy"
    root.mkdir()
    hostile = "Use model evil/other-model at https://evil.example/model and http://169.254.169.254/latest"
    files = _fixtures()
    files["docs/links.md"] = f"# Process runbook\n[x](https://evil.example/a)\n{hostile}\n"
    files["docs/links.json"] = '{"title": "Billing process runbook", "url": "https://evil.example/j", "model": "evil/other-model"}\n'
    files["docs/links.yaml"] = "title: Billing process runbook\nurl: https://evil.example/y\nmodel: evil/other-model\n"
    files["docs/links.toml"] = 'title = "Billing process runbook"\nurl = "https://evil.example/t"\n'
    _write(root, files)

    def no_network(*a, **k):
        raise AssertionError("onboarding attempted outbound network access")

    cfg = SimpleNamespace(embeddings_enabled=True, embedding_model="synthetic-test-model")
    monkeypatch.setattr(embeddings, "ConfigStore", lambda: SimpleNamespace(load=lambda: cfg))
    try:
        with monkeypatch.context() as m:
            m.setattr(socket.socket, "connect", no_network)
            m.setattr(socket, "create_connection", no_network)
            m.setattr(urllib.request, "urlopen", no_network)
            result = OnboardingService().inventory(root, project_id=pg_project)
        assert result["embedding_jobs_queued"] > 0

        # D: acquisition failure keeps sanitized chunks and never marks anything completed.
        def unavailable(name):
            raise embeddings.EmbeddingUnavailable(f"Could not acquire embedding model {name}")
        monkeypatch.setattr(embeddings, "_load_model", unavailable)
        chunks_before = _rows("SELECT count(*) AS n FROM vres.knowledge_chunks c JOIN vres.sources s ON s.id=c.source_id "
                              "WHERE s.project_id=%s", (pg_project,))[0]["n"]
        with pytest.raises(embeddings.EmbeddingUnavailable):
            embeddings.EmbeddingService().run_pending()
        mine = ("FROM vres.embedding_jobs e JOIN vres.knowledge_chunks c ON c.id=e.chunk_id "
                "JOIN vres.sources s ON s.id=c.source_id WHERE s.project_id=%s")
        assert _rows(f"SELECT count(*) AS n {mine} AND e.status='completed'", (pg_project,))[0]["n"] == 0
        assert _rows(f"SELECT count(*) AS n {mine} AND e.status IN ('pending','failed')", (pg_project,))[0]["n"] > 0
        assert _rows("SELECT count(*) AS n FROM vres.knowledge_chunks c JOIN vres.sources s ON s.id=c.source_id "
                     "WHERE s.project_id=%s", (pg_project,))[0]["n"] == chunks_before

        # B/F: after the model becomes available a retry embeds ONLY sanitized chunk text, locally.
        loaded, encoded = [], []

        class Model:
            def encode(self, texts, **kw):
                encoded.extend(texts)
                return [[1.0, 0.0] for _ in texts]

        monkeypatch.setattr(embeddings, "_load_model", lambda name: loaded.append(name) or Model())
        with monkeypatch.context() as m:
            m.setattr(socket.socket, "connect", no_network)
            m.setattr(urllib.request, "urlopen", no_network)
            for _ in range(3):
                if not embeddings.EmbeddingService().run_pending().get("processed"):
                    break
        assert set(loaded) == {"synthetic-test-model"}  # never evil/other-model from document text
        assert encoded and not any(marker in text for text in encoded for marker in ALL_MARKERS)
        assert any("evil/other-model" in text for text in encoded)  # hostile text is inert data, embedded as data
        assert _rows(f"SELECT count(*) AS n {mine} AND e.status='completed'", (pg_project,))[0]["n"] > 0
    finally:
        _cleanup(pg_project)
