from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
import yaml
from .facts import Fact, parse_fact


class SpaceError(Exception):
    pass


@dataclass
class Space:
    id: str
    root: Path
    remote: str = "local"
    policy: dict = field(default_factory=dict)

    def scope_dir(self, scope: str) -> Path:
        parts = scope.split("/")
        if parts[0] != self.id or len(parts) > 2:
            raise SpaceError(f"scope {scope!r} is not inside space {self.id!r}")
        return self.root if len(parts) == 1 else self.root / parts[1]

    def scopes(self) -> list[str]:
        out = [self.id]
        for d in sorted(p for p in self.root.iterdir() if p.is_dir()):
            if d.name in ("facts", "proposed"):
                continue
            if (d / "facts").is_dir() or (d / "about.md").is_file() or (d / "proposed").is_dir():
                out.append(f"{self.id}/{d.name}")
        return out

    def facts(self, include_proposed: bool = False) -> list[Fact]:
        found: list[Fact] = []
        for scope in self.scopes():
            d = self.scope_dir(scope)
            dirs = [d / "facts"] + ([d / "proposed"] if include_proposed else [])
            for fd in dirs:
                if fd.is_dir():
                    for p in sorted(fd.glob("*.md")):
                        found.append(parse_fact(p))
        return found

    def by_id(self, include_proposed: bool = False) -> dict[str, Fact]:
        return {f.id: f for f in self.facts(include_proposed)}


@dataclass
class Root:
    path: Path
    spaces: dict[str, Space]


def load_root(start: Path | None = None) -> Root:
    env = os.environ.get("MEMSPACE_ROOT")
    if env:
        base = Path(env)
        if not (base / "memory.yaml").is_file():
            raise SpaceError(f"MEMSPACE_ROOT={env} has no memory.yaml")
    else:
        cur = (start or Path.cwd()).resolve()
        base = None
        for cand in [cur, *cur.parents]:
            if (cand / "memory.yaml").is_file():
                base = cand
                break
        if base is None:
            raise SpaceError("no memory.yaml found walking up from " + str(cur))
    data = yaml.safe_load((base / "memory.yaml").read_text(encoding="utf-8")) or {}
    spaces = {}
    for sid, cfg in (data.get("spaces") or {}).items():
        spaces[sid] = Space(id=sid, root=base / cfg.get("root", f"spaces/{sid}"),
                            remote=cfg.get("remote", "local"), policy=cfg.get("policy") or {})
    if not spaces:
        raise SpaceError("memory.yaml declares no spaces")
    return Root(path=base, spaces=spaces)
