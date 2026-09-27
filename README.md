<h1 align="center">CHAINHAZARD</h1>

<p align="center"><b>A stateful GenLayer composition firewall for sequences of individually safe actions.</b></p>

CHAINHAZARD exists for a failure mode ordinary per-action policy checks miss:

> **safe(A) + safe(B) does not necessarily mean safe(A → B).**

An agent may be allowed to read private customer data. The same agent may also be allowed to send public material to an external recipient. The dangerous condition appears only when the second capability follows the first inside the same operational session.

CHAINHAZARD turns that sequence-level risk into deterministic protocol state. GenLayer validators independently classify the **current action only** into a bounded capability taxonomy. The contract then applies immutable directional hazard rules against capabilities already accumulated in the session.

```text
Action A: read private customer record
        |
        | consensus classifies SENSITIVE_ACCESS
        v
session accumulator = SENSITIVE_ACCESS
        |
        v
Action B: send held summary externally
        |
        | consensus classifies EXTERNAL_TRANSMIT
        v
rule: prior SENSITIVE_ACCESS -> new EXTERNAL_TRANSMIT
        |
        v
BLOCKED
```

In a fresh session, `EXTERNAL_TRANSMIT` can be allowed. The hazard exists in the **composition**, not in the isolated action.

## Primitive boundary

CHAINHAZARD is intentionally **contract-only**. There is **no frontend**, dashboard, wallet UX, backend product or application-specific workflow in this repository.

The package contains:

- `contracts/chainhazard.py` — the reusable primitive;
- `contracts/guarded_executor.py` — a minimal second IC proving another contract can consume the permit;
- Direct Mode tests with adversarial validator cases;
- a stable Studionet integration lifecycle;
- deployment and zero-dependency preflight scripts;
- reviewer/security/integration documentation.

If a full product UI is later built around CHAINHAZARD, that product belongs under Projects. This repository should remain a standalone Intelligent Contract submission.

## Network

**Target only:** GenLayer **Studionet**, chain ID **61999**  
**RPC:** `https://studio.genlayer.com/api`

This package intentionally contains no alternate preview-network configuration.

## Current package status

**Finalized on Studionet.** The canonical core contract is
`0x64DbC1429Cc698a59DA8331e44543c04c32cF0c1`; its bound demonstration
consumer is `0x0F9BeEDe80427b93dd83e54b6588071E92a1a1e8`.

Both deployments and the canonical lifecycle are FINALIZED on chain ID 61999.
See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for transaction-level evidence.

## The mechanism

### 1. Immutable directional policy

A policy is created from one or more rules:

```text
PRIOR REQUIRED CAPABILITY      CURRENT ACTION CAPABILITY
--------------------------------------------------------
SENSITIVE_ACCESS          ->   EXTERNAL_TRANSMIT
SECRET_ACCESS             ->   EXTERNAL_TRANSMIT
UNTRUSTED_INPUT           ->   CODE_EXECUTION
CREDENTIAL_USE            ->   PRIVILEGE_CHANGE
FUNDS_ACCESS              ->   DESTINATION_CHANGE
DERIVE_SENSITIVE          ->   PUBLICATION
```

Rules are directional. This matters:

```text
read private data -> send externally      BLOCK
send public data  -> later read privately not the same hazard
```

A policy is immutable after creation. A new rule set requires a new policy.

### 2. Monotonic session accumulator

Each session starts with an empty capability accumulator.

Only an `ALLOWED` action adds its policy-relevant capability bits to the session. A blocked or inconclusive action contributes nothing.

CHAINHAZARD deliberately uses **monotonic conservative accounting**: granting a permit reserves the effect immediately. The primitive does not attempt semantic "untainting" or model-decided declassification. If a caller wants a clean boundary, it opens a new session.

That avoids a dangerous design where an LLM can erase previously established context.

### 3. Consensus classifies only the current action

The classifier never receives authority to decide `ALLOW` or `BLOCK`.

It returns only:

```json
{
  "effect_mask": 16,
  "reason": "the action sends information to an external recipient"
}
```

