"use client";

import { PageHeader } from "@/components/page-header";
import { Badge, Button, ErrorState, Skeleton, StatCard } from "@/components/ui";
import { useSystemHealth } from "@/features/system/hooks/use-system-health";

// ─── Status dot ──────────────────────────────────────────────────────────────

function StatusDot({ status }: { status: "healthy" | "degraded" | "down" | "disabled" | "unknown" }) {
  const colors: Record<string, string> = {
    healthy: "var(--success)",
    degraded: "var(--warning)",
    down: "var(--danger)",
    disabled: "var(--text-muted)",
    unknown: "var(--text-muted)",
  };
  return (
    <span
      className="inline-block h-2 w-2 rounded-full"
      style={{ background: colors[status] ?? colors.unknown }}
    />
  );
}

// ─── Service card ──────────────────────────────────────────────────────────────

function ServiceCard({
  title,
  status,
  testId,
  children,
}: {
  title: string;
  status: "healthy" | "degraded" | "down" | "disabled" | "unknown";
  testId: string;
  children: React.ReactNode;
}) {
  const accentMap: Record<string, string> = {
    healthy: "var(--success)",
    degraded: "var(--warning)",
    down: "var(--danger)",
    disabled: "var(--border-bright)",
    unknown: "var(--border-bright)",
  };
  return (
    <section
      className="rounded border overflow-hidden"
      style={{
        background: "var(--bg-surface)",
        borderColor: "var(--border)",
        borderLeft: `3px solid ${accentMap[status]}`,
      }}
      data-testid={testId}
    >
      <div
        className="flex items-center justify-between border-b px-4 py-3"
        style={{ borderColor: "var(--border)" }}
      >
        <div className="flex items-center gap-2">
          <StatusDot status={status} />
          <h2
            className="text-xs font-semibold"
            style={{ color: "var(--text-primary)" }}
          >
            {title}
          </h2>
        </div>
        <StatusBadge status={status} />
      </div>
      <div className="px-4 py-3">{children}</div>
    </section>
  );
}

function StatusBadge({ status }: { status: string }) {
  const toneMap: Record<string, "success" | "warning" | "danger" | "default"> = {
    healthy: "success",
    degraded: "warning",
    down: "danger",
    disabled: "default",
    unknown: "default",
  };
  return (
    <Badge tone={toneMap[status] ?? "default"}>
      {status}
    </Badge>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
        {label}
      </span>
      <span
        className="font-mono-data text-xs"
        style={{ color: "var(--text-primary)" }}
      >
        {value}
      </span>
    </div>
  );
}

// ─── Sub-cards ────────────────────────────────────────────────────────────────

function DatabaseCard({ report }: { report: import("@/types/api").SystemHealthReport }) {
  const { db, pool } = report;
  const status = db.ok ? "healthy" : "down";
  return (
    <ServiceCard title="Database" status={status} testId="health-card-db">
      {db.ok ? (
        <div className="space-y-0.5">
          <MetaRow label="Pool size" value={String(pool.size)} />
          <MetaRow label="Idle" value={String(pool.free)} />
          <MetaRow label="In use" value={String(pool.busy)} />
        </div>
      ) : (
        <p className="text-xs" style={{ color: "var(--danger)" }}>
          {db.error ?? "Connection failed"}
        </p>
      )}
    </ServiceCard>
  );
}

function VaultCard({ report }: { report: import("@/types/api").SystemHealthReport }) {
  const { vault } = report;
  const status = !vault.enabled ? "disabled" : vault.ok ? "healthy" : "down";
  return (
    <ServiceCard title="Vault" status={status} testId="health-card-vault">
      {!vault.enabled ? (
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          Vault module not in TENNETCTL_MODULES.
        </p>
      ) : vault.ok ? (
        <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
          Root key loaded. Vault initialized.
        </p>
      ) : (
        <p className="text-xs" style={{ color: "var(--danger)" }}>
          Vault enabled but client not initialized.
        </p>
      )}
    </ServiceCard>
  );
}

function CatalogCard({ report }: { report: import("@/types/api").SystemHealthReport }) {
  const { catalog } = report;
  const hasReport = catalog.features !== null || catalog.sub_features !== null || catalog.nodes !== null;
  const status = hasReport ? "healthy" : "unknown";
  return (
    <ServiceCard title="Catalog" status={status} testId="health-card-catalog">
      {hasReport ? (
        <div className="space-y-0.5">
          <MetaRow label="Features" value={String(catalog.features ?? "—")} />
          <MetaRow label="Sub-features" value={String(catalog.sub_features ?? "—")} />
          <MetaRow label="Nodes" value={String(catalog.nodes ?? "—")} />
        </div>
      ) : (
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          No catalog upsert report this boot.
        </p>
      )}
    </ServiceCard>
  );
}

