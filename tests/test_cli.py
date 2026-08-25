import sys
from memspace.cli import main
from memspace.index import write_indexes
from memspace.space import load_root


def test_lint_exit_codes(space_a, capsys):
    assert main(["lint", "--today", "2026-08-23"]) == 1          # indexes not written yet -> stale errors
    write_indexes(load_root().spaces["alpha"])
    assert main(["lint", "--today", "2026-08-23"]) == 0
    assert "warn" in capsys.readouterr().out


def test_index_check(space_a):
    assert main(["index", "--check"]) == 1
    assert main(["index"]) == 0
    assert main(["index", "--check"]) == 0


def test_export_and_recall(space_a, capsys):
    main(["index"])
    assert main(["export-context", "alpha/proj-x", "--budget-tokens", "500"]) == 0
    assert "# alpha/proj-x — memory index" in capsys.readouterr().out
    assert main(["recall", "alpha/proj-x", "sqlite", "-k", "3"]) == 0
    assert "dec-0001-sqlite" in capsys.readouterr().out


def test_remember_and_supersede(space_a, capsys):
    main(["index"])
    assert main(["remember", "--scope", "alpha/proj-x", "--type", "decision", "--title", "Use Postgres",
                 "--summary", "Postgres now", "--source", "https://x/9", "--direct", "--author", "morris"]) == 0
    new_id = capsys.readouterr().out.strip().split("/")[-1].removesuffix(".md")
    assert main(["supersede", "dec-0001-sqlite", "--with", new_id]) == 0
    assert main(["lint", "--today", "2026-08-23"]) == 0


def test_no_root(tmp_path, monkeypatch):
    monkeypatch.delenv("MEMSPACE_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)
    assert main(["lint"]) == 2