The terminal decision is deterministic contract code.

### 4. Persistent state is validator-bound

A subtle consensus problem arises because the effect mask becomes future state. It would be unsafe to let the leader choose bits that validators merely consider "close enough".

CHAINHAZARD therefore computes the union of every capability bit actually referenced by the policy and calls it the **policy-relevant mask**.

Validators must independently agree exactly on every policy-relevant bit:

```text
leader_mask    & relevant_mask
==
validator_mask & relevant_mask
```

They may disagree on diagnostic capabilities that the current policy can never use, because those bits are discarded before storage and cannot alter present or future settlement.

This gives the equivalence rule a precise state-safety boundary instead of requiring brittle equality over irrelevant labels.

### 5. One-time downstream permit

An allowed action is bound to:

- `action_id`;
- `session_id`;
- a caller-chosen stable `action_ref`;
- a specific consumer Intelligent Contract address.

A consumer asks:

```python
is_permitted(action_id, session_id, action_ref, consumer_address)
```

The included `GuardedExecutor` demonstrates a typed IC-to-IC `view()` gate. After recording an execution locally, it emits a **finalization-gated** acknowledgement back to CHAINHAZARD, which marks the permit `CONSUMED`.

The consumer is locally idempotent by `action_id` before the acknowledgement is emitted.

## Capability taxonomy

| Bit | Capability | Meaning |
|---:|---|---|
| 1 | `SENSITIVE_ACCESS` | reads/acquires private or confidential information |
| 2 | `SECRET_ACCESS` | reads/acquires credentials, keys, tokens or hidden secrets |
| 4 | `UNTRUSTED_INPUT` | ingests caller-controlled or external input |
| 8 | `DERIVE_SENSITIVE` | transforms or derives material from sensitive input |
| 16 | `EXTERNAL_TRANSMIT` | sends/exposes information outside the trusted boundary |
| 32 | `CODE_EXECUTION` | executes code, scripts or dynamic instructions |
| 64 | `STATE_MUTATION` | mutates persistent state/configuration/resources |
| 128 | `PRIVILEGE_CHANGE` | changes roles, permissions or authorization |
| 256 | `FUNDS_ACCESS` | controls, authorizes or spends value |
| 512 | `DESTINATION_CHANGE` | changes payout/routing/delivery destination |
| 1024 | `CREDENTIAL_USE` | uses a secret/token/signing/authenticated capability |
| 2048 | `DELETE_OR_DESTROY` | irreversibly removes/revokes/destroys something |
| 4096 | `PUBLICATION` | publishes to a broad/public channel |
| 8192 | `TOOL_INVOKE` | invokes an external tool/API/service/sub-agent |
| 16384 | `MODEL_CONTROL` | materially steers another model/agent with instructions |

The taxonomy is intentionally bounded. Builders compose these bits into directional rules instead of asking the LLM to invent a new policy language at settlement time.

## Public API

### Policies

```text
create_policy(name, scope, rule_names, prior_masks, action_masks, rule_reasons) -> policy_id
get_policy(policy_id)
get_rule(policy_id, ordinal)
get_capability_dictionary()
```

### Sessions

```text
open_session(policy_id, context) -> session_id
close_session(session_id)
get_session(session_id)
```

### Actions

```text
propose_action(session_id, action_ref, description, consumer) -> action_id
resolve_action(action_id)
cancel_action(action_id)
consume(action_id)
get_action(action_id)
preview_triggers(session_id, effect_mask)
is_permitted(action_id, expected_session_id, expected_action_ref, expected_consumer)
```

## Action states

```text
PENDING
  |
  +--> ALLOWED ----> CONSUMED
  |
  +--> BLOCKED
  |
  +--> INCONCLUSIVE
  |
  +--> CANCELLED
```

`INCONCLUSIVE` is fail-closed. Malformed model output never becomes permission.

## Why GenLayer is needed

A deterministic contract can easily evaluate a bitmask once someone has produced it. The hard part is mapping a natural-language autonomous action into the bounded effect dimensions without trusting one centralized classifier.

