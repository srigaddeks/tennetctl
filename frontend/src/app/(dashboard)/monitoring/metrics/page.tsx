"use client";

import { useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Modal } from "@/components/modal";
import { Button, Field, Input, Select } from "@/components/ui";
import { MetricPicker } from "@/features/monitoring/_components/metric-picker";
import { MetricsChart } from "@/features/monitoring/_components/metrics-chart";
import { TimerangePicker } from "@/features/monitoring/_components/timerange-picker";
import {
  useCreateDashboard,
  useCreatePanel,
  useDashboards,
} from "@/features/monitoring/hooks/use-dashboards";
import type {
  Metric,
  MetricBucket,
  MetricsQuery,
  Timerange,
} from "@/types/api";

const PURPLE = "#9d6ef8";

const BUCKET_OPTIONS: { value: MetricBucket; label: string }[] = [
  { value: "1m", label: "1m" },
  { value: "5m", label: "5m" },
  { value: "1h", label: "1h" },
  { value: "1d", label: "1d" },
];

export default function MetricsPage() {
  const [metric, setMetric] = useState<Metric | null>(null);
  const [timerange, setTimerange] = useState<Timerange>({ last: "1h" });
  const [bucket, setBucket] = useState<MetricBucket>("5m");
  const [modalOpen, setModalOpen] = useState(false);
  const [newDashboardName, setNewDashboardName] = useState("");
  const [targetDashboardId, setTargetDashboardId] = useState<string>("");
  const [panelTitle, setPanelTitle] = useState("");

  const dashboards = useDashboards();
  const createDashboard = useCreateDashboard();
  const createPanel = useCreatePanel();

  const onAddToDashboard = async () => {
    if (!metric) return;
    let dashId = targetDashboardId;
    if (!dashId && newDashboardName) {
      const created = await createDashboard.mutateAsync({
        name: newDashboardName,
      });
      dashId = created.id;
    }
    if (!dashId) return;
    const dsl: MetricsQuery = {
      target: "metrics",
      metric_key: metric.key,
      timerange,
      bucket,
      aggregate: metric.kind === "counter" ? "rate" : "avg",
    };
    await createPanel.mutateAsync({
      dashboardId: dashId,
      body: {
        title: panelTitle || metric.key,
        panel_type: "timeseries",
        dsl: dsl as unknown as Record<string, unknown>,
        grid_pos: { x: 0, y: 0, w: 6, h: 4 },
      },
    });
    setModalOpen(false);
    setPanelTitle("");
    setNewDashboardName("");
    setTargetDashboardId("");
  };

  return (
    <>
      <PageHeader
        title="Metrics"
        description="Counters, gauges, and histograms — queried via Monitoring DSL."
        testId="heading-monitoring-metrics"
      />

      <div className="grid flex-1 grid-cols-1 gap-0 overflow-hidden lg:grid-cols-[300px_1fr] animate-fade-in">
        {/* Left panel: metric picker */}
        <div
          className="border-r overflow-y-auto"
          style={{
            borderColor: "var(--border)",
            background: "var(--bg-surface)",
          }}
        >
          <div
            className="border-b px-4 py-3"
            style={{ borderColor: "var(--border)" }}
          >
            <span
              className="label-caps"
              style={{ color: "var(--text-muted)" }}
            >
              Available metrics
            </span>
          </div>
          <div className="p-3 h-[calc(100dvh-160px)]">
            <MetricPicker
              selectedKey={metric?.key ?? null}
              onSelect={setMetric}
            />
          </div>
        </div>

        {/* Right panel: chart area */}
        <div
          className="flex flex-col overflow-y-auto"
          style={{ background: "var(--bg-base)" }}
        >
          {!metric ? (
            <div className="flex flex-1 flex-col items-center justify-center gap-4 p-12">
              <div
                className="flex h-12 w-12 items-center justify-center rounded"
                style={{
                  background: "rgba(157,110,248,0.08)",
                  border: "1px solid rgba(157,110,248,0.2)",
                }}
              >
                <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                  <polyline
                    points="2,18 7,11 11,14 15,7 20,9"
                    stroke={PURPLE}
                    strokeWidth="1.8"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <div className="text-center">
                <div
                  className="text-sm font-semibold mb-1"
                  style={{ color: "var(--text-primary)" }}
                >
                  Select a metric
                </div>
                <p
                  className="text-[12px]"
                  style={{ color: "var(--text-muted)" }}
                >
                  Choose a metric from the panel on the left to render a time-series chart.
                </p>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-0 p-0">
              {/* Metric header bar */}
              <div
                className="flex flex-wrap items-center justify-between gap-3 border-b px-6 py-3"
                style={{
                  borderColor: "var(--border)",
                  background: "var(--bg-surface)",
                }}
              >
                <div>
                  <div
                    className="font-mono-data text-[13px] font-semibold"
                    style={{ color: "var(--text-primary)" }}
                  >
                    {metric.key}
                  </div>
                  <div
                    className="text-[11px]"
                    style={{ color: "var(--text-muted)" }}
                  >
                    {metric.description ?? metric.kind}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {/* Kind badge */}
                  <span
                    className="label-caps px-2 py-1 rounded"
                    style={{
                      background: "rgba(157,110,248,0.1)",
                      color: PURPLE,
                      border: "1px solid rgba(157,110,248,0.25)",
                    }}
                  >
                    {metric.kind}
                  </span>

                  {/* Bucket selector */}
                  <div className="flex items-center gap-1">
                    {BUCKET_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        onClick={() => setBucket(opt.value)}
                        data-testid={bucket === opt.value ? "monitoring-metrics-bucket" : undefined}
                        className="h-7 px-2.5 rounded text-[11px] font-mono font-medium transition-all"
                        style={{
                          background:
                            bucket === opt.value
                              ? "rgba(157,110,248,0.15)"
                              : "var(--bg-elevated)",
                          color:
                            bucket === opt.value
                              ? PURPLE
                              : "var(--text-secondary)",
                          border: `1px solid ${
                            bucket === opt.value
                              ? "rgba(157,110,248,0.4)"
                              : "var(--border)"
                          }`,
                        }}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>

                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setModalOpen(true)}
                    data-testid="monitoring-metrics-add-to-dash"
                  >
                    + Dashboard
                  </Button>
                </div>
              </div>

              {/* Timerange picker */}
              <div
                className="border-b px-6 py-3"
                style={{
                  borderColor: "var(--border)",
                  background: "var(--bg-surface)",
                }}
              >
                <TimerangePicker value={timerange} onChange={setTimerange} />
              </div>

              {/* Chart */}
              <div className="p-6">
                <MetricsChart
                  metric={metric}
                  timerange={timerange}
                  bucket={bucket}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Add panel to dashboard"
        size="md"
      >
        <div className="flex flex-col gap-4">
          <Field label="Panel title" htmlFor="panel-title">
            <Input
              id="panel-title"
              value={panelTitle}
              onChange={(e) => setPanelTitle(e.target.value)}
              placeholder={metric?.key ?? ""}
            />
          </Field>
          <Field label="Existing dashboard" htmlFor="dash-select">
            <Select
              id="dash-select"
              value={targetDashboardId}
              onChange={(e) => setTargetDashboardId(e.target.value)}
            >
              <option value="">— Create new below —</option>
              {dashboards.data?.items.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </Select>
          </Field>
          {!targetDashboardId && (
            <Field label="Or new dashboard name" htmlFor="dash-new">
              <Input
                id="dash-new"
                value={newDashboardName}
                onChange={(e) => setNewDashboardName(e.target.value)}
                placeholder="My metrics dashboard"
              />
            </Field>
          )}
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={onAddToDashboard}
              loading={createPanel.isPending || createDashboard.isPending}
              disabled={!targetDashboardId && !newDashboardName}
            >
              Add panel
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
