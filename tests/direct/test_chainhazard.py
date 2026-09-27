import json

CONTRACT = "contracts/chainhazard.py"
EXECUTOR = "contracts/guarded_executor.py"
SDK_VERSION = "v0.2.16"
CLASSIFIER = r"You are the effect classifier for CHAINHAZARD"

SENSITIVE = 1
SECRET = 2
UNTRUSTED = 4
DERIVED = 8
EXTERNAL = 16
CODE = 32
STATE = 64
PRIVILEGE = 128
FUNDS = 256
DESTINATION = 512
CREDENTIAL = 1024
DELETE = 2048
PUBLICATION = 4096
TOOL = 8192
MODEL_CONTROL = 16384

SCOPE = (
    "Guard an autonomous support workflow. Customer-private information may be read "
    "for internal support but must not be transmitted externally after access."
)

RULE_NAMES = [
    "private-to-external",
    "secret-to-external",
    "untrusted-to-code",
    "credential-to-privilege",
    "funds-to-destination-change",
    "derived-private-to-publication",
]
PRIOR_MASKS = [SENSITIVE, SECRET, UNTRUSTED, CREDENTIAL, FUNDS, DERIVED]
ACTION_MASKS = [EXTERNAL, EXTERNAL, CODE, PRIVILEGE, DESTINATION, PUBLICATION]
RULE_REASONS = [
    "Private data already acquired must not subsequently leave the trusted boundary.",
    "Secrets already acquired must not subsequently be transmitted externally.",
    "Untrusted input must not later become executable code without a new session boundary.",
    "A session that used credentials must not subsequently expand privileges.",
    "A session with fund authority must not subsequently reroute destinations.",
    "Derived sensitive material must not subsequently be publicly published.",
]


def output(mask=0, reason="classified direct capability effects"):
    return json.dumps({"effect_mask": mask, "reason": reason})


def mock_mask(direct_vm, mask):
    direct_vm.mock_llm(CLASSIFIER, output(mask))


