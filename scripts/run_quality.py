#!/usr/bin/env python3
"""Run every local quality gate that is available in the current environment."""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager

ROOT = pathlib.Path(__file__).resolve().parents[1]


STABLE_GENVM_VERSION = "v0.2.16"


def run(
    cmd: list[str], required: bool = True, env: dict[str, str] | None = None
) -> bool:
    print("+", " ".join(cmd), flush=True)
    rc = subprocess.run(cmd, cwd=ROOT, check=False, env=env).returncode
    if rc != 0 and required:
        raise SystemExit(rc)
    return rc == 0


@contextmanager
def stable_genvm_environment() -> Iterator[dict[str, str]]:
    """Select the stable SDK containing the contracts' pinned runner hash."""
    if os.environ.get("GENVMROOT"):
        yield os.environ.copy()
        return

    from genvm_linter.validate.artifacts import download_artifacts
    from genvm_linter.validate.sdk_loader import extract_sdk_paths, parse_contract_header

    contract = ROOT / "contracts" / "chainhazard.py"
    tarball = download_artifacts(STABLE_GENVM_VERSION)
    sdk_paths, _ = extract_sdk_paths(tarball, parse_contract_header(contract))
    if not sdk_paths:
        raise SystemExit("ERROR: stable GenVM SDK extraction produced no paths")

    with tempfile.TemporaryDirectory(prefix="chainhazard-genvm-") as tmp:
        genvmroot = pathlib.Path(tmp)
        sdk_link = genvmroot / "runners" / "genlayer-py-std" / "src"
        sdk_link.parent.mkdir(parents=True)
        sdk_link.symlink_to(sdk_paths[0], target_is_directory=True)
        env = os.environ.copy()
        env["GENVMROOT"] = str(genvmroot)
        yield env


def main() -> int:
    run([sys.executable, "scripts/preflight.py"])
    run([sys.executable, "-m", "compileall", "-q", "contracts", "scripts", "tests"])

    if not shutil.which("pytest"):
        raise SystemExit("ERROR: pytest is required; install requirements-test.txt")
    run([sys.executable, "-m", "pytest", "tests/direct", "-v", "-s"])

    if not shutil.which("genvm-lint"):
        raise SystemExit("ERROR: genvm-lint is required; install requirements.txt")
    with stable_genvm_environment() as genvm_env:
        run(["genvm-lint", "check", "contracts/chainhazard.py"], env=genvm_env)
        run(["genvm-lint", "check", "contracts/guarded_executor.py"], env=genvm_env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
