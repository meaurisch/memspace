---
id: dec-0001-sqlite
type: decision
scope: alpha/proj-x
title: Use SQLite
summary: SQLite over Postgres because single-user
status: active
confidence: high
weight: 70
sources:
  - https://example.com/1
created: 2026-08-01
updated: 2026-08-01
supersedes: [dec-0002-old-orm]
superseded_by: null
author: morris
tags: []
---
One user means one writer, so SQLite is enough.
