"""Service layer: business logic for flows."""

from importlib import import_module
from typing import Any

from . import repository as repo
from .dag import DagValidation, DagValidationError, Edge, NodeInstance, validate_dag
from .port_resolver import is_compatible, resolve_ports
from .schemas import FlowCreate, FlowUpdate
from .version_publish import freeze_draft as freeze_draft_tx

_id = import_module("backend.01_core.id")
_resp = import_module("backend.01_core.response")
_audit = import_module("backend.02_features.04_audit.sub_features.01_events.service")


async def create_flow(
    conn: Any,
    org_id: str,
    workspace_id: str,
    body: FlowCreate,
    user_id: str,
    session_id: str,
) -> dict[str, Any]:
    """
    Create a flow with initial DAG.

    Validates DAG before persisting. Returns flow + version.
    """
    # Create flow and version
    flow, version = await repo.create_flow(
        conn, org_id, workspace_id, body.slug, body.name, body.description, user_id
    )

    # If DAG provided, populate it
    if body.nodes or body.edges:
        await _populate_version_dag(
            conn, version["id"], org_id, workspace_id, body.nodes, body.edges, user_id
        )

    # Emit audit
    await _audit.emit_audit(
        conn,
        category="product",
        event_key="flows.created",
        user_id=user_id,
        session_id=session_id,
        org_id=org_id,
        workspace_id=workspace_id,
        target_id=flow["id"],
        metadata={"slug": body.slug, "name": body.name},
    )

    return {"flow": flow, "version": version}


async def update_flow(
    conn: Any,
    flow_id: str,
    org_id: str,
    workspace_id: str,
    body: FlowUpdate,
    user_id: str,
    session_id: str,
) -> dict[str, Any]:
    """
    Update a flow: rename, change status, or publish version.

    PATCH handles all state changes per CLAUDE.md simplicity rules.
    """
    flow = await repo.get_flow(conn, flow_id)
    if not flow:
        raise ValueError(f"Flow {flow_id} not found")

    # Handle publish (delegates to version_publish.freeze_draft)
    if body.publish_version_id:
        await freeze_draft_tx(conn, flow_id, body.publish_version_id, user_id)

        # Fetch updated flow
        flow = await repo.get_flow(conn, flow_id)

        await _audit.emit_audit(
            conn,
            category="product",
            event_key="flows.published",
            user_id=user_id,
            session_id=session_id,
            org_id=org_id,
            workspace_id=workspace_id,
            target_id=flow_id,
            metadata={"version_id": body.publish_version_id},
        )

        return {"flow": flow}

    # Handle rename
    if body.name is not None:
        await conn.execute(
            """
            UPDATE "01_catalog"."10_fct_flows"
            SET name = $2, updated_by = $3, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            """,
            flow_id, body.name, user_id,
        )

        await _audit.emit_audit(
            conn,
            category="product",
            event_key="flows.renamed",
            user_id=user_id,
            session_id=session_id,
            org_id=org_id,
            workspace_id=workspace_id,
            target_id=flow_id,
            metadata={"new_name": body.name},
        )

    # Handle status change
    if body.status is not None:
        status_map = {"draft": 1, "published": 2, "archived": 3}
        status_id = status_map.get(body.status, 1)

        await conn.execute(
            """
            UPDATE "01_catalog"."10_fct_flows"
            SET status_id = $2, updated_by = $3, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            """,
            flow_id, status_id, user_id,
        )

        await _audit.emit_audit(
            conn,
            category="product",
            event_key="flows.status_changed",
            user_id=user_id,
            session_id=session_id,
            org_id=org_id,
            workspace_id=workspace_id,
            target_id=flow_id,
            metadata={"new_status": body.status},
        )

    flow = await repo.get_flow(conn, flow_id)
    return {"flow": flow}


