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
