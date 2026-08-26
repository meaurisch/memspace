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


def strict(space_a):
    p = space_a / "memory.yaml"
    p.write_text(p.read_text(encoding="utf-8").replace("    remote: local", "    remote: local\n    admission: strict"), encoding="utf-8")


def test_lax_space_allows_facts_without_an_action(space_a):
    sp = load_root().spaces["alpha"]
    write_indexes(sp)
    assert sp.admission == "lax"
    assert not has_errors(lint_space(sp, today=TODAY))


def test_strict_admission_rejects_unactionable_decision(space_a):
    strict(space_a)
    sp = load_root().spaces["alpha"]
    write_indexes(sp)
    assert sp.admission == "strict"
    errs = msgs(lint_space(sp, today=TODAY), "error")
    assert any(m == "dec-0001-sqlite: not actionable: name the agent action this fact changes, or retype it"
               for m in errs)


def test_strict_admission_accepts_trigger_plus_action_hint(space_a):
    strict(space_a)
    p = space_a / "spaces/alpha/proj-x/facts/dec-0001-sqlite.md"
    p.write_text(p.read_text(encoding="utf-8").replace(
        "tags: []", "tags: []\ntriggers: [database]\naction_hint: use SQLite, do not add a database service"),
        encoding="utf-8")
    sp = load_root().spaces["alpha"]
    write_indexes(sp)
    assert not any("dec-0001-sqlite" in m for m in msgs(lint_space(sp, today=TODAY), "error"))


def test_strict_admission_needs_both_a_trigger_and_a_hint(space_a):
    strict(space_a)
    p = space_a / "spaces/alpha/proj-x/facts/dec-0001-sqlite.md"
    p.write_text(p.read_text(encoding="utf-8").replace("tags: []", "tags: []\ntriggers: [database]"), encoding="utf-8")
    sp = load_root().spaces["alpha"]
    write_indexes(sp)
    assert any("dec-0001-sqlite" in m and "not actionable" in m for m in msgs(lint_space(sp, today=TODAY), "error"))


def test_strict_admission_ignores_other_types_and_inactive_facts(space_a):
    strict(space_a)
    sp = load_root().spaces["alpha"]
    write_indexes(sp)
    errs = msgs(lint_space(sp, today=TODAY), "error")
    for other in ("pref-0001-tabs", "epi-0001-ci-flake", "fact-0001-disputed", "dec-0002-old-orm"):
        assert not any(other in m for m in errs)


def test_proposed_file_with_wrong_status_warns(space_a):
    p = space_a / "spaces/alpha/proj-x/proposed"
    p.mkdir()
    src = (space_a / "spaces/alpha/proj-x/facts/epi-0001-ci-flake.md").read_text(encoding="utf-8")
    (p / "epi-0002-x.md").write_text(src.replace("id: epi-0001-ci-flake", "id: epi-0002-x"), encoding="utf-8")
    fs = lint_space(load_root().spaces["alpha"], today=TODAY)
    assert any("epi-0002-x" in m and "proposed" in m for m in msgs(fs, "warn"))
