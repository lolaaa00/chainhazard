# Architecture

## Core separation

CHAINHAZARD separates four responsibilities that should not be conflated:

```text
Human / integrating contract
        |
        | immutable directional rules
        v
Policy layer
        |
        | current proposed action
        v
GenLayer semantic classifier
        |
        | policy-relevant capability vector
        v
Deterministic sequence engine
        |
        +--> ALLOWED -> effect reserved in accumulator
        |
        +--> BLOCKED -> accumulator unchanged
        |
        +--> INCONCLUSIVE -> accumulator unchanged
```

## Why rules have two masks

A rule is:

```text
(prior_mask, action_mask)
```

It fires only if:

```python
(accumulated & prior_mask) == prior_mask
and
(effect & action_mask) == action_mask
```

That directionality prevents a common false positive from a simple unordered set model.

`EXTERNAL_TRANSMIT` followed later by `SENSITIVE_ACCESS` is not automatically the same hazard as `SENSITIVE_ACCESS` followed by `EXTERNAL_TRANSMIT`.

## Monotonic state

Allowed actions immediately reserve policy-relevant capability bits in the session accumulator.

There is intentionally no `clear_taint()`, `declassify()` or model-controlled reset. A clean boundary is represented by a new session.

This makes the state machine conservative and reviewable.

## Consumer contract

The included GuardedExecutor is not a product. It exists only to prove the stable integration surface:

```text
GuardedExecutor.execute(...)
        |
        | typed view
        v
ChainHazard.is_permitted(...)
        |
        +-- false -> revert
        |
        +-- true -> local idempotent execution record
                      |
                      | on finalized
                      v
                 ChainHazard.consume(action_id)
```

The finalization-gated acknowledgement means an accepted-but-not-final consumer result does not consume the permit early.
