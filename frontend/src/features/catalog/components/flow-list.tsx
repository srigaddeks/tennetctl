/**
 * Flow list table component.
 * Plan 44-01 implementation.
 */

"use client";

import { useState } from "react";
import Link from "next/link";
import { useFlows } from "../hooks/use-flows";

function relativeTime(dateStr: string): string {
  const now = new Date();
  const then = new Date(dateStr);
  const seconds = Math.floor((now.getTime() - then.getTime()) / 1000);

  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

export function FlowList() {
  const [search, setSearch] = useState("");
  const { data, isLoading, error } = useFlows({ q: search, limit: 50 });

  const flows = data?.items ?? [];

  return (
    <div className="space-y-4">
      {/* Search bar */}
      <div>
        <input
          type="text"
          placeholder="Search flows by slug..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="text-center py-8 text-gray-500">Loading...</div>
      ) : error ? (
        <div className="text-center py-8 text-red-500">
          Failed to load flows
        </div>
      ) : flows.length === 0 ? (
        <div className="text-center py-8 text-gray-500">No flows found</div>
      ) : (
        <div className="overflow-x-auto border border-gray-200 rounded-lg">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left font-semibold text-gray-900">
                  Name
                </th>
                <th className="px-6 py-3 text-left font-semibold text-gray-900">
                  Slug
                </th>
                <th className="px-6 py-3 text-center font-semibold text-gray-900">
                  Status
                </th>
                <th className="px-6 py-3 text-center font-semibold text-gray-900">
                  Versions
                </th>
                <th className="px-6 py-3 text-left font-semibold text-gray-900">
                  Updated
                </th>
              </tr>
            </thead>
            <tbody>
              {flows.map((flow) => (
                <tr
                  key={flow.id}
                  className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                >
                  <td className="px-6 py-3">
                    <Link
                      href={`/flows/${flow.id}`}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      {flow.display_name || flow.slug}
                    </Link>
                  </td>
                  <td className="px-6 py-3 font-mono text-gray-700">
                    {flow.slug}
                  </td>
                  <td className="px-6 py-3 text-center">
                    <span
                      className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                        flow.is_active
                          ? "bg-green-100 text-green-900"
                          : "bg-gray-100 text-gray-900"
                      }`}
                    >
                      {flow.is_active ? "active" : "inactive"}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-center text-gray-700">
                    {flow.version_count}
                  </td>
                  <td className="px-6 py-3 text-gray-600">
                    {relativeTime(flow.updated_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination info */}
      {data && (
        <div className="text-xs text-gray-500 text-center">
          Showing {flows.length} of {data.total} flows
        </div>
      )}
    </div>
  );
}
