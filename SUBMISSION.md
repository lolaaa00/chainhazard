# Builder submission draft

> Fill every `TBD` from actual final runtime evidence. Do not submit this file unchanged.

## Title

CHAINHAZARD — stateful composition firewall for autonomous action sequences

## Category

Standalone GenLayer Intelligent Contract

## Repository

`https://github.com/lolaaa00/chainhazard`

## Contract

`TBD`

## Network

Studionet, chain ID `61999`

## What it does

CHAINHAZARD prevents an autonomous workflow from combining actions that are individually permitted but dangerous in sequence. GenLayer validators classify only the current action into a bounded capability taxonomy. Immutable directional rules are then evaluated deterministically against capabilities already accumulated by the session.

The canonical demonstration is `SENSITIVE_ACCESS -> EXTERNAL_TRANSMIT`: reading private customer data can be allowed, and sending public information externally can be allowed in a fresh session, while sending externally after the sensitive read is blocked.

## Why GenLayer consensus is necessary

The non-deterministic boundary is deliberately narrow: independent validators determine which fixed capability bits are directly exercised by the current natural-language action. The model never writes the terminal allow/block result.

Because allowed capability bits become future protocol state, validators must agree exactly on every bit referenced by the immutable policy. Diagnostic bits outside the policy may vary because they are discarded and cannot affect state.

## Reusability

A downstream Intelligent Contract can call `is_permitted(...)` before execution. The repository includes `GuardedExecutor`, a second IC that performs that typed view gate, records execution idempotently, and acknowledges consumption back to CHAINHAZARD only after finalization.

## Deterministic protocol mechanics

- immutable directional hazard rules;
- monotonic per-session semantic effect accumulator;
- order-sensitive rule evaluation;
- fail-closed `INCONCLUSIVE` state;
- blocked actions do not alter accumulated context;
- consumer-bound one-time permits;
- closed sessions invalidate outstanding permits.

## Validation evidence

| Gate | Result |
|---|---|
| Zero-dependency preflight | `TBD` |
| Direct Mode | `TBD` |
| GenVM lint | `TBD` |
| Studionet integration | `TBD` |
| Core deployment | `TBD` |
| Consumer deployment | `TBD` |
| Cross-contract allowed path | `TBD` |
| Composition hazard blocked path | `TBD` |
| Fresh-session control path | `TBD` |

## Finalized transaction evidence

`TBD`

## Explicit limitations

CHAINHAZARD does not prove that an external side effect occurred, discover actions omitted from the session, or safely declassify accumulated semantic effects. Its guarantee is narrower: policy-relevant action semantics are consensus-bound before deterministic sequence rules issue a reusable permit.
