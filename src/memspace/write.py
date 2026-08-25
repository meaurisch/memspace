from __future__ import annotations
import datetime as dt, re
from pathlib import Path
from .facts import Fact, ID_PREFIXES, dump_fact, parse_fact
from .space import Space
from .index import write_indexes


def next_id(space: Space, scope: str, ftype: str) -> str:
    prefix = ID_PREFIXES[ftype]
    nums = [int(m.group(1)) for f in space.facts(include_proposed=True)
            if (m := re.match(rf"{prefix}-(\d+)", f.id))]
    return f"{prefix}-{(max(nums) + 1 if nums else 1):04d}"


def _slug(title: str) -> str:
    words = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-").split("-")
    return "-".join(w for w in words if w)[:60].strip("-") if words else "fact"


def remember(space: Space, scope: str, ftype: str, title: str, summary: str, sources: list[str],
             body: str = "", author: str = "claude-code", tags=(), direct: bool = False,
             today: dt.date | None = None) -> Path:
    today = today or dt.date.today()
    words = [w for w in _slug(title).split("-") if w][:4]
    fid = f"{next_id(space, scope, ftype)}-{'-'.join(words)}"
    target = space.scope_dir(scope) / ("facts" if direct else "proposed")
    target.mkdir(parents=True, exist_ok=True)
    fact = Fact(id=fid, type=ftype, scope=scope, title=title, summary=summary,
                status="active" if direct else "proposed", confidence="medium", weight=50,
                sources=list(sources), created=today, updated=today, supersedes=[], superseded_by=None,
                author=author, tags=list(tags), body=body.strip(), path=target / f"{fid}.md")
    fact.path.write_text(dump_fact(fact), encoding="utf-8", newline="\n")
    parse_fact(fact.path)  # validate what we wrote
    return fact.path


def _rewrite(fact: Fact) -> None:
    fact.path.write_text(dump_fact(fact), encoding="utf-8", newline="\n")


def supersede(space: Space, old_id: str, new_id: str, today: dt.date | None = None) -> None:
    today = today or dt.date.today()
    facts = space.by_id(include_proposed=True)
    old, new = facts[old_id], facts[new_id]
    old.status, old.superseded_by, old.updated = "superseded", new_id, today
    if old_id not in new.supersedes:
        new.supersedes.append(old_id)
    new.updated = today
    _rewrite(old); _rewrite(new)
    write_indexes(space)
