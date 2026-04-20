/**
 * Legend strip showing status colors, edge kinds, and port type colors.
 * Plan 44-01 implementation.
 */

"use client";

import type { CanvasPayload } from "@/types/api";
import { colorFor } from "../lib/port-color";

// Get unique port types from payload
function getPortTypesInUse(payload: CanvasPayload): Set<string> {
  const types = new Set<string>();
  Object.values(payload.ports).forEach((resolved) => {
    resolved.inputs?.forEach((port) => types.add(port.type));
    resolved.outputs?.forEach((port) => types.add(port.type));
  });
  return types;
}

export function CanvasTraceLegend({ payload }: { payload: CanvasPayload }) {
  const portTypes = getPortTypesInUse(payload);

  return (
    <div className="fixed bottom-4 left-4 bg-white rounded-lg shadow-lg border border-gray-200 p-4 max-w-sm z-40">
      {/* Status row */}
      <div className="mb-4">
        <h4 className="text-xs font-semibold text-gray-900 mb-2">
          Node Status
        </h4>
        <div className="flex flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full ring-2 ring-slate-400" />
            <span className="text-xs text-gray-600">Pending</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full ring-2 ring-blue-500 animate-pulse" />
            <span className="text-xs text-gray-600">Running</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full ring-2 ring-emerald-500" />
            <span className="text-xs text-gray-600">Success</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full ring-2 ring-red-500" />
            <span className="text-xs text-gray-600">Failure</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full ring-2 ring-zinc-400" />
            <span className="text-xs text-gray-600">Skipped</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full ring-2 ring-orange-500" />
            <span className="text-xs text-gray-600">Timed Out</span>
          </div>
        </div>
      </div>

      {/* Edge kinds row */}
      <div className="mb-4 pb-4 border-b border-gray-200">
        <h4 className="text-xs font-semibold text-gray-900 mb-2">Edge Type</h4>
        <div className="flex flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-gray-400" />
            <span className="text-xs text-gray-600">next</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-green-500" />
            <span className="text-xs text-gray-600">success</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-red-500" />
            <span className="text-xs text-gray-600">failure</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-blue-500" />
            <span className="text-xs text-gray-600">true</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-purple-500" />
            <span className="text-xs text-gray-600">false</span>
          </div>
        </div>
      </div>

      {/* Port types row (only visible types) */}
      {portTypes.size > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-gray-900 mb-2">
            Port Types
          </h4>
          <div className="flex flex-wrap gap-2">
            {Array.from(portTypes).sort().map((type) => {
              const colors = colorFor(type as any);
              return (
                <span
                  key={type}
                  className={`inline-block px-2 py-1 rounded text-xs font-medium ${colors.bg} ${colors.text}`}
                >
                  {type}
                </span>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
