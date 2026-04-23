"use client";

import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { Badge, Button, Skeleton, StatCard } from "@/components/ui";
import { AlertList } from "@/features/monitoring/_components/alert-list";
import { useAlertEvents } from "@/features/monitoring/hooks/use-alerts";

export default function AlertsPage() {
  const all = useAlertEvents();
  const firing = useAlertEvents("firing");

  const totalAlerts = all.data?.items.length ?? 0;
  const firingCount = firing.data?.items.length ?? 0;
  const resolvedCount = totalAlerts - firingCount;
  const silencedCount = (all.data?.items ?? []).filter((a) => a.silenced).length;

  return (
    <>
      <PageHeader
        title="Alerts"
        description="Active and recent alerts. Filter by state or severity. Silence to suppress notifications."
        testId="heading-monitoring-alerts"
        actions={
          <div className="flex items-center gap-2">
            <Link href="/monitoring/alerts/silences">
              <Button variant="secondary" size="sm">
                Silences
              </Button>
            </Link>
            <Link href="/monitoring/alerts/rules">
              <Button variant="secondary" size="sm" data-testid="alerts-goto-rules">
                Manage rules
              </Button>
            </Link>
          </div>
        }
      />

      <div className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in">
        <div className="flex flex-col gap-5">

          {/* Alert state strip */}
          {all.isLoading ? (
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <StatCard
                label="Firing"
                value={String(firingCount)}
                sub="Actively triggering now"
                accent={firingCount > 0 ? "red" : "green"}
              />
              <StatCard
                label="Resolved"
                value={String(resolvedCount)}
                sub="Recovered in window"
                accent="green"
              />
              <StatCard
                label="Silenced"
                value={String(silencedCount)}
                sub="Notifications muted"
                accent="amber"
              />
              <StatCard
                label="Total"
                value={String(totalAlerts)}
                sub="All events in window"
                accent="blue"
              />
            </div>
          )}

          {/* Status legend */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <Badge tone="danger" dot>firing</Badge>
            </div>
            <div className="flex items-center gap-1.5">
              <Badge tone="warning" dot>pending</Badge>
            </div>
            <div className="flex items-center gap-1.5">
              <Badge tone="success" dot>resolved</Badge>
            </div>
            <div className="flex items-center gap-1.5">
              <Badge tone="purple">silenced</Badge>
            </div>
            <span
              className="ml-auto label-caps"
              style={{ color: "var(--text-muted)" }}
            >
              Auto-refreshes every 15s
            </span>
          </div>

          {/* Alert list component */}
          <AlertList />
        </div>
      </div>
    </>
  );
}
