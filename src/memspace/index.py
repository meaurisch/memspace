from __future__ import annotations
import re
from pathlib import Path
from .facts import Fact
from .space import Space

SECTIONS = [("decision", "Decisions"), ("preference", "Preferences"), ("procedure", "Procedures"),
            ("fact", "Facts"), ("glossary", "Glossary"), ("episode", "Episodes")]


def _short_source(s: str) -> str:
    m = re.search(r"/issues/(\d+)$", s)
    if m:
        return f"#{m.group(1)}"
    m = re.search(r"/pull/(\d+)$", s)
    if m:
        return f"PR#{m.group(1)}"
    if s.startswith("git:"):
        return "git:" + s[4:11]
    return re.sub(r"^https?://", "", s)


def _about_first_paragraph(d: Path) -> str:
    p = d / "about.md"
    if not p.is_file():
        return ""
    text = p.read_text(encoding="utf-8").strip()
    return text.split("\n\n", 1)[0].replace("\n", " ").strip()


def render_index(space: Space, scope: str) -> str:
    d = space.scope_dir(scope)
    facts = [f for f in space.facts() if f.scope == scope and f.status in ("active", "disputed")]
    lines = [f"# {scope} — memory index"]
    about = _about_first_paragraph(d)
    if about:
        lines.append(about)
    if scope == space.id:
        subjects = [s for s in space.scopes() if s != space.id]
        if subjects:
            lines += ["", "## Subjects"]
            for s in subjects:
                lines.append(f"- {s.split('/')[1]} — {_about_first_paragraph(space.scope_dir(s))}".rstrip(" —"))
    for ftype, title in SECTIONS:
        group = sorted((f for f in facts if f.type == ftype), key=lambda f: (-f.weight, f.id))
        if not group:
            continue
        lines += ["", f"## {title}"]
        for f in group:
            flag = " (DISPUTED)" if f.status == "disputed" else ""
            srcs = ", ".join(_short_source(s) for s in f.sources[:2])
            lines.append(f"- [{f.id}] {f.summary}{flag} — {srcs}")
    return "\n".join(lines) + "\n"


def _index_paths(space: Space) -> dict[Path, str]:
    return {space.scope_dir(s) / "index.md": s for s in space.scopes()}


def write_indexes(space: Space) -> list[Path]:
    out = []
    for p, scope in _index_paths(space).items():
        p.write_text(render_index(space, scope), encoding="utf-8", newline="\n")
        out.append(p)
    return out


def stale_indexes(space: Space) -> list[Path]:
    stale = []
    for p, scope in _index_paths(space).items():
        current = p.read_text(encoding="utf-8").replace("\r\n", "\n") if p.is_file() else None
        if current != render_index(space, scope):
            stale.append(p)
    return stale


def index_line_counts(space: Space) -> dict[Path, int]:
    return {p: len(p.read_text(encoding="utf-8").splitlines()) for p in _index_paths(space) if p.is_file()}
