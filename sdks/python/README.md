# tennetctl (Python SDK)

Thin Python client for the TennetCTL API. Zero dependencies beyond `httpx`.

## Feature flags

```python
from tennetctl.flags import Client

with Client("http://localhost:51734", api_key="nk_...", environment="prod") as flags:
    if flags.evaluate("new_checkout_flow", user_id="u-123", org_id="o-456"):
        # rollout active for this user
        ...

    variant = flags.evaluate("homepage_variant", user_id="u-123", default="control")

    all_flags = flags.evaluate_bulk(
        ["a", "b", "c"], user_id="u-123", org_id="o-456"
    )
```

Async:

```python
from tennetctl.flags import AsyncClient

async with AsyncClient("http://localhost:51734") as flags:
    is_on = await flags.evaluate("new_checkout_flow", user_id="u-123")
```

## Cache

The client caches evaluations in-process with a 60s TTL by default. Override via
`cache_ttl_seconds=` on construction. Call `invalidate_cache()` to clear.
