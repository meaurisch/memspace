---
id: dec-0001-forward-only-migrations
type: decision
scope: demo/todo-api
title: Migrations are forward-only
summary: Migrations have no down scripts; roll forward with a new migration instead
status: active
confidence: high
weight: 85
sources:
- https://github.com/example/todo-api/pull/204
- migrations/README.md
created: 2026-01-19
updated: 2026-06-02
supersedes: []
superseded_by: null
author: morris
tags:
- database
- deploy
---
Every file in `migrations/` applies in one direction. There is no `downgrade()`, and the
runner refuses to execute one.

**Why it matters:** a rollback in production restores the previous container, not the
previous schema, so a migration has to be safe to leave in place while the old code runs.
Add columns nullable, backfill in a second migration, drop in a third. An agent asked to
"revert the schema change" should write a new forward migration.
