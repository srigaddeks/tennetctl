# TennetCTL Python SDK — Quickstart

> Status: 28-01 preview. Ships `client.auth` only. Flags + IAM + audit + notify land in 29-01; observability modules in v0.2.2; vault + catalog in v0.2.3.

## Install

From the repo root:

```bash
pip install -e sdk/python
# or, with dev tools for contributing:
pip install -e "sdk/python[dev]"
```

Requires Python ≥3.10.

## 60-second tour

```python
import asyncio
from tennetctl import Tennetctl, AuthError

async def main() -> None:
    async with Tennetctl("http://localhost:51734") as client:
        # 1. Signin — stores session token on the client
        await client.auth.signin(email="admin@example.com", password="hunter2")

        # 2. Read current user
        me = await client.auth.me()
        print(f"Signed in as {me['email']}")

        # 3. Create an API key (token is shown exactly once)
        key = await client.auth.api_keys.create(
            name="local-dev",
            scopes=["audit:read", "flags:read"],
        )
        print(f"New key: {key['token']}  — store it somewhere safe")

        # 4. List and revoke sessions
        for session in await client.auth.sessions.list():
            print(session["id"], session.get("user_agent"))

        # 5. Clean up
        await client.auth.api_keys.revoke(key["id"])
        await client.auth.signout()

asyncio.run(main())
```

## Using an API key instead of a session

```python
client = Tennetctl("http://localhost:51734", api_key="nk_xxxx.yyyy")
```

API keys use `Authorization: Bearer …` on every request. They never expire from the client side (server-side revocation + rotation via `client.auth.api_keys.rotate(id)`).

## Typed errors

Every failure raises a subclass of `TennetctlError`:

| Exception | HTTP status | When |
|---|---|---|
| `AuthError` | 401 / 403 | missing, invalid, expired credentials or scope |
| `ValidationError` | 400 / 422 | request body failed validation |
| `NotFoundError` | 404 | resource not found |
| `ConflictError` | 409 | duplicate, stale write |
| `RateLimitError` | 429 | too many requests |
| `ServerError` | 5xx | backend error after retries |
| `NetworkError` | — | connection / timeout before a response |

```python
from tennetctl import AuthError, RateLimitError

try:
    await client.auth.signin(email="a@b.c", password="wrong")
except AuthError as e:
    print(e.code, e.status, e.message)
except RateLimitError as e:
    print("slow down:", e.message)
```

## Retry policy

Transient errors (`NetworkError` + HTTP `502`/`503`/`504`) retry with exponential backoff: **0.5s, 1s, 2s** (max 3 retries, so up to 4 attempts total). Non-transient 4xx errors never retry.

## Capability preview — coming in 29-01

```python
# Feature flags (with 60s SWR cache per flag/entity)
enabled = await client.flags.evaluate("new-onboarding", entity="user:123")

# Audit events
await client.audit.emit({
    "category": "iam",
    "key": "user.exported_data",
    "outcome": "success",
    "metadata": {"exported_rows": 42},
})

# Transactional notify
await client.notify.send(
    template_key="password_reset",
    recipient_user_id="user:123",
    variables={"reset_link": "…"},
)
```

## Where to report issues

Open an issue against the `tennetctl` repository. For SDK-specific feedback, tag it `area:sdk`.
