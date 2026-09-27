#!/usr/bin/env python3
"""Deploy ChainHazard to stable GenLayer Studionet using the active CLI account."""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import json
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "chainhazard.py"
PREFLIGHT = ROOT / "scripts" / "preflight.py"
STUDIONET_RPC = "https://studio.genlayer.com/api"
EXPECTED_CHAIN_ID = 61999


def verify_chain_id() -> None:
    request = urllib.request.Request(
        STUDIONET_RPC,
        data=json.dumps({"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "chainhazard-preflight/1.0"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.load(response)
    actual = int(payload["result"], 16)
    if actual != EXPECTED_CHAIN_ID:
        raise SystemExit(f"ERROR: RPC chain ID {actual}, expected {EXPECTED_CHAIN_ID}")
    print(f"Verified Studionet chain ID: {actual}")


def run(command: list[str], *, cwd: pathlib.Path = ROOT) -> None:
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=cwd, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    cli = shutil.which("genlayer")
    if cli is None:
        print("ERROR: genlayer CLI is not installed or not on PATH.", file=sys.stderr)
        return 2
    if not CONTRACT.is_file():
        print(f"ERROR: contract not found: {CONTRACT}", file=sys.stderr)
        return 2

    run([sys.executable, str(PREFLIGHT)])
    verify_chain_id()
    run([cli, "account", "show"])

    print(f"Deploying ChainHazard to stable Studionet chain {EXPECTED_CHAIN_ID}.")
    run([
        cli,
        "deploy",
        "--contract",
        str(CONTRACT),
        "--rpc",
        STUDIONET_RPC,
    ])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
