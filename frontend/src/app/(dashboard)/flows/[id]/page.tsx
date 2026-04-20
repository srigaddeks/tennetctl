/**
 * Flow detail page with version sidebar.
 * Plan 44-01 implementation.
 */

"use client";

import { useFlow } from "@/features/catalog/hooks/use-flows";
import Link from "next/link";
import { useParams } from "next/navigation";

export default function FlowDetailPage() {
  const params = useParams();
  const flowId = params.id as string;
  const { data: flow, isLoading, error } = useFlow(flowId);

  if (isLoading) {
    return <div className="text-center py-8 text-gray-500">Loading...</div>;
  }

  if (error || !flow) {
    return (
      <div className="text-center py-8 text-red-500">
        Failed to load flow
      </div>
    );
  }

  // Find latest published version
  const versions = flow.versions ?? [];
  const latestPublished = versions.find((v) => v.status === "published") ||
    versions[0] || null;

  if (!latestPublished) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {flow.display_name || flow.slug}
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            No published versions available
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Main content */}
      <div className="lg:col-span-3">
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {flow.display_name || flow.slug}
            </h1>
            <p className="mt-1 text-sm text-gray-600 font-mono">
              {flow.slug}
            </p>
          </div>

          {latestPublished && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Latest Version
              </h2>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">
                    Version {latestPublished.version_number}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {latestPublished.status}
                  </p>
                </div>
                <Link
                  href={`/flows/${flowId}/versions/${latestPublished.id}`}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
                >
                  View Canvas
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Sidebar */}
      <div className="lg:col-span-1">
        <div className="bg-white border border-gray-200 rounded-lg p-4 sticky top-6">
          <h3 className="font-semibold text-gray-900 mb-3">Versions</h3>
          <div className="space-y-2">
            {versions.length === 0 ? (
              <p className="text-sm text-gray-500">No versions</p>
            ) : (
              versions.map((version) => (
                <Link
                  key={version.id}
                  href={`/flows/${flowId}/versions/${version.id}`}
                  className={`block px-3 py-2 rounded text-sm transition-colors ${
                    latestPublished.id === version.id
                      ? "bg-blue-50 text-blue-900 font-medium"
                      : "text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  <div className="font-medium">v{version.version_number}</div>
                  <div className="text-xs opacity-75">{version.status}</div>
                </Link>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
