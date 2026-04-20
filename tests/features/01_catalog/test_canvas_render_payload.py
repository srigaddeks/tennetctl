"""Test canvas render payload endpoint."""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_canvas_payload_contains_all_five_keys(pool):
    """AC-1: Canvas payload has exactly the 5 keys."""
    from backend.02_features.01_catalog.sub_features.05_canvas import service

    conn = AsyncMock()

    # Mock flow version DAG
    version_data = {
        "flow_id": "flow-1",
        "nodes": [
            {
                "id": "node-1",
                "instance_label": "auth",
                "node_key": "iam.auth_required",
                "kind": "request",
                "config_json": {},
                "position_x": None,
                "position_y": None,
            }
        ],
        "edges": [],
    }

    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])

    from backend.02_features.01_catalog.sub_features.05_canvas import repository
    repository.load_version_dag = AsyncMock(return_value=version_data)

    # Mock registry
    registry = MagicMock()
    registry.get.return_value = {
        "input_schema": {"properties": {}},
        "output_schema": {"properties": {}},
    }

    payload = await service.assemble_canvas(
        conn, "flow-1", "version-1", registry=registry
    )

    # Check all 5 keys
    assert hasattr(payload, "nodes")
    assert hasattr(payload, "edges")
    assert hasattr(payload, "ports")
    assert hasattr(payload, "layout")
    assert hasattr(payload, "trace")

    assert isinstance(payload.nodes, list)
    assert isinstance(payload.edges, list)
    assert isinstance(payload.ports, dict)
    assert isinstance(payload.layout, dict)
    assert payload.trace is None  # No trace_id provided


@pytest.mark.asyncio
async def test_canvas_404_on_version_mismatch():
    """AC-1: Returns 404 if version belongs to different flow."""
    from backend.02_features.01_catalog.sub_features.05_canvas import service, repository

    conn = AsyncMock()
    repository.load_version_dag = AsyncMock(return_value=None)

    with pytest.raises(ValueError, match="not found"):
        await service.assemble_canvas(conn, "flow-1", "version-1")


@pytest.mark.asyncio
async def test_canvas_includes_node_keys_and_configs():
    """AC-1: Nodes include id, instance_label, node_key, kind, config_json, position."""
    from backend.02_features.01_catalog.sub_features.05_canvas import service, repository

    conn = AsyncMock()

    version_data = {
        "flow_id": "flow-1",
        "nodes": [
            {
                "id": "n1",
                "instance_label": "step1",
                "node_key": "test.step",
                "kind": "effect",
                "config_json": {"key": "value"},
                "position_x": 100,
                "position_y": 50,
            }
        ],
        "edges": [],
    }

    repository.load_version_dag = AsyncMock(return_value=version_data)

    registry = MagicMock()
    registry.get.return_value = {
        "input_schema": {"properties": {}},
        "output_schema": {"properties": {}},
    }

    payload = await service.assemble_canvas(
        conn, "flow-1", "version-1", registry=registry
    )

    node = payload.nodes[0]
    assert node.id == "n1"
    assert node.instance_label == "step1"
    assert node.node_key == "test.step"
    assert node.kind == "effect"
    assert node.config_json == {"key": "value"}
    assert node.position == {"x": 100, "y": 50}
