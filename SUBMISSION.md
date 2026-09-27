# Builder submission

## Title

CHAINHAZARD — stateful composition firewall for autonomous action sequences

## Category

Standalone GenLayer Intelligent Contract

## Repository

`https://github.com/lolaaa00/chainhazard`

## Contract

Core: `0x836226b0BC083384fee8F483C82Fa44605FE5f91`

Consumer: `0x7AeD4D7F069A1247e14296aC89B75EdD1A5B0Ac7`

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

Local rows reflect this checkout. Studionet rows were independently rechecked
as `FINALIZED` against the canonical pair deployed from commit `617c02b`.

| Gate | Result |
|---|---|
| Zero-dependency preflight | PASS — 158 checks |
| Direct Mode | PASS — 39 tests |
| GenVM lint | PASS — 3 AST checks plus semantic validation for each contract against cached stable v0.2.16 SDK |
| Studionet integration | PASS — canonical finalized lifecycle executed directly against the hardened pair |
| Core deployment | FINALIZED, `MAJORITY_AGREE`, execution `SUCCESS` |
| Consumer deployment | FINALIZED, `MAJORITY_AGREE`, execution `SUCCESS` |
| Cross-contract allowed path | FINALIZED; executor receipt recorded and permit became `CONSUMED` |
| Composition hazard blocked path | FINALIZED; action 3 `BLOCKED`, rule `1:1`; executor attempt failed as expected |
| Fresh-session control path | FINALIZED; action 4 `ALLOWED` with `EXTERNAL_TRANSMIT` mask 16 |

## Finalized transaction evidence

Full hashes are recorded in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md). Key evidence:

- core deployment: `0x5ce1c754ef5c5c0f3e3ce712e788068f404d751f8b44e3fc13b567c332eeae6d`;
- consumer deployment: `0x1e543d71a4d7de574a0bd486138e0c26104f7337a59b4f402d2144ff2c317368`;
- sensitive read allowed: `0x481b50e05f58835b0a7e9f7aaee7e6b17f4a2bee8477b0e7b7fee913bfd922af`;
- allowed permit executed: `0xf92cbce2d844755d76eb54779d36af5f2dcafe18722e249ff3c3772483694950`;
- same-session external test marker blocked: `0x4e85eb844edfbf2d3624b19baecb39d98ddf5532b72164dacda573ed387f94e1`;
- blocked execution rejected: `0x0042d1e2d33808177506c39faf165e1a9ff1ce3b2400e0e5c33153979d26ef68`;
- fresh-session external test marker allowed: `0xecc556ce2dd9d27f4e1cc991e20688bcd2e3a386e1cb505a9167446fefaccd67`.

Deployed source commit: `617c02bcc03f9ee86aadf18d7d8327d8c8ca6525`.
Studionet RPC source retrieval produced exact byte-for-byte SHA-256 matches for both contracts.

## Explicit limitations

CHAINHAZARD does not prove that an external side effect occurred, discover actions omitted from the session, or safely declassify accumulated semantic effects. Its guarantee is narrower: policy-relevant action semantics are consensus-bound before deterministic sequence rules issue a reusable permit.
