/**
 * Custom React Flow edge component with animated/dashed states based on trace.
 * Plan 44-01 implementation.
 */

"use client";

import {
  EdgeProps,
  getBezierPath,
  getEdgeCenter,
  EdgeLabelRenderer,
} from "react-flow-renderer";
import type { TennetEdgeData } from "../lib/canvas-transform";

function kindStrokeColor(
  kind: "next" | "success" | "failure" | "true_branch" | "false_branch"
): string {
  switch (kind) {
    case "next":
      return "stroke-gray-400";
    case "success":
      return "stroke-green-500";
    case "failure":
      return "stroke-red-500";
    case "true_branch":
      return "stroke-blue-500";
    case "false_branch":
      return "stroke-purple-500";
    default:
      return "stroke-gray-300";
  }
}

export function CanvasEdgeComponent({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  markerEnd,
}: EdgeProps<TennetEdgeData>) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const strokeColor = kindStrokeColor(data.kind);

  // Animated dashes when actively traversed with no finished_at
  // Solid when traversed and finished
  // Dashed gray when traced but not traversed
  // Plain default when no trace
  let strokeDasharray = "";
  let animationClass = "";

  if (data.hasTrace) {
    if (data.traversed) {
      strokeDasharray = "";
      animationClass = "";
    } else {
      strokeDasharray = "5,5";
    }
  }

  return (
    <>
      <path
        id={id}
        d={edgePath}
        stroke="currentColor"
        strokeWidth={2}
        fill="none"
        className={`${strokeColor} ${animationClass}`}
        strokeDasharray={strokeDasharray}
        markerEnd={markerEnd}
        style={{
          strokeDashoffset: data.traversed && data.hasTrace ? "5" : "0",
          animation:
            data.traversed && data.hasTrace && !strokeDasharray
              ? "none"
              : "none",
        }}
      />
    </>
  );
}
