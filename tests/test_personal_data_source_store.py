"""Offline current-user catalog persistence with synthetic metadata, no DB or vault."""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from vres_os.personal_data_sources import DataSourceRefused, PersonalDataSources
from vres_os.personal_data_source_store import (
    CatalogStoreRefused,
    CurrentUserDataSourceStore,
)

NAMESPACE = "a" * 64
FOREIGN_NAMESPACE = "b" * 64
CREDENTIAL = "credential-" + "a" * 32
ORIGIN = "example.gr:5432/vres_app"
A, B, C = ("project:" + x * 24 for x in "abc")


def lookup(resource_id):
    if resource_id != CREDENTIAL:
        raise KeyError("unknown nonsecret resource")
    return SimpleNamespace(resource_id=CREDENTIAL, service_type="postgres", origin=ORIGIN)


def protect(path: Path, *, directory: bool) -> None:
    """Synthetic current-user ACL in disposable fixtures; never touch real Vres user roots."""
    path.chmod(0o700 if directory else 0o600)


@pytest.fixture
def storage(tmp_path):
    root = tmp_path / "VresOS"
    root.mkdir()
    store = CurrentUserDataSourceStore(root, NAMESPACE, lookup, owner_protector=protect)
    return store


def add_source(store: CurrentUserDataSourceStore):
    return store.update(
        lambda c: c.register_postgres(ORIGIN, CREDENTIAL, authorized=True),
        expected_revision=0,
        authorized=True,
    )


def add_binding(store, source_id, project_key, expected_revision):
    return store.update(
        lambda c: c.bind(source_id, project_key, authorized=True),
        expected_revision=expected_revision, authorized=True,
    )


def test_read_and_inspect_have_zero_filesystem_side_effects(storage):
    root = storage.root
    catalog, revision = storage.load()
    assert revision == 0
    assert catalog.to_document() == PersonalDataSources(NAMESPACE, lookup).to_document()
    assert storage.inspect_previous() is None
    assert sorted(root.iterdir()) == []


def test_missing_user_root_is_read_only_refused_without_creation(tmp_path):
    root = tmp_path / "not-installed-vres"
    store = CurrentUserDataSourceStore(root, NAMESPACE, lookup, owner_protector=protect)
    with pytest.raises(CatalogStoreRefused, match="missing"):
        store.load()
    with pytest.raises(CatalogStoreRefused, match="missing"):
        add_source(store)
    assert not root.exists()


def test_full_user_metadata_register_link_a_b_deny_c_and_persist(storage):
    sid, revision = add_source(storage)
    assert sid.startswith("data-source-") and revision == 1
    assert add_binding(storage, sid, A, 1) == (True, 2)
    assert add_binding(storage, sid, B, 2) == (True, 3)
    loaded, actual = storage.load()
    assert actual == 3
    assert loaded.summary_for(sid, A)["origin"] == ORIGIN
    assert loaded.summary_for(sid, B)["origin"] == ORIGIN
    with pytest.raises(DataSourceRefused, match="explicit project binding"):
        loaded.summary_for(sid, C)
    reloaded = CurrentUserDataSourceStore(storage.root, NAMESPACE, lookup, owner_protector=protect)
    assert reloaded.load()[1] == 3
    assert reloaded.load()[0].summary_for(sid, B)["credential_resource_id"] == CREDENTIAL
    assert reloaded.inspect_previous()[1] == 2


def test_unlink_a_keeps_b_and_does_not_link_c(storage):
    sid, _ = add_source(storage)
    add_binding(storage, sid, A, 1)
    add_binding(storage, sid, B, 2)
    assert storage.update(lambda c: c.unlink(sid, A, authorized=True), expected_revision=3, authorized=True) == (True, 4)
    loaded, revision = storage.load()
    assert revision == 4
    with pytest.raises(DataSourceRefused):
        loaded.summary_for(sid, A)
    with pytest.raises(DataSourceRefused):
        loaded.summary_for(sid, C)
    assert loaded.summary_for(sid, B)["origin"] == ORIGIN


def test_previous_preimage_is_exact_prior_bytes(storage):
    sid, _ = add_source(storage)
    before = (storage.root / "data-source-catalog" / "catalog-v1.json").read_bytes()
    add_binding(storage, sid, A, 1)
    assert (storage.root / "data-source-catalog" / "catalog-v1.previous.json").read_bytes() == before
    assert storage.inspect_previous()[1] == 1
    assert storage.load()[1] == 2


