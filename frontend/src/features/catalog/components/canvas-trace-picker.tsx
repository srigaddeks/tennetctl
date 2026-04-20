/**
 * Dropdown for selecting a run to overlay as trace.
 * Plan 44-01 implementation.
 */

"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useFlowRuns } from "../hooks/use-flow-runs";
import type { TraceNodeStatus } from "@/types/api";

function relativeTime(dateStr: string): string {
  const now = new Date();
  const then = new Date(dateStr);
  const seconds = Math.floor((now.getTime() - then.getTime()) / 1000);

  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

function statusBadgeColor(status: TraceNodeStatus): string {
  switch (status) {
    case "pending":
      return "bg-slate-100 text-slate-900";
    case "running":
      return "bg-blue-100 text-blue-900";
    case "success":
      return "bg-green-100 text-green-900";
    case "failure":
      return "bg-red-100 text-red-900";
    case "skipped":
      return "bg-zinc-100 text-zinc-900";
    case "timed_out":
      return "bg-orange-100 text-orange-900";
    default:
      return "bg-gray-100 text-gray-900";
  }
}

export function CanvasTracePicker({
  flowId,
  versionId,
}: {
  flowId: string;
  versionId: string;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const traceId = searchParams.get("trace_id");
  const [open, setOpen] = useState(false);

  const { data: runs, isLoading } = useFlowRuns(flowId, versionId);

  const handleSelect = (runId: string) => {
    const params = new URLSearchParams(searchParams);
    params.set("trace_id", runId);
    router.replace(`?${params.toString()}`, { scroll: false });
    setOpen(false);
  };

  const handleClear = () => {
    const params = new URLSearchParams(searchParams);
    params.delete("trace_id");
    router.replace(
      params.toString() ? `?${params.toString()}` : "",
      { scroll: false }
    );
    setOpen(false);
  };

  const selectedRun = runs?.find((r) => r.id === traceId);

  return (
    <div className="fixed top-4 left-4 z-40">
      <div className="relative">
        <button
          onClick={() => setOpen(!open)}
          className="px-3 py-2 bg-white border border-gray-300 rounded-lg shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-medium text-gray-900 transition-shadow"
        >
          {selectedRun
            ? `${selectedRun.status} - ${relativeTime(selectedRun.started_at)}`
            : "Select run..."}
        </button>

        {/* Dropdown */}
        {open && (
          <div className="absolute top-full left-0 mt-1 bg-white border border-gray-300 rounded-lg shadow-lg z-50 w-64 max-h-96 overflow-y-auto">
            {/* Clear option */}
            <button
              onClick={handleClear}
              className="w-full text-left px-3 py-2 hover:bg-gray-50 border-b border-gray-100 text-sm text-gray-600"
            >
              Clear trace
            </button>

            {/* Runs list */}
            {isLoading ? (
              <div className="px-3 py-4 text-sm text-gray-500">Loading...</div>
            ) : runs && runs.length > 0 ? (
              runs.map((run) => (
                <button
                  key={run.id}
                  onClick={() => handleSelect(run.id)}
                  className={`w-full text-left px-3 py-2 border-b border-gray-100 hover:bg-blue-50 last:border-b-0 transition-colors ${
                    traceId === run.id ? "bg-blue-50" : ""
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-0.5 text-xs font-medium rounded ${statusBadgeColor(
                            run.status
                          )}`}
                        >
                          {run.status}
                        </span>
                        <span className="font-mono text-xs text-gray-600">
                          {run.id.slice(0, 8)}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {relativeTime(run.started_at)}
                      </p>
                    </div>
                  </div>
                </button>
              ))
            ) : (
              <div className="px-3 py-4 text-sm text-gray-500">No runs</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
