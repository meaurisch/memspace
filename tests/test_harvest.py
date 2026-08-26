import json
from pathlib import Path

from memspace.cli import main
from memspace.facts import parse_fact
from memspace.harvest import harvest
from memspace.space import load_root

FIX = json.loads((Path(__file__).parent / "fixtures/gh/api-harvest.json").read_text(encoding="utf-8"))
REPO = "example-org/example-repo"
SINCE = "2026-02-01"


class FakeRun:
    """Replays recorded `gh api` responses; the suite never touches the network."""

    def __init__(self):
        self.calls = []
        self.kwargs = []

    def __call__(self, args, **kw):
        self.calls.append(args)
        self.kwargs.append(kw)
        endpoint = args[-1].split("?")[0]
        if endpoint not in FIX:
            raise AssertionError(f"unrecorded gh api call: {args}")

        class R:
            pass
        r = R(); r.returncode = 0; r.stdout = json.dumps(FIX[endpoint]); r.stderr = ""
        return r


def _proposed(space_a):
    return sorted((space_a / "spaces/alpha/proposed").glob("*.md"))


def test_harvest_writes_candidates_to_proposed_only(space_a):
    sp = load_root().spaces["alpha"]
    before = {p.name for p in (space_a / "spaces/alpha/facts").glob("*.md")}
    written = harvest(sp, REPO, SINCE, runner=FakeRun())
    assert written and all(p.parent.name == "proposed" for p in written)
    assert {p.name for p in (space_a / "spaces/alpha/facts").glob("*.md")} == before
    f = parse_fact(written[0])
    assert f.status == "proposed" and f.scope == "alpha"
    assert any(s.startswith("https://github.com/example-org/example-repo/pull/") for s in f.sources)
    assert "discussion_r" in " ".join(f.sources)


def test_only_prs_merged_since_are_read(space_a):
    sp = load_root().spaces["alpha"]
    run = FakeRun()
    harvest(sp, REPO, SINCE, runner=run)
    endpoints = [a[-1].split("?")[0] for a in run.calls]
    assert f"repos/{REPO}/pulls/42/comments" in endpoints
    assert f"repos/{REPO}/pulls/40/comments" in endpoints
    assert f"repos/{REPO}/pulls/41/comments" not in endpoints   # closed, never merged
    assert f"repos/{REPO}/pulls/39/comments" not in endpoints   # merged before --since


def test_trivial_and_bot_comments_are_skipped(space_a):
    sp = load_root().spaces["alpha"]
    harvest(sp, REPO, SINCE, runner=FakeRun())
    text = "\n".join(p.read_text(encoding="utf-8") for p in _proposed(space_a))
    assert "LGTM" not in text and "nit." not in text
    assert "Coverage decreased" not in text
    assert "Key the cache by URL" in text


def test_duplicate_comment_text_lands_once(space_a):
    """PR 40 repeats PR 42's comment with different case and spacing."""
    sp = load_root().spaces["alpha"]
    harvest(sp, REPO, SINCE, runner=FakeRun())
    summaries = [parse_fact(p).summary for p in _proposed(space_a)]
    assert len(summaries) == 2
    assert sum("key the cache by url" in s.casefold() for s in summaries) == 1


def test_second_run_adds_nothing(space_a):
    sp = load_root().spaces["alpha"]
    harvest(sp, REPO, SINCE, runner=FakeRun())
    first = _proposed(space_a)
    assert harvest(load_root().spaces["alpha"], REPO, SINCE, runner=FakeRun()) == []
    assert _proposed(space_a) == first


def test_gh_output_is_decoded_as_utf8(space_a):
    run = FakeRun()
    harvest(load_root().spaces["alpha"], REPO, SINCE, runner=run)
    assert run.kwargs and all(kw.get("encoding") == "utf-8" for kw in run.kwargs)


def test_cli_harvest(space_a, capsys, monkeypatch):
    import memspace.harvest as mod
    monkeypatch.setattr(mod.subprocess, "run", FakeRun())
    assert main(["harvest", "alpha", "--repo", REPO, "--since", SINCE]) == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert out and all("/proposed/" in line for line in out)


def test_cli_rejects_bad_since(space_a, capsys):
    assert main(["harvest", "alpha", "--repo", REPO, "--since", "last tuesday"]) == 1
    assert "error:" in capsys.readouterr().err
