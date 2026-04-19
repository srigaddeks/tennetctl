# tennetctl

Unified Python SDK for the [TennetCTL](https://github.com/) platform. One client covers auth, feature flags, IAM, audit, notify, metrics, logs, traces, vault, and catalog inspection.

**Status:** early preview. This release ships the SDK core + `client.auth` module. Flags / iam / audit / notify modules land in the next phase.

## Install

```bash
pip install -e sdk/python     # from the tennetctl repo root
# or: pip install tennetctl   # once published
```

Requires Python ≥3.10.

## Quickstart

```python
import asyncio
from tennetctl import Tennetctl

async def main():
    async with Tennetctl("http://localhost:51734") as client:
        # Signin (stores session cookie on the client)
        await client.auth.signin(email="admin@example.com", password="hunter2")

        # Read current user
        me = await client.auth.me()
        print(me["email"])

        # Create an API key (shown exactly once)
        key = await client.auth.api_keys.create(name="ci", scopes=["audit:read"])
        print("Token:", key["token"])

        # List + revoke sessions
        sessions = await client.auth.sessions.list()
        for s in sessions:
            print(s["id"], s["user_agent"])

        await client.auth.signout()

asyncio.run(main())
```

Or use an API key directly:

```python
client = Tennetctl("http://localhost:51734", api_key="nk_xxxx.yyyy")
```

## Features

| Module | Status | Covers |
|---|---|---|
| `client.auth` | ✅ 28-01 | signin / signout / me / signup / sessions / api_keys |
| `client.flags` | ⏳ 29-01 | evaluate / evaluate_bulk (with SWR cache) |
| `client.iam` | ⏳ 29-01 | users / orgs / workspaces / roles (read-only) |
| `client.audit` | ⏳ 29-01 | emit / query |
| `client.notify` | ⏳ 29-01 | send transactional |
| `client.metrics` | ⏳ v0.2.2 | increment / observe / gauge |
| `client.logs` | ⏳ v0.2.2 | emit structured log |
| `client.traces` | ⏳ v0.2.2 | start_span / autoinstrument |
| `client.vault` | ⏳ v0.2.3 | get_secret |
| `client.catalog` | ⏳ v0.2.3 | list_features / list_nodes / get_flow |

## Errors

Every typed error descends from `TennetctlError`:

```python
from tennetctl import AuthError, RateLimitError, NetworkError, TennetctlError

try:
    await client.auth.signin(email="...", password="wrong")
except AuthError as e:
    print(e.code, e.status, e.message)
```

## License

AGPL-3.0-or-later. See repo root for details.
