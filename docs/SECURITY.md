# Security model

## Security objective

Prevent a downstream action from receiving a CHAINHAZARD permit when its policy-relevant semantic capabilities complete a forbidden directional composition with effects already reserved by the same session.

## Main invariants

### 1. Policies are immutable

There is no mutation method for existing rules. A changed rule set is a new policy.

### 2. Sessions are monotonic

Allowed effects only accumulate. No semantic operation can remove previously reserved bits.

### 3. Blocked actions do not contaminate state

A rejected action is recorded but contributes no capability bits to the accumulator.

### 4. Inconclusive is fail-closed

Malformed or unparseable model output cannot grant permission.

### 5. Persistent semantic bits are validator-bound

The leader cannot choose future session semantics unilaterally. Every policy-relevant bit must match an independent validator classification.

### 6. Permits are consumer-bound

`is_permitted` includes the expected consumer contract address, session ID and action reference.

### 7. Consumption is one-time

Only the bound consumer can move an `ALLOWED` permit to `CONSUMED`.

### 8. Closing a session invalidates outstanding permits

`is_permitted` returns false when the owning session is closed.

### 9. Session resolution is serialized

A session may have only one pending action. It must be resolved or cancelled
before another action is proposed, and a session with a pending action cannot
close. This prevents reverse-resolution races from changing the meaning of
"prior" session effects.

## Deliberate conservative choice: reservation on allow

CHAINHAZARD merges capabilities when permission is granted, not only after downstream execution.

This can over-account if a permitted action is later abandoned, but it prevents a more dangerous race where another action is approved while the first effect is still pending acknowledgement.

The protocol therefore chooses:

```text
possible false positive
```

over:

```text
unsafe temporary under-accounting
```

A new session is the reset boundary.

## Threats not solved

- omitted actions that never pass through CHAINHAZARD;
- inaccurate/misleading action descriptions supplied by the integration layer;
- malicious validator majority;
- external side effects that occur outside participating contracts;
- perfect semantic classification for arbitrary text;
- automatic proof that a consumer executed the same real-world operation described by the action;
- safe semantic declassification.

Integrators should treat CHAINHAZARD as a composition-permit layer, not a full sandbox.
