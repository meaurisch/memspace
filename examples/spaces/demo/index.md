# demo — memory index
A two-service side project: a Python task API and a small React client. Conventions that hold across both live here; anything specific to one service lives in its own subject.

## Subjects
- todo-api — The task API. FastAPI over Postgres, deployed as a single container. `make test` runs the unit suite; the integration suite needs a live database and is not part of CI.

## Preferences
- [pref-0001-hand-written-sql] Queries are hand-written SQL; adding an ORM is a decision, not a refactor — #12
