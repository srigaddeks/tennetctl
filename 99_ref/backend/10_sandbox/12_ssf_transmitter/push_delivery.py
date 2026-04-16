from __future__ import annotations

import httpx


async def push_set(
    *,
    receiver_url: str,
    set_jwt: str,
    authorization_header: str | None = None,
) -> tuple[int, str | None]:
    """POST a SET JWT to a receiver endpoint.

    Returns (http_status_code, error_message_or_none).
    A status of 0 indicates a transport-level failure.
    """
    headers = {"Content-Type": "application/secevent+jwt"}
    if authorization_header:
        headers["Authorization"] = authorization_header
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(receiver_url, content=set_jwt, headers=headers)
            return resp.status_code, None if resp.is_success else resp.text
        except httpx.HTTPError as e:
            return 0, str(e)
