# Deployment evidence

This file intentionally contains no fabricated transaction evidence.

## Target

- Network: Studionet
- Chain ID: `61999`
- RPC: `https://studio.genlayer.com/api`

## Final deployment

| Evidence | Value |
|---|---|
| ChainHazard address | `TBD` |
| ChainHazard deployment tx | `TBD` |
| ChainHazard deployment state | `TBD` |
| GuardedExecutor address | `TBD` |
| GuardedExecutor deployment tx | `TBD` |
| GuardedExecutor deployment state | `TBD` |
| Source commit | `TBD` |
| Source parity check | `TBD` |

## Required smoke transactions

Record FINALIZED evidence for all of these before submission:

1. create immutable demo policy;
2. open Session A;
3. allow `SENSITIVE_ACCESS` action;
4. prove GuardedExecutor consumes that allowed permit;
5. propose `EXTERNAL_TRANSMIT` in the same session;
6. prove the action is `BLOCKED` by the directional rule;
7. prove GuardedExecutor cannot execute that blocked action;
8. open Session B with no sensitive history;
9. prove an ordinary external-public transmission is `ALLOWED`;
10. record all action/session reads after finalization.

## Never write "final" for ACCEPTED

Submission evidence must distinguish transaction lifecycle state. Only record a deployment/action as final when the network reports FINALIZED.
