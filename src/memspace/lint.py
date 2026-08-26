from __future__ import annotations
import datetime as dt
from dataclasses import dataclass
from .facts import Fact, FactError, parse_fact
from .space import Space
from .index import stale_indexes, index_line_counts

EPISODE_TTL_DAYS = 90
DISPUTED_TTL_DAYS = 7
INDEX_MAX_LINES = 60
ACTIONABLE_TYPES = {"decision", "procedure"}
NOT_ACTIONABLE = "not actionable: name the agent action this fact changes, or retype it"


@dataclass
class Finding:
    level: str          # "error" | "warn"
    fact_id: str | None
    message: str


def has_errors(findings: list[Finding]) -> bool:
    return any(f.level == "error" for f in findings)


def _load_all(space: Space, out: list[Finding]) -> list[tuple[Fact, str, bool]]:
    """(fact, scope_of_directory, is_proposed) for every md file; parse errors become findings."""
    loaded = []
    for scope in space.scopes():
        d = space.scope_dir(scope)
        for sub, proposed in (("facts", False), ("proposed", True)):
            fd = d / sub
            if not fd.is_dir():
                continue
            for p in sorted(fd.glob("*.md")):
                try:
                    loaded.append((parse_fact(p), scope, proposed))
                except FactError as e:
                    out.append(Finding("error", p.stem, f"{p.stem}: {e}"))
    return loaded


def lint_space(space: Space, today: dt.date | None = None) -> list[Finding]:
    today = today or dt.date.today()
    out: list[Finding] = []
    loaded = _load_all(space, out)
    unparseable = bool(out)  # _load_all only appends parse errors
    strict = space.admission == "strict"
    seen: dict[str, Fact] = {}
    for fact, dir_scope, proposed in loaded:
        if fact.id in seen:
            out.append(Finding("error", fact.id, f"{fact.id}: duplicate id (also {seen[fact.id].path})"))
        seen[fact.id] = fact
        if fact.scope != dir_scope:
            out.append(Finding("error", fact.id, f"{fact.id}: scope {fact.scope!r} but file sits in scope {dir_scope!r}"))
        if proposed and fact.status != "proposed":
            out.append(Finding("warn", fact.id, f"{fact.id}: in proposed/ but status is {fact.status} (expected proposed)"))
        if fact.type == "episode" and (today - fact.updated).days > EPISODE_TTL_DAYS:
            out.append(Finding("warn", fact.id, f"{fact.id}: episode not updated for >{EPISODE_TTL_DAYS} days — still relevant?"))
        if strict and fact.type in ACTIONABLE_TYPES and fact.status == "active" \
                and not ((fact.triggers or fact.paths) and fact.action_hint):
            out.append(Finding("error", fact.id, f"{fact.id}: {NOT_ACTIONABLE}"))
        if fact.status == "disputed" and (today - fact.updated).days > DISPUTED_TTL_DAYS:
            out.append(Finding("warn", fact.id, f"{fact.id}: disputed for >{DISPUTED_TTL_DAYS} days — resolve it"))
    for fact in seen.values():
        for sid in fact.supersedes:
            if sid not in seen:
                out.append(Finding("error", fact.id, f"{fact.id}: supersedes unknown id {sid}"))
            elif seen[sid].superseded_by != fact.id:
                out.append(Finding("error", fact.id, f"{fact.id}: asymmetric supersession — {sid}.superseded_by is {seen[sid].superseded_by!r}"))
        if fact.superseded_by:
            if fact.superseded_by not in seen:
                out.append(Finding("error", fact.id, f"{fact.id}: superseded_by unknown id {fact.superseded_by}"))
            elif fact.id not in seen[fact.superseded_by].supersedes:
                out.append(Finding("error", fact.id, f"{fact.id}: asymmetric supersession — {fact.superseded_by}.supersedes lacks {fact.id}"))
    if unparseable:
        # Index rendering re-reads every fact; it cannot run over a space that
        # has a file we could not parse. Fix those errors first, then re-lint.
        return out
    for p in stale_indexes(space):
        out.append(Finding("error", None, f"{p}: index is stale — run `memspace index`"))
    for p, n in index_line_counts(space).items():
        if n > INDEX_MAX_LINES:
            out.append(Finding("error", None, f"{p}: index has {n} lines (max {INDEX_MAX_LINES})"))
    return out
