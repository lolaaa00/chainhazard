# Integration

## Recommended flow

A consuming system should treat the action description as part of its own canonical request construction rather than arbitrary user commentary.

```text
1. create/fetch immutable policy
2. open session
3. propose exact action + bound consumer
4. resolve action
5. consumer checks is_permitted(...)
6. consumer performs its own idempotent operation
7. consumer emits finalized consume(action_id)
```

## Typed interface

```python
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
```

## Consumer-side idempotency

The consumer must reject duplicate `action_id` use locally before emitting the asynchronous acknowledgement.

The included GuardedExecutor does exactly this.

## Finalization

The acknowledgement uses:

```python
hazard.emit(on="finalized").consume(action_id)
```

Do not weaken this to an earlier lifecycle state for privileged actions. The consumer's execution should be final before the permit is consumed in the parent primitive.

## Session design advice

Use a session boundary that matches the context in which accumulated effects remain meaningfully connected, for example:

- one customer-support case;
- one autonomous purchase flow;
- one administrative maintenance window;
- one agent task;
- one privileged execution plan.

Do not reuse one session forever merely to save calls. Overly broad sessions accumulate conservative effects and become intentionally restrictive.
