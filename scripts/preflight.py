#!/usr/bin/env python3
"""Zero-dependency repository gate for ChainHazard.

This intentionally runs without genlayer-test or the GenVM linter. It catches
network contamination, missing invariants, syntax errors, accidental frontend
material, and weak source regressions before the expensive toolchain is invoked.
"""

from __future__ import annotations

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORE = ROOT / "contracts" / "chainhazard.py"
CONSUMER = ROOT / "contracts" / "guarded_executor.py"
CONFIG = ROOT / "gltest.config.yaml"

FORBIDDEN = (
    "619" + "97",
    "studio" + "-dev",
    "studio" + "-next",
    "studio" + "Devnet",
)

checks = 0
IGNORED_PARTS = {".git", ".pytest_cache", ".venv", "__pycache__", "artifacts"}


def ok(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


def text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    ok(CORE.is_file(), "missing contracts/chainhazard.py")
    ok(CONSUMER.is_file(), "missing contracts/guarded_executor.py")
    ok(not (ROOT / "frontend").exists(), "standalone primitive must not ship a frontend")

    # Syntax compilation without importing unavailable GenLayer packages.
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts):
            continue
        source = text(path)
        ast.parse(source, filename=str(path))
        ok(True, f"syntax: {path.relative_to(ROOT)}")

    core = text(CORE)
    consumer = text(CONSUMER)
    config = text(CONFIG)

    required_core = (
        "class ChainHazard(gl.Contract)",
        "gl.vm.run_nondet_unsafe",
        "def validator_fn",
        "relevant_mask",
        "_triggered_keys",
        "session.accumulated_mask",
        "ACTION_INCONCLUSIVE",
        "def is_permitted",
        "def consume",
        "CAP_SENSITIVE_ACCESS",
        "CAP_EXTERNAL_TRANSMIT",
        "CAP_UNTRUSTED_INPUT",
        "CAP_CODE_EXECUTION",
        "@gl.public.write",
        "@gl.public.view",
    )
    for needle in required_core:
        ok(needle in core, f"core invariant missing: {needle}")

    ok(
        "(leader_mask & relevant_mask) != (own_mask & relevant_mask)" in core,
        "validator must bind every policy-relevant persistent capability bit",
    )
    ok(
        "session.accumulated_mask = u32(int(session.accumulated_mask) | effect_mask)" in core,
        "allowed actions must monotonically reserve effects",
    )
    ok(
        "if len(triggered) > 0:" in core and "ACTION_BLOCKED" in core,
        "triggered sequence rule must deterministically block",
    )
    ok(
        "@gl.contract_interface" in consumer
        and ".view().is_permitted" in consumer
        and '.emit(on="finalized").consume' in consumer,
        "consumer must prove typed read gate plus finalized one-time acknowledgement",
    )

    ok("https://studio.genlayer.com/api" in config, "missing stable Studionet RPC")
    ok("studionet:" in config, "missing Studionet network entry")
    ok("61999" in text(ROOT / "scripts" / "deploy_studionet.py"), "deployment script must pin expected chain ID")

    # User requirement: no preview-network contamination anywhere in the package.
    for path in sorted(ROOT.rglob("*")):
        if (
            not path.is_file()
            or any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts)
            or path.suffix.lower() in {".zip", ".pyc"}
        ):
            continue
        value = text(path)
        for token in FORBIDDEN:
            ok(token not in value, f"forbidden preview-network token in {path.relative_to(ROOT)}")

    direct = text(ROOT / "tests" / "direct" / "test_chainhazard.py")
    ok(direct.count("def test_") >= 25, "expected at least 25 direct-mode cases")
    ok("individually_safe_actions_compose" in direct, "missing thesis regression")
    ok("order_matters" in direct, "missing sequence-direction regression")
    ok("policy_relevant_disagreement" in direct, "missing adversarial validator regression")
    ok("policy_irrelevant_bit" in direct, "missing equivalence-boundary regression")

    readme = text(ROOT / "README.md")
    ok("no frontend" in readme.lower(), "README must make primitive boundary explicit")
    ok("not deployed yet" in readme.lower(), "README must not fake deployment evidence")
    ok("61999" in readme, "README must state target chain")

    print(f"PASS: {checks} preflight checks")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
