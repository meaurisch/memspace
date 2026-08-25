# Why memspace looks like this

Every choice here was made against a working system: coding agents that open pull requests
against ~17 repos on a schedule, with one human reviewing them. That constraint — a human
has to be able to read and reject the memory — decided nearly everything below.

## Files in git, not a memory service

The alternatives were a hosted memory layer (mem0, Zep, Letta) and a knowledge graph. Both
put their cleverness on the **write** path, and the write path is exactly where the risk
sits: a cheap model deciding on its own what is worth remembering, with no gate. Neither can
be handed to an agent as a directory, which rules them out for the delivery mechanism that
already worked — mounting a repo read-only into the agent's workspace.

Plain files also survive their tooling. A space is useful with `cat` and `grep` and no
`memspace` installed at all; the CLI is a convenience over a format, not a runtime the
memory depends on.

The revisit conditions are concrete: a corpus past roughly two thousand facts, *and*
cross-repo multi-hop questions becoming common. Neither has happened.

## One fact per file, with a mandatory source

A long conventions document gets skimmed and rubber-stamped. A twelve-line file that claims
one thing, with a URL you can click, gets read — and rejected when it is wrong. The unit of
memory is the unit of review.

`sources:` is required and cannot be empty. A claim nobody can check against an issue, a
commit or a file path is not memory, it is a rumour, and rumours are what make an injected
context worse than no context at all.

## The index is generated, and capped

`index.md` is rendered from the facts, ordered by weight, and lint fails when it is stale or
over sixty lines. Two reasons.

The obvious one is drift: a hand-maintained summary of a growing corpus is wrong within a
month, and a wrong summary is worse than none.

The real one is that the index is what gets injected. Only a small budget of an agent's
context can go to memory before it crowds out the actual task, and the evidence on injected
context is not "more is better" — correct, concise memory helps; a large pool the agent has
to browse can land below baseline. The cap is a design constraint on the corpus, not a
formatting rule. When the index will not fit, that is the signal to consolidate facts, not
to raise the limit.

## No expiry, explicit supersession

Nothing is deleted on a timer. A decision from two years ago can still be the reason the
code looks the way it does. What changes is a fact's `status`: `superseded` when a newer
fact replaces it — with both sides of the link written symmetrically, so the trail survives
— or `disputed` when the record and reality disagree and nobody has settled it yet.

Lint *warns* on `episode` facts untouched for ninety days and on `disputed` facts left
hanging for a week. It never acts on those warnings. A human reading a lint report is the
consolidation mechanism.

## Memory beats the prompt, and says so out loud

Memory is the reviewed record. An instruction in an issue is one unreviewed input, often
written by another agent. When they conflict, the interactive case is easy — ask. The
autonomous case is where systems quietly go wrong, so the rule is deliberately blunt: an
agent that cannot carry out a request without contradicting an active fact produces **no
implementation and no pull request**, and reports the conflict by id and source instead. A
contradiction has to arrive as a blocked job. Buried in a diff, it is invisible.

That protocol lives in the space's own `AGENTS.md`, not in this tool. `memspace` has no
opinion about who is allowed to write what; it only makes `proposed/` the default landing
place, so the human stays in the loop by construction.

## What the tool refuses to do

No LLM calls and no network, anywhere. `seed-brief` shells out to `gh` and nothing else.
This is not minimalism for its own sake: the moment the tool can call a model, "what should
we remember" becomes the tool's decision instead of a reviewer's, and the review gate that
makes the whole thing safe stops being load-bearing.

Locality is declared per space rather than assumed. A space of personal notes can require
that storage, embeddings and any model all stay local, and the tool refuses a step that
would violate that instead of quietly falling back to whatever is available. Falling back is
how private data leaks.

The full-text index is stdlib SQLite FTS5 built in memory on every call. There is no index
file to go stale, corrupt, or need rebuilding — the tradeoff is that recall re-reads the
corpus each time, which at this scale costs milliseconds.

## Not built

MCP tool wrappers, a vector index, a graph, a web UI, autonomous write-back without review.
Each is straightforward to add on top of the format. None is worth the maintenance until
something concrete demands it, and the format is deliberately boring enough that adding one
later costs nothing today.

## Does injected memory actually help?

Unknown, and being measured rather than assumed. The system this was built for runs a
pre-registered ablation — no memory, index only, all facts, and index plus on-demand search
— against the same tasks, with the decision rule fixed in advance and a no-harm check on a
task memory should not affect. Wiring memory into live agents waits on that result.

If you are considering something like this, that is the part worth copying.
