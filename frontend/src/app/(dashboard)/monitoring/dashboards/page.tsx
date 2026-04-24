"use client";

import { useState } from "react";
import Link from "next/link";

import { Modal } from "@/components/modal";
import { ApplicationScopeBar } from "@/components/application-scope-bar";
import { PageHeader } from "@/components/page-header";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Skeleton,
  Textarea,
} from "@/components/ui";
import {
  useCreateDashboard,
  useDashboards,
  useDeleteDashboard,
} from "@/features/monitoring/hooks/use-dashboards";

const PURPLE = "#9d6ef8";

// Mini grid thumbnail — decorative placeholder
function DashboardThumbnail({ panelCount }: { panelCount: number }) {
  const cells = Math.min(panelCount, 4);
  return (
    <div
      className="relative h-24 w-full overflow-hidden rounded-t"
      style={{ background: "var(--bg-base)" }}
    >
      {/* Grid pattern */}
      <div className="absolute inset-0 bg-grid-dots opacity-30" />

      {/* Fake panel blocks */}
      <div className="absolute inset-2 grid grid-cols-2 gap-1.5">
        {[...Array(Math.max(cells, 2))].map((_, i) => (
          <div
            key={i}
            className="rounded"
            style={{
              background:
                i === 0
                  ? "rgba(157,110,248,0.15)"
                  : "rgba(157,110,248,0.07)",
              border: "1px solid rgba(157,110,248,0.2)",
            }}
          />
        ))}
      </div>

      {/* Fake sparkline on first panel */}
      <svg
        className="absolute left-3 bottom-5"
        width="52"
        height="20"
        viewBox="0 0 52 20"
        fill="none"
      >
        <polyline
          points="0,15 8,10 16,12 24,6 32,8 40,4 52,7"
          stroke={PURPLE}
          strokeWidth="1.5"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity="0.7"
        />
      </svg>
    </div>
  );
}

export default function DashboardsPage() {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [appFilter, setAppFilter] = useState<string | null>(null);

  const { data, isLoading, isError, error, refetch } = useDashboards();
  const create = useCreateDashboard();
  const del = useDeleteDashboard();

  const submit = async () => {
    if (!name) return;
    await create.mutateAsync({ name, description: description || null });
    setOpen(false);
    setName("");
    setDescription("");
  };

  return (
    <>
      <PageHeader
        title="Dashboards"
        description="Grid-layout dashboards of panels. Each panel runs a DSL query."
        testId="heading-monitoring-dashboards"
        actions={
          <Button
            variant="accent"
            onClick={() => setOpen(true)}
            data-testid="monitoring-dashboard-new"
          >
            + New dashboard
          </Button>
        }
      />

      <div className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in">
        <div className="mb-5">
          <ApplicationScopeBar
            appId={appFilter}
            onChange={setAppFilter}
            label="Dashboards for application"
          />
        </div>

        {isLoading && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-48 w-full" />
            ))}
          </div>
        )}

        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}

        {data && data.items.length === 0 && (
          <EmptyState
            title="No dashboards yet"
            description="Create a dashboard then add panels to start visualizing your metrics, logs, and traces."
            action={
              <Button onClick={() => setOpen(true)}>New dashboard</Button>
            }
          />
        )}

        {data && data.items.length > 0 && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((d) => (
              <div
                key={d.id}
                className="group relative flex flex-col overflow-hidden rounded border transition-all duration-200"
                style={{
                  background: "var(--bg-surface)",
                  borderColor: "var(--border)",
                }}
                data-testid={`monitoring-dashboard-card-${d.id}`}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(157,110,248,0.5)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border)";
                }}
              >
                {/* Thumbnail */}
                <Link href={`/monitoring/dashboards/${d.id}`}>
                  <DashboardThumbnail panelCount={d.panel_count} />
                </Link>

                {/* Card body */}
                <div className="flex flex-col gap-2 p-4">
                  <div className="flex items-start justify-between gap-2">
                    <Link
                      href={`/monitoring/dashboards/${d.id}`}
                      className="text-[14px] font-semibold leading-snug hover:underline"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {d.name}
                    </Link>
                    {d.shared && (
                      <Badge tone="blue">Shared</Badge>
                    )}
                  </div>

                  {d.description && (
                    <p
                      className="text-[12px] leading-relaxed"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      {d.description}
                    </p>
                  )}

                  <div
                    className="flex items-center gap-3 text-[11px]"
                    style={{ color: "var(--text-muted)" }}
                  >
                    <span
                      className="font-mono-data"
                      style={{ color: PURPLE }}
                    >
                      {d.panel_count} panel{d.panel_count !== 1 ? "s" : ""}
                    </span>
                    <span style={{ color: "var(--border-bright)" }}>·</span>
                    <span>
                      Updated {new Date(d.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {/* Delete button (hover reveal) */}
                <button
                  type="button"
                  onClick={() => {
                    if (confirm(`Delete dashboard "${d.name}"?`)) {
                      void del.mutateAsync(d.id);
                    }
                  }}
                  data-testid={`monitoring-dashboard-delete-${d.id}`}
                  className="absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded text-[11px] opacity-0 transition-opacity group-hover:opacity-100"
                  style={{
                    background: "var(--danger-muted)",
                    color: "var(--danger)",
                    border: "1px solid rgba(255,63,85,0.3)",
                  }}
                  aria-label="Delete dashboard"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="New dashboard"
        size="md"
      >
        <div className="flex flex-col gap-4">
          <Field label="Name" htmlFor="dash-name" required>
            <Input
              id="dash-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              data-testid="monitoring-dashboard-name"
            />
          </Field>
          <Field label="Description" htmlFor="dash-desc">
            <Textarea
              id="dash-desc"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </Field>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button onClick={submit} loading={create.isPending} disabled={!name}>
              Create
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
