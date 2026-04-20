"""Flow version publishing and freezing tests."""

import pytest
from backend.02_features.01_catalog.sub_features.04_flows.version_publish import (
    compute_dag_hash,
)
from backend.02_features.01_catalog.sub_features.04_flows.dag import Edge, NodeInstance


def test_dag_hash_stable():
    """Test that dag_hash is stable across re-serialization."""
    nodes = [
        NodeInstance("n1", "auth", "iam.auth_required", {"scope": "read"}),
        NodeInstance("n2", "handler", "core.run_handler", {}),
    ]

    edges = [
        Edge("e1", "n1", "out", "n2", "in", "success"),
    ]

    hash1 = compute_dag_hash(nodes, edges)
    hash2 = compute_dag_hash(nodes, edges)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex digest is 64 chars


def test_dag_hash_changes_on_config_change():
    """Test that hash changes when node config changes."""
    nodes1 = [NodeInstance("n1", "auth", "iam.auth_required", {"scope": "read"})]
    nodes2 = [NodeInstance("n1", "auth", "iam.auth_required", {"scope": "write"})]

    hash1 = compute_dag_hash(nodes1, [])
    hash2 = compute_dag_hash(nodes2, [])

    assert hash1 != hash2


def test_dag_hash_changes_on_edge_change():
    """Test that hash changes when edges change."""
    nodes = [
        NodeInstance("n1", "a", "node.a", {}),
        NodeInstance("n2", "b", "node.b", {}),
        NodeInstance("n3", "c", "node.c", {}),
    ]

    edges1 = [Edge("e1", "n1", "out", "n2", "in", "next")]
    edges2 = [Edge("e1", "n1", "out", "n3", "in", "next")]

    hash1 = compute_dag_hash(nodes, edges1)
    hash2 = compute_dag_hash(nodes, edges2)

    assert hash1 != hash2


def test_dag_hash_independent_of_node_order():
    """Test that hash is independent of node insertion order."""
    nodes_ordered = [
        NodeInstance("n1", "a", "node.a", {}),
        NodeInstance("n2", "b", "node.b", {}),
        NodeInstance("n3", "c", "node.c", {}),
    ]

    nodes_reversed = [
        NodeInstance("n3", "c", "node.c", {}),
        NodeInstance("n1", "a", "node.a", {}),
        NodeInstance("n2", "b", "node.b", {}),
    ]

    edges = [
        Edge("e1", "n1", "out", "n2", "in", "next"),
        Edge("e2", "n2", "out", "n3", "in", "next"),
    ]

    hash1 = compute_dag_hash(nodes_ordered, edges)
    hash2 = compute_dag_hash(nodes_reversed, edges)

    assert hash1 == hash2


def test_dag_hash_independent_of_edge_order():
    """Test that hash is independent of edge insertion order."""
    nodes = [
        NodeInstance("n1", "a", "node.a", {}),
        NodeInstance("n2", "b", "node.b", {}),
        NodeInstance("n3", "c", "node.c", {}),
    ]

    edges_ordered = [
        Edge("e1", "n1", "out", "n2", "in", "next"),
        Edge("e2", "n2", "out", "n3", "in", "next"),
    ]

    edges_reversed = [
        Edge("e2", "n2", "out", "n3", "in", "next"),
        Edge("e1", "n1", "out", "n2", "in", "next"),
    ]

    hash1 = compute_dag_hash(nodes, edges_ordered)
    hash2 = compute_dag_hash(nodes, edges_reversed)

    assert hash1 == hash2


def test_dag_hash_format():
    """Test that hash is valid SHA256 hex."""
    nodes = [NodeInstance("n1", "test", "test.node", {})]
    hash_value = compute_dag_hash(nodes, [])

    # Should be 64 hex chars
    assert len(hash_value) == 64
    assert all(c in '0123456789ABCDEF' for c in hash_value)


def test_dag_hash_empty():
    """Test hash of empty DAG."""
    hash_value = compute_dag_hash([], [])
    assert len(hash_value) == 64
    # Empty DAG has deterministic hash
    hash_value2 = compute_dag_hash([], [])
    assert hash_value == hash_value2


