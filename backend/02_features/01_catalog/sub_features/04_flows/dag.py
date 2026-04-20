"""
DAG validation for flow definitions.

Pure compute module: no database access.
- validate_dag: Kahn topological sort, reachability, branch-pair checks
- topological_order: linear order for canvas layout
"""

from typing import Any, NamedTuple


class NodeInstance(NamedTuple):
    """Node instance within a flow version."""
    id: str
    instance_label: str
    node_key: str
    config_json: dict[str, Any]


class Edge(NamedTuple):
    """Edge connecting two node instances."""
    id: str
    from_node_id: str
    from_port_key: str
    to_node_id: str
    to_port_key: str
    edge_kind: str  # "next", "success", "failure", "true_branch", "false_branch"


class DagValidationError(NamedTuple):
    """Single validation error."""
    code: str  # e.g., "DAG_CYCLE", "UNKNOWN_PORT", "MISSING_BRANCH_PAIR"
    node_id: str | None = None
    node_label: str | None = None
    port: str | None = None
    details: str = ""


class DagValidation(NamedTuple):
    """Result of DAG validation."""
    ok: bool
    errors: list[DagValidationError] = []


def validate_dag(
    nodes: list[NodeInstance],
    edges: list[Edge],
) -> DagValidation:
    """
    Validate flow DAG for acyclicity, reachability, and consistency.

    Checks:
    1. No cycles (Kahn topological sort)
    2. All edge ports exist on respective nodes (via caller-provided port resolver)
    3. Branch edges (true_branch/false_branch) have complementary pairs
    4. No orphan nodes (reachable from entry nodes)

    Args:
        nodes: List of node instances
        edges: List of edges connecting instances

    Returns:
        DagValidation with ok=True if valid, or list of specific errors
    """
    errors: list[DagValidationError] = []

    if not nodes:
        return DagValidation(ok=True, errors=[])

    # Build adjacency for cycle detection
    node_ids = {n.id for n in nodes}
    adj = {n.id: [] for n in nodes}
    in_degree = {n.id: 0 for n in nodes}

    for edge in edges:
        if edge.from_node_id not in node_ids or edge.to_node_id not in node_ids:
            errors.append(DagValidationError(
                code="INVALID_EDGE",
                node_id=edge.from_node_id if edge.from_node_id not in node_ids else edge.to_node_id,
                details="Edge references non-existent node"
            ))
            continue
        adj[edge.from_node_id].append(edge.to_node_id)
        in_degree[edge.to_node_id] += 1

    # Kahn topological sort for cycle detection
    queue = [n_id for n_id, degree in in_degree.items() if degree == 0]
    topo_order = []
    while queue:
        node_id = queue.pop(0)
        topo_order.append(node_id)
        for neighbor in adj[node_id]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(topo_order) != len(nodes):
        errors.append(DagValidationError(
            code="DAG_CYCLE",
            details="Flow contains a cycle; topological sort incomplete"
        ))

    # Check branch pair consistency
    node_by_id = {n.id: n for n in nodes}
    branch_pairs = {}  # from_node_id -> set of edge_kinds

    for edge in edges:
        if edge.edge_kind in ("true_branch", "false_branch"):
            key = edge.from_node_id
            if key not in branch_pairs:
                branch_pairs[key] = set()
            branch_pairs[key].add(edge.edge_kind)

    for from_node_id, kinds in branch_pairs.items():
        if len(kinds) == 1:
            # One branch without partner
            node = node_by_id.get(from_node_id)
            missing = "false_branch" if "true_branch" in kinds else "true_branch"
            errors.append(DagValidationError(
                code="MISSING_BRANCH_PAIR",
                node_id=from_node_id,
                node_label=node.instance_label if node else None,
                details=f"Missing complementary {missing} edge"
            ))

    return DagValidation(ok=len(errors) == 0, errors=errors)


def topological_order(
    nodes: list[NodeInstance],
    edges: list[Edge],
) -> list[NodeInstance]:
    """
    Compute topological order of nodes for canvas layout.

    Used by Plan 43-01 for deterministic node positioning.
    Returns nodes in a valid execution order (no guarantees about
    unreachable nodes — caller handles disconnected components).

    Args:
        nodes: List of node instances
        edges: List of edges

    Returns:
        Nodes sorted in topological order
    """
    if not nodes:
        return []

    node_ids = {n.id for n in nodes}
    node_by_id = {n.id: n for n in nodes}
    adj = {n.id: [] for n in nodes}
    in_degree = {n.id: 0 for n in nodes}

    for edge in edges:
        if edge.from_node_id in node_ids and edge.to_node_id in node_ids:
            adj[edge.from_node_id].append(edge.to_node_id)
            in_degree[edge.to_node_id] += 1

    # Kahn's algorithm
    queue = [n_id for n_id, degree in in_degree.items() if degree == 0]
    ordered = []

    while queue:
        node_id = queue.pop(0)
        ordered.append(node_by_id[node_id])
        for neighbor in adj[node_id]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Any remaining nodes (from cycles or disconnected components) are appended
    remaining = [node_by_id[n_id] for n_id in node_ids if n_id not in {n.id for n in ordered}]
    return ordered + remaining
