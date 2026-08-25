"""The examples/ space is documentation that runs.

The README walks a reader through it and quotes its generated index, so both have to
stay true as the facts change.
"""
from pathlib import Path

from memspace.lint import has_errors, lint_space
from memspace.space import load_root

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def _space():
    return load_root(EXAMPLES).spaces["demo"]


def test_example_space_lints_clean():
    findings = lint_space(_space())
    assert not has_errors(findings), [f.message for f in findings if f.level == "error"]


def test_readme_quotes_the_current_index():
    """The README's 60-second example shows the real generated index. Keep it real."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    index = (EXAMPLES / "spaces/demo/todo-api/index.md").read_text(encoding="utf-8")
    missing = [line for line in index.splitlines() if line.strip() and line not in readme]
    assert not missing, f"README no longer matches the generated index: {missing}"
