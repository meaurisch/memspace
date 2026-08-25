# demo/todo-api — memory index
The task API. FastAPI over Postgres, deployed as a single container. `make test` runs the unit suite; the integration suite needs a live database and is not part of CI.

## Decisions
- [dec-0001-forward-only-migrations] Migrations have no down scripts; roll forward with a new migration instead — PR#204, migrations/README.md

## Procedures
- [proc-0001-integration-suite-is-manual] CI runs unit tests only; the integration suite needs a live database and is run before a release — .github/workflows/test.yml:22, #171
