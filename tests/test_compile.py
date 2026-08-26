from __future__ import annotations
import json, shutil, subprocess
from pathlib import Path

import pytest

from memspace.cli import main
from memspace.compile import CompileError, compile_space
from memspace.space import load_root

BASH = shutil.which("bash")
needs_bash = pytest.mark.skipif(not BASH, reason="bash is not on PATH")

GATE = """---
id: proc-0009-gate
type: procedure
scope: beta
title: A gate under test
summary: The condition this gate guards
status: active
confidence: high
weight: 90
sources:
  - https://example.com/handbook/gate
created: 2026-08-01
updated: 2026-08-01
supersedes: []
superseded_by: null
author: morris
tags: []
action_hint: do the thing
failure_if_ignored: the thing was left undone
check: {check}
enforce: stop
---
Body.
"""


def _space():
    return load_root().spaces["beta"]


def _gate_hook(space_b, tmp_path, check: str) -> Path:
    (space_b / "spaces/beta/facts/proc-0009-gate.md").write_text(
        GATE.format(check=check), encoding="utf-8")
    compile_space(_space(), tmp_path / "repo")
    return tmp_path / "repo/.claude/hooks/proc-0009-gate.sh"


def _run(hook: Path):
    return subprocess.run([BASH, str(hook)], capture_output=True, text=True, cwd=str(hook.parent))


def test_enforced_fact_gets_a_stop_hook(space_b, tmp_path):
    out = tmp_path / "repo"
    compile_space(_space(), out)
    settings = json.loads((out / ".claude/settings.json").read_text(encoding="utf-8"))
    commands = [h["command"] for entry in settings["hooks"]["Stop"] for h in entry["hooks"]]
    assert commands == ["bash .claude/hooks/proc-0001-changelog-entry.sh"]
    assert all(h["type"] == "command" for entry in settings["hooks"]["Stop"] for h in entry["hooks"])
    hook = (out / ".claude/hooks/proc-0001-changelog-entry.sh").read_text(encoding="utf-8")
    assert "test -f CHANGELOG.md" in hook
    assert "proc-0001-changelog-entry" in hook
    assert "the release notes miss the change" in hook
    assert "exit 2" in hook


def test_fact_with_paths_gets_a_rule(space_b, tmp_path):
    out = tmp_path / "repo"
    compile_space(_space(), out)
    rule = (out / ".claude/rules/pref-0001-no-print-logging.md").read_text(encoding="utf-8")
    assert rule.startswith("---\n")
    head, body = rule.split("---\n", 2)[1:]
    assert "src/**/*.py" in head and "lib/**/*.py" in head
    assert "Library code logs with the logging module" in body
    assert "logging.getLogger(__name__)" in body


def test_facts_without_actionable_fields_compile_to_nothing(space_b, tmp_path):
    out = tmp_path / "repo"
    written = {p.name for p in compile_space(_space(), out)}
    assert "dec-0001-plain-files.md" not in written           # no paths -> no rule
    assert "proc-0002-retired-gate.md" not in written         # superseded -> ignored
    assert "proc-0002-retired-gate.sh" not in written
    assert not (out / ".claude/rules/dec-0001-plain-files.md").exists()
    assert not (out / ".claude/hooks/proc-0002-retired-gate.sh").exists()
    assert not (out / ".claude/hooks/pref-0001-no-print-logging.sh").exists()   # check without enforce


def test_output_is_deterministic_and_idempotent(space_b, tmp_path):
    out = tmp_path / "repo"
    first = compile_space(_space(), out)
    before = {p: p.read_bytes() for p in first}
    second = compile_space(_space(), out)
    assert second == first
    assert {p: p.read_bytes() for p in second} == before
    assert first == sorted(first)


def test_compile_keeps_unrelated_settings(space_b, tmp_path):
    out = tmp_path / "repo"
    (out / ".claude").mkdir(parents=True)
    (out / ".claude/settings.json").write_text(
        json.dumps({"model": "sonnet", "hooks": {"PreToolUse": [{"matcher": "Bash"}]}}), encoding="utf-8")
    compile_space(_space(), out)
    settings = json.loads((out / ".claude/settings.json").read_text(encoding="utf-8"))
    assert settings["model"] == "sonnet"
    assert settings["hooks"]["PreToolUse"] == [{"matcher": "Bash"}]
    assert settings["hooks"]["Stop"]


def test_unknown_target_is_refused(space_b, tmp_path):
    with pytest.raises(CompileError, match="target"):
        compile_space(_space(), tmp_path / "repo", target="cursor")


@needs_bash
def test_hook_allows_the_stop_when_the_check_passes(space_b, tmp_path):
    r = _run(_gate_hook(space_b, tmp_path, "true"))
    assert r.returncode == 0 and r.stderr == ""


@needs_bash
def test_hook_blocks_the_stop_when_the_check_fails(space_b, tmp_path):
    r = _run(_gate_hook(space_b, tmp_path, "false"))
    assert r.returncode == 2
    assert "the thing was left undone" in r.stderr
    assert "proc-0009-gate" in r.stderr
    assert "The condition this gate guards" in r.stderr


@needs_bash
def test_hook_never_blocks_when_the_check_itself_is_broken(space_b, tmp_path):
    for check in ("memspace-no-such-command-9x", "/etc", '"$(exit 127)"', '"if then fi"'):
        r = _run(_gate_hook(space_b, tmp_path, check))
        assert r.returncode == 0, f"{check!r} bricked the session: {r.stderr}"


def test_cli_compile(space_b, tmp_path, capsys):
    out = tmp_path / "repo"
    assert main(["compile", "beta", "--target", "claude", "--out", str(out)]) == 0
    printed = capsys.readouterr().out.splitlines()
    assert any(line.endswith("settings.json") for line in printed)
    assert (out / ".claude/hooks/proc-0001-changelog-entry.sh").is_file()
    assert (out / ".claude/rules/proc-0001-changelog-entry.md").is_file()


def test_cli_rejects_unknown_target(space_b, tmp_path):
    with pytest.raises(SystemExit):
        main(["compile", "beta", "--target", "cursor", "--out", str(tmp_path)])
