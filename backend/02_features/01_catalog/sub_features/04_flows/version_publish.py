"""
Flow version publishing and freezing logic.

- compute_dag_hash: Pure compute hash of DAG state
- freeze_draft: Database transaction to publish a draft version
"""

import hashlib
import json
from typing import Any

from .dag import Edge, NodeInstance


def compute_dag_hash(nodes: list[NodeInstance], edges: list[Edge]) -> str:
    """
    Compute stable SHA256 hash of a DAG state.

    Hash is computed over canonical-sorted JSON of:
    - Nodes: (node_key, instance_label, config_json, position_x, position_y)
    - Edges: (from_node_id, from_port_key, to_node_id, to_port_key, edge_kind)

    Sorted to ensure consistency across re-serialization and dict insertion order.

    Args:
        nodes: List of node instances
        edges: List of edges

    Returns:
        40-character uppercase hex SHA256 digest
    """
    # Canonical node representation (sorted by instance_label for determinism)
    node_data = [
        {
            "node_key": n.node_key,
            "instance_label": n.instance_label,
            "config_json": _canonical_json(n.config_json),
            "position_x": n.position_x,
            "position_y": n.position_y,
        }
        for n in sorted(nodes, key=lambda n: n.instance_label)
    ]

    # Canonical edge representation (sorted by from/to/ports)
    edge_data = [
        {
            "from_node_id": e.from_node_id,
            "from_port_key": e.from_port_key,
            "to_node_id": e.to_node_id,
            "to_port_key": e.to_port_key,
            "edge_kind": e.edge_kind,
        }
        for e in sorted(
            edges,
            key=lambda e: (e.from_node_id, e.from_port_key, e.to_node_id, e.to_port_key)
        )
    ]

    # Combine into canonical JSON
    canonical = {
        "nodes": node_data,
        "edges": edge_data,
    }

    # Hash the JSON
    canonical_json = json.dumps(canonical, sort_keys=True, separators=(',', ':'))
    digest = hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
    return digest.upper()


def _canonical_json(obj: Any) -> str:
    """
    Convert object to canonical JSON string.

    Used within compute_dag_hash to ensure config_json is sorted.
    """
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


