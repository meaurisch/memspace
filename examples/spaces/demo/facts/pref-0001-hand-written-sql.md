---
id: pref-0001-hand-written-sql
type: preference
scope: demo
title: Hand-written SQL, no ORM
summary: Queries are hand-written SQL; adding an ORM is a decision, not a refactor
status: active
confidence: high
weight: 80
sources:
- https://github.com/example/todo-api/issues/12
created: 2026-03-04
updated: 2026-03-04
supersedes: []
superseded_by: null
author: morris
tags:
- database
- conventions
---
The project ran on SQLAlchemy for two months in 2025 and the ORM was removed again: the
queries that mattered were all hand-tuned anyway, and the mapping layer made the slow ones
hard to read.

**Why it matters:** an agent that "modernises" a query into ORM calls is undoing a decision,
not cleaning up. Propose it as a change if you think it is right — do not slip it into an
unrelated pull request.
