import datetime as dt
from memspace.space import load_root
from memspace.lint import lint_space, has_errors
from memspace.index import write_indexes

TODAY = dt.date(2026, 8, 23)


def msgs(findings, level=None):
    return [f.message for f in findings if level is None or f.level == level]


def test_fixture_has_only_expected_warnings(space_a):
    sp = load_root().spaces["alpha"]
    write_indexes(sp)
    fs = lint_space(sp, today=TODAY)
    assert not has_errors(fs)
    w = msgs(fs, "warn")
    assert any("epi-0001-ci-flake" in m and "90" in m for m in w)
    assert any("fact-0001-disputed" in m and "7" in m for m in w)
    assert len(w) == 2


def test_parse_error_is_reported(space_a):
    bad = space_a / "spaces/alpha/proj-x/facts/dec-0009-bad.md"
    bad.write_text("---\nid: dec-0009-bad\n---\nno fields\n", encoding="utf-8")
    fs = lint_space(load_root().spaces["alpha"], today=TODAY)
    assert has_errors(fs)
    assert any("dec-0009-bad" in m for m in msgs(fs, "error"))


def test_scope_dir_mismatch(space_a):
    p = space_a / "spaces/alpha/proj-x/facts/dec-0001-sqlite.md"
    p.write_text(p.read_text(encoding="utf-8").replace("scope: alpha/proj-x", "scope: alpha"), encoding="utf-8")
    fs = lint_space(load_root().spaces["alpha"], today=TODAY)
    assert any("scope" in m and "dec-0001-sqlite" in m for m in msgs(fs, "error"))


def test_dangling_and_asymmetric_supersedes(space_a):
    p = space_a / "spaces/alpha/proj-x/facts/dec-0002-old-orm.md"
    p.write_text(p.read_text(encoding="utf-8").replace("superseded_by: dec-0001-sqlite", "superseded_by: dec-0077-ghost"), encoding="utf-8")
    fs = lint_space(load_root().spaces["alpha"], today=TODAY)
    errs = msgs(fs, "error")
    assert any("dec-0077-ghost" in m for m in errs)
    assert any("asymmetric" in m.lower() for m in errs)


def test_proposed_file_with_wrong_status_warns(space_a):
    p = space_a / "spaces/alpha/proj-x/proposed"
    p.mkdir()
    src = (space_a / "spaces/alpha/proj-x/facts/epi-0001-ci-flake.md").read_text(encoding="utf-8")
    (p / "epi-0002-x.md").write_text(src.replace("id: epi-0001-ci-flake", "id: epi-0002-x"), encoding="utf-8")
    fs = lint_space(load_root().spaces["alpha"], today=TODAY)
    assert any("epi-0002-x" in m and "proposed" in m for m in msgs(fs, "warn"))
