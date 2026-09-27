# Handoff to Lola

## What you received

A source package for the proposed repository:

`lolaaa00/chainhazard`

It intentionally has no frontend.

The package is **pre-deployment**. It contains the core Intelligent Contract, a minimal consuming IC, Direct Mode coverage, a Studionet integration lifecycle, deployment scripts and reviewer documentation. It does not invent a contract address or claim tests were run where they were not.

## How to hand it to Claude

1. Unzip the package locally.
2. Create/open the empty `lolaaa00/chainhazard` repository locally when ready.
3. Copy the unzipped contents into that repository root.
4. Open that folder in Claude Code yourself.
5. Paste the handoff prompt supplied by Papito/ChatGPT into Claude.
6. Let the agent inspect and finish the existing codebase. It must not replace the concept with a different project.

## Non-negotiable target

- GenLayer Studionet only
- chain ID `61999`
- RPC `https://studio.genlayer.com/api`
- no frontend
- standalone Intelligent Contract category
- final GitHub destination: `lolaaa00/chainhazard`

## Required finish line

The agent must not say "done" merely because source files exist. It should only return submission-ready after:

- preflight passes;
- Direct Mode passes;
- GenVM linter passes or any runtime/tooling limitation is explicitly documented;
- integration lifecycle passes on Studionet;
- core and consumer are actually deployed;
- deployment transactions are FINALIZED;
- source parity is checked against deployed code if the CLI supports it;
- `docs/DEPLOYMENT.md` contains real addresses and tx hashes;
- `SUBMISSION.md` contains no unresolved evidence placeholders;
- README badges/counts, if added, match actual evidence;
- there are no references to any other network;
- no private keys or secrets are committed.
