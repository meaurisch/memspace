from memspace.space import load_root
from memspace.recall import recall


def test_exact_id_ranks_first(space_a):
    sp = load_root().spaces["alpha"]
    hits = recall(sp, "alpha/proj-x", "dec-0001-sqlite")
    assert hits[0].id == "dec-0001-sqlite"


def test_keyword_query(space_a):
    sp = load_root().spaces["alpha"]
    assert [f.id for f in recall(sp, "alpha/proj-x", "postgres single user")][0] == "dec-0001-sqlite"


def test_space_facts_visible_from_subject(space_a):
    sp = load_root().spaces["alpha"]
    assert any(f.id == "pref-0001-tabs" for f in recall(sp, "alpha/proj-x", "tabs indent"))


def test_superseded_excluded_unless_asked(space_a):
    sp = load_root().spaces["alpha"]
    assert not any(f.id == "dec-0002-old-orm" for f in recall(sp, "alpha/proj-x", "ORM layer"))
    assert any(f.id == "dec-0002-old-orm" for f in recall(sp, "alpha/proj-x", "ORM layer", include_superseded=True))


def test_type_filter_and_k(space_a):
    sp = load_root().spaces["alpha"]
    hits = recall(sp, "alpha/proj-x", "the", k=1, types=["episode"])
    assert len(hits) == 1 and hits[0].type == "episode"


def test_no_crash_on_punctuation(space_a):
    sp = load_root().spaces["alpha"]
    assert isinstance(recall(sp, "alpha/proj-x", 'load_config() "weird" -x'), list)


def _add_source(space_a, extra):
    p = space_a / "spaces/alpha/proj-x/facts/dec-0001-sqlite.md"
    p.write_text(p.read_text(encoding="utf-8").replace(
        "sources:\n  - https://example.com/1", f"sources:\n  - https://example.com/1\n  - {extra}"),
        encoding="utf-8")


def test_validate_drops_hit_with_dead_path_citation(space_a):
    _add_source(space_a, "does-not-exist.txt")
    sp = load_root().spaces["alpha"]
    hits = recall(sp, "alpha/proj-x", "sqlite", validate=True, repo_root=space_a)
    assert not any(f.id == "dec-0001-sqlite" for f in hits)


def test_validate_keeps_hit_with_resolvable_path_citation(space_a):
    (space_a / "README.md").write_text("hi\n", encoding="utf-8")
    _add_source(space_a, "README.md")
    sp = load_root().spaces["alpha"]
    hits = recall(sp, "alpha/proj-x", "sqlite", validate=True, repo_root=space_a)
    assert any(f.id == "dec-0001-sqlite" for f in hits)


def test_validate_checks_line_number_in_path_line_citation(space_a):
    (space_a / "settings.py").write_text("a = 1\n", encoding="utf-8")
    _add_source(space_a, "settings.py:99")
    sp = load_root().spaces["alpha"]
    hits = recall(sp, "alpha/proj-x", "sqlite", validate=True, repo_root=space_a)
    assert not any(f.id == "dec-0001-sqlite" for f in hits)


def test_validate_accepts_valid_path_line_citation(space_a):
    (space_a / "settings.py").write_text("a = 1\nb = 2\n", encoding="utf-8")
    _add_source(space_a, "settings.py:2")
    sp = load_root().spaces["alpha"]
    hits = recall(sp, "alpha/proj-x", "sqlite", validate=True, repo_root=space_a)
    assert any(f.id == "dec-0001-sqlite" for f in hits)


def test_validate_never_invalidates_url_sources(space_a):
    sp = load_root().spaces["alpha"]
    hits = recall(sp, "alpha/proj-x", "sqlite", validate=True, repo_root=space_a)
    assert any(f.id == "dec-0001-sqlite" for f in hits)


def test_validate_off_by_default_keeps_dead_citation_hit(space_a):
    _add_source(space_a, "does-not-exist.txt")
    sp = load_root().spaces["alpha"]
    hits = recall(sp, "alpha/proj-x", "sqlite")
    assert any(f.id == "dec-0001-sqlite" for f in hits)
