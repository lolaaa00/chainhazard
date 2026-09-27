# Deployment evidence

All transaction states below were checked after finalization on 2026-09-27.

## Target

- Network: Studionet
- Chain ID: `61999`
- RPC: `https://studio.genlayer.com/api`

## Final deployment

| Evidence | Value |
|---|---|
| ChainHazard address | `0x836226b0BC083384fee8F483C82Fa44605FE5f91` |
| ChainHazard deployment tx | `0x5ce1c754ef5c5c0f3e3ce712e788068f404d751f8b44e3fc13b567c332eeae6d` |
| ChainHazard deployment state | `FINALIZED`, `MAJORITY_AGREE`, execution `SUCCESS` |
| GuardedExecutor address | `0x7AeD4D7F069A1247e14296aC89B75EdD1A5B0Ac7` |
| GuardedExecutor deployment tx | `0x1e543d71a4d7de574a0bd486138e0c26104f7337a59b4f402d2144ff2c317368` |
| GuardedExecutor deployment state | `FINALIZED`, `MAJORITY_AGREE`, execution `SUCCESS` |
| Deployed source commit | `617c02bcc03f9ee86aadf18d7d8327d8c8ca6525` |
| Source parity check | RPC deployment payload; exact byte-for-byte SHA-256 match |

Source digests:

- `contracts/chainhazard.py`: `427c1c5855c3f22c694ac6fcc2249eb4464662b74c0cedfefc83bd277260a647`
- `contracts/guarded_executor.py`: `5525912c0c711510a5766b306d9b56db2a32921b3786706b5efbd07dc27ccd07`

## Required smoke transactions

| Step | FINALIZED transaction | Verified result |
|---|---|---|
| Create immutable policy | `0xbbb09841a624447341c0d8fc59c7a24dad94dbf0b2401e8ade145dc7ce12a27a` | policy 1 created |
| Open Session A | `0x146c7c549066ae8803d8d31675617c8bf7d3515dd743b69f4283a3bf632d2198` | session 1 open |
| Propose sensitive read | `0xe40c9ee253a6cf71dac2a5ca8d71759a8f0c9df5efeef92f976e1eb0060a39e5` | action 1 pending |
| Resolve sensitive read | `0x481b50e05f58835b0a7e9f7aaee7e6b17f4a2bee8477b0e7b7fee913bfd922af` | `ALLOWED`, mask 1 (`SENSITIVE_ACCESS`) |
| Execute allowed permit | `0xf92cbce2d844755d76eb54779d36af5f2dcafe18722e249ff3c3772483694950` | executor recorded action; finalized acknowledgement changed core state to `CONSUMED` |
| Propose same-session public test marker | `0x3d38aab2eaf9ccfe774c0a9412d81bb71f75aba4989b13a51b09d61f5caba606` | action 3 pending in Session A |
| Resolve same-session public test marker | `0x4e85eb844edfbf2d3624b19baecb39d98ddf5532b72164dacda573ed387f94e1` | `BLOCKED`; mask 16 (`EXTERNAL_TRANSMIT`); triggered rule `1:1` |
| Attempt blocked execution | `0x0042d1e2d33808177506c39faf165e1a9ff1ce3b2400e0e5c33153979d26ef68` | FINALIZED expected execution error; no executor receipt created |
| Open Session B | `0xaa8107f9bf0e84d2e09349afaefc6f08743b7c85e33af5f1aeb00150c7812d64` | fresh session 2 open |
| Propose fresh-session public test marker | `0x43ae451797549c4067b40790615c7ffcaeeb0b064507dffa0c105386c8340396` | action 4 pending in Session B |
| Resolve fresh-session public test marker | `0xecc556ce2dd9d27f4e1cc991e20688bcd2e3a386e1cb505a9167446fefaccd67` | `ALLOWED`, mask includes 16 (`EXTERNAL_TRANSMIT`) |

## Never write "final" for ACCEPTED

Submission evidence must distinguish transaction lifecycle state. Only record a deployment/action as final when the network reports FINALIZED.

Every transaction in the table above was independently rechecked through the
Studionet explorer API and reported `FINALIZED`.

## Informational tooling notes

- `genvm-linter==0.11.0` defaulted to the latest cached v0.6.0 release-candidate
  archive, which does not contain the contract's pinned stable SDK hash. The
  semantic checks were therefore run with `GENVMROOT` pointed at the cached
  stable v0.2.16 SDK; both contracts passed. This was a linter artifact-selection
  issue, not a contract diagnostic.
- GenLayer CLI 0.39.1 printed a deprecation notice for its internal
  `initializeConsensusSmartContract()` call. Deployment and receipt retrieval
  still completed successfully.
- The CLI encountered transient Studionet gateway timeouts while polling some
  receipts. No transaction was resubmitted blindly; each recorded hash was
  independently queried and confirmed `FINALIZED`.
- A separate `gltest` fresh-deployment attempt finalized as `NO_MAJORITY` before
  any lifecycle call. The canonical pair above was therefore exercised directly
  with the deploying owner; every transaction recorded in the table finalized.