def test_filesystem_surfaces_are_only_own_subdirectory(storage):
    (storage.root / "untouched-config.json").write_bytes(b"DO NOT MUTATE")
    first_root_mode = storage.root.stat().st_mode
    add_source(storage)
    directory = storage.root / "data-source-catalog"
    names = {p.name for p in directory.iterdir()}
    assert names == {"catalog-v1.json"}
    assert (storage.root / "untouched-config.json").read_bytes() == b"DO NOT MUTATE"
    assert storage.root.stat().st_mode == first_root_mode
    if os.name != "nt":
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
        assert stat.S_IMODE((directory / "catalog-v1.json").stat().st_mode) == 0o600


def test_no_implicit_network_or_credential_lookup_on_load(storage):
    calls = []
    denied_lookup = lambda rid: calls.append(rid)
    alternate = CurrentUserDataSourceStore(storage.root, NAMESPACE, denied_lookup, owner_protector=protect)
    alternate.load()
    assert calls == []
    add_source(storage)
    alternate.load()
    assert calls == []


@pytest.mark.parametrize("authorized", [False, None, 1, "yes"])
def test_outer_store_update_requires_exact_boolean_authorization(storage, authorized):
    with pytest.raises(CatalogStoreRefused, match="explicit current-user"):
        storage.update(lambda c: c.register_postgres(ORIGIN, CREDENTIAL, authorized=True),
                       expected_revision=0, authorized=authorized)
    assert list(storage.root.iterdir()) == []


@pytest.mark.parametrize("revision", [-1, 1.0, True, "0", None, 1000000])
def test_store_requires_valid_revision_token(storage, revision):
    with pytest.raises(CatalogStoreRefused, match="exact prior revision"):
        storage.update(lambda c: None, expected_revision=revision, authorized=True)
    assert list(storage.root.iterdir()) == []


def test_stale_revision_refuses_without_modifying_current_or_previous(storage):
    sid, _ = add_source(storage)
    directory = storage.root / "data-source-catalog"
    before = (directory / "catalog-v1.json").read_bytes()
    with pytest.raises(CatalogStoreRefused, match="revision changed"):
        add_binding(storage, sid, A, 0)
    assert (directory / "catalog-v1.json").read_bytes() == before
    assert not (directory / "catalog-v1.previous.json").exists()


def test_no_op_idempotent_mutation_preserves_revision_and_no_preimage(storage):
    sid, _ = add_source(storage)
    before = storage.load()[0].to_document()
    assert storage.update(lambda c: c.register_postgres(ORIGIN, CREDENTIAL, authorized=True),
                          expected_revision=1, authorized=True) == (sid, 1)
    assert storage.load()[0].to_document() == before
    assert storage.inspect_previous() is None


def test_no_op_before_first_write_does_not_create_a_document(storage):
    result, rev = storage.update(lambda c: "looked-only", expected_revision=0, authorized=True)
    assert (result, rev) == ("looked-only", 0)
    directory = storage.root / "data-source-catalog"
    assert {p.name for p in directory.iterdir()} == set()


def test_two_instances_use_same_revision_token_and_stale_writer_refused(storage):
    other = CurrentUserDataSourceStore(storage.root, NAMESPACE, lookup, owner_protector=protect)
    assert other.load()[1] == 0
    sid, _ = add_source(storage)
    with pytest.raises(CatalogStoreRefused, match="revision changed"):
        add_binding(other, sid, A, 0)
    assert add_binding(other, sid, A, 1) == (True, 2)


def test_existing_writer_lock_refuses_without_deleting_it(storage):
    sid, _ = add_source(storage)
    directory = storage.root / "data-source-catalog"
    lock = directory / "catalog-update.lock"
    lock.write_bytes(b"LOCKED-OTHER-PROCESS")
    before = storage.load()[0].to_document()
    with pytest.raises(CatalogStoreRefused, match="interrupted writer"):
        add_binding(storage, sid, A, 1)
    assert lock.read_bytes() == b"LOCKED-OTHER-PROCESS"
    assert storage.load()[0].to_document() == before


