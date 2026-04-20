/**
 * Main React Flow canvas viewer with custom node/edge types.
 * Plan 44-01 implementation.
 */

"use client";

import ReactFlow, {
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
} from "react-flow-renderer";
import { useMemo, useCallback } from "react";
import type { CanvasPayload } from "@/types/api";
import { toReactFlow } from "../lib/canvas-transform";
import { CanvasNodeComponent } from "./canvas-node";
import { CanvasEdgeComponent } from "./canvas-edge";

const nodeTypes = {
  tennetNode: CanvasNodeComponent,
};

const edgeTypes = {
  tennetEdge: CanvasEdgeComponent,
};

export function CanvasViewer({ payload }: { payload: CanvasPayload }) {
  // Transform payload to React Flow nodes/edges
  const { nodes: rfNodes, edges: rfEdges } = useMemo(() => {
    return toReactFlow(payload, payload.trace);
  }, [payload]);

  const [nodes, setNodes, onNodesChange] = useNodesState(rfNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(rfEdges);

  // Update when payload changes
  useMemo(() => {
    setNodes(rfNodes);
    setEdges(rfEdges);
  }, [rfNodes, rfEdges, setNodes, setEdges]);

  const fitViewOptions = useMemo(
    () => ({
      padding: 0.2,
    }),
    []
  );

  return (
    <div className="w-full h-full relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
      >
        <Background color="#aaa" gap={16} />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            // Color nodes by kind
            const kind = node.data?.kind;
            switch (kind) {
              case "request":
                return "#60a5fa";
              case "effect":
                return "#4ade80";
              case "control":
                return "#fbbf24";
              default:
                return "#e5e7eb";
            }
          }}
        />
      </ReactFlow>
    </div>
  );
}
