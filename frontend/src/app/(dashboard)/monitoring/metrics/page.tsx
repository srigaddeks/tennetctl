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
      <div className="grid flex-1 grid-cols-1 gap-4 overflow-hidden px-8 py-6 lg:grid-cols-[320px_1fr]">
        <div className="h-[calc(100dvh-220px)]">
          <MetricPicker
            selectedKey={metric?.key ?? null}
            onSelect={setMetric}
          />
        </div>
        <div className="flex flex-col gap-4 overflow-y-auto">
          {!metric && (
            <p className="rounded-lg border border-dashed border-zinc-300 bg-white p-6 text-center text-sm text-zinc-500 dark:border-zinc-700 dark:bg-zinc-950">
              Select a metric on the left to chart it.
            </p>
          )}
          {metric && (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="font-mono text-sm font-semibold text-zinc-900 dark:text-zinc-50">
                    {metric.key}
                  </h2>
                  <p className="text-xs text-zinc-500">{metric.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Select
                    value={bucket}
                    onChange={(e) => setBucket(e.target.value as MetricBucket)}
                    className="h-9 w-auto text-xs"
                    data-testid="monitoring-metrics-bucket"
                  >
                    <option value="1m">1m</option>
                    <option value="5m">5m</option>
                    <option value="1h">1h</option>
                    <option value="1d">1d</option>
                  </Select>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setModalOpen(true)}
                    data-testid="monitoring-metrics-add-to-dash"
                  >
                    Add to dashboard
                  </Button>
                </div>
              </div>
              <TimerangePicker value={timerange} onChange={setTimerange} />
              <MetricsChart
                metric={metric}
                timerange={timerange}
                bucket={bucket}
              />
            </>
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
