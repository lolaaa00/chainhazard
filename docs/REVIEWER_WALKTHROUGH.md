# Five-minute reviewer walkthrough

## The one sentence

**CHAINHAZARD blocks dangerous action sequences that no per-action policy check can detect because each individual action can be safe in isolation.**

## Read these first

1. `contracts/chainhazard.py`
2. `tests/direct/test_chainhazard.py`
3. `docs/CONSENSUS.md`
4. `docs/SECURITY.md`
5. `docs/DEPLOYMENT.md` after live evidence is filled in

## The thesis test

Policy:

```text
prior SENSITIVE_ACCESS -> current EXTERNAL_TRANSMIT
```

Session A:

```text
Read private account record   -> ALLOWED
Send held summary externally  -> BLOCKED
```

Fresh Session B:

```text
Send public brochure externally -> ALLOWED
```

If the third result is also blocked, the implementation is merely a static external-send policy gate and has failed its own thesis.

## Consensus property to inspect

Search for:

```python
(leader_mask & relevant_mask) != (own_mask & relevant_mask)
```

That is what prevents a leader from deciding the future semantic accumulator by itself.

Then inspect the direct-mode regressions:

- policy-relevant disagreement is rejected;
- irrelevant diagnostic disagreement is accepted because it is discarded;
- blocked actions do not contaminate the accumulator;
- sequence order changes the result;
- malformed LLM output is inconclusive, never allowed.
