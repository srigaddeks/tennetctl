"""
Canvas frontend smoke test — validates backend payload shape.
Plan 44-01 implementation.

These tests ensure the /v1/flows/{id}/versions/{versionId}/canvas endpoint
returns the shape the React Flow frontend expects, catching accidental
backend regressions that would break the canvas viewer.
"""

import pytest


@pytest.mark.asyncio
async def test_canvas_payload_has_required_keys(client, org_id, flow_version_id):
    """AC-1: Payload contains all 5 required keys."""
    response = await client.get(
        f"/v1/flows/{org_id}/versions/{flow_version_id}/canvas"
    )
    assert response.status_code == 200

    data = response.json()
    assert data["ok"] is True
    payload = data["data"]

    # Must have exactly these 5 keys
    required_keys = {"nodes", "edges", "ports", "layout", "trace"}
    assert set(payload.keys()) == required_keys


@pytest.mark.asyncio
async def test_canvas_nodes_have_required_fields(client, org_id, flow_version_id):
    """AC-1: Each node has required fields."""
    response = await client.get(
        f"/v1/flows/{org_id}/versions/{flow_version_id}/canvas"
    )
    assert response.status_code == 200

    payload = response.json()["data"]
    nodes = payload["nodes"]

    for node in nodes:
        assert "id" in node
        assert "instance_label" in node
        assert "node_key" in node
        assert "kind" in node
        assert "config_json" in node
        assert node["kind"] in ["request", "effect", "control"]


@pytest.mark.asyncio
async def test_canvas_edges_have_required_fields(client, org_id, flow_version_id):
    """AC-1: Each edge has required fields."""
    response = await client.get(
        f"/v1/flows/{org_id}/versions/{flow_version_id}/canvas"
    )
    assert response.status_code == 200

    payload = response.json()["data"]
    edges = payload["edges"]

    for edge in edges:
        assert "id" in edge
        assert "from_node_id" in edge
        assert "from_port" in edge
        assert "to_node_id" in edge
        assert "to_port" in edge
        assert "kind" in edge
        assert edge["kind"] in [
            "next",
            "success",
            "failure",
            "true_branch",
            "false_branch",
        ]


@pytest.mark.asyncio
async def test_canvas_ports_resolve_from_registry(client, org_id, flow_version_id):
    """AC-4: Ports are resolved live from registry."""
    response = await client.get(
        f"/v1/flows/{org_id}/versions/{flow_version_id}/canvas"
    )
    assert response.status_code == 200

    payload = response.json()["data"]
    ports = payload["ports"]

    # Should have an entry for each node_key
    for node in payload["nodes"]:
        assert node["node_key"] in ports
        port_data = ports[node["node_key"]]
        assert "inputs" in port_data
        assert "outputs" in port_data
        # Check port structure
        for port in port_data["inputs"]:
            assert "key" in port
            assert "type" in port
        for port in port_data["outputs"]:
            assert "key" in port
            assert "type" in port


@pytest.mark.asyncio
async def test_canvas_layout_present(client, org_id, flow_version_id):
    """AC-1: Layout map has x, y for each node."""
    response = await client.get(
        f"/v1/flows/{org_id}/versions/{flow_version_id}/canvas"
    )
    assert response.status_code == 200

    payload = response.json()["data"]
    layout = payload["layout"]

    for node in payload["nodes"]:
        assert node["id"] in layout
        position = layout[node["id"]]
        assert "x" in position
        assert "y" in position
        assert isinstance(position["x"], (int, float))
        assert isinstance(position["y"], (int, float))


@pytest.mark.asyncio
async def test_canvas_trace_null_without_param(client, org_id, flow_version_id):
    """AC-1: Trace is null when no trace_id param."""
    response = await client.get(
        f"/v1/flows/{org_id}/versions/{flow_version_id}/canvas"
    )
    assert response.status_code == 200

    payload = response.json()["data"]
    assert payload["trace"] is None


@pytest.mark.asyncio
async def test_canvas_unresolved_node_marker(client, org_id, flow_version_id_missing_node):
    """AC-4: Missing node returns unresolved=true in ports."""
    response = await client.get(
        f"/v1/flows/{org_id}/versions/{flow_version_id_missing_node}/canvas"
    )
    assert response.status_code == 200

    payload = response.json()["data"]
    ports = payload["ports"]

    # Should have an entry with unresolved=true
    unresolved = [p for p in ports.values() if p.get("unresolved")]
    assert len(unresolved) > 0


@pytest.mark.asyncio
async def test_canvas_flow_version_mismatch_returns_404(client, org_id, flow_id, other_flow_version_id):
    """AC-1: Returns 404 if version belongs to different flow."""
    response = await client.get(
        f"/v1/flows/{flow_id}/versions/{other_flow_version_id}/canvas"
    )
    # Should either be 404 or check ownership
    assert response.status_code in [404, 400]
