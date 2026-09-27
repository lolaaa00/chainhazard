# Builder submission

## Title

CHAINHAZARD — stateful composition firewall for autonomous action sequences

## Category

Standalone GenLayer Intelligent Contract

## Repository

`https://github.com/lolaaa00/chainhazard`

## Contract

Core: `0x64DbC1429Cc698a59DA8331e44543c04c32cF0c1`

Consumer: `0x0F9BeEDe80427b93dd83e54b6588071E92a1a1e8`

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
| Zero-dependency preflight | PASS — 154 checks |
| Direct Mode | PASS — 37 tests (latest run: 4.02s) |
| GenVM lint | PASS — 3 AST checks plus semantic validation for each contract against cached stable v0.2.16 SDK |
| Studionet integration | PASS — expanded lifecycle in 282.32s |
| Core deployment | FINALIZED, execution SUCCESS |
| Consumer deployment | FINALIZED, execution SUCCESS |
| Cross-contract allowed path | FINALIZED; executor receipt recorded and permit became `CONSUMED` |
| Composition hazard blocked path | FINALIZED; action 2 `BLOCKED`, rule `1:1`; executor attempt failed as expected |
| Fresh-session control path | FINALIZED; action 3 `ALLOWED` with `EXTERNAL_TRANSMIT` mask 16 |

## Finalized transaction evidence

Full hashes are recorded in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md). Key evidence:

- core deployment: `0x6237ad5ff26f967af3df45dd4dd0316d583054fa1a57f106edb0827053e7570d`;
- consumer deployment: `0xf2e1ce9daf8e7152e51eb2f76f17924421b524badfe12fc61a2485e203942afc`;
- sensitive read allowed: `0x86b288bd4edef10dd80370c9c421098cf8f85fd41497867a8c9a36d7c7f4a533`;
- allowed permit executed: `0x9420490e2dbc440f913ce62af49413b86f1aa8c9bf305a5dbd80564930cdf569`;
- same-session external send blocked: `0xaf475ff0869c86ea3935ab1c8c198f379685eb227809f5cf090eefc672566911`;
- blocked execution rejected: `0x73402367d369865f67bb4899c65ad4302b85e57d428142c22ecf01be32d8414a`;
- fresh-session public send allowed: `0xf9ad18caa21c9b1a6c3945a3b2457e1a23ddd02475f82368e080895cc21a43e8`.

Deployed source commit: `1f900b3bc8ce44f89bf2163aaf3c6ec7c8a6db61`.
Official CLI source retrieval produced exact SHA-256 matches for both contracts.

## Explicit limitations

CHAINHAZARD does not prove that an external side effect occurred, discover actions omitted from the session, or safely declassify accumulated semantic effects. Its guarantee is narrower: policy-relevant action semantics are consensus-bound before deterministic sequence rules issue a reusable permit.
