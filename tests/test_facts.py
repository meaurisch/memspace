from pathlib import Path
import pytest
from memspace.facts import Fact, FactError, parse_fact, dump_fact

GOOD = """---
id: dec-0001-sqlite
type: decision
scope: alpha/proj-x
title: Use SQLite
summary: SQLite over Postgres because single-user
status: active
confidence: high
weight: 70
sources:
  - https://github.com/x/y/issues/1
created: 2026-08-01
updated: 2026-08-02
supersedes: []
superseded_by: null
author: morris
tags: [db]
---
Body text.
"""


def write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_parse_good(tmp_path):
    f = parse_fact(write(tmp_path, "dec-0001-sqlite.md", GOOD))
    assert f.id == "dec-0001-sqlite"
    assert f.type == "decision"
    assert f.scope == "alpha/proj-x"
    assert f.sources == ["https://github.com/x/y/issues/1"]
    assert f.weight == 70
    assert f.body == "Body text."
    assert f.path.name == "dec-0001-sqlite.md"


def test_id_must_match_filename(tmp_path):
    with pytest.raises(FactError, match="filename"):
        parse_fact(write(tmp_path, "dec-0009-other.md", GOOD))


def test_missing_sources_is_error(tmp_path):
    bad = GOOD.replace("sources:\n  - https://github.com/x/y/issues/1\n", "sources: []\n")
    with pytest.raises(FactError, match="sources"):
        parse_fact(write(tmp_path, "dec-0001-sqlite.md", bad))


def test_bad_source_format(tmp_path):
    bad = GOOD.replace("https://github.com/x/y/issues/1", "just a note")
    with pytest.raises(FactError, match="source"):
        parse_fact(write(tmp_path, "dec-0001-sqlite.md", bad))


def test_prefix_must_match_type(tmp_path):
    bad = GOOD.replace("type: decision", "type: preference")
    with pytest.raises(FactError, match="prefix"):
        parse_fact(write(tmp_path, "dec-0001-sqlite.md", bad))


def test_superseded_requires_superseded_by(tmp_path):
    bad = GOOD.replace("status: active", "status: superseded")
    with pytest.raises(FactError, match="superseded_by"):
        parse_fact(write(tmp_path, "dec-0001-sqlite.md", bad))


def test_roundtrip(tmp_path):
    f = parse_fact(write(tmp_path, "dec-0001-sqlite.md", GOOD))
    again = parse_fact(write(tmp_path, "dec-0001-sqlite.md", dump_fact(f)))
    assert again == f


ACTIONABLE = GOOD.replace("tags: [db]\n", """tags: [db]
triggers: [migration, schema]
paths:
  - "db/**/*.py"
action_hint: reach for SQLite before adding a database service
failure_if_ignored: agent stands up Postgres nobody runs
check: python -c "import sqlite3"
enforce: stop
""")


def test_parse_actionable_fields(tmp_path):
    f = parse_fact(write(tmp_path, "dec-0001-sqlite.md", ACTIONABLE))
    assert f.triggers == ["migration", "schema"]
    assert f.paths == ["db/**/*.py"]
    assert f.action_hint == "reach for SQLite before adding a database service"
    assert f.failure_if_ignored == "agent stands up Postgres nobody runs"
    assert f.check == 'python -c "import sqlite3"'
    assert f.enforce == "stop"


def test_actionable_fields_default_empty(tmp_path):
    f = parse_fact(write(tmp_path, "dec-0001-sqlite.md", GOOD))
    assert f.triggers == [] and f.paths == []
    assert f.action_hint is None and f.failure_if_ignored is None
    assert f.check is None and f.enforce is None


def test_actionable_fields_roundtrip(tmp_path):
    f = parse_fact(write(tmp_path, "dec-0001-sqlite.md", ACTIONABLE))
    again = parse_fact(write(tmp_path, "dec-0001-sqlite.md", dump_fact(f)))
    assert again == f


def test_dump_omits_unset_actionable_fields(tmp_path):
    text = dump_fact(parse_fact(write(tmp_path, "dec-0001-sqlite.md", GOOD)))
    for key in ("triggers:", "paths:", "action_hint:", "failure_if_ignored:", "check:", "enforce:"):
        assert key not in text


def test_enforce_value_is_checked(tmp_path):
    bad = ACTIONABLE.replace("enforce: stop", "enforce: warn")
    with pytest.raises(FactError, match="enforce"):
        parse_fact(write(tmp_path, "dec-0001-sqlite.md", bad))


def test_triggers_must_be_a_list(tmp_path):
    bad = ACTIONABLE.replace("triggers: [migration, schema]", "triggers: migration")
    with pytest.raises(FactError, match="triggers"):
        parse_fact(write(tmp_path, "dec-0001-sqlite.md", bad))
