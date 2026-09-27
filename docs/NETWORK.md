# Network target

This package targets one environment only:

| Field | Value |
|---|---|
| Network | Studionet |
| Chain ID | `61999` |
| RPC | `https://studio.genlayer.com/api` |
| Studio | `https://studio.genlayer.com` |

The deployment scripts pass the RPC explicitly so they do not depend on whichever default network happens to be configured in the CLI.

Before deployment, Lola's agent must run:

```bash
genlayer network info
```

and independently confirm the target is Studionet / chain `61999`.

If that check does not match, stop. Do not deploy and do not "fix" the package by switching networks.