@pytest.mark.asyncio
async def test_freeze_draft_publishes_version(test_db):
    """Test that freeze_draft publishes a version."""
    from backend.02_features.01_catalog.sub_features.04_flows import repository as repo
    from backend.02_features.01_catalog.sub_features.04_flows.version_publish import freeze_draft

    conn = test_db.conn
    org_id = "org-123"
    workspace_id = "ws-123"
    user_id = "user-123"

    flow, version = await repo.create_flow(
        conn, org_id, workspace_id, "test-freeze", "Test Freeze", None, user_id
    )

    # Freeze the draft
    await freeze_draft(conn, flow["id"], version["id"], user_id)

    # Check that version is now published
    updated_version = await conn.fetchrow(
        'SELECT status_id, dag_hash, published_at FROM "01_catalog"."11_fct_flow_versions" WHERE id = $1',
        version["id"],
    )

    assert updated_version["status_id"] == 2  # published
    assert updated_version["dag_hash"] is not None
    assert updated_version["published_at"] is not None


@pytest.mark.asyncio
async def test_freeze_draft_creates_new_draft(test_db):
    """Test that freeze_draft creates a new draft version."""
    from backend.02_features.01_catalog.sub_features.04_flows import repository as repo
    from backend.02_features.01_catalog.sub_features.04_flows.version_publish import freeze_draft

    conn = test_db.conn
    org_id = "org-123"
    workspace_id = "ws-123"
    user_id = "user-123"

    flow, version1 = await repo.create_flow(
        conn, org_id, workspace_id, "test-new-draft", "Test", None, user_id
    )

    # Freeze v1
    await freeze_draft(conn, flow["id"], version1["id"], user_id)

    # Check that new draft v2 was created
    version2 = await conn.fetchrow(
        'SELECT id, version_number, status_id FROM "01_catalog"."11_fct_flow_versions" WHERE flow_id = $1 AND version_number = 2',
        flow["id"],
    )

    assert version2 is not None
    assert version2["version_number"] == 2
    assert version2["status_id"] == 1  # draft


@pytest.mark.asyncio
async def test_freeze_draft_updates_current_version(test_db):
    """Test that freeze_draft updates flow.current_version_id."""
    from backend.02_features.01_catalog.sub_features.04_flows import repository as repo
    from backend.02_features.01_catalog.sub_features.04_flows.version_publish import freeze_draft

    conn = test_db.conn
    org_id = "org-123"
    workspace_id = "ws-123"
    user_id = "user-123"

    flow, version1 = await repo.create_flow(
        conn, org_id, workspace_id, "test-current", "Test", None, user_id
    )

    old_current = flow["current_version_id"]

    await freeze_draft(conn, flow["id"], version1["id"], user_id)

    # Check that flow.current_version_id changed
    updated_flow = await conn.fetchrow(
        'SELECT current_version_id FROM "01_catalog"."10_fct_flows" WHERE id = $1',
        flow["id"],
    )

    assert updated_flow["current_version_id"] != old_current


@pytest.mark.asyncio
async def test_freeze_draft_rejects_published_version(test_db):
    """Test that freeze_draft rejects already-published versions."""
    from backend.02_features.01_catalog.sub_features.04_flows import repository as repo
    from backend.02_features.01_catalog.sub_features.04_flows.version_publish import freeze_draft

    conn = test_db.conn
    org_id = "org-123"
    workspace_id = "ws-123"
    user_id = "user-123"

    flow, version = await repo.create_flow(
        conn, org_id, workspace_id, "test-reject", "Test", None, user_id
    )

    # Mark as published
    await conn.execute(
        'UPDATE "01_catalog"."11_fct_flow_versions" SET status_id = 2 WHERE id = $1',
        version["id"],
    )

    # Try to freeze again
    with pytest.raises(ValueError, match="not in draft status"):
        await freeze_draft(conn, flow["id"], version["id"], user_id)
