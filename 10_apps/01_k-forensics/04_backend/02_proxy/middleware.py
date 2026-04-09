"""Reverse proxy — forwards unmatched requests to the tennetctl backend.

Uses httpx.AsyncClient with connection pooling. Strips CORS headers from
upstream responses so only the gateway sets CORS policy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
from fastapi import Request
from fastapi.responses import StreamingResponse

if TYPE_CHECKING:
    from fastapi import FastAPI

STRIP_RESPONSE_HEADERS = {
    "access-control-allow-origin",
    "access-control-allow-methods",
    "access-control-allow-headers",
    "access-control-allow-credentials",
    "access-control-expose-headers",
    "access-control-max-age",
    "transfer-encoding",
}

STRIP_REQUEST_HEADERS = {
    "host",
}


async def proxy_request(request: Request) -> StreamingResponse:
    """Catch-all proxy handler. Forwards to tennetctl backend."""
    client: httpx.AsyncClient = request.app.state.proxy_client
    upstream_url: str = request.app.state.upstream_url

    url = f"{upstream_url}{request.url.path}"
    if request.url.query:
        url = f"{url}?{request.url.query}"

    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in STRIP_REQUEST_HEADERS
    }

    body = await request.body()

    upstream = await client.request(
        method=request.method,
        url=url,
        headers=headers,
        content=body if body else None,
        timeout=60.0,
    )

    response_headers = {
        k: v
        for k, v in upstream.headers.items()
        if k.lower() not in STRIP_RESPONSE_HEADERS
    }

    return StreamingResponse(
        content=iter([upstream.content]),
        status_code=upstream.status_code,
        headers=response_headers,
    )


def mount_proxy(app: "FastAPI") -> None:
    """Mount the catch-all proxy as the lowest-priority route."""
    app.add_api_route(
        "/{path:path}",
        proxy_request,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        include_in_schema=False,
    )
