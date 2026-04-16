from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SSEEvent:
    event: str
    data: dict = field(default_factory=dict)

    def encode(self) -> str:
        return f"event: {self.event}\ndata: {json.dumps(self.data)}\n\n"


def run_started(run_id: str, agent_code: str) -> SSEEvent:
    return SSEEvent(event="run_started", data={"run_id": run_id, "agent_code": agent_code})


def node_entered(node: str, step_index: int) -> SSEEvent:
    return SSEEvent(event="node_entered", data={"node": node, "step_index": step_index})


def llm_call_start(node: str, system: str) -> SSEEvent:
    return SSEEvent(event="llm_call_start", data={"node": node, "system": system[:200]})


def llm_call_complete(node: str, tokens: int, duration_ms: int) -> SSEEvent:
    return SSEEvent(event="llm_call_complete", data={"node": node, "tokens": tokens, "duration_ms": duration_ms})


def tool_call_start(node: str, tool: str) -> SSEEvent:
    return SSEEvent(event="tool_call_start", data={"node": node, "tool": tool})


def tool_call_result(node: str, tool: str, duration_ms: int) -> SSEEvent:
    return SSEEvent(event="tool_call_result", data={"node": node, "tool": tool, "duration_ms": duration_ms})


def node_completed(node: str, transition: str, next_node: str | None) -> SSEEvent:
    return SSEEvent(event="node_completed", data={"node": node, "transition": transition, "next": next_node})


def approval_needed(node: str, question: str) -> SSEEvent:
    return SSEEvent(event="approval_needed", data={"node": node, "question": question})


def budget_update(tokens: int, cost_usd: float, pct_tokens: float, pct_cost: float) -> SSEEvent:
    return SSEEvent(event="budget_update", data={
        "tokens": tokens, "cost_usd": cost_usd,
        "pct_tokens": round(pct_tokens, 1), "pct_cost": round(pct_cost, 1),
    })


def run_completed(status: str, total_tokens: int, total_cost_usd: float) -> SSEEvent:
    return SSEEvent(event="run_completed", data={
        "status": status, "total_tokens": total_tokens, "total_cost_usd": total_cost_usd,
    })


def run_failed(status: str, error: str) -> SSEEvent:
    return SSEEvent(event="run_failed", data={"status": status, "error": error})
