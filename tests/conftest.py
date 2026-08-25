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