@pytest.mark.parametrize("target", ["catalog-v1.json", "catalog-v1.previous.json"])
def test_link_redirect_in_catalog_is_refused_without_touching_target(storage, tmp_path, target):
    sid, _ = add_source(storage)
    directory = storage.root / "data-source-catalog"
    original_path = directory / target
    if original_path.exists():
        original_path.unlink()
    external = tmp_path / "EXTERNAL-DO-NOT-TOUCH"
    external.write_bytes(b"SENTINEL")
    try:
        original_path.symlink_to(external)
    except (OSError, NotImplementedError):
        pytest.skip("Windows symlink privilege unavailable")
    before = external.read_bytes()
    with pytest.raises(CatalogStoreRefused, match="link"):
        if target == "catalog-v1.json":
            storage.load()
        else:
            add_binding(storage, sid, A, 1)
    assert external.read_bytes() == before


def test_link_redirect_of_store_subdir_refused(storage, tmp_path):
    exterior = tmp_path / "outside"
    exterior.mkdir()
    directory = storage.root / "data-source-catalog"
    try:
        directory.symlink_to(exterior, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Windows symlink privilege unavailable")
    with pytest.raises(CatalogStoreRefused, match="Redirected"):
        storage.load()
    with pytest.raises(CatalogStoreRefused, match="Redirected"):
        add_source(storage)
    assert list(exterior.iterdir()) == []


def test_hardlink_in_catalog_is_refused(storage, tmp_path):
    sid, _ = add_source(storage)
    actual = storage.root / "data-source-catalog" / "catalog-v1.json"
    duplicate = tmp_path / "hardlinked-data"
    try:
        os.link(actual, duplicate)
    except OSError:
        pytest.skip("Hardlink not supported in this filesystem")
    with pytest.raises(CatalogStoreRefused, match="hard link"):
        storage.load()
    assert actual.read_bytes() == duplicate.read_bytes()


def test_wrong_user_namespace_refuses_stored_document_and_preserves_bytes(storage):
    sid, _ = add_source(storage)
    path = storage.root / "data-source-catalog" / "catalog-v1.json"
    before = path.read_bytes()
    foreign = CurrentUserDataSourceStore(storage.root, FOREIGN_NAMESPACE, lookup, owner_protector=protect)
    with pytest.raises(CatalogStoreRefused, match="wrong-user|another user"):
        foreign.load()
    assert path.read_bytes() == before


def test_tampered_document_refuses_and_preimage_is_not_corrupted(storage):
    sid, _ = add_source(storage)
    add_binding(storage, sid, A, 1)
    current = storage.root / "data-source-catalog" / "catalog-v1.json"
    previous = storage.root / "data-source-catalog" / "catalog-v1.previous.json"
    old_previous = previous.read_bytes()
    body = json.loads(current.read_bytes())
    body["sources"][sid]["secret"] = "HIDDEN"
    current.write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(CatalogStoreRefused, match="unreadable"):
        storage.load()
    assert previous.read_bytes() == old_previous


def test_noncanonical_stored_json_refused_for_exact_recovery_provenance(storage):
    add_source(storage)
    path = storage.root / "data-source-catalog" / "catalog-v1.json"
    original = path.read_bytes()
    path.write_text(json.dumps(json.loads(original), indent=4), encoding="utf-8")
    with pytest.raises(CatalogStoreRefused, match="canonical format"):
        storage.load()


def test_read_only_previous_refuses_tampered_preimage(storage):
    sid, _ = add_source(storage)
    add_binding(storage, sid, A, 1)
    path = storage.root / "data-source-catalog" / "catalog-v1.previous.json"
    path.write_bytes(b'{}')
    with pytest.raises(CatalogStoreRefused, match="Previous"):
        storage.inspect_previous()
    assert storage.load()[1] == 2


def test_owner_protection_failure_prevents_mutating_existing_current(storage):
    sid, _ = add_source(storage)
    path = storage.root / "data-source-catalog" / "catalog-v1.json"
    before = path.read_bytes()
    pre = storage.inspect_previous()

    def refuse_file(p, *, directory):
        if not directory:
            raise RuntimeError("OS failed to restrict owner-only file ACL")
        protect(p, directory=directory)

    denied = CurrentUserDataSourceStore(storage.root, NAMESPACE, lookup, owner_protector=refuse_file)
    with pytest.raises(CatalogStoreRefused, match="lock|owner-only"):
        add_binding(denied, sid, A, 1)
    assert path.read_bytes() == before
    assert pre is None and storage.inspect_previous() is None


def test_previous_snapshot_committed_before_new_catalog_and_write_failure_keeps_current(storage, monkeypatch):
    sid, _ = add_source(storage)
    path = storage.root / "data-source-catalog" / "catalog-v1.json"
    old = path.read_bytes()
    before = storage.inspect_previous()
    original = storage._atomic_write

    def fail_on_current(p, contents):
        if p.name == "catalog-v1.json":
            raise CatalogStoreRefused("synthetic stop before replacement")
        return original(p, contents)

    monkeypatch.setattr(storage, "_atomic_write", fail_on_current)
    with pytest.raises(CatalogStoreRefused, match="synthetic stop"):
        add_binding(storage, sid, A, 1)
    assert path.read_bytes() == old
    assert before is None and storage.inspect_previous()[0].to_document() == old


def test_untrusted_operation_cannot_keep_revision_static_or_store_malformed_json(storage):
    add_source(storage)
    current = storage.root / "data-source-catalog" / "catalog-v1.json"
    before = current.read_bytes()

    def corrupt(catalog):
        catalog._state["sources"][next(iter(catalog._state["sources"]))]["extra"] = "unsafe"
        catalog._state["revision"] += 1

    with pytest.raises(CatalogStoreRefused, match="structural validation"):
        storage.update(corrupt, expected_revision=1, authorized=True)
    assert current.read_bytes() == before


def test_from_broker_uses_only_nonsecret_metadata_and_namespace(storage):
    broker = SimpleNamespace(user_namespace=NAMESPACE, lookup=lookup)
    same = CurrentUserDataSourceStore.from_broker(storage.root, broker, owner_protector=protect)
    sid, _ = add_source(same)
    assert same.load()[1] == 1
    with pytest.raises(CatalogStoreRefused, match="Credential Broker"):
        CurrentUserDataSourceStore.from_broker(storage.root, object(), owner_protector=protect)


def test_cleanup_does_not_delete_other_vres_files_even_after_failure(storage):
    untouched = storage.root / "other-vres-state.json"
    untouched.write_bytes(b"ALWAYS-PRESERVED")
    with pytest.raises(DataSourceRefused):
        storage.update(lambda c: c.register_postgres("user:pw@example.gr:5432/vres_app", CREDENTIAL, authorized=True),
                       expected_revision=0, authorized=True)
    assert untouched.read_bytes() == b"ALWAYS-PRESERVED"
    assert storage.load()[1] == 0


def test_module_imports_cannot_execute_db_network_or_user_credential_locker():
    import ast
    source = Path(__file__).resolve().parents[1] / "src" / "vres_os" / "personal_data_source_store.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    modules = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    modules.extend(alias.name for n in ast.walk(tree) if isinstance(n, ast.Import) for alias in n.names)
    assert all((name or "").split(".")[0] not in {"psycopg", "requests", "socket", "subprocess", "keyring", "sqlite3"} for name in modules)
    # Production ACL protector is imported only inside the explicitly approved write callback.
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    assert any(n.name == "_default_protect" for n in functions)


# Existing saved file evidence is not operator provenance or live database truth.

def test_saved_snapshot_requires_existing_file_and_no_writer_lock(storage):
    import hashlib

    with pytest.raises(CatalogStoreRefused, match="No existing saved"):
        storage.load_saved_snapshot()
    sid, revision = add_source(storage)
    assert revision == 1
    add_binding(storage, sid, A, revision)
    file = storage.root / "data-source-catalog" / "catalog-v1.json"
    saved = file.read_bytes()
    calls = []
    silent = CurrentUserDataSourceStore(
        storage.root, NAMESPACE, lambda rid: calls.append(rid),
        owner_protector=protect)
    current, rev, sha = silent.load_saved_snapshot()
    assert rev == 2
    assert sha == hashlib.sha256(saved).hexdigest()
    assert current.summary_for(sid, A)["engine"] == "postgres"
    assert calls == []
    assert file.read_bytes() == saved
    lock = storage.root / "data-source-catalog" / "catalog-update.lock"
    lock.write_bytes(b"synthetic writer lock")
    with pytest.raises(CatalogStoreRefused, match="writer lock"):
        silent.load_saved_snapshot()
    assert file.read_bytes() == saved


def test_saved_snapshot_rejects_noncanonical_storage_without_rewriting(storage):
    sid, revision = add_source(storage)
    file = storage.root / "data-source-catalog" / "catalog-v1.json"
    original = file.read_bytes()
    file.write_bytes(original + b"\n")
    with pytest.raises(CatalogStoreRefused, match="not canonical"):
        storage.load_saved_snapshot()
    assert file.read_bytes() == original + b"\n"
