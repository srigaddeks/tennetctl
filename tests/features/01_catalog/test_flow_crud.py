"""CRUD tests for flows sub-feature."""

import pytest
from backend.02_features.01_catalog.sub_features.04_flows import repository as repo
from backend.02_features.01_catalog.sub_features.04_flows.schemas import FlowCreate


@pytest.mark.asyncio
async def test_create_flow_and_fetch(test_db):
    """Test creating and fetching a flow."""
    conn = test_db.conn
    org_id = "org-123"
    workspace_id = "ws-123"
    user_id = "user-123"

    flow, version = await repo.create_flow(
        conn,
        org_id,
        workspace_id,
        "public-api",
        "Public API Preset",
        "Example flow",
        user_id,
    )

    assert flow["slug"] == "public-api"
    assert flow["name"] == "Public API Preset"
    assert flow["status"] == "draft"
    assert flow["current_version_id"] == version["id"]
    assert version["version_number"] == 1
    assert version["status"] == "draft"


@pytest.mark.asyncio
async def test_slug_uniqueness_within_org(test_db):
    """Test that slug must be unique within org (soft-delete ignored)."""
    conn = test_db.conn
    org_id = "org-123"
    workspace_id = "ws-123"
    user_id = "user-123"

    # Create first flow
    flow1, _ = await repo.create_flow(
        conn, org_id, workspace_id, "my-flow", "Flow 1", None, user_id
    )

    # Try to create second with same slug — should fail
    with pytest.raises(Exception):  # UNIQUE constraint violation
        await repo.create_flow(
            conn, org_id, workspace_id, "my-flow", "Flow 2", None, user_id
        )


@pytest.mark.asyncio
async def test_soft_delete_semantics(test_db):
    """Test soft-delete: deleted_at set, undeleted rows visible in list."""
    conn = test_db.conn
    org_id = "org-123"
    workspace_id = "ws-123"
    user_id = "user-123"

    flow, _ = await repo.create_flow(
        conn, org_id, workspace_id, "flow-del", "Delete Test", None, user_id
    )

    # List should show the flow
    flows = await repo.list_flows(conn, org_id)
    assert len(flows) >= 1
    assert any(f["id"] == flow["id"] for f in flows)

    # Delete it
    await repo.soft_delete(conn, flow["id"], user_id)

    # List should not show it
    flows = await repo.list_flows(conn, org_id)
    assert not any(f["id"] == flow["id"] for f in flows)


@pytest.mark.asyncio
async def test_list_flows_filters(test_db):
    """Test list_flows with status and workspace filters."""
    conn = test_db.conn
    org_id = "org-123"
    ws1 = "ws-1"
    ws2 = "ws-2"
    user_id = "user-123"

    # Create flows in different workspaces
    flow1, _ = await repo.create_flow(conn, org_id, ws1, "flow-1", "Flow 1", None, user_id)
    flow2, _ = await repo.create_flow(conn, org_id, ws2, "flow-2", "Flow 2", None, user_id)

    # Filter by workspace
    flows_ws1 = await repo.list_flows(conn, org_id, workspace_id=ws1)
    assert any(f["id"] == flow1["id"] for f in flows_ws1)
    assert not any(f["id"] == flow2["id"] for f in flows_ws1)

    flows_ws2 = await repo.list_flows(conn, org_id, workspace_id=ws2)
    assert any(f["id"] == flow2["id"] for f in flows_ws2)
    assert not any(f["id"] == flow1["id"] for f in flows_ws2)


@pytest.mark.asyncio
async def test_search_by_name(test_db):
    """Test search by name/slug with ILIKE."""
    conn = test_db.conn
    org_id = "org-123"
    workspace_id = "ws-123"
    user_id = "user-123"

    flow, _ = await repo.create_flow(
        conn, org_id, workspace_id, "auth-flow", "Authentication Flow", None, user_id
    )

    # Search by slug
    results = await repo.list_flows(conn, org_id, q="auth")
    assert any(f["id"] == flow["id"] for f in results)

    # Search by name
    results = await repo.list_flows(conn, org_id, q="Authen")
    assert any(f["id"] == flow["id"] for f in results)

    # No match
    results = await repo.list_flows(conn, org_id, q="webhook")
    assert not any(f["id"] == flow["id"] for f in results)


@pytest.mark.asyncio
async def test_version_immutability(test_db):
    """Test that published versions cannot be updated."""
    conn = test_db.conn
    org_id = "org-123"
    workspace_id = "ws-123"
    user_id = "user-123"

    flow, version = await repo.create_flow(
        conn, org_id, workspace_id, "immutable-test", "Test", None, user_id
    )

    # Publish version
    status_map = {"draft": 1, "published": 2}
    await conn.execute(
        'UPDATE "01_catalog"."11_fct_flow_versions" SET status_id = $1 WHERE id = $2',
        status_map["published"],
        version["id"],
    )

    # Try to replace DAG should fail
    from backend.02_features.01_catalog.sub_features.04_flows import service

    result = await service.replace_version_dag(
        conn,
        flow["id"],
        version["id"],
        org_id,
        workspace_id,
        [],
        [],
        user_id,
        "session-123",
    )

    assert result.get("ok") is False
    assert result.get("code") == "VERSION_FROZEN"
