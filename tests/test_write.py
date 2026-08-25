import datetime as dt
from memspace.space import load_root
from memspace.write import remember, supersede, next_id
from memspace.facts import parse_fact
from memspace.lint import lint_space, has_errors
from memspace.index import write_indexes

T = dt.date(2026, 8, 23)


def test_next_id_is_space_wide(space_a):
    sp = load_root().spaces["alpha"]
    assert next_id(sp, "alpha", "decision") == "dec-0003"


def test_remember_into_proposed(space_a):
    sp = load_root().spaces["alpha"]
    p = remember(sp, "alpha/proj-x", "decision", "Use Click for CLI", "Click over argparse for subcommands",
                 ["https://github.com/x/y/issues/5"], body="Because plugins.", today=T)
    assert p.parent.name == "proposed" and p.name == "dec-0003-use-click-for-cli.md"
    f = parse_fact(p)
    assert f.status == "proposed" and f.author == "claude-code" and f.created == T


def test_remember_direct(space_a):
    sp = load_root().spaces["alpha"]
    p = remember(sp, "alpha", "preference", "Prefer uv", "uv over pip", ["https://x/1"], direct=True, author="morris", today=T)
    assert p.parent.name == "facts" and parse_fact(p).status == "active"


def test_supersede_flips_both_sides(space_a):
    sp = load_root().spaces["alpha"]
    write_indexes(sp)
    new = remember(sp, "alpha/proj-x", "decision", "Use Postgres after all", "Postgres now that we have users",
                   ["https://x/2"], direct=True, today=T)
    supersede(sp, "dec-0001-sqlite", parse_fact(new).id, today=T)
    old = sp.by_id()["dec-0001-sqlite"]
    assert old.status == "superseded" and old.superseded_by == "dec-0003-use-postgres-after-all"
    assert "dec-0001-sqlite" in sp.by_id()["dec-0003-use-postgres-after-all"].supersedes
    assert not has_errors(lint_space(sp, today=T))
    assert "dec-0001-sqlite" not in (sp.scope_dir("alpha/proj-x") / "index.md").read_text(encoding="utf-8")
