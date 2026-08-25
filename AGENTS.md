# Agent guide — memspace

Conventions for ANY coding agent (vendor-neutral). Full standards live in the private
`meaurisch/studio` repo under `conventions/`; the rules that matter here are below, and
[docs/design.md](docs/design.md) explains why this tool is shaped the way it is.

- Never push to `master`: branch, push, open a PR, let Morris merge
  (conventions/pull-requests.md).
- Entry points: `python tasks.py test | run | check` — never invent others.
- Keep the README honest: its 60-second example is tested against the real output
  (`tests/test_examples.py`), so doc changes run through the suite like code changes.
- Never commit secrets; `.env` is generated, never edited or committed.
- Write PR descriptions and issue proposals in plain language:
  conventions/writing-style.md.

## memspace specifics

- Dependencies are **PyYAML only**. No network calls, no LLM calls anywhere in
  this package. `seed-brief` shells out to `gh` and nothing else.
- `sources:` is mandatory and non-empty on every fact.
- `index.md` files are generated — never hand-edit one. Run `memspace index`.
- Every behaviour change starts with a failing test under `tests/`.
