---
id: proc-0001-changelog-entry
type: procedure
scope: beta
title: Every change updates the changelog
summary: A change to src/ is not finished until CHANGELOG.md has a line for it
status: active
confidence: high
weight: 80
sources:
  - https://example.com/handbook/changelog
  - CONTRIBUTING.md
created: 2026-08-01
updated: 2026-08-01
supersedes: []
superseded_by: null
author: morris
tags: [release]
triggers: [changelog, release]
paths:
  - "src/**"
action_hint: add one line under "Unreleased" in CHANGELOG.md before you finish
failure_if_ignored: the release notes miss the change and users find it by breaking
check: test -f CHANGELOG.md
enforce: stop
---
The changelog is written while the change is fresh, not reconstructed from git log later.
