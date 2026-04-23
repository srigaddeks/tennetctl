"use client";

import { useSearchParams, useParams } from "next/navigation";
import Link from "next/link";

import { CanvasViewer } from "@/features/catalog/components/canvas-viewer";
import { CanvasSearch } from "@/features/catalog/components/canvas-search";
import { CanvasTracePicker } from "@/features/catalog/components/canvas-trace-picker";
import { CanvasTraceLegend } from "@/features/catalog/components/canvas-trace-legend";
import { CanvasNodeInspector } from "@/features/catalog/components/canvas-node-inspector";
import { useCanvas } from "@/features/catalog/hooks/use-canvas";
import { Badge } from "@/components/ui";

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
    <div
      className="relative h-screen w-screen overflow-hidden"
      style={{ background: "var(--bg-base)" }}
    >
      {/* Loading overlay */}
      {isLoading && (
        <div
          className="absolute inset-0 z-50 flex items-center justify-center"
          style={{ background: "var(--bg-base)" }}
        >
          <div className="flex flex-col items-center gap-4">
            {/* Spinner */}
            <div
              className="h-10 w-10 animate-spin rounded-full border-2"
              style={{
                borderColor: "var(--border)",
                borderTopColor: "#7ef7c8",
              }}
            />
            <span
              className="font-mono-data text-xs"
              style={{ color: "var(--text-muted)" }}
            >
              Loading canvas…
            </span>
          </div>
        </div>
      )}

      {/* Error overlay */}
      {error && (
        <div
          className="absolute inset-0 z-50 flex items-center justify-center"
          style={{ background: "var(--bg-base)" }}
        >
          <div
            className="flex max-w-sm flex-col items-center gap-4 rounded border p-8 text-center"
            style={{
              background: "var(--bg-surface)",
              borderColor: "var(--border)",
            }}
          >
            <div
              className="h-8 w-8 rounded-full border-2 flex items-center justify-center"
              style={{ borderColor: "var(--danger)", color: "var(--danger)" }}
            >
              ✕
            </div>
            <div>
              <p
                className="text-sm font-medium"
                style={{ color: "var(--text-primary)" }}
              >
                Failed to load canvas
              </p>
              <p
                className="mt-1 text-xs"
                style={{ color: "var(--text-muted)" }}
              >
                {error instanceof Error ? error.message : "Unknown error"}
              </p>
            </div>
            <Link
              href={`/flows/${flowId}`}
              className="text-xs transition-colors"
              style={{ color: "var(--accent)" }}
            >
              ← Back to flow
            </Link>
          </div>
        </div>
      )}

      {/* Top bar overlay — shown when canvas loaded */}
      {payload && (
        <div
          className="absolute left-0 right-0 top-0 z-20 flex h-10 items-center gap-3 border-b px-4"
          style={{
            background: "rgba(6, 11, 23, 0.85)",
            backdropFilter: "blur(8px)",
            borderColor: "var(--border)",
          }}
        >
          <Link
            href={`/flows/${flowId}`}
            className="text-xs transition-colors"
            style={{ color: "var(--text-secondary)" }}
          >
            ← Flows
          </Link>
          <span style={{ color: "var(--border)" }}>/</span>
          <span
            className="font-mono-data text-xs"
            style={{ color: "var(--text-primary)" }}
          >
            {flowId.slice(0, 8)}…
          </span>
          <span style={{ color: "var(--border)" }}>/</span>
          <span
            className="font-mono-data text-xs"
            style={{ color: "#7ef7c8" }}
          >
            v{versionId.slice(0, 8)}…
          </span>

          <Badge tone="info" className="ml-1">
            read-only
          </Badge>

          {traceId && (
            <Badge tone="amber" dot className="ml-auto">
              trace: {traceId.slice(0, 8)}…
            </Badge>
          )}
        </div>
      )}

      {/* Canvas */}
      {payload && (
        <>
          <CanvasViewer payload={payload} />
          <CanvasSearch payload={payload} />
          <CanvasTracePicker flowId={flowId} versionId={versionId} />
          <CanvasTraceLegend payload={payload} />
          <CanvasNodeInspector />
        </>
      )}
    </div>
  );
}