function NatsCard({ report }: { report: import("@/types/api").SystemHealthReport }) {
  const { nats } = report;
  const status = nats.configured ? "healthy" : "disabled";
  return (
    <ServiceCard title="NATS JetStream" status={status} testId="health-card-nats">
      <div className="space-y-0.5">
        <MetaRow label="Host" value={nats.url_host || "—"} />
        <p
          className="pt-1 text-[11px]"
          style={{ color: "var(--text-muted)" }}
        >
          Live-probe status arriving in v0.3.0 alerting.
        </p>
      </div>
    </ServiceCard>
  );
}

function ModulesCard({ report }: { report: import("@/types/api").SystemHealthReport }) {
  const enabledSet = new Set(report.modules.enabled);
  const enabledCount = report.modules.enabled.length;
  const availableCount = report.modules.available.length;
  return (
    <ServiceCard
      title={`Modules — ${enabledCount} / ${availableCount} enabled`}
      status="healthy"
      testId="health-card-modules"
    >
      <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {report.modules.available.map((m) => {
          const on = enabledSet.has(m);
          return (
            <li
              key={m}
              className="flex items-center justify-between rounded border px-3 py-2"
              style={{
                background: on ? "var(--success-muted)" : "var(--bg-base)",
                borderColor: on ? "var(--success)" : "var(--border)",
              }}
              data-testid={`health-module-${m}`}
            >
              <span
                className="font-mono-data text-xs"
                style={{ color: on ? "var(--success)" : "var(--text-muted)" }}
              >
                {m}
              </span>
              <Badge tone={on ? "success" : "default"}>{on ? "on" : "off"}</Badge>
            </li>
          );
        })}
      </ul>
    </ServiceCard>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function SystemHealthPage() {
  const { data, isLoading, isError, error, refetch, isFetching } = useSystemHealth();

  const overallStatus = data
    ? data.db.ok
      ? "healthy"
      : "down"
    : "unknown";

  const overallColor: Record<string, string> = {
    healthy: "var(--success)",
    down: "var(--danger)",
    unknown: "var(--text-muted)",
  };

  return (
    <>
      <PageHeader
        title="System Health"
        description="Subsystem status at a glance. Auto-refreshes every 30 seconds."
        testId="heading-system-health"
        actions={
          <Button
            variant="secondary"
            onClick={() => refetch()}
            loading={isFetching}
            data-testid="system-health-refresh"
          >
            Refresh
          </Button>
        }
      />
      <div
        className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in bg-grid-dots"
        data-testid="system-health-body"
      >
        {isLoading && (
          <div className="grid gap-4 md:grid-cols-2">
            {[0, 1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-40 w-full" />
            ))}
          </div>
        )}

        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Failed to load system health"}
            retry={() => refetch()}
          />
        )}

        {data && (
          <>
            {/* Top stat row */}
            <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatCard
                label="Overall"
                value={overallStatus.toUpperCase()}
                accent={overallStatus === "healthy" ? "green" : "red"}
              />
              <StatCard
                label="Database"
                value={data.db.ok ? "OK" : "DOWN"}
                accent={data.db.ok ? "green" : "red"}
              />
              <StatCard
                label="Vault"
                value={!data.vault.enabled ? "N/A" : data.vault.ok ? "OK" : "DOWN"}
                accent={data.vault.ok ? "green" : "amber"}
              />
              <StatCard
                label="Modules"
                value={`${data.modules.enabled.length}/${data.modules.available.length}`}
                accent="blue"
              />
            </div>

            {/* Meta bar */}
            <div
              className="mb-5 flex flex-wrap items-center gap-4 rounded border px-4 py-2.5"
              style={{
                background: "var(--bg-surface)",
                borderColor: "var(--border)",
              }}
            >
              <span className="label-caps text-[11px]" style={{ color: "var(--text-muted)" }}>
                Version
              </span>
              <span className="font-mono-data text-xs" style={{ color: "var(--text-primary)" }}>
                {data.app.version}
              </span>
              <span style={{ color: "var(--border)" }}>·</span>
              <span className="label-caps text-[11px]" style={{ color: "var(--text-muted)" }}>
                Checked
              </span>
              <span className="font-mono-data text-xs" style={{ color: "var(--text-secondary)" }}>
                {new Date(data.app.checked_at).toLocaleTimeString()}
              </span>
              <span
                className="ml-auto flex items-center gap-1.5"
              >
                <span
                  className="inline-block h-2 w-2 rounded-full"
                  style={{ background: overallColor[overallStatus] }}
                />
                <span
                  className="label-caps text-[11px]"
                  style={{ color: overallColor[overallStatus] }}
                >
                  {overallStatus}
                </span>
              </span>
            </div>

            {/* Service cards */}
            <div className="grid gap-4 md:grid-cols-2">
              <DatabaseCard report={data} />
              <VaultCard report={data} />
              <CatalogCard report={data} />
              <NatsCard report={data} />
              <div className="md:col-span-2">
                <ModulesCard report={data} />
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
}
