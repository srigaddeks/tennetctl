"use client";

import { use, useState } from "react";

import type { DashboardLayouts } from "@/features/monitoring/_components/dashboard-grid";

import { Modal } from "@/components/modal";
import { PageHeader } from "@/components/page-header";
import {
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Select,
  Skeleton,
  Textarea,
} from "@/components/ui";
import { DashboardGrid } from "@/features/monitoring/_components/dashboard-grid";
import {
  useCreatePanel,
  useDashboard,
  useUpdatePanel,
} from "@/features/monitoring/hooks/use-dashboards";
import type { PanelType } from "@/types/api";

type Params = { id: string };

const PANEL_TYPES: { value: PanelType; label: string }[] = [
  { value: "timeseries", label: "Timeseries (metrics)" },
  { value: "stat", label: "Stat (single value)" },
  { value: "table", label: "Table (metrics)" },
  { value: "log_stream", label: "Log stream" },
  { value: "trace_list", label: "Trace list" },
];

export default function DashboardDetailPage({
  params,
}: {
  params: Promise<Params>;
}) {
  const { id } = use(params);
  const { data, isLoading, isError, error, refetch } = useDashboard(id);
  const [editing, setEditing] = useState(false);
  const [layouts, setLayouts] = useState<DashboardLayouts>({});
  const [addOpen, setAddOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [panelType, setPanelType] = useState<PanelType>("timeseries");
  const [dslText, setDslText] = useState(
    '{\n  "target": "metrics",\n  "metric_key": "",\n  "timerange": {"last": "1h"},\n  "bucket": "5m",\n  "aggregate": "avg"\n}',
  );
  const [dslError, setDslError] = useState<string | null>(null);

  const createPanel = useCreatePanel();
  const updatePanel = useUpdatePanel();

  const saveLayouts = async () => {
    if (!data) return;
    const lg = layouts.lg ?? [];
    for (const l of lg) {
      const panel = data.panels.find((p) => p.id === l.i);
      if (!panel) continue;
      const current = panel.grid_pos ?? { x: 0, y: 0, w: 4, h: 4 };
      const next = { x: l.x, y: l.y, w: l.w, h: l.h };
      if (
        current.x !== next.x ||
        current.y !== next.y ||
        current.w !== next.w ||
        current.h !== next.h
      ) {
        await updatePanel.mutateAsync({
          dashboardId: data.id,
          panelId: panel.id,
          body: { grid_pos: next },
        });
      }
    }
    setEditing(false);
  };

  const submitPanel = async () => {
    if (!data) return;
    let dsl: Record<string, unknown>;
    try {
      dsl = JSON.parse(dslText);
    } catch (err) {
      setDslError(err instanceof Error ? err.message : "Invalid JSON");
      return;
    }
    setDslError(null);
    await createPanel.mutateAsync({
      dashboardId: data.id,
      body: {
        title: title || "Untitled panel",
        panel_type: panelType,
        dsl,
        grid_pos: { x: 0, y: 0, w: 6, h: 4 },
      },
    });
    setAddOpen(false);
    setTitle("");
  };

  return (
    <>
      <PageHeader
        title={data?.name ?? "Dashboard"}
        description={data?.description ?? undefined}
        testId="heading-monitoring-dashboard"
        breadcrumbs={[
          { label: "Monitoring", href: "/monitoring" },
          { label: "Dashboards", href: "/monitoring/dashboards" },
          { label: data?.name ?? "…" },
        ]}
        actions={
          data && (
            <div className="flex gap-2">
              {editing ? (
                <>
                  <Button variant="ghost" onClick={() => setEditing(false)}>
                    Cancel
                  </Button>
                  <Button onClick={saveLayouts} loading={updatePanel.isPending}>
                    Save layout
                  </Button>
                </>
              ) : (
                <>
                  <Button variant="secondary" onClick={() => setEditing(true)}>
                    Edit layout
                  </Button>
                  <Button
                    variant="accent"
                    onClick={() => setAddOpen(true)}
                    data-testid="monitoring-dashboard-add-panel"
                  >
                    + Add panel
                  </Button>
                </>
              )}
            </div>
          )
        }
      />

      <div className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in">
        {/* Dashboard meta strip */}
        {data && (
          <div
            className="mb-5 flex items-center gap-4 rounded border px-4 py-2.5"
            style={{
              background: "var(--bg-surface)",
              borderColor: "var(--border)",
            }}
          >
            <span
              className="label-caps"
              style={{ color: "var(--text-muted)" }}
            >
              Panels
            </span>
            <span
              className="font-mono-data text-[13px] font-semibold"
              style={{ color: "#9d6ef8" }}
            >
              {data.panels.length}
            </span>
            <span
              className="h-3 w-px"
              style={{ background: "var(--border)" }}
            />
            <span
              className="label-caps"
              style={{ color: "var(--text-muted)" }}
            >
              Updated
            </span>
            <span
              className="font-mono-data text-[12px]"
              style={{ color: "var(--text-secondary)" }}
            >
              {new Date(data.updated_at).toLocaleString()}
            </span>
            {typeof (data.layout as Record<string, unknown>)?.application_id === "string" && (
              <>
                <span
                  className="h-3 w-px"
                  style={{ background: "var(--border)" }}
                />
                <span
                  className="label-caps"
                  style={{ color: "var(--text-muted)" }}
                >
                  App
                </span>
                <span
                  className="font-mono-data text-[12px]"
                  style={{ color: "#4a9eff" }}
                >
                  {String((data.layout as Record<string, unknown>).application_id).slice(0, 8)}
                </span>
              </>
            )}
            {editing && (
              <>
                <span
                  className="h-3 w-px"
                  style={{ background: "var(--border)" }}
                />
                <span
                  className="label-caps"
                  style={{ color: "var(--warning)" }}
                >
                  Edit mode
                </span>
              </>
            )}
          </div>
        )}

        {isLoading && <Skeleton className="h-96 w-full" />}

        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}

        {data && data.panels.length === 0 && (
          <EmptyState
            title="No panels yet"
            description="Add a panel to start visualizing data on this dashboard."
            action={
              <Button onClick={() => setAddOpen(true)}>Add panel</Button>
            }
          />
        )}

        {data && data.panels.length > 0 && (
          <DashboardGrid
            panels={data.panels}
            editing={editing}
            onLayoutChange={setLayouts}
          />
        )}
      </div>

      <Modal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        title="Add panel"
        size="lg"
      >
        <div className="flex flex-col gap-4">
          <Field label="Title" htmlFor="panel-new-title" required>
            <Input
              id="panel-new-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              data-testid="monitoring-panel-title"
            />
          </Field>
          <Field label="Panel type" htmlFor="panel-new-type">
            <Select
              id="panel-new-type"
              value={panelType}
              onChange={(e) => setPanelType(e.target.value as PanelType)}
            >
              {PANEL_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </Select>
          </Field>
          <Field
            label="DSL (JSON)"
            htmlFor="panel-new-dsl"
            hint="Monitoring Query DSL — see ADR-029"
            error={dslError ?? undefined}
          >
            <Textarea
              id="panel-new-dsl"
              rows={10}
              value={dslText}
              onChange={(e) => setDslText(e.target.value)}
              className="font-mono text-xs"
            />
          </Field>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setAddOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={submitPanel}
              loading={createPanel.isPending}
              disabled={!title}
            >
              Create
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