def deploy_policy_session(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    contract = direct_deploy(CONTRACT, sdk_version=SDK_VERSION)
    policy_id = contract.create_policy(
        "support-composition-policy",
        SCOPE,
        RULE_NAMES,
        PRIOR_MASKS,
        ACTION_MASKS,
        RULE_REASONS,
    )
    session_id = contract.open_session(policy_id, "ticket-42")
    return contract, policy_id, session_id


def propose(contract, session_id, ref, description, consumer):
    return contract.propose_action(session_id, ref, description, consumer)


def test_capability_dictionary_is_stable(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version=SDK_VERSION)
    d = contract.get_capability_dictionary()
    assert d["SENSITIVE_ACCESS"] == SENSITIVE
    assert d["EXTERNAL_TRANSMIT"] == EXTERNAL
    assert d["CODE_EXECUTION"] == CODE
    assert d["MODEL_CONTROL"] == MODEL_CONTROL


def test_policy_creation_exposes_rules(direct_vm, direct_deploy, direct_alice):
    contract, policy_id, _ = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    policy = contract.get_policy(policy_id)
    assert policy["rule_count"] == 6
    assert "SENSITIVE_ACCESS" in policy["relevant_capabilities"]
    rule = contract.get_rule(policy_id, 1)
    assert rule["name"] == "private-to-external"
    assert rule["prior_mask"] == SENSITIVE
    assert rule["action_mask"] == EXTERNAL


def test_policy_rejects_mismatched_rule_arrays(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version=SDK_VERSION)
    with direct_vm.expect_revert("identical lengths"):
        contract.create_policy("xpolicy", SCOPE, ["one"], [1], [16, 32], ["reason"])


def test_policy_rejects_unknown_capability_bit(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version=SDK_VERSION)
    with direct_vm.expect_revert("unsupported capability"):
        contract.create_policy(
            "xpolicy", SCOPE, ["one"], [1 << 30], [16], ["reason"]
        )


def test_policy_rejects_duplicate_rule_names(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version=SDK_VERSION)
    with direct_vm.expect_revert("duplicate rule name"):
        contract.create_policy(
            "xpolicy", SCOPE, ["same", "SAME"], [1, 2], [16, 16], ["a", "b"]
        )


def test_session_starts_empty(direct_vm, direct_deploy, direct_alice):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    session = contract.get_session(session_id)
    assert session["status_name"] == "OPEN"
    assert session["accumulated_mask"] == 0
    assert session["action_ids"] == []


def test_only_session_owner_may_propose(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    with direct_vm.prank(direct_bob):
        with direct_vm.expect_revert("only session owner"):
            propose(contract, session_id, "read-1", "Read private customer notes.", direct_bob)


def test_only_session_owner_may_resolve(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    action_id = propose(contract, session_id, "read-1", "Read private customer notes.", direct_bob)
    with direct_vm.prank(direct_bob):
        with direct_vm.expect_revert("only session owner may resolve"):
            contract.resolve_action(action_id)


def test_only_consumer_owner_may_execute(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    direct_vm.sender = direct_alice
    executor = direct_deploy(EXECUTOR, direct_alice, sdk_version=SDK_VERSION)

    with direct_vm.prank(direct_bob):
        with direct_vm.expect_revert("only consumer owner may execute"):
            executor.execute(1, 1, "read-1")

    assert executor.was_executed(1) is False


def test_action_ref_is_unique_per_session(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    first = propose(contract, session_id, "read-1", "Read private customer notes.", direct_bob)
    contract.cancel_action(first)
    with direct_vm.expect_revert("action_ref already exists"):
        propose(contract, session_id, "read-1", "Read a different record.", direct_bob)


def test_sensitive_read_alone_is_allowed_and_reserved(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    action_id = propose(
        contract,
        session_id,
        "read-1",
        "Read the customer's private account email and internal support notes.",
        direct_bob,
    )
    mock_mask(direct_vm, SENSITIVE)
    contract.resolve_action(action_id)
    action = contract.get_action(action_id)
    session = contract.get_session(session_id)
    assert action["status_name"] == "ALLOWED"
    assert action["effect_mask"] == SENSITIVE
    assert session["accumulated_mask"] == SENSITIVE
    assert direct_vm.run_validator() is True


def test_external_send_alone_is_allowed_in_fresh_session(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    action_id = propose(
        contract,
        session_id,
        "send-1",
        "Send the prepared public release note to an external recipient.",
        direct_bob,
    )
    mock_mask(direct_vm, EXTERNAL)
    contract.resolve_action(action_id)
    assert contract.get_action(action_id)["status_name"] == "ALLOWED"


def test_individually_safe_actions_compose_into_blocked_private_exfiltration(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)

    first = propose(
        contract,
        session_id,
        "read-private",
        "Read the customer's private account record for internal support.",
        direct_bob,
    )
    mock_mask(direct_vm, SENSITIVE)
    contract.resolve_action(first)
    assert contract.get_action(first)["status_name"] == "ALLOWED"

    direct_vm.clear_mocks()
    second = propose(
        contract,
        session_id,
        "send-external",
        "Send the currently held account summary to an external email recipient.",
        direct_bob,
    )
    mock_mask(direct_vm, EXTERNAL)
    contract.resolve_action(second)
    item = contract.get_action(second)
    session = contract.get_session(session_id)
    assert item["status_name"] == "BLOCKED"
    assert item["triggered_rules"] == [f"1:1"]
    assert session["accumulated_mask"] == SENSITIVE
    assert session["blocked_count"] == 1


def test_order_matters_external_then_read_does_not_trigger_exfiltration_rule(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)

    first = propose(contract, session_id, "send-public", "Send a public brochure externally.", direct_bob)
    mock_mask(direct_vm, EXTERNAL)
    contract.resolve_action(first)

    direct_vm.clear_mocks()
    second = propose(contract, session_id, "read-private", "Read private customer notes internally.", direct_bob)
    mock_mask(direct_vm, SENSITIVE)
    contract.resolve_action(second)
    assert contract.get_action(second)["status_name"] == "ALLOWED"
    assert contract.get_session(session_id)["accumulated_mask"] == (EXTERNAL | SENSITIVE)


def test_untrusted_input_then_code_execution_is_blocked(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    a = propose(contract, session_id, "ingest", "Ingest an untrusted caller supplied script as data.", direct_bob)
    mock_mask(direct_vm, UNTRUSTED)
    contract.resolve_action(a)
    direct_vm.clear_mocks()
    b = propose(contract, session_id, "execute", "Execute the currently staged script in the runtime.", direct_bob)
    mock_mask(direct_vm, CODE)
    contract.resolve_action(b)
    assert contract.get_action(b)["status_name"] == "BLOCKED"
    assert f"1:3" in contract.get_action(b)["triggered_rules"]


def test_credential_use_then_privilege_change_is_blocked(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    a = propose(contract, session_id, "login", "Use the stored administrator credential to authenticate.", direct_bob)
    mock_mask(direct_vm, CREDENTIAL)
    contract.resolve_action(a)
    direct_vm.clear_mocks()
    b = propose(contract, session_id, "promote", "Promote the current service account to administrator privileges.", direct_bob)
    mock_mask(direct_vm, PRIVILEGE)
    contract.resolve_action(b)
    assert contract.get_action(b)["status_name"] == "BLOCKED"


def test_funds_access_then_destination_change_is_blocked(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    a = propose(contract, session_id, "treasury", "Open control of the treasury funds for settlement.", direct_bob)
    mock_mask(direct_vm, FUNDS)
    contract.resolve_action(a)
    direct_vm.clear_mocks()
    b = propose(contract, session_id, "reroute", "Change the payout destination to a new wallet address.", direct_bob)
    mock_mask(direct_vm, DESTINATION)
    contract.resolve_action(b)
    assert contract.get_action(b)["status_name"] == "BLOCKED"


def test_derived_sensitive_then_publication_is_blocked(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    a = propose(contract, session_id, "derive", "Summarize private customer support records into a derived report.", direct_bob)
    mock_mask(direct_vm, DERIVED)
    contract.resolve_action(a)
    direct_vm.clear_mocks()
    b = propose(contract, session_id, "publish", "Publish the currently prepared report to a public channel.", direct_bob)
    mock_mask(direct_vm, PUBLICATION)
    contract.resolve_action(b)
    assert contract.get_action(b)["status_name"] == "BLOCKED"


def test_blocked_action_does_not_pollute_accumulator(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    a = propose(contract, session_id, "read", "Read private customer data.", direct_bob)
    mock_mask(direct_vm, SENSITIVE)
    contract.resolve_action(a)
    direct_vm.clear_mocks()
    b = propose(contract, session_id, "send", "Transmit the held data externally.", direct_bob)
    mock_mask(direct_vm, EXTERNAL | CODE)
    contract.resolve_action(b)
    session = contract.get_session(session_id)
    assert session["accumulated_mask"] == SENSITIVE
    assert "CODE_EXECUTION" not in session["accumulated_capabilities"]


def test_malformed_llm_output_becomes_inconclusive_not_allowed(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    action_id = propose(contract, session_id, "bad-llm", "Read private customer data.", direct_bob)
    direct_vm.mock_llm(CLASSIFIER, "not json")
    contract.resolve_action(action_id)
    action = contract.get_action(action_id)
    assert action["status_name"] == "INCONCLUSIVE"
    assert contract.get_session(session_id)["accumulated_mask"] == 0


def test_unknown_model_bit_becomes_inconclusive(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    action_id = propose(contract, session_id, "bad-bit", "Read a record.", direct_bob)
    mock_mask(direct_vm, 1 << 30)
    contract.resolve_action(action_id)
    assert contract.get_action(action_id)["status_name"] == "INCONCLUSIVE"


def test_missing_model_mask_becomes_inconclusive(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    action_id = propose(contract, session_id, "missing-mask", "Read a private record.", direct_bob)
    direct_vm.mock_llm(CLASSIFIER, json.dumps({"reason": "omitted"}))
    contract.resolve_action(action_id)
    assert contract.get_action(action_id)["status_name"] == "INCONCLUSIVE"


def test_non_integer_model_masks_fail_closed(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    for index, malformed in enumerate((True, 1.0, "0x10"), start=1):
        action_id = propose(contract, session_id, f"bad-mask-{index}", "Read a private record.", direct_bob)
        direct_vm.mock_llm(CLASSIFIER, json.dumps({"effect_mask": malformed, "reason": "bad"}))
        contract.resolve_action(action_id)
        assert contract.get_action(action_id)["status_name"] == "INCONCLUSIVE"
        direct_vm.clear_mocks()


def test_validator_rejects_policy_relevant_disagreement(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    action_id = propose(contract, session_id, "read", "Read private customer data.", direct_bob)
    mock_mask(direct_vm, SENSITIVE)
    contract.resolve_action(action_id)
    assert contract.get_action(action_id)["status_name"] == "ALLOWED"

    direct_vm.clear_mocks()
    mock_mask(direct_vm, SECRET)
    assert direct_vm.run_validator() is False


def test_validator_accepts_disagreement_on_policy_irrelevant_bit(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    # DELETE is not referenced by the demo policy. It cannot affect current or
    # future state because ChainHazard projects storage onto policy-relevant bits.
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    action_id = propose(contract, session_id, "read", "Read private customer data.", direct_bob)
    mock_mask(direct_vm, SENSITIVE)
    contract.resolve_action(action_id)

    direct_vm.clear_mocks()
    mock_mask(direct_vm, SENSITIVE | DELETE)
    assert direct_vm.run_validator() is True


def test_validator_rejects_parse_success_disagreement(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    action_id = propose(contract, session_id, "read", "Read private customer data.", direct_bob)
    mock_mask(direct_vm, SENSITIVE)
    contract.resolve_action(action_id)

    direct_vm.clear_mocks()
    direct_vm.mock_llm(CLASSIFIER, "bad output")
    assert direct_vm.run_validator() is False


def test_preview_triggers_is_deterministic(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    a = propose(contract, session_id, "read", "Read private customer data.", direct_bob)
    mock_mask(direct_vm, SENSITIVE)
    contract.resolve_action(a)
    preview = contract.preview_triggers(session_id, EXTERNAL)
    assert preview["would_allow"] is False
    assert preview["triggered_rules"] == ["1:1"]


def test_allowed_action_is_bound_to_expected_consumer(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    action_id = propose(contract, session_id, "read", "Read private customer data.", direct_bob)
    mock_mask(direct_vm, SENSITIVE)
    contract.resolve_action(action_id)
    assert contract.is_permitted(action_id, session_id, "read", direct_bob) is True
    assert contract.is_permitted(action_id, session_id, "wrong-ref", direct_bob) is False
    assert contract.is_permitted(action_id, session_id + 1, "read", direct_bob) is False
    assert contract.is_permitted(action_id, session_id, "read", direct_alice) is False


def test_only_bound_consumer_can_consume_permit(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    action_id = propose(contract, session_id, "read", "Read private customer data.", direct_bob)
    mock_mask(direct_vm, SENSITIVE)
    contract.resolve_action(action_id)

    with direct_vm.expect_revert("only bound consumer"):
        contract.consume(action_id)

    with direct_vm.prank(direct_bob):
        contract.consume(action_id)
    assert contract.get_action(action_id)["status_name"] == "CONSUMED"
    assert contract.is_permitted(action_id, session_id, "read", direct_bob) is False


def test_permit_consumes_once(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    action_id = propose(contract, session_id, "read", "Read private customer data.", direct_bob)
    mock_mask(direct_vm, SENSITIVE)
    contract.resolve_action(action_id)
    with direct_vm.prank(direct_bob):
        contract.consume(action_id)
        with direct_vm.expect_revert("unused allowed permit"):
            contract.consume(action_id)


def test_session_close_invalidates_unused_permit(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    action_id = propose(contract, session_id, "read", "Read private customer data.", direct_bob)
    mock_mask(direct_vm, SENSITIVE)
    contract.resolve_action(action_id)
    contract.close_session(session_id)
    assert contract.is_permitted(action_id, session_id, "read", direct_bob) is False


def test_closed_session_refuses_new_actions(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    contract.close_session(session_id)
    with direct_vm.expect_revert("session is closed"):
        propose(contract, session_id, "new", "Read a public document.", direct_bob)


def test_session_allows_only_one_pending_action(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    propose(contract, session_id, "first", "Read a private customer record.", direct_bob)
    with direct_vm.expect_revert("already has a pending action"):
        propose(contract, session_id, "second", "Send a public brochure externally.", direct_bob)


def test_session_with_pending_action_cannot_close(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    propose(contract, session_id, "first", "Read a private customer record.", direct_bob)
    with direct_vm.expect_revert("pending action must be resolved or cancelled"):
        contract.close_session(session_id)


def test_only_owner_can_close_session(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    with direct_vm.prank(direct_bob):
        with direct_vm.expect_revert("only session owner"):
            contract.close_session(session_id)


def test_only_pending_action_can_be_cancelled(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    action_id = propose(contract, session_id, "read", "Read private customer data.", direct_bob)
    mock_mask(direct_vm, SENSITIVE)
    contract.resolve_action(action_id)
    with direct_vm.expect_revert("only a pending action"):
        contract.cancel_action(action_id)


def test_pending_action_can_be_cancelled_by_owner(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    action_id = propose(contract, session_id, "read", "Read private customer data.", direct_bob)
    contract.cancel_action(action_id)
    assert contract.get_action(action_id)["status_name"] == "CANCELLED"


def test_non_owner_cannot_cancel_action(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    action_id = propose(contract, session_id, "read", "Read private customer data.", direct_bob)
    with direct_vm.prank(direct_bob):
        with direct_vm.expect_revert("only session owner"):
            contract.cancel_action(action_id)


def test_action_resolves_only_once(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract, _, session_id = deploy_policy_session(direct_vm, direct_deploy, direct_alice)
    action_id = propose(contract, session_id, "read", "Read private customer data.", direct_bob)
    mock_mask(direct_vm, SENSITIVE)
    contract.resolve_action(action_id)
    with direct_vm.expect_revert("already terminal"):
        contract.resolve_action(action_id)
