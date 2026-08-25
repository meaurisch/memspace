from __future__ import annotations
from .space import Space
from .index import render_index


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def export_context(space: Space, scope: str, budget_tokens: int = 3000) -> str:
    parts = [render_index(space, space.id)]
    if scope != space.id:
        parts.append(render_index(space, scope))
    text = "\n".join(parts) + "\n## Details\n"
    ordered = []
    for sc in ([scope] if scope != space.id else []) + [space.id]:
        ordered += sorted((f for f in space.facts() if f.scope == sc and f.status in ("active", "disputed")),
                          key=lambda f: (-f.weight, f.id))
    for f in ordered:
        block = f"\n### [{f.id}] {f.title}\n{f.body}\n"
        if estimate_tokens(text + block) > budget_tokens:
            break
        text += block
    return text