async def replace_version_dag(
    conn: Any,
    flow_id: str,
    version_id: str,
    org_id: str,
    workspace_id: str,
    nodes_in: list[dict[str, Any]],
    edges_in: list[dict[str, Any]],
    user_id: str,
    session_id: str,
) -> dict[str, Any]:
    """
    Replace DAG of a flow version (draft only).

    Validates DAG, resolves ports, checks port compatibility.
    Returns 409 if version is published.
    """
    version = await repo.get_version(conn, version_id)
    if not version:
        raise ValueError(f"Version {version_id} not found")

    # Check status
    if version["status"] != "draft":
        return _resp.error(
            code="VERSION_FROZEN",
            message="Cannot edit published versions",
        )

    # Resolve ports for all nodes and validate
    node_instances = []
    node_configs = {}  # node_key -> config for port resolution

    for node_in in nodes_in:
        node_instances.append(
            NodeInstance(
                id=_id.uuid7(),  # Temp ID for validation
                instance_label=node_in["instance_label"],
                node_key=node_in["node_key"],
                config_json=node_in.get("config_json", {}),
            )
        )
        node_configs[node_in["instance_label"]] = {
            "node_key": node_in["node_key"],
            "input_schema": node_in.get("input_schema", {}),
            "output_schema": node_in.get("output_schema", {}),
        }

    # Build edges with resolved node instances
    edges = []
    errors: list[dict[str, Any]] = []

    for edge_in in edges_in:
        # Resolve node IDs from instance labels
        from_node = next(
            (n for n in node_instances if n.instance_label == edge_in["from_instance_label"]),
            None,
        )
        to_node = next(
            (n for n in node_instances if n.instance_label == edge_in["to_instance_label"]),
            None,
        )

        if not from_node or not to_node:
            errors.append({
                "code": "UNKNOWN_NODE",
                "details": f"Node reference not found",
            })
            continue

        edges.append(
            Edge(
                id=_id.uuid7(),  # Temp ID
                from_node_id=from_node.id,
                from_port_key=edge_in["from_port"],
                to_node_id=to_node.id,
                to_port_key=edge_in["to_port"],
                edge_kind=edge_in["kind"],
            )
        )

        # Validate port compatibility
        from_config = node_configs.get(edge_in["from_instance_label"], {})
        to_config = node_configs.get(edge_in["to_instance_label"], {})

        from_ports = resolve_ports(from_config["node_key"], from_config)
        to_ports = resolve_ports(to_config["node_key"], to_config)

        from_port_type = next(
            (p.type for p in from_ports.outputs if p.key == edge_in["from_port"]),
            None,
        )
        to_port_type = next(
            (p.type for p in to_ports.inputs if p.key == edge_in["to_port"]),
            None,
        )

        if from_port_type is None or to_port_type is None:
            errors.append({
                "code": "UNKNOWN_PORT",
                "node": edge_in["from_instance_label"] if from_port_type is None else edge_in["to_instance_label"],
                "port": edge_in["from_port"] if from_port_type is None else edge_in["to_port"],
            })
            continue

        if not is_compatible(from_port_type, to_port_type):
            errors.append({
                "code": "PORT_TYPE_MISMATCH",
                "from_port": edge_in["from_port"],
                "to_port": edge_in["to_port"],
                "expected": to_port_type,
                "got": from_port_type,
            })

    if errors:
        return _resp.error(
            code="VALIDATION_ERROR",
            message="DAG validation failed",
            details={"errors": errors},
        )

    # Validate DAG structure
    dag_validation = validate_dag(node_instances, edges)
    if not dag_validation.ok:
        return _resp.error(
            code=dag_validation.errors[0].code if dag_validation.errors else "DAG_INVALID",
            message="DAG validation failed",
            details={
                "errors": [
                    {
                        "code": e.code,
                        "node": e.node_label,
                        "details": e.details,
                    }
                    for e in dag_validation.errors
                ]
            },
        )

    # Persist new DAG
    await repo.replace_version_dag(conn, version_id, nodes_in, edges_in)

    # Emit audit
    await _audit.emit_audit(
        conn,
        category="product",
        event_key="flows.dag_updated",
        user_id=user_id,
        session_id=session_id,
        org_id=org_id,
        workspace_id=workspace_id,
        target_id=flow_id,
        metadata={"version_id": version_id, "node_count": len(nodes_in), "edge_count": len(edges_in)},
    )

    version = await repo.get_version(conn, version_id)
    return {"version": version}


async def _populate_version_dag(
    conn: Any,
    version_id: str,
    org_id: str,
    workspace_id: str,
    nodes_in: list[dict[str, Any]],
    edges_in: list[dict[str, Any]],
    user_id: str,
) -> None:
    """Helper: populate version DAG without audit (used during creation)."""
    # Similar validation to replace_version_dag
    node_instances = []
    for node_in in nodes_in:
        node_instances.append(
            NodeInstance(
                id=_id.uuid7(),
                instance_label=node_in["instance_label"],
                node_key=node_in["node_key"],
                config_json=node_in.get("config_json", {}),
            )
        )

    edges = []
    for edge_in in edges_in:
        from_node = next(
            (n for n in node_instances if n.instance_label == edge_in["from_instance_label"]),
            None,
        )
        to_node = next(
            (n for n in node_instances if n.instance_label == edge_in["to_instance_label"]),
            None,
        )

        if from_node and to_node:
            edges.append(
                Edge(
                    id=_id.uuid7(),
                    from_node_id=from_node.id,
                    from_port_key=edge_in["from_port"],
                    to_node_id=to_node.id,
                    to_port_key=edge_in["to_port"],
                    edge_kind=edge_in["kind"],
                )
            )

    # Validate DAG
    dag_validation = validate_dag(node_instances, edges)
    if not dag_validation.ok:
        raise ValueError(f"Invalid DAG: {dag_validation.errors[0].details}")

    # Persist
    await repo.replace_version_dag(conn, version_id, nodes_in, edges_in)
