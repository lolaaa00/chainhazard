"""High-signal live Studionet lifecycle for ChainHazard.

This suite targets stable Studionet only. It deploys a fresh primitive plus the
minimal GuardedExecutor consumer, proves a permitted action can be consumed by
another IC, and proves a later action is blocked only because of accumulated
session context.
"""

from gltest import get_contract_factory, get_default_account
from gltest.assertions import tx_execution_failed, tx_execution_succeeded
import time


CHAINHAZARD = "chainhazard.py"
CONSUMER = "guarded_executor.py"
TX_KW = {"consensus_max_rotations": 3, "wait_interval": 10000, "wait_retries": 25}

SENSITIVE = 1
EXTERNAL = 16


def assert_success(receipt):
    assert tx_execution_succeeded(receipt), receipt


def test_composition_hazard_and_cross_contract_gate():
    account = get_default_account()

    hazard_factory = get_contract_factory(contract_file_path=CHAINHAZARD)
    hazard = hazard_factory.deploy(account=account, **TX_KW)
    assert hazard.address

    consumer_factory = get_contract_factory(contract_file_path=CONSUMER)
    consumer = consumer_factory.deploy(args=[hazard.address], account=account, **TX_KW)
    assert consumer.address

    created = hazard.create_policy(args=[
        "private-data-egress",
        "Customer-private data may be used internally for support but may not be transmitted to an external recipient after it has been accessed in the same session.",
        ["private-to-external"],
        [SENSITIVE],
        [EXTERNAL],
        ["Private data already acquired must not later leave the trusted boundary."],
    ]).transact(**TX_KW)
    assert_success(created)

    opened = hazard.open_session(args=[1, "Studionet composition-hazard demonstration"]).transact(**TX_KW)
    assert_success(opened)

    first = hazard.propose_action(args=[
        1,
        "read-private",
        "Read the customer's private account email and internal support notes for internal support handling.",
        consumer.address,
    ]).transact(**TX_KW)
    assert_success(first)

    resolved_first = hazard.resolve_action(args=[1]).transact(**TX_KW)
    assert_success(resolved_first)
    first_state = hazard.get_action(args=[1]).call()
    assert first_state["status_name"] == "ALLOWED"
    assert first_state["effect_mask"] & SENSITIVE

    executed = consumer.execute(args=[1, 1, "read-private"]).transact(**TX_KW)
    assert_success(executed)
    assert consumer.was_executed(args=[1]).call() is True
    for _ in range(12):
        if hazard.get_action(args=[1]).call()["status_name"] == "CONSUMED":
            break
        time.sleep(5)
    assert hazard.get_action(args=[1]).call()["status_name"] == "CONSUMED"

    second = hazard.propose_action(args=[
        1,
        "send-external",
        "Send the currently held customer account summary to an external public email recipient.",
        consumer.address,
    ]).transact(**TX_KW)
    assert_success(second)

    resolved_second = hazard.resolve_action(args=[2]).transact(**TX_KW)
    assert_success(resolved_second)
    second_state = hazard.get_action(args=[2]).call()
    assert second_state["status_name"] == "BLOCKED"
    assert second_state["triggered_rules"] == ["1:1"]

    denied = consumer.execute(args=[2, 1, "send-external"]).transact(**TX_KW)
    assert tx_execution_failed(denied), denied
    assert consumer.was_executed(args=[2]).call() is False

    opened_fresh = hazard.open_session(args=[1, "Fresh-session control"]).transact(**TX_KW)
    assert_success(opened_fresh)
    public_send = hazard.propose_action(args=[
        2,
        "send-public",
        "Send an ordinary public brochure to an external recipient.",
        consumer.address,
    ]).transact(**TX_KW)
    assert_success(public_send)
    resolved_public = hazard.resolve_action(args=[3]).transact(**TX_KW)
    assert_success(resolved_public)
    public_state = hazard.get_action(args=[3]).call()
    assert public_state["status_name"] == "ALLOWED"
    assert public_state["effect_mask"] & EXTERNAL
