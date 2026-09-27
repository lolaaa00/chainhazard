# v0.2.18
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *

from dataclasses import dataclass
import typing


@gl.contract_interface
class IChainHazard:
    class View:
        def is_permitted(
            self,
            action_id: u256,
            expected_session_id: u256,
            expected_action_ref: str,
            expected_consumer: Address,
        ) -> bool: ...

    class Write:
        def consume(self, action_id: u256) -> None: ...


@allow_storage
@dataclass
class ExecutionReceipt:
    caller: Address
    action_id: u256
    session_id: u256
    action_ref: str
    executed_at: str


def current_datetime() -> str:
    message = getattr(gl, "message", None)
    raw = getattr(message, "raw", None)
    value = getattr(raw, "datetime", None)
    if isinstance(value, str) and value != "":
        return value
    mapping = getattr(gl, "message_raw", None)
    if isinstance(mapping, dict):
        fallback = mapping.get("datetime")
        if isinstance(fallback, str) and fallback != "":
            return fallback
    return ""


def require_address(value: typing.Any) -> Address:
    if isinstance(value, Address):
        return value
    try:
        return Address(value)
    except Exception as exc:
        raise gl.vm.UserError("EXPECTED: invalid ChainHazard address") from exc


class GuardedExecutor(gl.Contract):
    """Minimal consumer proving a ChainHazard permit can gate another IC."""

    chainhazard_address: Address
    executions: TreeMap[u256, ExecutionReceipt]
    execution_count: u256

    def __init__(self, chainhazard_address: Address):
        self.chainhazard_address = require_address(chainhazard_address)
        self.execution_count = u256(0)

    @gl.public.write
    def execute(
        self,
        action_id: u256,
        session_id: u256,
        action_ref: str,
    ) -> None:
        if action_id in self.executions:
            raise gl.vm.UserError("EXPECTED: action already executed")

        hazard = IChainHazard(self.chainhazard_address)
        if not hazard.view().is_permitted(
            action_id,
            session_id,
            str(action_ref),
            gl.message.contract_address,
        ):
            raise gl.vm.UserError("EXPECTED: ChainHazard permit is not valid")

        receipt = self.executions.get_or_insert_default(action_id)
        receipt.caller = gl.message.sender_address
        receipt.action_id = action_id
        receipt.session_id = session_id
        receipt.action_ref = str(action_ref)
        receipt.executed_at = current_datetime()
        self.execution_count = u256(int(self.execution_count) + 1)

        # The consumer is locally idempotent before it emits the finalization-
        # gated acknowledgement. ChainHazard then marks this one permit consumed.
        hazard.emit(on="finalized").consume(action_id)

    @gl.public.view
    def was_executed(self, action_id: u256) -> bool:
        return action_id in self.executions

    @gl.public.view
    def get_execution(self, action_id: u256) -> dict[str, typing.Any]:
        item = self.executions.get(action_id)
        if item is None:
            raise gl.vm.UserError("EXPECTED: unknown execution")
        return {
            "caller": str(item.caller),
            "action_id": int(item.action_id),
            "session_id": int(item.session_id),
            "action_ref": str(item.action_ref),
            "executed_at": str(item.executed_at),
        }
