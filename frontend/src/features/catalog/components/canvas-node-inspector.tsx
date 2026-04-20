/**
 * Slide-over inspector panel for node details and config.
 * Uses zustand for state scoped to canvas pages.
 * Plan 44-01 implementation.
 */

"use client";

import { create } from "zustand";
import { useEffect } from "react";
import type { TennetNodeData } from "../lib/canvas-transform";
import type { TraceNodeStatus } from "@/types/api";
import { colorFor } from "../lib/port-color";

export type CanvasInspectorStore = {
  node: TennetNodeData | null;
  setNode: (node: TennetNodeData | null) => void;
};

export const useCanvasInspectorStore = create<CanvasInspectorStore>(
  (set) => ({
    node: null,
    setNode: (node) => set({ node }),
  })
);

export function CanvasNodeInspector() {
  const { node, setNode } = useCanvasInspectorStore();

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setNode(null);
      }
    };

    if (node) {
      document.addEventListener("keydown", handleEscape);
      return () => document.removeEventListener("keydown", handleEscape);
    }
  }, [node, setNode]);

  if (!node) {
    return null;
  }

  return (
    <div
      className="fixed right-0 top-0 h-screen w-96 bg-white shadow-xl overflow-y-auto border-l border-gray-200 z-50"
      onClick={(e) => e.stopPropagation()}
    >
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            {node.label}
          </h2>
          <p className="text-sm text-gray-500 font-mono">{node.nodeKey}</p>
        </div>
        <button
          onClick={() => setNode(null)}
          className="text-gray-400 hover:text-gray-600"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      {/* Kind badge */}
      <div className="px-4 py-3 border-b border-gray-200">
        <span
          className={`inline-block px-2 py-1 text-xs font-medium rounded ${
            node.kind === "request"
              ? "bg-blue-100 text-blue-900"
              : node.kind === "effect"
              ? "bg-green-100 text-green-900"
              : "bg-amber-100 text-amber-900"
          }`}
        >
          {node.kind}
        </span>
      </div>

      {/* Warning banner for unresolved nodes */}
      {node.unresolved && (
        <div className="mx-4 mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
          <p className="text-sm text-yellow-800">
            <strong>Node not in registry:</strong> This node key is not
            currently loaded. It may have been removed or renamed in a newer
            version.
          </p>
        </div>
      )}

      {/* Config JSON section */}
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-900 mb-2">Config</h3>
        <pre className="bg-gray-50 p-2 rounded text-xs text-gray-700 overflow-x-auto">
          {JSON.stringify(node.configJson, null, 2)}
        </pre>
      </div>

      {/* Ports section */}
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Ports</h3>

        {/* Input ports */}
        {node.ports.inputs.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-medium text-gray-600 mb-2">Inputs</p>
            <table className="w-full text-xs">
              <tbody>
                {node.ports.inputs.map((port) => {
                  const colors = colorFor(port.type as any);
                  return (
                    <tr key={port.key} className="border-b border-gray-100">
                      <td className="py-1 text-gray-900">{port.key}</td>
                      <td className="py-1 text-right">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-xs ${colors.bg} ${colors.text}`}
                        >
                          {port.type}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Output ports */}
        {node.ports.outputs.length > 0 && (
          <div>
            <p className="text-xs font-medium text-gray-600 mb-2">Outputs</p>
            <table className="w-full text-xs">
              <tbody>
                {node.ports.outputs.map((port) => {
                  const colors = colorFor(port.type as any);
                  return (
                    <tr key={port.key} className="border-b border-gray-100">
                      <td className="py-1 text-gray-900">{port.key}</td>
                      <td className="py-1 text-right">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-xs ${colors.bg} ${colors.text}`}
                        >
                          {port.type}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {node.ports.inputs.length === 0 && node.ports.outputs.length === 0 && (
          <p className="text-xs text-gray-500">No ports defined</p>
        )}
      </div>

      {/* Trace status section (if statusDurationMs is set) */}
      {node.statusDurationMs !== undefined && (
        <div className="px-4 py-3">
          <h3 className="text-sm font-semibold text-gray-900 mb-2">Trace</h3>
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-gray-600">Status:</span>
              <span className="font-medium text-gray-900">
                {node.status}
              </span>
            </div>
            {node.statusDurationMs > 0 && (
              <div className="flex justify-between text-xs">
                <span className="text-gray-600">Duration:</span>
                <span className="font-mono text-gray-900">
                  {node.statusDurationMs}ms
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
