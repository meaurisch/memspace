# Example space

A tiny, complete memory space you can run the whole CLI against. It is checked in with its
generated `index.md` files, and `tests/test_examples.py` keeps it valid — if you change a
fact here and forget to re-run `memspace index`, the test suite says so.

```bash
cd examples

memspace index                                      # regenerate every index.md
memspace lint                                       # 0 errors, 0 warnings
memspace recall demo/todo-api "migration rollback"
memspace export-context demo/todo-api --budget-tokens 700
```

Three facts across two scopes:

```
memory.yaml                                    the space registry
spaces/demo/
  about.md                                     hand-written, stable
  index.md                                     GENERATED
  facts/pref-0001-hand-written-sql.md          holds across the whole project
  todo-api/
    about.md
    index.md                                   GENERATED
    facts/dec-0001-forward-only-migrations.md
    facts/proc-0001-integration-suite-is-manual.md
```

`remote: local` and an all-local policy in `memory.yaml` mean this space never leaves the
machine. A space that needs to be readable by CI would set `remote: github` instead.
