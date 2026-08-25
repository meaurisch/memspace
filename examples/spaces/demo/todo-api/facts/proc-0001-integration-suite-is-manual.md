---
id: proc-0001-integration-suite-is-manual
type: procedure
scope: demo/todo-api
title: The integration suite runs by hand
summary: CI runs unit tests only; the integration suite needs a live database and is run before a release
status: active
confidence: medium
weight: 45
sources:
- .github/workflows/test.yml:22
- https://github.com/example/todo-api/issues/171
created: 2026-02-11
updated: 2026-02-11
supersedes: []
superseded_by: null
author: seed
tags:
- testing
- ci
---
`make test` and CI both run `tests/unit`. `tests/integration` talks to a real Postgres and
is run by hand before a release.

**Why it matters:** green CI does not mean the integration suite passed. If a change touches
queries or migrations, say so in the pull request so someone runs the integration suite
before the release, and do not read a green check as coverage you did not get.
