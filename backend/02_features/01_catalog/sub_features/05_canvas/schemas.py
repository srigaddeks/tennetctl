"""Canvas schemas: data models for the render payload."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class CanvasPort(BaseModel):
    """A single input or output port on a node."""
    key: str
    type: str


class CanvasNodePorts(BaseModel):
    """Input and output ports for a node."""
    inputs: list[CanvasPort]
    outputs: list[CanvasPort]
    unresolved: bool = False


class CanvasNode(BaseModel):
    """Node in the canvas DAG."""
    id: str
    instance_label: str
    node_key: str
    kind: Literal["request", "effect", "control"]
    config_json: dict = {}
    position: dict = {}  # {x, y} if set by operator


class CanvasEdge(BaseModel):
    """Edge in the canvas DAG."""
    id: str
    from_node_id: str
    from_port: str
    to_node_id: str
    to_port: str
    kind: Literal["next", "success", "failure", "true_branch", "false_branch"]


class CanvasLayoutEntry(BaseModel):
    """Position and lane for a node."""
    x: int
    y: int
    lane: int


class TraceNodeStatus(BaseModel):
    """Status of a node in a trace."""
    status: Literal["pending", "running", "success", "failure", "skipped", "timed_out"]
    started_at: datetime | None = None
    finished_at: datetime | None = None


class CanvasTrace(BaseModel):
    """Trace overlay information for a flow run."""
    node_status: dict[str, TraceNodeStatus]
    edge_traversed: dict[str, bool]
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total_duration_ms: int | None = None


class CanvasPayload(BaseModel):
    """Complete render payload for the React Flow canvas."""
    nodes: list[CanvasNode]
    edges: list[CanvasEdge]
    ports: dict[str, CanvasNodePorts]
    layout: dict[str, CanvasLayoutEntry]
    trace: CanvasTrace | None = None


class FlowRunSummary(BaseModel):
    """Summary of a flow run for the run picker."""
    id: str
    version_id: str
    started_at: datetime
    finished_at: datetime | None = None
    status: Literal["pending", "running", "success", "failure"]
    total_duration_ms: int | None = None
