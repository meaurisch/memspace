from __future__ import annotations
import datetime as dt, re
from dataclasses import dataclass, field
from pathlib import Path
import yaml

VALID_TYPES = {"decision", "preference", "fact", "procedure", "episode", "glossary"}
ID_PREFIXES = {"decision": "dec", "preference": "pref", "fact": "fact",
               "procedure": "proc", "episode": "epi", "glossary": "glos"}
VALID_STATUS = {"active", "superseded", "disputed", "proposed"}
VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_AUTHORS = {"morris", "claude-code", "worker", "interviewer", "seed"}
_SOURCE_RE = re.compile(r"^(https?://\S+|git:[0-9a-f]{7,40}|[\w./-]+\.\w+(:\d+)?)$")
_FM_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", re.S)
_ORDER = ["id", "type", "scope", "title", "summary", "status", "confidence", "weight",
          "sources", "created", "updated", "supersedes", "superseded_by", "author", "tags"]


class FactError(ValueError):
    pass


@dataclass
class Fact:
    id: str
    type: str
    scope: str
    title: str
    summary: str
    status: str
    confidence: str
    weight: int
    sources: list[str]
    created: dt.date
    updated: dt.date
    supersedes: list[str]
    superseded_by: str | None
    author: str
    tags: list[str]
    body: str
    path: Path = field(compare=False, default=Path())

    @property
    def prefix(self) -> str:
        return self.id.split("-", 1)[0]


def _date(v, name):
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v))
    except ValueError as e:
        raise FactError(f"{name}: not an ISO date: {v!r}") from e


def parse_fact(path: Path) -> Fact:
    text = path.read_text(encoding="utf-8")
    m = _FM_RE.match(text)
    if not m:
        raise FactError(f"{path}: missing frontmatter")
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise FactError(f"{path}: bad YAML: {e}") from e
    missing = [k for k in _ORDER if k not in meta and k not in ("supersedes", "superseded_by", "tags")]
    if missing:
        raise FactError(f"{path}: missing fields {missing}")
    fid = str(meta["id"])
    if fid != path.stem:
        raise FactError(f"{path}: id {fid!r} does not match filename stem {path.stem!r}")
    ftype = meta["type"]
    if ftype not in VALID_TYPES:
        raise FactError(f"{path}: type {ftype!r} not in {sorted(VALID_TYPES)}")
    if not fid.startswith(ID_PREFIXES[ftype] + "-"):
        raise FactError(f"{path}: id prefix must be {ID_PREFIXES[ftype]!r} for type {ftype}")
    if meta["status"] not in VALID_STATUS:
        raise FactError(f"{path}: status {meta['status']!r} invalid")
    if meta["confidence"] not in VALID_CONFIDENCE:
        raise FactError(f"{path}: confidence {meta['confidence']!r} invalid")
    if meta["author"] not in VALID_AUTHORS:
        raise FactError(f"{path}: author {meta['author']!r} invalid")
    weight = int(meta["weight"])
    if not 0 <= weight <= 100:
        raise FactError(f"{path}: weight must be 0-100")
    sources = meta.get("sources") or []
    if not isinstance(sources, list) or not sources:
        raise FactError(f"{path}: sources must be a non-empty list")
    for s in sources:
        if not _SOURCE_RE.match(str(s)):
            raise FactError(f"{path}: bad source {s!r} (need URL, git:<sha>, or path[:line])")
    status = meta["status"]
    sb = meta.get("superseded_by")
    if status == "superseded" and not sb:
        raise FactError(f"{path}: status superseded requires superseded_by")
    if status != "superseded" and sb:
        raise FactError(f"{path}: superseded_by set but status is {status}")
    if not re.fullmatch(r"[a-z0-9-]+(/[a-z0-9-]+)?", str(meta["scope"])):
        raise FactError(f"{path}: scope must be <space> or <space>/<subject>")
    return Fact(
        id=fid, type=ftype, scope=str(meta["scope"]), title=str(meta["title"]).strip(),
        summary=str(meta["summary"]).strip(), status=status, confidence=meta["confidence"],
        weight=weight, sources=[str(s) for s in sources],
        created=_date(meta["created"], "created"), updated=_date(meta["updated"], "updated"),
        supersedes=[str(x) for x in (meta.get("supersedes") or [])], superseded_by=sb,
        author=meta["author"], tags=[str(t) for t in (meta.get("tags") or [])],
        body=m.group(2).strip(), path=path,
    )


def dump_fact(fact: Fact) -> str:
    meta = {k: getattr(fact, k) for k in _ORDER}
    meta["created"] = fact.created.isoformat()
    meta["updated"] = fact.updated.isoformat()
    fm = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, default_flow_style=None).strip()
    return f"---\n{fm}\n---\n{fact.body}\n"
