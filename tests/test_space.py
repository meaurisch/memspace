from pathlib import Path
import pytest
from memspace.space import load_root, SpaceError


def test_load_root_from_env(space_a):
    root = load_root()
    assert root.path == space_a
    assert list(root.spaces) == ["alpha"]
    assert root.spaces["alpha"].policy["embeddings"] == "local"
    assert root.spaces["alpha"].admission == "lax"


def test_admission_read_from_memory_yaml(space_a):
    p = space_a / "memory.yaml"
    p.write_text(p.read_text(encoding="utf-8").replace("    remote: local", "    remote: local\n    admission: strict"), encoding="utf-8")
    assert load_root().spaces["alpha"].admission == "strict"


def test_load_root_walks_up(space_a, monkeypatch):
    monkeypatch.delenv("MEMSPACE_ROOT")
    root = load_root(space_a / "spaces" / "alpha" / "proj-x")
    assert root.path == space_a


def test_missing_root(tmp_path, monkeypatch):
    monkeypatch.delenv("MEMSPACE_ROOT", raising=False)
    with pytest.raises(SpaceError):
        load_root(tmp_path)


def test_scope_dir_and_scopes(space_a):
    sp = load_root().spaces["alpha"]
    assert sp.scope_dir("alpha") == space_a / "spaces" / "alpha"
    assert sp.scope_dir("alpha/proj-x") == space_a / "spaces" / "alpha" / "proj-x"
    assert sp.scopes() == ["alpha", "alpha/proj-x"]
    with pytest.raises(SpaceError):
        sp.scope_dir("beta/x")


def test_facts_and_by_id(space_a):
    sp = load_root().spaces["alpha"]
    ids = sorted(f.id for f in sp.facts())
    assert ids == ["dec-0001-sqlite", "dec-0002-old-orm", "epi-0001-ci-flake",
                   "fact-0001-disputed", "pref-0001-tabs"]
    assert sp.by_id()["dec-0001-sqlite"].scope == "alpha/proj-x"


def test_proposed_included_on_request(space_a):
    p = space_a / "spaces/alpha/proj-x/proposed"
    p.mkdir()
    src = (space_a / "spaces/alpha/proj-x/facts/dec-0001-sqlite.md").read_text(encoding="utf-8")
    (p / "dec-0003-new.md").write_text(
        src.replace("id: dec-0001-sqlite", "id: dec-0003-new").replace("status: active", "status: proposed")
           .replace("supersedes: [dec-0002-old-orm]", "supersedes: []"), encoding="utf-8")
    sp = load_root().spaces["alpha"]
    assert "dec-0003-new" not in sp.by_id()
    assert "dec-0003-new" in sp.by_id(include_proposed=True)
