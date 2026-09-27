#!/usr/bin/env python3
"""Run every local quality gate that is available in the current environment."""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def run(cmd: list[str], required: bool = True) -> bool:
    print("+", " ".join(cmd), flush=True)
    rc = subprocess.run(cmd, cwd=ROOT, check=False).returncode
    if rc != 0 and required:
        raise SystemExit(rc)
    return rc == 0


def main() -> int:
    run([sys.executable, "scripts/preflight.py"])
    run([sys.executable, "-m", "compileall", "-q", "contracts", "scripts", "tests"])

    if shutil.which("pytest"):
        run([sys.executable, "-m", "pytest", "tests/direct", "-v", "-s"])
    else:
        print("SKIP: pytest not installed")

    if shutil.which("genvm-lint"):
        run(["genvm-lint", "check", "contracts/chainhazard.py"])
        run(["genvm-lint", "check", "contracts/guarded_executor.py"])
    else:
        print("SKIP: genvm-lint not installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
