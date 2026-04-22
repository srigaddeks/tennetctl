/**
 * Canvas search component supporting default and port-prefix modes.
 * Plan 44-01 implementation.
 */

"use client";

import { useState, useRef, useEffect } from "react";
import { useReactFlow } from "@xyflow/react";
import type { CanvasPayload } from "@/types/api";

type SearchResult = {
  id: string;
  label: string;
  type: "label" | "key" | "input_port" | "output_port";
};

export function CanvasSearch({ payload }: { payload: CanvasPayload }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [highlighted, setHighlighted] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { getNode, setCenter } = useReactFlow();

  // Parse query and generate results
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const results: SearchResult[] = [];
    const q = query.toLowerCase();

    // Check for port prefix syntax
    const inMatch = q.match(/^in:\s*(.*)$/);
    const outMatch = q.match(/^out:\s*(.*)$/);

    if (inMatch) {
      // Search input ports
      const portQuery = inMatch[1];
      payload.nodes.forEach((node) => {
        const ports = payload.ports[node.node_key];
        if (!ports) return;
        ports.inputs.forEach((port) => {
          if (port.key.toLowerCase().includes(portQuery)) {
            results.push({
              id: node.id,
              label: `${node.instance_label} → ${port.key}`,
              type: "input_port",
            });
          }
        });
      });
    } else if (outMatch) {
      // Search output ports
      const portQuery = outMatch[1];
      payload.nodes.forEach((node) => {
        const ports = payload.ports[node.node_key];
        if (!ports) return;
        ports.outputs.forEach((port) => {
          if (port.key.toLowerCase().includes(portQuery)) {
            results.push({
              id: node.id,
              label: `${node.instance_label} ← ${port.key}`,
              type: "output_port",
            });
          }
        });
      });
    } else {
      // Default: search instance_label and node_key
      payload.nodes.forEach((node) => {
        if (node.instance_label.toLowerCase().includes(q)) {
          results.push({
            id: node.id,
            label: node.instance_label,
            type: "label",
          });
        }
        if (node.node_key.toLowerCase().includes(q)) {
          results.push({
            id: node.id,
            label: `(${node.node_key})`,
            type: "key",
          });
        }
      });
    }

    setResults(results.slice(0, 8));
  }, [query, payload]);

  const handleSelect = (result: SearchResult) => {
    const node = getNode(result.id);
    if (node) {
      setCenter(node.position.x, node.position.y, { zoom: 1.2, duration: 600 });
      setHighlighted(result.id);
      setTimeout(() => setHighlighted(null), 2000);
    }
    setQuery("");
    setOpen(false);
  };

  return (
    <div className="fixed top-4 right-4 z-40 w-96">
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          placeholder="Search nodes (or in:/out: ports)..."
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
        />

        {/* Results dropdown */}
        {open && results.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-lg shadow-lg z-50">
            {results.map((result) => (
              <button
                key={`${result.id}-${result.type}`}
                onClick={() => handleSelect(result)}
                className="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-gray-100 last:border-b-0 text-sm transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-gray-900">{result.label}</span>
                  <span className="text-xs text-gray-500">
                    {result.type === "label" && "label"}
                    {result.type === "key" && "key"}
                    {result.type === "input_port" && "in"}
                    {result.type === "output_port" && "out"}
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
