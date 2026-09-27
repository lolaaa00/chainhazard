#!/usr/bin/env python3
"""Deploy GuardedExecutor against an already deployed ChainHazard contract."""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
import json
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "guarded_executor.py"
STUDIONET_RPC = "https://studio.genlayer.com/api"
EXPECTED_CHAIN_ID = 61999


def verify_chain_id() -> None:
    request = urllib.request.Request(
        STUDIONET_RPC,
        data=json.dumps({"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.load(response)
    actual = int(payload["result"], 16)
    if actual != EXPECTED_CHAIN_ID:
        raise SystemExit(f"ERROR: RPC chain ID {actual}, expected {EXPECTED_CHAIN_ID}")
    print(f"Verified Studionet chain ID: {actual}")


def valid_address(value: str) -> str:
    text = value.strip()
    if len(text) != 42 or not text.startswith("0x"):
        raise argparse.ArgumentTypeError("expected a 20-byte 0x-prefixed address")
    try:
        int(text[2:], 16)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("address must be hexadecimal") from exc
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("chainhazard_address", type=valid_address)
    args = parser.parse_args()

    cli = shutil.which("genlayer")
    if cli is None:
        print("ERROR: genlayer CLI is not installed or not on PATH.", file=sys.stderr)
        return 2

    verify_chain_id()
    print(f"Deploying GuardedExecutor to stable Studionet chain {EXPECTED_CHAIN_ID}.")
    command = [
        cli,
        "deploy",
        "--contract",
        str(CONTRACT),
        "--args",
        args.chainhazard_address,
        "--rpc",
        STUDIONET_RPC,
    ]
    print("+", " ".join(command), flush=True)
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
