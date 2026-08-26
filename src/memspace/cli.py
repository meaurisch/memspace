from __future__ import annotations
import argparse, datetime as dt, sys
from pathlib import Path
from .space import load_root, SpaceError
from .lint import lint_space, has_errors
from .index import write_indexes, stale_indexes
from .export import export_context
from .recall import recall
from .write import remember, supersede
from .seed import seed_brief
from .compile import TARGETS, compile_space


def _space(root, name):
    if name:
        if name not in root.spaces:
            raise SpaceError(f"unknown space {name!r}; have {list(root.spaces)}")
        return root.spaces[name]
    return next(iter(root.spaces.values()))


def _space_of_scope(root, scope):
    return _space(root, scope.split("/")[0])


def build_parser():
    p = argparse.ArgumentParser(prog="memspace")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("lint"); s.add_argument("space", nargs="?"); s.add_argument("--today")
    s = sub.add_parser("index"); s.add_argument("space", nargs="?"); s.add_argument("--check", action="store_true")
    s = sub.add_parser("export-context"); s.add_argument("scope"); s.add_argument("--budget-tokens", type=int, default=3000)
    s = sub.add_parser("recall"); s.add_argument("scope"); s.add_argument("query"); s.add_argument("-k", type=int, default=8)
    s.add_argument("--type", action="append", dest="types"); s.add_argument("--include-superseded", action="store_true")
    s.add_argument("--validate", action="store_true",
                    help="drop hits whose path/path:line sources no longer resolve; URL sources are never checked")
    s = sub.add_parser("remember")
    for a in ("--scope", "--type", "--title", "--summary"):
        s.add_argument(a, required=True)
    s.add_argument("--source", action="append", required=True, dest="sources")
    s.add_argument("--body-file"); s.add_argument("--author", default="claude-code")
    s.add_argument("--tag", action="append", default=[], dest="tags"); s.add_argument("--direct", action="store_true")
    s = sub.add_parser("supersede"); s.add_argument("old_id"); s.add_argument("--with", dest="new_id", required=True)
    s = sub.add_parser("seed-brief"); s.add_argument("repo"); s.add_argument("--since"); s.add_argument("-o", dest="out")
    s = sub.add_parser("compile"); s.add_argument("space", nargs="?")
    s.add_argument("--target", choices=sorted(TARGETS), default="claude"); s.add_argument("--out", default=".")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "seed-brief":
        text = seed_brief(args.repo, since=args.since)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8", newline="\n"); print(args.out)
        else:
            print(text)
        return 0
    try:
        root = load_root()
    except SpaceError as e:
        print(f"error: {e}", file=sys.stderr); return 2
    try:
        if args.cmd == "lint":
            today = dt.date.fromisoformat(args.today) if args.today else None
            findings = lint_space(_space(root, args.space), today=today, repo_root=root.path)
            for f in findings:
                print(f"{f.level}: {f.message}")
            print(f"{sum(f.level=='error' for f in findings)} error(s), {sum(f.level=='warn' for f in findings)} warning(s)")
            return 1 if has_errors(findings) else 0
        if args.cmd == "index":
            sp = _space(root, args.space)
            if args.check:
                stale = stale_indexes(sp)
                for p in stale:
                    print(f"stale: {p}")
                return 1 if stale else 0
            for p in write_indexes(sp):
                print(p)
            return 0
        if args.cmd == "export-context":
            print(export_context(_space_of_scope(root, args.scope), args.scope, args.budget_tokens), end=""); return 0
        if args.cmd == "recall":
            for f in recall(_space_of_scope(root, args.scope), args.scope, args.query, k=args.k,
                            types=args.types, include_superseded=args.include_superseded,
                            validate=args.validate, repo_root=root.path):
                print(f"{f.id} · {f.type} · {f.status} · {f.title} — {f.summary} · {f.path}")
            return 0
        if args.cmd == "remember":
            body = Path(args.body_file).read_text(encoding="utf-8") if args.body_file else ""
            p = remember(_space_of_scope(root, args.scope), args.scope, args.type, args.title, args.summary,
                         args.sources, body=body, author=args.author, tags=args.tags, direct=args.direct)
            print(p.as_posix()); return 0
        if args.cmd == "compile":
            for p in compile_space(_space(root, args.space), Path(args.out), target=args.target):
                print(p.as_posix())
            return 0
        if args.cmd == "supersede":
            supersede(_space(root, None), args.old_id, args.new_id)   # ids are space-wide unique; default space
            return 0
    except (SpaceError, ValueError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr); return 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
