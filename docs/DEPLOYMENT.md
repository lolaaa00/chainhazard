# Deployment evidence

All transaction states below were checked after finalization on 2026-09-27.

## Target

- Network: Studionet
- Chain ID: `61999`
- RPC: `https://studio.genlayer.com/api`

## Final deployment

| Evidence | Value |
|---|---|
| ChainHazard address | `0x64DbC1429Cc698a59DA8331e44543c04c32cF0c1` |
| ChainHazard deployment tx | `0x6237ad5ff26f967af3df45dd4dd0316d583054fa1a57f106edb0827053e7570d` |
| ChainHazard deployment state | `FINALIZED`, `MAJORITY_AGREE`, execution `SUCCESS` |
| GuardedExecutor address | `0x0F9BeEDe80427b93dd83e54b6588071E92a1a1e8` |
| GuardedExecutor deployment tx | `0xf2e1ce9daf8e7152e51eb2f76f17924421b524badfe12fc61a2485e203942afc` |
| GuardedExecutor deployment state | `FINALIZED`, `MAJORITY_AGREE`, execution `SUCCESS` |
| Deployed source commit | `1f900b3bc8ce44f89bf2163aaf3c6ec7c8a6db61` |
| Source parity check | official `genlayer code`; exact SHA-256 match after removing the CLI's two display-only trailing newlines |

Source digests:

- `contracts/chainhazard.py`: `e8206d54e4caadbda1f65263ba3142a29a1b8e9cbd36460734bc1b9f216e0eba`
- `contracts/guarded_executor.py`: `462c6b1a85107db1a1e03f11f8b31b177e773eaf48a13fb7cdc1ff6d563d6080`

## Required smoke transactions

| Step | FINALIZED transaction | Verified result |
|---|---|---|
| Create immutable policy | `0x0891a9d3fa74e5307d9d50067ccaec6390eabfe08cc0d3e33962bb9e2a66a6c5` | policy 1 created |
| Open Session A | `0x4aaac1471a53473b03a0e36d266d1a62229b9e87cd455a89184e6e1d19077282` | session 1 open |
| Propose sensitive read | `0xb2c07186aa25797f7efc9658ddb96965122f2a51ed7deee84d22eef0e532401e` | action 1 pending |
| Resolve sensitive read | `0x86b288bd4edef10dd80370c9c421098cf8f85fd41497867a8c9a36d7c7f4a533` | `ALLOWED`, mask 1 (`SENSITIVE_ACCESS`) |
| Execute allowed permit | `0x9420490e2dbc440f913ce62af49413b86f1aa8c9bf305a5dbd80564930cdf569` | executor recorded action; finalized acknowledgement changed core state to `CONSUMED` |
| Propose external send | `0xcea95d810f3d00efbe22d17597557c8e043d727de9d1f241f6c5d9414eaeadca` | action 2 pending in Session A |
| Resolve external send | `0xaf475ff0869c86ea3935ab1c8c198f379685eb227809f5cf090eefc672566911` | `BLOCKED`; triggered rule `1:1`; stored mask 17 |
| Attempt blocked execution | `0x73402367d369865f67bb4899c65ad4302b85e57d428142c22ecf01be32d8414a` | FINALIZED expected execution error; no executor receipt created |
| Open Session B | `0xf49a35153f934e46725fd19811ada668c7f13ba5d10c77447248b6bb45b580d2` | fresh session 2 open |
| Propose public send | `0xbfadbae43453ff3af54a6745098b9cc857f77c13a8cdc33df4de36203e9fe279` | action 3 pending in Session B |
| Resolve public send | `0xf9ad18caa21c9b1a6c3945a3b2457e1a23ddd02475f82368e080895cc21a43e8` | `ALLOWED`, mask 16 (`EXTERNAL_TRANSMIT`) |

## Never write "final" for ACCEPTED

Submission evidence must distinguish transaction lifecycle state. Only record a deployment/action as final when the network reports FINALIZED.

Every transaction in the table above was independently rechecked through the
Studionet explorer API and reported `FINALIZED`.
