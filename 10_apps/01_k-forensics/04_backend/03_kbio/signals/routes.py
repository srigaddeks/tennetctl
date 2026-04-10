"""kbio signal catalog routes."""
from __future__ import annotations
import importlib
from fastapi import APIRouter, Query
from .service import list_signals, get_signal

_resp = importlib.import_module("01_core.response")

router = APIRouter(prefix="/v1/kbio/signals", tags=["kbio-signals"])


@router.get("")
async def list_signals_route(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    category: str | None = Query(None),
    tag: str | None = Query(None),
):
    result = await list_signals(limit=limit, offset=offset, category=category, tag=tag)
    return _resp.success_list_response(
        [item.model_dump() for item in result.items],
        total=result.total, limit=result.limit, offset=result.offset,
    )


@router.get("/{code}")
async def get_signal_route(code: str):
    result = await get_signal(code)
    return _resp.success_response(result.model_dump())
