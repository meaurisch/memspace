from memspace.space import load_root
from memspace.index import write_indexes
from memspace.export import export_context, estimate_tokens


def test_export_contains_both_indexes_and_details(space_a):
    sp = load_root().spaces["alpha"]; write_indexes(sp)
    out = export_context(sp, "alpha/proj-x")
    assert out.startswith("# alpha — memory index")
    assert "# alpha/proj-x — memory index" in out
    assert "### [dec-0001-sqlite] Use SQLite" in out or "### [dec-0001-sqlite]" in out
    assert "dec-0002-old-orm" not in out          # superseded excluded


def test_budget_limits_details(space_a):
    sp = load_root().spaces["alpha"]; write_indexes(sp)
    small = export_context(sp, "alpha/proj-x", budget_tokens=estimate_tokens(export_context(sp, "alpha/proj-x", 0)) + 5)
    assert "## Details" in small and "### [" not in small


def test_subject_before_space_facts(space_a):
    sp = load_root().spaces["alpha"]; write_indexes(sp)
    out = export_context(sp, "alpha/proj-x")
    assert out.index("### [dec-0001-sqlite]") < out.index("### [pref-0001-tabs]")
