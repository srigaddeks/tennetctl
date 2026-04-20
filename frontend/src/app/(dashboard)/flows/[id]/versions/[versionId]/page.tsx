/**
 * Canvas viewer page with full-bleed layout.
 * Plan 44-01 implementation.
 */

"use client";

import { useCanvas } from "@/features/catalog/hooks/use-canvas";
import { useSearchParams, useParams } from "next/navigation";
import { CanvasViewer } from "@/features/catalog/components/canvas-viewer";
import { CanvasSearch } from "@/features/catalog/components/canvas-search";
import { CanvasTracePicker } from "@/features/catalog/components/canvas-trace-picker";
import { CanvasTraceLegend } from "@/features/catalog/components/canvas-trace-legend";
import { CanvasNodeInspector } from "@/features/catalog/components/canvas-node-inspector";

export default function CanvasPage() {
  const params = useParams();
  const searchParams = useSearchParams();

  const flowId = params.id as string;
  const versionId = params.versionId as string;
  const traceId = searchParams.get("trace_id") || undefined;

  const { data: payload, isLoading, error } = useCanvas(
    flowId,
    versionId,
    traceId
  );

  return (
    <div className="h-screen w-screen overflow-hidden bg-gray-50">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white z-50">
          <div className="text-center">
            <p className="text-gray-600 mb-4">Loading canvas...</p>
            <div className="inline-block animate-spin">
              <svg
                className="w-8 h-8 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-white z-50">
          <div className="text-center">
            <p className="text-red-600 font-medium mb-2">Failed to load</p>
            <p className="text-gray-600 text-sm">
              {error instanceof Error ? error.message : "Unknown error"}
            </p>
          </div>
        </div>
      )}

      {payload && (
        <>
          {/* Canvas viewer */}
          <CanvasViewer payload={payload} />

          {/* Overlays */}
          <CanvasSearch payload={payload} />
          <CanvasTracePicker flowId={flowId} versionId={versionId} />
          <CanvasTraceLegend payload={payload} />
          <CanvasNodeInspector />
        </>
      )}
    </div>
  );
}
