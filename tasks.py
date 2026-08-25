"""Uniform entry points: python tasks.py test|run|check (studio convention).

Ecosystem-aware: a Node project (package.json) delegates to npm/pnpm; a Python
project runs pytest. Detection is self-contained so this stays correct copied
byte-for-byte into every studio project."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def _is_node():
    return (ROOT / "package.json").is_file()
def _node_cmd():
    # pnpm when its lockfile is present, else npm (bare package.json or npm lock)
    return "pnpm" if (ROOT / "pnpm-lock.yaml").is_file() else "npm"

def test():
    if _is_node():
        return subprocess.call([_node_cmd(), "test"], cwd=str(ROOT))
    rc = subprocess.call([sys.executable, "-m", "pytest", "-q"], cwd=str(ROOT))
    # pytest exit 5 = no tests collected. Tolerate only for a Python project
    # with no tests/ dir yet (green until the first test exists); never mask it
    # once tests/ exists, and never for Node.
    return 0 if rc == 5 and not (ROOT / "tests").is_dir() else rc
def run():
    if _is_node():
        return subprocess.call([_node_cmd(), "start"], cwd=str(ROOT))
    print("no run target yet"); return 0
def check(): return test()

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    sys.exit({"test": test, "run": run, "check": check}[cmd]())
