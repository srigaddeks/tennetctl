from __future__ import annotations
import json
import asyncio
from typing import AsyncIterator

async def sse_event(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


async def sse_tool_call_start(tool_name: str, tool_category: str, input_summary: str) -> str:
    return await sse_event("tool_call_start", {
        "tool_name": tool_name,
        "tool_category": tool_category,
        "input_summary": input_summary,
    })


async def sse_tool_call_result(tool_name: str, is_successful: bool, output_summary: str) -> str:
    return await sse_event("tool_call_result", {
        "tool_name": tool_name,
        "is_successful": is_successful,
        "output_summary": output_summary,
    })


async def sse_navigate(
    entity_type: str,
    entity_id: str,
    label: str,
    framework_id: str | None = None,
) -> str:
    return await sse_event("navigate", {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "label": label,
        "framework_id": framework_id,
    })


async def sse_navigate_page(page: str, label: str) -> str:
    return await sse_event("navigate_page", {
        "page": page,
        "label": label,
    })


async def sse_session_named(conversation_id: str, title: str) -> str:
    return await sse_event("session_named", {
        "conversation_id": conversation_id,
        "title": title,
    })


async def sse_form_fill_proposed(fields: dict, explanation: str) -> str:
    return await sse_event("form_fill_proposed", {
        "fields": fields,
        "explanation": explanation,
    })


async def sse_report_queued(
    report_id: str,
    report_type: str,
    title: str | None,
    status: str,
) -> str:
    return await sse_event("report_queued", {
        "report_id": report_id,
        "report_type": report_type,
        "title": title,
        "status": status,
    })


async def stream_mock_response(message_id: str, content: str) -> AsyncIterator[str]:
    """Placeholder streaming — real LangGraph streaming wired in 04_agents."""
    yield await sse_event("message_start", {"message_id": message_id})
    # Stream word by word for now
    words = content.split()
    for i, word in enumerate(words):
        chunk = word + (" " if i < len(words) - 1 else "")
        yield await sse_event("content_delta", {"delta": chunk})
        await asyncio.sleep(0.02)
    yield await sse_event("message_end", {"usage": {"input_tokens": 0, "output_tokens": len(words)}})