CHAINHAZARD uses GenLayer only where ordinary deterministic logic cannot safely do the job:

1. validators independently interpret the current proposed action;
2. every capability bit capable of influencing policy state must independently agree;
3. deterministic code applies sequence rules, writes state, issues permits and enforces one-time consumption.

The LLM does **not**:

- author policies;
- create hazard rules;
- choose the terminal action status;
- erase accumulated context;
- choose a consumer;
- mark a permit consumed.

## Why this is not a policy gate

A policy gate typically evaluates:

```text
Is action B permitted?
```

CHAINHAZARD evaluates:

```text
Given effects already accumulated by A1, A2, ... An,
would adding action B complete one of the immutable directional hazard patterns?
```

The exact same action can be `ALLOWED` in one session and `BLOCKED` in another because the sessions have different prior semantic effects.

## Reviewer thesis test

The shortest meaningful test is:

1. create `SENSITIVE_ACCESS -> EXTERNAL_TRANSMIT`;
2. open Session A;
3. classify `Read private customer notes` as `SENSITIVE_ACCESS` — **allowed**;
4. classify `Send the held summary externally` as `EXTERNAL_TRANSMIT` — **blocked**;
5. open Session B;
6. run only `Send a public brochure externally` — **allowed**.

That proves the primitive is about composition, not a disguised static classifier.

## Validation commands

### Zero-dependency preflight

```bash
python scripts/preflight.py
```

### Direct Mode

```bash
pip install -r requirements-test.txt
pytest tests/direct/ -v -s
```

### GenVM linter

```bash
pip install -r requirements.txt
genvm-lint check contracts/chainhazard.py
genvm-lint check contracts/guarded_executor.py
```

### Live Studionet integration

```bash
pytest tests/integration/ -v -s --network studionet
```

Measured final results: preflight `154` checks passed; Direct Mode `37` tests
passed; both contracts passed the GenVM linter's three AST checks and semantic
SDK validation; the expanded live Studionet lifecycle passed in `282.32s`.

## Deployment

Core primitive:

```bash
python scripts/deploy_studionet.py
```

After recording the finalized CHAINHAZARD address:

```bash
python scripts/deploy_consumer_studionet.py <CHAINHAZARD_ADDRESS>
```

The deployment scripts use the active/unlocked GenLayer CLI account and never read or print a private key.

Canonical deployment and proof evidence is recorded in
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) and [`SUBMISSION.md`](SUBMISSION.md).

## Repository layout

```text
.
├── contracts/
│   ├── chainhazard.py
│   └── guarded_executor.py
├── tests/
│   ├── direct/
│   │   └── test_chainhazard.py
│   └── integration/
│       └── test_chainhazard_studionet.py
├── scripts/
│   ├── deploy_studionet.py
│   ├── deploy_consumer_studionet.py
│   ├── preflight.py
│   └── run_quality.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CONSENSUS.md
│   ├── DEPLOYMENT.md
│   ├── INTEGRATION.md
│   ├── NETWORK.md
│   ├── REVIEWER_WALKTHROUGH.md
│   └── SECURITY.md
├── HANDOFF_TO_LOLA.md
├── SUBMISSION.md
├── gltest.config.yaml
├── requirements-test.txt
├── requirements.txt
└── LICENSE
```

## Non-goals

CHAINHAZARD does not claim to:

- prove that an external action actually occurred;
- reverse arbitrary internet side effects;
- infer hidden actions omitted from the session;
- provide perfect information-flow control for arbitrary programs;
- sanitize prompt injection;
- replace authorization, identity or dispute-resolution systems;
- safely clear/declassify accumulated semantic effects inside a session;
- make a malicious validator majority honest.

Its narrower primitive is:

> **Consensus-bind the policy-relevant semantic effects of proposed actions and deterministically prevent forbidden directional compositions across a persistent session.**

## Target repository

[github.com/lolaaa00/chainhazard](https://github.com/lolaaa00/chainhazard)

## Licence

MIT. See [`LICENSE`](LICENSE).
