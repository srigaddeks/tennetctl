"""Pydantic schemas for flows sub-feature."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# Type unions
FlowStatus = Literal["draft", "published", "archived"]
EdgeKind = Literal["next", "success", "failure", "true_branch", "false_branch"]
PortType = Literal[
    "any", "string", "number", "boolean", "object", "array", "uuid", "datetime", "binary", "error"
]


# ── Request/Response schemas ────────────────────────────────────────


class FlowCreate(BaseModel):
    """Create a new flow."""
    slug: str
    name: str
    description: str | None = None
    nodes: list["NodeInstanceIn"] = Field(default_factory=list)
    edges: list["EdgeIn"] = Field(default_factory=list)


class FlowUpdate(BaseModel):
    """Patch a flow (rename, archive, publish)."""
    name: str | None = None
    description: str | None = None
    status: FlowStatus | None = None
    publish_version_id: str | None = None  # Publish a specific version


class FlowResponse(BaseModel):
    """Flow response model."""
    id: str
    org_id: str
    workspace_id: str
    slug: str
    name: str
    description: str | None
    current_version_id: str | None
    status: FlowStatus
    current_version_number: int | None = None
    node_count: int = 0
    edge_count: int = 0
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class FlowVersionResponse(BaseModel):
    """Flow version with full DAG details."""
    id: str
    flow_id: str
    flow_slug: str
    flow_name: str
    version_number: int
    status: FlowStatus
    dag_hash: str | None = None
    published_at: datetime | None = None
    published_by_user_id: str | None = None
    nodes: list["NodeInstanceOut"] = Field(default_factory=list)
    edges: list["EdgeOut"] = Field(default_factory=list)
    created_at: datetime
    deleted_at: datetime | None = None


class NodeInstanceIn(BaseModel):
    """Node instance input (for creation/update)."""
    instance_label: str
    node_key: str
    config: dict[str, Any] = Field(default_factory=dict)
    position: dict[str, int] | None = None  # {x, y}


class NodeInstanceOut(BaseModel):
    """Node instance output (with resolved ports)."""
    id: str
    instance_label: str
    node_key: str
    config: dict[str, Any]
    position: dict[str, int] | None = None
    inputs: list["PortOut"] = Field(default_factory=list)
    outputs: list["PortOut"] = Field(default_factory=list)


class PortOut(BaseModel):
    """Resolved input or output port."""
    key: str
    type: PortType
    description: str = ""


class EdgeIn(BaseModel):
    """Edge input (node labels or IDs)."""
    from_instance_label: str | None = None  # For creation
    from_node_id: str | None = None  # For existing edges
    from_port: str
    to_instance_label: str | None = None  # For creation
    to_node_id: str | None = None  # For existing edges
    to_port: str
    kind: EdgeKind


class EdgeOut(BaseModel):
    """Edge output (resolved node and port info)."""
    id: str
    from_node_id: str
    from_port_key: str
    to_node_id: str
    to_port_key: str
    kind: EdgeKind


class DagValidationErrorOut(BaseModel):
    """DAG validation error details."""
    code: str  # e.g., "DAG_CYCLE", "UNKNOWN_PORT", "PORT_TYPE_MISMATCH"
    node_id: str | None = None
    node_label: str | None = None
    port: str | None = None
    details: str = ""


class DagValidationOut(BaseModel):
    """DAG validation result."""
    ok: bool
    errors: list[DagValidationErrorOut] = Field(default_factory=list)


# Update forward refs
FlowCreate.model_rebuild()
NodeInstanceIn.model_rebuild()
EdgeIn.model_rebuild()
FlowVersionResponse.model_rebuild()
NodeInstanceOut.model_rebuild()
PortOut.model_rebuild()
EdgeOut.model_rebuild()
