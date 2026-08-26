"""Harvest fact candidates from the review comments on merged pull requests.

Code review is where conventions get stated out loud: why this way, what broke last
time, what not to do again. This turns those comments into candidate facts a human can
read and reject.

Every candidate lands in `proposed/`. Nothing here can write into `facts/` — harvesting
is a suggestion, and the review is still the thing that makes a fact memory. The only
network access is `gh`, and it goes through an injectable runner so tests replay
recorded responses instead.
"""
from __future__ import annotations
import datetime as dt, json, re, subprocess
from dataclasses import dataclass
from pathlib import Path
from .space import Space
from .write import remember

MIN_LENGTH = 40          # shorter than this and the comment carries no rule
SUMMARY_LIMIT = 200
TITLE_LIMIT = 60
PR_LIMIT = 100
# One-word verdicts. They mean something in the thread and nothing outside it.
TRIVIAL = {"lgtm", "nit", "nits", "done", "fixed", "same", "ditto", "agreed", "ok", "okay",
           "thanks", "ship it", "wontfix", "good catch", "typo"}
_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]")
_SENTENCE = re.compile(r"^(.+?[.!?])(?:\s|$)", re.S)


@dataclass
class Candidate:
    title: str
    summary: str
    body: str
    sources: list[str]


def _gh(endpoint: str, runner) -> list | dict:
    # encoding is explicit: gh writes UTF-8, and the platform default (cp1252 on
    # Windows) kills the stdout reader thread on the first non-ASCII byte.
    r = runner(["gh", "api", endpoint], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"gh api {endpoint} failed: {r.stderr}")
    return json.loads(r.stdout or "[]")


def _norm(text: str) -> str:
    return _WS.sub(" ", text).strip().casefold()


def _clean(body: str) -> str:
    """Drop quoted lines: a reply that quotes the diff is not itself a claim."""
    return "\n".join(l for l in (body or "").splitlines() if not l.lstrip().startswith(">")).strip()


def _shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:.-") + "..."


def _is_bot(login: str) -> bool:
    return login.endswith("[bot]") or login.startswith("app/")


def merged_since(pulls: list[dict], since: str) -> list[dict]:
    return [p for p in pulls if (p.get("merged_at") or "")[:10] >= since]


def fetch_review_comments(repo: str, since: str, runner=None) -> list[dict]:
    """Review comments on every pull request of `repo` merged on or after `since`."""
    runner = runner or subprocess.run
    pulls = _gh(f"repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page={PR_LIMIT}", runner)
    out = []
    for pr in sorted(merged_since(pulls, since), key=lambda p: p["number"]):
        for c in _gh(f"repos/{repo}/pulls/{pr['number']}/comments?per_page={PR_LIMIT}", runner) or []:
            out.append({**c, "pull_request": pr})
    return out


def candidate(comment: dict) -> Candidate | None:
    """A comment worth proposing, or None when the heuristics say it is noise."""
    if _is_bot((comment.get("user") or {}).get("login", "")):
        return None
    body = _clean(comment.get("body", ""))
    flat = _WS.sub(" ", body).strip()
    if len(flat) < MIN_LENGTH or _PUNCT.sub("", _norm(flat)).strip() in TRIVIAL:
        return None
    m = _SENTENCE.match(flat)
    first = m.group(1) if m else flat
    summary = _shorten(first if len(first) >= MIN_LENGTH else flat, SUMMARY_LIMIT)
    pr = comment.get("pull_request") or {}
    sources = [s for s in (comment.get("html_url"), pr.get("html_url")) if s]
    return Candidate(title=_shorten(summary, TITLE_LIMIT), summary=summary, body=body, sources=sources)


def harvest(space: Space, repo: str, since: str, runner=None, scope: str | None = None,
            today: dt.date | None = None) -> list[Path]:
    """Write one proposed fact per novel review comment; return what was written."""
    dt.date.fromisoformat(since)   # fail on a bad date before shelling out
    scope = scope or space.id
    seen = {_norm(f.summary) for f in space.facts(include_proposed=True)}
    written: list[Path] = []
    for comment in fetch_review_comments(repo, since, runner=runner):
        cand = candidate(comment)
        if cand is None or _norm(cand.summary) in seen:
            continue
        seen.add(_norm(cand.summary))
        written.append(remember(space, scope, "fact", cand.title, cand.summary, cand.sources,
                                body=cand.body, author="seed", tags=["harvested"], today=today))
    return written
