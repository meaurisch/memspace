# memspace

[![test](https://github.com/meaurisch/memspace/actions/workflows/test.yml/badge.svg)](https://github.com/meaurisch/memspace/actions/workflows/test.yml)

## What & why

**Memory for coding agents, kept as markdown files you review in a pull request.**

An agent starts every session knowing nothing about why your code looks the way it does.
`memspace` gives it a *space*: a directory of one-fact-per-file markdown with YAML
frontmatter, and a generated `index.md` per scope that is short enough to drop into a
context window. No database, no vector store, no hosted service — the memory is plain
files you can read, grep, diff and reject.

The tool is deliberately dumb. It validates, indexes, searches and writes facts. It never
calls an LLM and it never touches the network. What makes the memory trustworthy is not the
tool, it is that a human read every fact before it landed.

## Quickstart — 60 seconds

```bash
pip install git+https://github.com/meaurisch/memspace
git clone https://github.com/meaurisch/memspace && cd memspace/examples
```

`examples/` is a small, complete space. Ask it what it knows about the `todo-api` service:

```bash
memspace export-context demo/todo-api --budget-tokens 700
```

What comes back leads with the generated indexes — the space's, then the subject's. The
index is the whole point: it is what an agent reads before it touches the repo. Here is
`todo-api`'s:

```markdown
# demo/todo-api — memory index
The task API. FastAPI over Postgres, deployed as a single container. `make test` runs the unit suite; the integration suite needs a live database and is not part of CI.

## Decisions
- [dec-0001-forward-only-migrations] Migrations have no down scripts; roll forward with a new migration instead — PR#204, migrations/README.md

## Procedures
- [proc-0001-integration-suite-is-manual] CI runs unit tests only; the integration suite needs a live database and is run before a release — .github/workflows/test.yml:22, #171
```

Then the fact bodies, highest `weight` first, until the token budget runs out. Every line
carries an id you can open and a source you can check.

Search instead of dumping everything:

```bash
memspace recall demo/todo-api "migration rollback"
# dec-0001-forward-only-migrations · decision · active · Migrations are forward-only · …
```

Add something learned the hard way:

```bash
memspace remember --scope demo/todo-api --type episode \
  --title "Redis eviction wiped the session store" \
  --summary "maxmemory-policy was allkeys-lru; sessions must live in Postgres" \
  --source https://github.com/example/todo-api/issues/233
```

That writes into `proposed/`, not `facts/`. It becomes memory when a human merges it.

## Why one fact per file

Because the review is the feature. A 400-line `CONVENTIONS.md` gets a rubber stamp; a
12-line file claiming one thing, with a URL you can click, gets read. Small files also make
supersession honest — a decision that changes leaves a trail instead of a diff.

The editorial rule that keeps a space worth reading: **cut anything derivable from reading
the code.** Keep pitfalls, rationale, and conventions that differ from the defaults. And
when a fact describes something that should simply be fixed, fix it and delete the fact.

## Commands

Run from anywhere inside a space. The root is found by walking up for `memory.yaml`, or
taken from `$MEMSPACE_ROOT`.

| Command | What it does |
|---|---|
| `memspace lint [space] [--today DATE]` | Validates schema, sources, supersession links, scope↔directory, index freshness. Exit 1 on errors, 0 with warnings. |
| `memspace index [space] [--check]` | Regenerates every `index.md`. `--check` exits 1 when one is stale — use it in CI. |
| `memspace export-context <scope> [--budget-tokens N]` | Space index + subject index + highest-weight fact bodies until the budget (default 3000 tokens ≈ 4 chars/token). |
| `memspace recall <scope> "<query>" [-k N] [--type T] [--include-superseded]` | FTS5/bm25 search over id, title, summary, body and tags. The index is built in memory per call — nothing persists, nothing rots. |
| `memspace remember --scope S --type T --title X --summary Y --source URL… [--body-file F] [--direct]` | Writes a schema-valid fact to `proposed/`, or straight to `facts/` with `--direct`. |
| `memspace supersede <old-id> --with <new-id>` | Flips both sides of the link symmetrically and re-indexes. |
| `memspace seed-brief <owner/repo> [--since DATE] [-o FILE]` | Turns a repo's issues and pull requests into one markdown brief for an agent to distil into facts. Shells out to `gh`; no LLM. |
| `memspace compile <space> --target claude --out DIR` | Turns actionable facts into Claude Code hooks and rules under `DIR/.claude/`. Deterministic and idempotent. |
| `memspace harvest <space> --repo <owner/name> --since DATE` | Reads review comments on pull requests merged since DATE and writes candidate facts to `proposed/`. Shells out to `gh`; no LLM. |

## A space

```
memory.yaml                     which spaces exist, where they live, what may leave the machine
spaces/<space>/
  about.md                      hand-written, stable: what this is
  index.md                      GENERATED — never hand-edit
  facts/                        reviewed facts
  proposed/                     agent-written, lands via pull request
  <subject>/                    one per project or service, same shape
```

`memory.yaml` declares each space's remote and its locality policy:

```yaml
spaces:
  demo:
    root: spaces/demo
    remote: local            # local | github
    policy: {storage: local, embeddings: local, llm: local}
```

Locality is a property of the space, not of the tool. A space holding personal notes can say
`local` everywhere and never reach a provider; a space that CI has to read sets
`remote: github`. The tool refuses any step stricter than the policy allows rather than
quietly falling back.

## A fact

```yaml
---
id: dec-0001-forward-only-migrations   # == filename stem; prefix dec|pref|fact|proc|epi|glos
type: decision                         # decision | preference | fact | procedure | episode | glossary
scope: demo/todo-api                   # <space> or <space>/<subject>; must match the directory
title: Migrations are forward-only
summary: Migrations have no down scripts; roll forward with a new migration instead
status: active                         # active | superseded | disputed | proposed
confidence: high                       # high | medium | low
weight: 85                             # 0-100, index ordering
sources:                               # MANDATORY, at least one
  - https://github.com/example/todo-api/pull/204     # URL, git:<sha>, or path[:line]
  - migrations/README.md
created: 2026-01-19
updated: 2026-06-02
supersedes: []
superseded_by: null                    # required iff status == superseded
author: morris                         # morris | claude-code | worker | interviewer | seed
tags: [database, deploy]
---
The body. Why the rule exists and what breaks when you ignore it.
```

`lint` enforces every line of that: ids match filenames, prefixes match types, scopes match
directories, `sources` is non-empty and well formed, supersession is symmetric on both
sides, no index is stale or over 60 lines. It warns — never deletes — on `episode` facts
untouched for 90 days and `disputed` facts left unresolved for a week. There is no
time-based expiry: a human reads the lint report and decides.

## Facts that do something — `compile`

A fact an agent reads is a suggestion. Some conventions want teeth, so a fact may say what
to do, where it applies, and how to tell whether it was followed. All six fields are
optional:

```yaml
triggers: [changelog, release]         # keywords that should bring this fact to mind
paths: ["src/**"]                      # globs this fact governs
action_hint: add one line under "Unreleased" in CHANGELOG.md before you finish
failure_if_ignored: the release notes miss the change and users find it by breaking
check: "! git diff --quiet -- CHANGELOG.md"    # nonzero exit == convention violated
enforce: stop                          # block the agent from ending its turn
```

`memspace compile` turns those fields — and only those fields, never a fact body — into
files the agent already obeys:

```bash
memspace compile demo --target claude --out .
```

```
.claude/settings.json                       Stop-hook entries, merged into what is already there
.claude/hooks/proc-0001-changelog-entry.sh  one script per fact with enforce: stop and a check
.claude/rules/proc-0001-changelog-entry.md  one rule per fact with paths:, globs in frontmatter
```

A hook runs its `check` when the agent tries to end its turn. Check passes, the turn ends.
Check fails, the hook exits 2 and hands `failure_if_ignored`, the fact id and its summary
back to the agent as the reason it may not stop yet.

**A broken fact must never brick a session.** The generated script only blocks when the
check actually ran and said no. A check that does not parse, names a command that is not
installed, or points at something it cannot execute exits 0 and lets the turn end. Only
`active` facts compile — superseded and disputed ones are ignored however loud their
frontmatter is.

Output is deterministic and idempotent: facts compile in id order, JSON keys are sorted,
and recompiling an unchanged space rewrites byte-identical files, so the result is
reviewable in a diff or regenerable in CI. `settings.json` is merged, not replaced — your
other settings and other hook events survive.

## Mining review comments — `harvest`

Code review is where conventions get said out loud, and then scroll away. `harvest` reads
the review comments on pull requests merged since a date and writes each one it thinks
carries a rule into `proposed/`:

```bash
memspace harvest demo --repo example-org/example-repo --since 2026-02-01
# spaces/demo/proposed/fact-0007-key-the-cache-by-url.md
```

Each candidate keeps the comment text as its body, its first sentence as the summary, and
both the comment permalink and the pull request URL as `sources` — so a reviewer can open
the thread the claim came from. The filters are deliberately blunt: bot accounts, quoted
lines, comments under 40 characters and one-word verdicts (`LGTM`, `nit`, `done`) are
dropped, and a candidate whose summary already matches a fact in `facts/` or `proposed/`
is skipped, so re-running on a wider date range adds only what is new.

**`harvest` cannot write to `facts/`.** There is no `--direct` here. Candidates arrive
unedited, unranked and often wrong; they become memory when a human rewrites one into a
fact and merges it. Treat the output as a reading list, not as a draft space.

## Working on it

```bash
pip install -e .[dev] && python tasks.py check
```

Python 3.11+. The only runtime dependency is PyYAML — the full-text index is stdlib
`sqlite3` FTS5, built in memory per call. Every behaviour change starts with a failing test
under `tests/`, and that includes documentation: the README's example is asserted against
the tool's real output.

## Current state

v0.1 — the nine commands above, 89 tests, CI on Python 3.11, 3.12 and 3.13. In real use by
one private system; not on PyPI, and the API is not frozen. The premise the whole thing rests
on — that injecting this into an agent's context measurably helps — is still being measured.
Treat it as a well-tested tool built on an untested idea.

## Next up

- The ablation result: whether injected memory helps, how much is enough, and which variant
  gets wired into live agents. Until it lands, nothing reads a space automatically.
- MCP tool wrappers, so an agent can call `recall` instead of reading files.
- PyPI, if anyone other than its author wants it.

## Where this came from

Built for a working system rather than as a demo. `memspace` holds the coding memory for a
private setup where agents open pull requests against ~17 repos on a schedule and one person
reviews them — which is why the review gate, not the tool, is the load-bearing part.

[docs/design.md](docs/design.md) has the reasoning: why files in git rather than a memory
service, why the index is generated and capped, why `sources` is mandatory, why nothing
expires on a timer, and why the tool refuses to call a model. It also describes the
pre-registered experiment measuring whether injected memory helps at all — that result is
still pending, and until it lands, treat the premise as untested.

Not built: MCP tool wrappers, a vector index, a graph, autonomous write-back. The conditions
under which each becomes worth building are in that document, and none are met yet.

## License

MIT — see [LICENSE](LICENSE).
