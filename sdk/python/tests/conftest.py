from __future__ import annotations

import httpx
import pytest
import respx

from tennetctl import Tennetctl

BASE_URL = "http://testserver"


@pytest.fixture
def respx_mock():
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as mock:
        yield mock


@pytest.fixture
async def client(respx_mock):
    # Share an httpx client so respx intercepts correctly
    http = httpx.AsyncClient(base_url=BASE_URL, timeout=5.0)
    c = Tennetctl(BASE_URL, api_key="nk_test.secret", client=http)
    try:
        yield c
    finally:
        await c.close()
        await http.aclose()


@pytest.fixture
async def session_client(respx_mock):
    http = httpx.AsyncClient(base_url=BASE_URL, timeout=5.0)
    c = Tennetctl(BASE_URL, client=http)  # no api key — test session-cookie path
    try:
        yield c
    finally:
        await c.close()
        await http.aclose()
