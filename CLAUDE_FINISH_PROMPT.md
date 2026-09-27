# Prompt to paste into Claude after unzipping

You are finishing an existing GenLayer standalone Intelligent Contract repository called **CHAINHAZARD**.

The folder I have given you is already the intended codebase. **Do not throw it away and start a different project.** First audit what is present, understand the mechanism, then fix or strengthen anything required for a real submission.

## Hard constraints

- Final repository: `lolaaa00/chainhazard`
- Network: **GenLayer Studionet only**
- Chain ID: **61999**
- RPC: `https://studio.genlayer.com/api`
- No frontend. Do not add Next.js, React, wallet UI, dashboard, backend or Vercel deployment.
- This is a **Standalone GenLayer Intelligent Contract** submission, not a Project.
- Do not switch networks.
- Do not add WalletConnect, browser-wallet logic or server-held keys.
- Never commit a private key, seed phrase, credential or `.env` secret.
- Treat ACCEPTED and FINALIZED as different states. Submission/deployment evidence must use FINALIZED where finality is claimed.

## Product thesis you must preserve

CHAINHAZARD is a **stateful composition firewall for action sequences**.

Its core property is:

> An action can be safe in isolation and unsafe only because of semantic effects already accumulated earlier in the same session.

Canonical example:

```text
Policy rule:
prior SENSITIVE_ACCESS -> current EXTERNAL_TRANSMIT

Session A:
1. Read private customer record -> ALLOWED
2. Send held summary externally -> BLOCKED

Fresh Session B:
1. Send an ordinary public brochure externally -> ALLOWED
```

If your changes turn the contract into a normal static policy classifier where external transmission is always blocked, you have broken the project.

The directional order is intentional. Do not replace it with an unordered pair check.

## Existing architecture to audit, not casually remove

The repository should contain:

- `contracts/chainhazard.py`
- `contracts/guarded_executor.py`
- Direct Mode tests
- Studionet integration lifecycle
- preflight and deployment scripts
- security, consensus, integration and deployment docs
- submission draft

The semantic classifier returns only a bounded capability bitmask for the **current action**. It must never directly choose `ALLOWED` or `BLOCKED`.

The deterministic contract owns:

- policy rules;
- sequence direction;
- session accumulator;
- triggered-rule calculation;
- terminal action state;
- consumer binding;
- one-time permit consumption.

Allowed effects are deliberately accumulated monotonically. Do not introduce an LLM-controlled `clear`, `untaint` or declassification mechanism.

## Consensus property that must survive

The effect mask becomes future shared state. Therefore a leader must not be able to choose policy-relevant bits without validator agreement.

Audit the custom validator and preserve/improve this invariant:

```text
leader policy-relevant effect bits
==
validator policy-relevant effect bits
```

Bits outside the current policy may differ only if they are discarded before storage and cannot affect current or future settlement.

Do not weaken validation into JSON/schema checking.

## Your job

### 1. Audit the source against the actual current stable Studionet runtime

Check syntax and SDK compatibility for the target network. In particular audit:

- dependency header/runtime version;
- storage dataclasses and nested `DynArray` usage;
- `TreeMap` behavior;
- `@gl.public.write` / `@gl.public.view`;
- `@gl.contract_interface`;
- typed IC-to-IC `view()` call;
- finalized `emit()` acknowledgement;
- event syntax;
- `gl.vm.run_nondet_unsafe` leader/validator behavior;
- Direct Mode compatibility and pickling.

If the stable runtime requires a small syntax/API correction, make it. Do not migrate the repository to another network to avoid fixing stable compatibility.

### 2. Run the zero-dependency gate

```bash
python scripts/preflight.py
```

It must pass after your changes.

### 3. Install the committed testing dependencies and run Direct Mode

```bash
pip install -r requirements-test.txt
pytest tests/direct/ -v -s
```

Fix the code or tests until the real contract passes. Do not delete hard tests merely to obtain green output.

Keep high-signal cases covering at least:

- individually safe actions composing into a block;
- sequence order matters;
- several different directional rule pairs;
- blocked action does not alter accumulated state;
- malformed model output fails closed;
- relevant leader/validator disagreement is rejected;
- irrelevant diagnostic disagreement is accepted only because it is discarded;
- one-time bound permit consumption;
- closing a session invalidates unused permits;
- action/state terminality and ownership checks.

Add additional adversarial cases if the audit identifies uncovered state-safety issues.

### 4. Run the GenVM linter

