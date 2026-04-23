"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { PageHeader } from "@/components/page-header";
import { Badge, ErrorState, Skeleton, StatCard } from "@/components/ui";
import { useFlow } from "@/features/catalog/hooks/use-flows";

function relativeTime(dateStr: string): string {
  const now = new Date();
  const then = new Date(dateStr);
  const seconds = Math.floor((now.getTime() - then.getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

const VERSION_STATUS_TONE: Record<string, "success" | "warning" | "default"> = {
  published: "success",
  draft: "warning",
  archived: "default",
};

export default function FlowDetailPage() {
  const params = useParams();
  const flowId = params.id as string;
  const { data: flow, isLoading, error } = useFlow(flowId);

  if (isLoading) {
    return (
      <div className="flex flex-1 flex-col animate-fade-in">
        <PageHeader title="Flow" testId="heading-flow-detail" />
        <div className="px-6 py-5 space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      </div>
    );
  }

  if (error || !flow) {
    return (
      <div className="flex flex-1 flex-col animate-fade-in">
        <PageHeader title="Flow" testId="heading-flow-detail" />
        <div className="px-6 py-5">
          <ErrorState
            message={error instanceof Error ? error.message : "Failed to load flow"}
          />
        </div>
      </div>
    );
  }

  const versions = flow.versions ?? [];
  const latestPublished =
    versions.find((v) => v.status === "published") || versions[0] || null;

  const publishedVersions = versions.filter((v) => v.status === "published");
  const draftVersions = versions.filter((v) => v.status === "draft");

  return (
    <div className="flex flex-1 flex-col animate-fade-in">
      <PageHeader
        title={flow.display_name ?? flow.slug}
        description={`Sub-feature: ${flow.sub_feature_key} · Module: ${flow.module}`}
        testId="heading-flow-detail"
        breadcrumbs={[
          { label: "Flows", href: "/flows" },
          { label: flow.slug },
        ]}
        actions={
          latestPublished ? (
            <Link
              href={`/flows/${flowId}/versions/${latestPublished.id}`}
              className="inline-flex items-center gap-1.5 rounded border px-3 py-1.5 text-xs font-medium transition-colors"
              style={{
                background: "var(--accent-muted)",
                borderColor: "var(--accent)",
                color: "var(--accent)",
              }}
            >
              Open Canvas
            </Link>
          ) : undefined
        }
      />

      <div className="flex-1 overflow-y-auto px-6 py-5">
        {/* Stat row */}
        <div className="mb-6 grid grid-cols-3 gap-3">
          <StatCard
            label="Versions"
            value={versions.length}
            accent="blue"
          />
          <StatCard
            label="Published"
            value={publishedVersions.length}
            accent="green"
          />
          <StatCard
            label="Draft"
            value={draftVersions.length}
            accent="amber"
          />
        </div>

        <div className="grid gap-5 lg:grid-cols-3">
          {/* Main content */}
          <div className="lg:col-span-2 space-y-5">
            {/* Flow metadata */}
            <div
              className="rounded border p-5"
              style={{
                background: "var(--bg-surface)",
                borderColor: "var(--border)",
              }}
            >
              <h2
                className="label-caps mb-4 text-xs"
                style={{ color: "var(--text-muted)" }}
              >
                Flow metadata
              </h2>
              <dl className="grid grid-cols-2 gap-3">
                {[
                  { label: "Slug", value: flow.slug, mono: true },
                  { label: "Module", value: flow.module, mono: true },
                  {
                    label: "Sub-feature",
                    value: flow.sub_feature_key,
                    mono: true,
                  },
                  {
                    label: "Status",
                    value: flow.is_active ? "active" : "inactive",
                    mono: false,
                  },
                  {
                    label: "Created",
                    value: new Date(flow.created_at).toLocaleString(),
                    mono: false,
                  },
                  {
                    label: "Updated",
                    value: relativeTime(flow.updated_at),
                    mono: false,
                  },
                ].map(({ label, value, mono }) => (
                  <div key={label}>
                    <dt
                      className="label-caps mb-1 text-[10px]"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {label}
                    </dt>
                    <dd
                      className={mono ? "font-mono-data text-xs" : "text-xs"}
                      style={{ color: "var(--text-primary)" }}
                    >
                      {value}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>

            {/* Latest published */}
            {latestPublished && (
              <div
                className="rounded border p-5"
                style={{
                  background: "var(--bg-surface)",
                  borderColor: "var(--border)",
                }}
              >
                <div className="mb-4 flex items-center justify-between">
                  <h2
                    className="label-caps text-xs"
                    style={{ color: "var(--text-muted)" }}
                  >
                    Latest version
                  </h2>
                  <Badge
                    tone={VERSION_STATUS_TONE[latestPublished.status] ?? "default"}
                    dot
                  >
                    {latestPublished.status}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <span
                      className="font-mono-data text-lg font-bold"
                      style={{ color: "#7ef7c8" }}
                    >
                      v{latestPublished.version_number}
                    </span>
                    <span
                      className="ml-3 text-xs"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {latestPublished.published_at
                        ? `Published ${new Date(latestPublished.published_at).toLocaleDateString()}`
                        : `Created ${new Date(latestPublished.created_at).toLocaleDateString()}`}
                    </span>
                  </div>
                  <Link
                    href={`/flows/${flowId}/versions/${latestPublished.id}`}
                    className="inline-flex items-center gap-1.5 rounded border px-3 py-1.5 text-xs font-medium transition-colors"
                    style={{
                      background: "var(--accent-muted)",
                      borderColor: "var(--accent)",
                      color: "var(--accent)",
                    }}
                  >
                    View Canvas →
                  </Link>
                </div>
              </div>
            )}

            {versions.length === 0 && (
              <div
                className="rounded border p-8 text-center"
                style={{
                  background: "var(--bg-surface)",
                  borderColor: "var(--border)",
                }}
              >
                <p
                  className="text-sm"
                  style={{ color: "var(--text-muted)" }}
                >
                  No versions available for this flow.
                </p>
              </div>
            )}
          </div>

          {/* Sidebar — versions list */}
          <div className="lg:col-span-1">
            <div
              className="sticky top-6 rounded border"
              style={{
                background: "var(--bg-surface)",
                borderColor: "var(--border)",
              }}
            >
              <div
                className="border-b px-4 py-3"
                style={{ borderColor: "var(--border)" }}
              >
                <h3
                  className="label-caps text-xs"
                  style={{ color: "var(--text-muted)" }}
                >
                  All versions ({versions.length})
                </h3>
              </div>
              <div className="p-2">
                {versions.length === 0 ? (
                  <p
                    className="px-2 py-4 text-center text-xs"
                    style={{ color: "var(--text-muted)" }}
                  >
                    No versions
                  </p>
                ) : (
                  <ul className="space-y-1">
                    {versions.map((version) => {
                      const isActive = latestPublished?.id === version.id;
                      return (
                        <li key={version.id}>
                          <Link
                            href={`/flows/${flowId}/versions/${version.id}`}
                            className="flex items-center justify-between rounded px-3 py-2 transition-colors"
                            style={{
                              background: isActive
                                ? "var(--accent-muted)"
                                : "transparent",
                              borderLeft: isActive
                                ? "2px solid var(--accent)"
                                : "2px solid transparent",
                            }}
                          >
                            <span
                              className="font-mono-data text-xs font-medium"
                              style={{
                                color: isActive
                                  ? "var(--accent)"
                                  : "var(--text-primary)",
                              }}
                            >
                              v{version.version_number}
                            </span>
                            <Badge
                              tone={
                                VERSION_STATUS_TONE[version.status] ?? "default"
                              }
                            >
                              {version.status}
                            </Badge>
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
