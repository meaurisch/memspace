from pathlib import Path
from memspace.space import load_root
from memspace.index import render_index, write_indexes, stale_indexes, index_line_counts
from memspace.lint import lint_space, has_errors

GOLDEN = Path(__file__).parent / "fixtures/golden/alpha-proj-x-index.md"


def test_render_matches_golden(space_a):
    sp = load_root().spaces["alpha"]
    assert render_index(sp, "alpha/proj-x") == GOLDEN.read_text(encoding="utf-8")


def test_space_index_lists_subjects(space_a):
    sp = load_root().spaces["alpha"]
    text = render_index(sp, "alpha")
    assert "## Subjects" in text and "- proj-x — proj-x is a fixture project: a tiny CLI." in text
    assert "[pref-0001-tabs]" in text and "dec-0001-sqlite" not in text


def test_write_then_not_stale(space_a):
    sp = load_root().spaces["alpha"]
    assert stale_indexes(sp)  # none written yet
    written = write_indexes(sp)
    assert sorted(p.name for p in written) == ["index.md", "index.md"]
    assert stale_indexes(sp) == []
    assert not has_errors(lint_space(sp))


def test_short_sources():
    from memspace.index import _short_source
    assert _short_source("https://github.com/o/r/issues/9") == "#9"
    assert _short_source("https://github.com/o/r/pull/14") == "PR#14"
    assert _short_source("git:3d840e8abc") == "git:3d840e8"
    assert _short_source("src/config.py:42") == "src/config.py:42"


def test_line_cap_is_linted(space_a):
    sp = load_root().spaces["alpha"]
    write_indexes(sp)
    idx = sp.scope_dir("alpha/proj-x") / "index.md"
    idx.write_text(idx.read_text(encoding="utf-8") + "\n" * 70, encoding="utf-8")
    counts = index_line_counts(sp)
    assert counts[idx] > 60
