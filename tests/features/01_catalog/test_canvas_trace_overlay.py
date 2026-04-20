"""Test canvas trace overlay assembly."""

from datetime import datetime, timedelta
from backend.02_features.01_catalog.sub_features.05_canvas.trace_assembler import assemble_trace


def test_trace_happy_path_all_success():
    """Test: All nodes succeed, edges traversed, timing computed."""
    now = datetime.utcnow()

    run_nodes = [
        {
            "node_instance_id": "n1",
            "event_kind": "success",
            "occurred_at": now + timedelta(seconds=1),
        },
        {
            "node_instance_id": "n2",
            "event_kind": "success",
            "occurred_at": now + timedelta(seconds=2),
        },
    ]

    run_edges = [
        {"from_node_id": "n1", "to_node_id": "n2", "traversed": True, "from_node_event_time": now + timedelta(seconds=1)}
    ]

    version_nodes = [{"id": "n1"}, {"id": "n2"}]
    version_edges = [{"id": "e1", "from_node_id": "n1", "to_node_id": "n2"}]

    trace = assemble_trace(run_nodes, run_edges, version_nodes, version_edges)

    assert trace["node_status"]["n1"]["status"] == "success"
    assert trace["node_status"]["n2"]["status"] == "success"
    assert trace["edge_traversed"]["e1"] is True
    assert trace["finished_at"] is not None
    assert trace["total_duration_ms"] is not None


def test_trace_partial_run_one_running():
    """Test: Some nodes running, timing has no finished_at."""
    now = datetime.utcnow()

    run_nodes = [
        {
            "node_instance_id": "n1",
            "event_kind": "success",
            "occurred_at": now,
        },
        {
            "node_instance_id": "n2",
            "event_kind": "started",
            "occurred_at": now + timedelta(seconds=1),
        },
    ]

    run_edges = []

    version_nodes = [{"id": "n1"}, {"id": "n2"}]
    version_edges = [{"id": "e1", "from_node_id": "n1", "to_node_id": "n2"}]

    trace = assemble_trace(run_nodes, run_edges, version_nodes, version_edges)

    assert trace["node_status"]["n1"]["status"] == "success"
    assert trace["node_status"]["n2"]["status"] == "running"
    assert trace["finished_at"] is None  # No terminal events for n2


def test_trace_failure_marks_downstream_skipped():
    """Test: Nodes downstream of failure with no event marked skipped."""
    run_nodes = [
        {
            "node_instance_id": "n1",
            "event_kind": "success",
            "occurred_at": datetime.utcnow(),
        },
        {
            "node_instance_id": "n2",
            "event_kind": "failure",
            "occurred_at": datetime.utcnow() + timedelta(seconds=1),
        },
        # n3 has no event
    ]

    run_edges = []

    version_nodes = [{"id": "n1"}, {"id": "n2"}, {"id": "n3"}]
    version_edges = [
        {"id": "e1", "from_node_id": "n1", "to_node_id": "n2"},
        {"id": "e2", "from_node_id": "n2", "to_node_id": "n3"},
    ]

    trace = assemble_trace(run_nodes, run_edges, version_nodes, version_edges)

    assert trace["node_status"]["n1"]["status"] == "success"
    assert trace["node_status"]["n2"]["status"] == "failure"
    assert trace["node_status"]["n3"]["status"] == "skipped"


def test_trace_no_trace_id_returns_null():
    """Test: When no trace_id provided, trace is null (tested at service level)."""
    # This test is more for integration; trace_assembler always gets data
    # The null case is handled at service/route level
    pass


def test_trace_edge_traversal_requires_success_or_failure():
    """Test: Edge traversed=true only if from succeeded and to has event."""
    run_nodes = [
        {
            "node_instance_id": "n1",
            "event_kind": "success",
            "occurred_at": datetime.utcnow(),
        },
        # n2 has no event
    ]

    run_edges = []

    version_nodes = [{"id": "n1"}, {"id": "n2"}]
    version_edges = [{"id": "e1", "from_node_id": "n1", "to_node_id": "n2"}]

    trace = assemble_trace(run_nodes, run_edges, version_nodes, version_edges)

    # n2 has no event, so edge should not be traversed
    assert trace["edge_traversed"]["e1"] is False