```bash
pip install -r requirements.txt
genvm-lint check contracts/chainhazard.py
genvm-lint check contracts/guarded_executor.py
```

Resolve real contract issues. Record informational warnings honestly instead of pretending they do not exist.

### 5. Audit the cross-contract consumer carefully

`GuardedExecutor` is intentionally tiny. Its purpose is proof of composition, not a product.

It must:

1. ask CHAINHAZARD whether the exact action/session/ref is permitted for the executor's own contract address;
2. reject an invalid permit;
3. reject local replay by `action_id`;
4. record execution locally;
5. acknowledge consumption only after finalization.

Do not add a frontend to demonstrate this.

### 6. Run the live Studionet integration test

Target stable Studionet only:

```bash
pytest tests/integration/ -v -s --network studionet
```

The lifecycle should prove on a fresh deployment:

- policy creation;
- session creation;
- sensitive-read action allowed;
- allowed action consumed by GuardedExecutor;
- later external-send action blocked because of session history;
- GuardedExecutor rejects the blocked action.

If live LLM wording causes unstable capability classification, improve the prompt/equivalence design without weakening the thesis or hardcoding the expected demo result.

### 7. Strengthen anything that could cost reviewer confidence

Look specifically for:

- any leader-controlled field affecting future state without validator binding;
- action-ref replay/collision issues;
- session races;
- permit replay;
- non-canonical input normalization problems;
- model output coercion (`bool` as `int`, float masks, hex masks, unsupported bits);
- mutable policy loopholes;
- overbroad model authority;
- incorrect order handling;
- blocked/inconclusive actions polluting accumulated state;
- session closure edge cases;
- unsafe accepted-vs-finalized message timing;
- claims in docs not supported by actual runtime evidence.

Prefer fail-closed behavior.

### 8. Deploy the final core contract to Studionet

Use the provided stable deployment script or equivalent official CLI command.

Before submitting, explicitly verify the active network reports chain ID `61999`.

Deploy CHAINHAZARD first and wait for FINALIZED.

Record:

- contract address;
- deployment transaction hash;
- final lifecycle state;
- execution result;
- source commit.

Then deploy `GuardedExecutor` with the finalized CHAINHAZARD address and wait for FINALIZED.

### 9. Re-run the canonical live proof against the final deployed addresses

Do not rely only on disposable integration deployments.

On the final canonical deployment, produce reviewer-verifiable transactions for:

1. policy creation;
2. Session A open;
3. `SENSITIVE_ACCESS` action proposal/resolution -> `ALLOWED`;
4. GuardedExecutor successfully uses the allowed permit;
5. `EXTERNAL_TRANSMIT` action in the same session -> `BLOCKED`;
6. GuardedExecutor attempt with blocked action -> rejected;
7. Session B open;
8. external-public action with no prior sensitive state -> `ALLOWED`.

This last control case is important. It proves CHAINHAZARD is not simply an external-transmission denylist.

### 10. Verify deployed-source parity

Use available official CLI/RPC tooling to retrieve or otherwise verify the deployed source against the final repository version.

Record the exact method and digest/commit evidence. Do not claim parity without checking it.

### 11. Finish the documentation from evidence

Update:

- `README.md`
- `docs/DEPLOYMENT.md`
- `SUBMISSION.md`

Replace every `TBD` with real evidence.

Only add badges/test counts after they are actually measured.

The README should remain contract-first and should explain the computer-science primitive before explaining GenLayer implementation details.

Do not add marketing filler.

### 12. Final repository audit

Before pushing:

- no frontend directory;
- no build artefacts or virtualenv;
- no secrets;
- no stale addresses;
- no fake tx hashes;
- no `TBD` in submission-facing docs;
- all links correct for `lolaaa00/chainhazard`;
- all network references point to Studionet chain `61999`;
- tests and documented counts agree;
- canonical deployed source matches the final commit.

### 13. Push only when actually submission-ready

The target repo will be `lolaaa00/chainhazard` after I create it.

Do not push to `ometere123`.

If the repo does not yet exist/remotes are not configured, finish the local code first and tell me exactly what command or repository step I must do. Do not create some substitute repository under a different owner.

## What I want back from you

Return a concise final audit report containing:

- `SUBMISSION READY: YES/NO`
- final commit SHA
- Direct Mode result
- linter result
- Studionet integration result
- CHAINHAZARD address
- GuardedExecutor address
- both deployment tx hashes
- canonical live demo tx hashes
- source-parity evidence
- any remaining limitation or warning

Do not say `YES` while anything material is still outstanding.
