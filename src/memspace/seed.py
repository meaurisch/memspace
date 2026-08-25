from __future__ import annotations
import datetime as dt, json, subprocess


def _gh(args: list[str], runner):
    # encoding is explicit: gh writes UTF-8, and the platform default (cp1252 on
    # Windows) kills the stdout reader thread on the first non-ASCII byte.
    r = runner(["gh", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {r.stderr}")
    return json.loads(r.stdout or "[]")


def _comments(items):
    return "\n".join(f"- @{(c.get('author') or {}).get('login', '?')} ({c.get('createdAt', '')[:10]}): {c.get('body', '').strip()}"
                     for c in items or [])


def _is_dependabot(pr) -> bool:
    login = (pr.get("author") or {}).get("login", "")
    return login in ("app/dependabot", "dependabot[bot]") or pr.get("title", "").startswith("Bump ")


def seed_brief(repo: str, since: str | None = None, runner=subprocess.run) -> str:
    issues = _gh(["issue", "list", "--repo", repo, "--state", "all", "--limit", "200", "--json",
                  "number,title,body,state,labels,createdAt,closedAt,comments,url"], runner)
    prs = _gh(["pr", "list", "--repo", repo, "--state", "all", "--limit", "200", "--json",
               "number,title,body,state,mergedAt,createdAt,comments,reviews,url,author"], runner)
    if since:
        issues = [i for i in issues if i.get("createdAt", "")[:10] >= since]
        prs = [p for p in prs if p.get("createdAt", "")[:10] >= since]
    out = [f"# Seed brief: {repo}  (generated {dt.date.today().isoformat()})",
           "Instructions for the distilling agent: one fact per decision/preference/episode; every fact needs a source URL; "
           "cut anything derivable from reading the code.", "", "## Issues"]
    for i in sorted(issues, key=lambda x: x["number"]):
        out += [f"### #{i['number']} {i['title']} ({i['state'].lower()} {(i.get('closedAt') or i.get('createdAt') or '')[:10]}) — {i.get('url','')}",
                (i.get("body") or "(no body)").strip(), "**Comments:**", _comments(i.get("comments")) or "- (none)", ""]
    out.append("## Pull requests")
    bots = []
    for p in sorted(prs, key=lambda x: x["number"]):
        if _is_dependabot(p):
            bots.append(f"- PR #{p['number']} {p['title']} ({'merged' if p.get('mergedAt') else p['state'].lower()})")
            continue
        reviews = "\n".join(f"- review by @{(r.get('author') or {}).get('login','?')}: {r.get('state','')} {r.get('body','').strip()}"
                            for r in p.get("reviews") or [])
        out += [f"### PR #{p['number']} {p['title']} ({'merged ' + p['mergedAt'][:10] if p.get('mergedAt') else p['state'].lower()}) — {p.get('url','')}",
                (p.get("body") or "(no body)").strip(), "**Comments:**", _comments(p.get("comments")) or "- (none)",
                "**Reviews:**", reviews or "- (none)", ""]
    if bots:
        out += ["## Dependabot PRs", *bots, ""]
    return "\n".join(out)
