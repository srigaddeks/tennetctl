/**
 * Custom React Flow node component showing kind badge, label, key, and port handles.
 * Plan 44-01 implementation.
 */

"use client";

import { Handle, Position } from "@xyflow/react";
import type { NodeProps, Node } from "@xyflow/react";
import { colorFor } from "../lib/port-color";
import { useCanvasInspectorStore } from "./canvas-node-inspector";
import type { TennetNodeData } from "../lib/canvas-transform";
import type { TraceNodeStatus } from "@/types/api";

function kindBadgeColor(kind: string): string {
  switch (kind) {
    case "request":
      return "bg-blue-100 text-blue-900";
    case "effect":
      return "bg-green-100 text-green-900";
    case "control":
      return "bg-amber-100 text-amber-900";
    default:
      return "bg-gray-100 text-gray-900";
  }
}

function statusRingColor(status: TraceNodeStatus | undefined): string {
  switch (status) {
    case "pending":
      return "ring-2 ring-slate-400";
    case "running":
      return "ring-2 ring-blue-500 animate-pulse";
    case "success":
      return "ring-2 ring-emerald-500";
    case "failure":
      return "ring-2 ring-red-500";
    case "skipped":
      return "ring-2 ring-zinc-400";
    case "timed_out":
      return "ring-2 ring-orange-500";
    default:
      return "";
  }
}

export function CanvasNodeComponent({
  data,
}: NodeProps<Node<TennetNodeData>>) {
  const setInspectedNode = useCanvasInspectorStore(
    (state) => state.setNode
  );
  const status = data.status as TraceNodeStatus | undefined;

  const borderClass = data.unresolved
    ? "border-2 border-red-500"
    : "border border-gray-300";
  const ringClass = statusRingColor(status);

  return (
    <div
      className={`
        relative px-3 py-2 min-w-max bg-white rounded-lg shadow-md
        ${borderClass} ${ringClass}
        cursor-pointer hover:shadow-lg transition-shadow
      `}
      onClick={() => setInspectedNode(data)}
    >
      {/* Kind badge */}
      <div className="flex items-center justify-between mb-1">
        <span
          className={`px-2 py-0.5 text-xs font-medium rounded ${kindBadgeColor(
            data.kind
          )}`}
        >
          {data.kind}
        </span>
        {data.unresolved && (
          <span className="ml-2 px-1.5 py-0.5 text-xs font-medium bg-red-100 text-red-900 rounded">
            missing
          </span>
        )}
      </div>

      {/* Label */}
      <div className="font-semibold text-sm text-gray-900">
        {data.label}
      </div>

      {/* Node key */}
      <div className="text-xs text-gray-500 font-mono">
        {data.nodeKey}
      </div>

      {/* Input handles */}
      {data.ports.inputs.map((port) => {
        const colors = colorFor(port.type as any);
        return (
          <Handle
            key={`in-${port.key}`}
            type="target"
            position={Position.Left}
            id={port.key}
            className={`!w-3 !h-3 ${
              data.unresolved ? "!opacity-50 !border-dashed" : ""
            }`}
            style={{
              background: data.unresolved
                ? "rgb(209, 213, 219)"
                : colors.bg.replace("bg-", ""),
            }}
          />
        );
      })}

      {/* Output handles */}
      {data.ports.outputs.map((port) => {
        const colors = colorFor(port.type as any);
        return (
          <Handle
            key={`out-${port.key}`}
            type="source"
            position={Position.Right}
            id={port.key}
            className={`!w-3 !h-3 ${
              data.unresolved ? "!opacity-50 !border-dashed" : ""
            }`}
            style={{
              background: data.unresolved
                ? "rgb(209, 213, 219)"
                : colors.bg.replace("bg-", ""),
            }}
          />
        );
      })}
    </div>
  );
}
