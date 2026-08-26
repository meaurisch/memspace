---
id: pref-0001-no-print-logging
type: preference
scope: beta
title: Log through the logger
summary: Library code logs with the logging module, never with print()
status: active
confidence: high
weight: 60
sources:
  - https://example.com/handbook/logging
created: 2026-08-01
updated: 2026-08-01
supersedes: []
superseded_by: null
author: morris
tags: [style]
paths:
  - "src/**/*.py"
  - "lib/**/*.py"
action_hint: use logging.getLogger(__name__) instead of print()
check: "! grep -rn '^ *print(' src"
---
Callers choose where output goes. print() takes that choice away.
