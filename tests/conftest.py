import shutil
from pathlib import Path
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def space_a(tmp_path, monkeypatch):
    dst = tmp_path / "space-a"
    shutil.copytree(FIXTURES / "space-a", dst)
    monkeypatch.setenv("MEMSPACE_ROOT", str(dst))
    return dst


@pytest.fixture
def space_b(tmp_path, monkeypatch):
    """A space whose facts carry triggers, paths, checks and enforcement."""
    dst = tmp_path / "space-b"
    shutil.copytree(FIXTURES / "space-b", dst)
    monkeypatch.setenv("MEMSPACE_ROOT", str(dst))
    return dst