async def freeze_draft(
    conn: Any,
    flow_id: str,
    version_id: str,
    user_id: str,
) -> None:
    """
    Publish a draft flow version, atomically creating a new draft.

    Transaction steps (all-or-nothing):
    1. SELECT FOR UPDATE the version (lock)
    2. Assert status_id = 1 (draft)
    3. Compute dag_hash from current nodes/edges
    4. Update version: status=published, published_at=NOW(), published_by_user_id
    5. Copy all dtl_* rows into a new draft version (version_number+1)
    6. Update flow.current_version_id to point at the new draft

    Args:
        conn: asyncpg connection
        flow_id: Flow ID
        version_id: Version ID to publish
        user_id: User publishing the version

    Raises:
        ValueError: if version not found or not in draft status
        asyncpg.Error: on transaction failure
    """
    # Fetch version and lock it
    version = await conn.fetchrow(
        """
        SELECT
            id, flow_id, version_number, status_id
        FROM "01_catalog"."11_fct_flow_versions"
        WHERE id = $1
        FOR UPDATE
        """,
        version_id
    )

    if not version:
        raise ValueError(f"Version {version_id} not found")

    if version["status_id"] != 1:  # 1 = draft
        raise ValueError(f"Version {version_id} is not in draft status")

    # Fetch all nodes and edges for this version
    nodes = await conn.fetch(
        """
        SELECT id, node_key, instance_label, config_json, position_x, position_y
        FROM "01_catalog"."20_dtl_flow_nodes"
        WHERE flow_version_id = $1
        """,
        version_id
    )

    edges = await conn.fetch(
        """
        SELECT
            id, from_node_id, from_port_key, to_node_id, to_port_key, edge_kind_id
        FROM "01_catalog"."21_dtl_flow_edges"
        WHERE flow_version_id = $1
        """,
        version_id
    )

    # Convert to NodeInstance and Edge for hash computation
    # (simplified — in real code, resolve edge_kind_id to string)
    edge_kind_map = {1: "next", 2: "success", 3: "failure", 4: "true_branch", 5: "false_branch"}

    node_instances = [
        NodeInstance(
            id=n["id"],
            instance_label=n["instance_label"],
            node_key=n["node_key"],
            config_json=n["config_json"] or {},
        )
        for n in nodes
    ]

    edge_instances = [
        Edge(
            id=e["id"],
            from_node_id=e["from_node_id"],
            from_port_key=e["from_port_key"],
            to_node_id=e["to_node_id"],
            to_port_key=e["to_port_key"],
            edge_kind=edge_kind_map.get(e["edge_kind_id"], "next"),
        )
        for e in edges
    ]

    # Compute dag_hash
    dag_hash = compute_dag_hash(node_instances, edge_instances)

    # Publish the current version
    await conn.execute(
        """
        UPDATE "01_catalog"."11_fct_flow_versions"
        SET
            status_id = 2,  -- published
            dag_hash = $2,
            published_at = CURRENT_TIMESTAMP,
            published_by_user_id = $3
        WHERE id = $1
        """,
        version_id,
        dag_hash,
        user_id,
    )

    # Create new draft version (version_number + 1)
    from importlib import import_module
    _id = import_module("backend.01_core.id")

    new_version_number = version["version_number"] + 1
    new_version_id = _id.uuid7()

    await conn.execute(
        """
        INSERT INTO "01_catalog"."11_fct_flow_versions"
        (id, flow_id, version_number, status_id, created_at)
        VALUES ($1, $2, $3, 1, CURRENT_TIMESTAMP)
        """,
        new_version_id,
        flow_id,
        new_version_number,
    )

    # Copy nodes to new version
    for node in nodes:
        new_node_id = _id.uuid7()
        await conn.execute(
            """
            INSERT INTO "01_catalog"."20_dtl_flow_nodes"
            (id, flow_version_id, node_key, instance_label, config_json, position_x, position_y, sort_order, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP)
            """,
            new_node_id,
            new_version_id,
            node["node_key"],
            node["instance_label"],
            node["config_json"],
            node["position_x"],
            node["position_y"],
            (await conn.fetchval(
                "SELECT sort_order FROM \"01_catalog\".\"20_dtl_flow_nodes\" WHERE id = $1",
                node["id"]
            )),
        )

    # Map old node IDs to new node IDs for edge copying
    old_to_new_node = {}
    old_nodes = await conn.fetch(
        "SELECT id, instance_label FROM \"01_catalog\".\"20_dtl_flow_nodes\" WHERE flow_version_id = $1",
        version_id
    )
    new_nodes = await conn.fetch(
        "SELECT id, instance_label FROM \"01_catalog\".\"20_dtl_flow_nodes\" WHERE flow_version_id = $1",
        new_version_id
    )

    for old_n, new_n in zip(
        sorted(old_nodes, key=lambda x: x["instance_label"]),
        sorted(new_nodes, key=lambda x: x["instance_label"])
    ):
        old_to_new_node[old_n["id"]] = new_n["id"]

    # Copy edges to new version with remapped node IDs
    for edge in edges:
        new_from_node_id = old_to_new_node.get(edge["from_node_id"])
        new_to_node_id = old_to_new_node.get(edge["to_node_id"])

        if new_from_node_id and new_to_node_id:
            await conn.execute(
                """
                INSERT INTO "01_catalog"."21_dtl_flow_edges"
                (id, flow_version_id, from_node_id, from_port_key, to_node_id, to_port_key, edge_kind_id, sort_order, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP)
                """,
                _id.uuid7(),
                new_version_id,
                new_from_node_id,
                edge["from_port_key"],
                new_to_node_id,
                edge["to_port_key"],
                edge["edge_kind_id"],
                (await conn.fetchval(
                    "SELECT sort_order FROM \"01_catalog\".\"21_dtl_flow_edges\" WHERE id = $1",
                    edge["id"]
                )),
            )

    # Update flow.current_version_id to new draft
    await conn.execute(
        """
        UPDATE "01_catalog"."10_fct_flows"
        SET current_version_id = $2
        WHERE id = $1
        """,
        flow_id,
        new_version_id,
    )
