/**
 * Pure transform from backend CanvasPayload to React Flow nodes + edges.
 * Plan 44-01 implementation — exhaustive unit-testable, no side effects.
 */

import type {
  CanvasPayload,
  CanvasTrace,
  TraceNodeStatus,
} from "@/types/api";
import type { Node, Edge } from "@xyflow/react";

export type TennetNodeData = {
  label: string;
  nodeKey: string;
  kind: "request" | "effect" | "control";
  configJson: Record<string, unknown>;
  ports: {
    inputs: Array<{ key: string; type: string }>;
    outputs: Array<{ key: string; type: string }>;
  };
  status?: TraceNodeStatus;
  statusDurationMs?: number;
  unresolved: boolean;
  [key: string]: unknown;
};

export type TennetEdgeData = {
  kind: "next" | "success" | "failure" | "true_branch" | "false_branch";
  traversed: boolean;
  hasTrace: boolean;
  [key: string]: unknown;
};

export function toReactFlow(
  payload: CanvasPayload,
  _trace?: CanvasTrace | null
): { nodes: Node<TennetNodeData>[]; edges: Edge<TennetEdgeData>[] } {
  const trace = _trace || null;

  // Transform nodes
  const nodes: Node<TennetNodeData>[] = payload.nodes.map((node) => {
    const layout = payload.layout[node.id];
    const ports = payload.ports[node.node_key];
    const status = trace?.node_status[node.id];

    return {
      id: node.id,
      type: "tennetNode",
      position: layout ? { x: layout.x, y: layout.y } : { x: 0, y: 0 },
      data: {
        label: node.instance_label,
        nodeKey: node.node_key,
        kind: node.kind,
        configJson: node.config_json,
        ports: {
          inputs: ports?.inputs ?? [],
          outputs: ports?.outputs ?? [],
        },
        status: status?.status ?? undefined,
        unresolved: ports?.unresolved ?? false,
      },
    };
  });

  // Transform edges
  const edges: Edge<TennetEdgeData>[] = payload.edges.map((edge) => {
    const traversed = trace?.edge_traversed[edge.id] ?? false;

    return {
      id: edge.id,
      source: edge.from_node_id,
      target: edge.to_node_id,
      sourceHandle: edge.from_port,
      targetHandle: edge.to_port,
      type: "tennetEdge",
      data: {
        kind: edge.kind,
        traversed,
        hasTrace: trace !== null,
      },
    };
  });

  return { nodes, edges };
}
