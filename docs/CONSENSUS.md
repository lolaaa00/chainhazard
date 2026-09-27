# Consensus design

## Nondeterministic responsibility

CHAINHAZARD has one semantic question:

> Which bounded capability bits are directly exercised by the current proposed action?

The model never receives the authority to decide `ALLOWED` or `BLOCKED`.

## Leader path

The leader receives the immutable action description and policy scope and returns:

```json
{
  "parse_ok": true,
  "effect_mask": 16,
  "reason": "the action transmits information to an external recipient"
}
```

Malformed output becomes `parse_ok = false`.

## Validator path

A validator independently runs the same classification over the same immutable action description.

It validates:

1. `parse_ok` is a real boolean;
2. leader and validator agree whether parsing succeeded;
3. successful masks are bounded integers with no unsupported bits;
4. every **policy-relevant capability bit** agrees exactly after projection.

The core rule is:

```text
leader_effect & policy_relevant_mask
==
validator_effect & policy_relevant_mask
```

## Why not exact equality over every taxonomy bit?

Suppose a policy contains only:

```text
SENSITIVE_ACCESS -> EXTERNAL_TRANSMIT
```

Two honest validators could disagree on whether the same action also counts as `STATE_MUTATION`. If the policy never references `STATE_MUTATION`, that disagreement cannot affect present or future state because CHAINHAZARD discards that bit before storage.

Requiring equality over irrelevant diagnostic labels would create needless consensus brittleness.

## Why not compare only the current allow/block result?

That is unsafe because an allowed action's capability bits become persistent state for future decisions.

A malicious leader could report an effect vector that happens not to trigger a rule now but deliberately omits a capability required to block a later action.

Therefore every capability bit that can influence any current or future rule under the policy must independently agree before it can enter the accumulator.

## Settlement

After consensus, deterministic code:

1. projects the effect onto the policy-relevant mask;
2. evaluates directional rules against the prior session accumulator;
3. stores `BLOCKED`, `INCONCLUSIVE`, or `ALLOWED`;
4. merges the projected mask only for an allowed action;
5. issues no permit for blocked or inconclusive actions.

No model output directly writes terminal state.
