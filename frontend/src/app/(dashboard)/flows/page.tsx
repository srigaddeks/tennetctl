"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header";
import {
  Badge,
  EmptyState,
  ErrorState,
  Input,
  Select,
  Skeleton,
  StatCard,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import { useFlows } from "@/features/catalog/hooks/use-flows";

function relativeTime(dateStr: string): string {
  const now = new Date();
  const then = new Date(dateStr);
  const seconds = Math.floor((now.getTime() - then.getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

const STATUS_TONE: Record<string, "success" | "warning" | "default"> = {
  published: "success",
  draft: "warning",
  archived: "default",
};

export default function FlowsPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");

  const { data, isLoading, isError, error, refetch } = useFlows({
    q: search || undefined,
    status: statusFilter || undefined,
    limit: 100,
  });

  const flows = data?.items ?? [];

  const publishedCount = useMemo(
    () => flows.filter((f) => f.is_active).length,
    [flows],
  );
  const draftCount = useMemo(
    () => flows.filter((f) => !f.is_active && f.version_count > 0).length,
    [flows],
  );
  const noVersionCount = useMemo(
    () => flows.filter((f) => f.version_count === 0).length,
    [flows],
  );

  return (
    <>
      <PageHeader
        title="Flows"
        description="DAG workflow definitions. Each flow is versioned and immutable once published."
        testId="heading-flows"
        actions={
          <Link
            href="/catalog"
            className="text-xs transition-colors"
            style={{ color: "var(--text-secondary)" }}
          >
            View catalog →
          </Link>
        }
      />

      <div className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in">
        {/* Stat cards */}
        <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard
            label="Total Flows"
            value={data?.total ?? 0}
            accent="blue"
          />
          <StatCard
            label="Active"
            value={publishedCount}
            accent="green"
          />
          <StatCard
            label="Draft"
            value={draftCount}
            accent="amber"
          />
          <StatCard
            label="No Versions"
            value={noVersionCount}
            accent="red"
          />
        </div>

        {/* Toolbar */}
        <div
          className="mb-5 flex flex-wrap items-center gap-3 rounded border px-4 py-3"
          style={{ background: "var(--bg-surface)", borderColor: "var(--border)" }}
        >
          <Input
            type="search"
            placeholder="Search by slug or name…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-sm"
            data-testid="flows-search"
          />
          <div className="flex items-center gap-2">
            <span
              className="label-caps text-[11px]"
              style={{ color: "var(--text-muted)" }}
            >
              Status
            </span>
            <Select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-36"
              data-testid="flows-status-filter"
            >
              <option value="">All</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </Select>
          </div>
          {data && (
            <span
              className="font-mono-data ml-auto text-xs"
              style={{ color: "var(--text-muted)" }}
            >
              {flows.length} / {data.total}
            </span>
          )}
        </div>

        {/* Table */}
        {isLoading && (
          <div className="flex flex-col gap-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        )}

        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Failed to load flows"}
            retry={() => refetch()}
          />
        )}

        {!isLoading && !isError && flows.length === 0 && (
          <EmptyState
            title="No flows"
            description="Flows are defined via feature manifests. No flows match the current filters."
          />
        )}

        {!isLoading && !isError && flows.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>Slug</TH>
                <TH>Sub-feature</TH>
                <TH>Status</TH>
                <TH className="text-right">Versions</TH>
                <TH className="text-right">Updated</TH>
              </tr>
            </THead>
            <TBody>
              {flows.map((flow) => (
                <TR key={flow.id} data-testid={`flow-row-${flow.id}`}>
                  <TD>
                    <Link
                      href={`/flows/${flow.id}`}
                      className="transition-colors"
                      style={{ color: "#7ef7c8" }}
                    >
                      <span className="font-mono-data text-xs">
                        {flow.slug}
                      </span>
                    </Link>
                    {flow.display_name && (
                      <span
                        className="ml-2 text-xs"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {flow.display_name}
                      </span>
                    )}
                  </TD>
                  <TD>
                    <span
                      className="font-mono-data text-xs"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {flow.sub_feature_key}
                    </span>
                  </TD>
                  <TD>
                    <Badge
                      tone={flow.is_active ? "success" : "warning"}
                      dot
                    >
                      {flow.is_active ? "active" : "inactive"}
                    </Badge>
                  </TD>
                  <TD className="text-right">
                    <span
                      className="font-mono-data text-xs"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      {flow.version_count}
                    </span>
                  </TD>
                  <TD className="text-right">
                    <span
                      className="font-mono-data text-xs"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {relativeTime(flow.updated_at)}
                    </span>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </div>
    </>
  );
}
