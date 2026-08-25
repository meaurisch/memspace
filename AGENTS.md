# Agent guide — memspace

Conventions for ANY coding agent working in this repo, vendor-neutral.
[docs/design.md](docs/design.md) explains why the tool is shaped the way it is; read it
before changing behaviour.

- Never push to `master`: branch, push, open a pull request, let the maintainer merge.
- Entry points: `python tasks.py test | run | check` — never invent others.
- Keep the README honest: its 60-second example is tested against the real output
  (`tests/test_examples.py`), so doc changes run through the suite like code changes.
- Never commit secrets; `.env` is generated, never edited or committed.
- Write pull request text in plain language. Short sentences, one claim each, no
  marketing. Keep every number, filename and condition — plain is not the same as vague.

## memspace specifics

- Dependencies are **PyYAML only**. No network calls, no LLM calls anywhere in
  this package. `seed-brief` shells out to `gh` and nothing else.
- `sources:` is mandatory and non-empty on every fact.
- `index.md` files are generated — never hand-edit one. Run `memspace index`.
- Every behaviour change starts with a failing test under `tests/`.
