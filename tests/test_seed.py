import json
from pathlib import Path
from memspace.seed import seed_brief

FIX = Path(__file__).parent / "fixtures/gh"


class FakeRun:
    def __init__(self):
        self.calls = []
        self.kwargs = []

    def __call__(self, args, **kw):
        self.calls.append(args)
        self.kwargs.append(kw)
        name = "issues.json" if args[1] == "issue" else "prs.json"

        class R:
            pass
        r = R(); r.returncode = 0; r.stdout = (FIX / name).read_text(encoding="utf-8"); r.stderr = ""
        return r


def test_brief_sections():
    run = FakeRun()
    out = seed_brief("example/todo-api", runner=run)
    assert "# Seed brief: example/todo-api" in out
    assert "### #9" in out and "we do not skip them" in out
    assert "### PR #14" in out
    assert "## Dependabot PRs" in out and "- PR #1 Bump pytest" in out
    assert "### PR #1 " not in out
    assert any("--repo" in a and "example/todo-api" in a for a in run.calls)


def test_since_filters(tmp_path):
    out = seed_brief("o/r", since="2030-01-01", runner=FakeRun())
    assert "### #9" not in out


def test_gh_output_is_decoded_as_utf8():
    """`gh` writes UTF-8. Without an explicit encoding, subprocess decodes with the
    platform default — cp1252 on Windows — and a single non-ASCII byte kills the
    reader thread, leaving stdout empty and the brief silently short a section."""
    run = FakeRun()
    seed_brief("o/r", runner=run)
    assert run.kwargs
    assert all(kw.get("encoding") == "utf-8" for kw in run.kwargs)
