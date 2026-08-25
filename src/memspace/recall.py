from __future__ import annotations
import re, sqlite3
from .facts import Fact
from .space import Space


def _fts_query(q: str) -> str:
    words = re.findall(r"[A-Za-z0-9_-]+", q)
    return " OR ".join(f'"{w}"' for w in words) or '""'


def recall(space: Space, scope: str, query: str, k: int = 8,
           types: list[str] | None = None, include_superseded: bool = False) -> list[Fact]:
    cands = [f for f in space.facts() if f.scope in (scope, space.id)]
    if not include_superseded:
        cands = [f for f in cands if f.status != "superseded"]
    if types:
        cands = [f for f in cands if f.type in set(types)]
    if not cands:
        return []
    con = sqlite3.connect(":memory:")
    con.execute("CREATE VIRTUAL TABLE f USING fts5(id, title, summary, body, tags, tokenize='porter unicode61')")
    con.executemany("INSERT INTO f VALUES (?,?,?,?,?)",
                    [(f.id, f.title, f.summary, f.body, " ".join(f.tags)) for f in cands])
    rows = con.execute(
        "SELECT id FROM f WHERE f MATCH ? ORDER BY bm25(f, 5.0, 5.0, 3.0, 1.0, 1.0) LIMIT ?",
        (_fts_query(query), k)).fetchall()
    by_id = {f.id: f for f in cands}
    return [by_id[r[0]] for r in rows]
