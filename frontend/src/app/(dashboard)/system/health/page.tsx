"use client";

import { PageHeader } from "@/components/page-header";
import { Badge, Button, ErrorState, Skeleton } from "@/components/ui";
import { useSystemHealth } from "@/features/system/hooks/use-system-health";

export default function SystemHealthPage() {
  const { data, isLoading, isError, error, refetch, isFetching } = useSystemHealth();

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
      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="system-health-body">
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
            <div className="mb-4 flex items-baseline gap-3">
              <span className="text-xs text-zinc-500">Version</span>
              <span className="font-mono text-xs text-zinc-700 dark:text-zinc-300">
                {data.app.version}
              </span>
              <span className="text-xs text-zinc-500">·</span>
              <span className="text-xs text-zinc-500">
                Checked {new Date(data.app.checked_at).toLocaleTimeString()}
              </span>
            </div>

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

function Card({
  title,
  badge,
  testId,
  children,
}: {
  title: string;
  badge: React.ReactNode;
  testId: string;
  children: React.ReactNode;
}) {
  return (
    <section
      className="rounded-lg border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950"
      data-testid={testId}
    >
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
          {title}
        </h2>
        {badge}
      </div>
      {children}
    </section>
  );
}

function DatabaseCard({ report }: { report: import("@/types/api").SystemHealthReport }) {
  const { db, pool } = report;
  const badge = db.ok ? (
    <Badge tone="emerald">ok</Badge>
  ) : (
    <Badge tone="red">down</Badge>
  );
  return (
    <Card title="Database" badge={badge} testId="health-card-db">
      {db.ok ? (
        <dl className="space-y-1 text-xs text-zinc-600 dark:text-zinc-400">
          <div className="flex justify-between">
            <dt>Pool</dt>
            <dd className="font-mono">
              {pool.free} idle / {pool.size} total
            </dd>
          </div>
          <div className="flex justify-between">
            <dt>In use</dt>
            <dd className="font-mono">{pool.busy}</dd>
          </div>
        </dl>
      ) : (
        <p className="text-xs text-red-600 dark:text-red-400">
          {db.error ?? "Database connection failed"}
        </p>
      )}
    </Card>
  );
}

function VaultCard({ report }: { report: import("@/types/api").SystemHealthReport }) {
  const { vault } = report;
  let badge: React.ReactNode;
  let body: React.ReactNode;
  if (!vault.enabled) {
    badge = <Badge tone="zinc">disabled</Badge>;
    body = (
      <p className="text-xs text-zinc-500">
        Vault module not in TENNETCTL_MODULES.
      </p>
    );
  } else if (vault.ok) {
    badge = <Badge tone="emerald">ok</Badge>;
    body = (
      <p className="text-xs text-zinc-600 dark:text-zinc-400">
        Vault initialized; root key loaded.
      </p>
    );
  } else {
    badge = <Badge tone="red">down</Badge>;
    body = (
      <p className="text-xs text-red-600 dark:text-red-400">
        Vault enabled but client not initialized.
      </p>
    );
  }
  return (
    <Card title="Vault" badge={badge} testId="health-card-vault">
      {body}
    </Card>
  );
}

function CatalogCard({ report }: { report: import("@/types/api").SystemHealthReport }) {
  const { catalog } = report;
  const hasReport =
    catalog.features !== null ||
    catalog.sub_features !== null ||
    catalog.nodes !== null;
  const badge = hasReport ? (
    <Badge tone="emerald">ok</Badge>
  ) : (
    <Badge tone="amber">unreported</Badge>
  );
  return (
    <Card title="Catalog" badge={badge} testId="health-card-catalog">
      {hasReport ? (
        <dl className="space-y-1 text-xs text-zinc-600 dark:text-zinc-400">
          <div className="flex justify-between">
            <dt>Features</dt>
            <dd className="font-mono">{catalog.features}</dd>
          </div>
          <div className="flex justify-between">
            <dt>Sub-features</dt>
            <dd className="font-mono">{catalog.sub_features}</dd>
          </div>
          <div className="flex justify-between">
            <dt>Nodes</dt>
            <dd className="font-mono">{catalog.nodes}</dd>
          </div>
        </dl>
      ) : (
        <p className="text-xs text-zinc-500">
          No catalog upsert report available this boot.
        </p>
      )}
    </Card>
  );
}

function NatsCard({ report }: { report: import("@/types/api").SystemHealthReport }) {
  const { nats } = report;
  const badge = nats.configured ? (
    <Badge tone="zinc">configured</Badge>
  ) : (
    <Badge tone="zinc">not configured</Badge>
  );
  return (
    <Card title="NATS JetStream" badge={badge} testId="health-card-nats">
      <dl className="space-y-1 text-xs text-zinc-600 dark:text-zinc-400">
        <div className="flex justify-between">
          <dt>Host</dt>
          <dd className="font-mono">{nats.url_host || "—"}</dd>
        </div>
        <p className="mt-2 text-[11px] text-zinc-500">
          Live-probe status coming with v0.3.0 alerting.
        </p>
      </dl>
    </Card>
  );
}

function ModulesCard({ report }: { report: import("@/types/api").SystemHealthReport }) {
  const enabledSet = new Set(report.modules.enabled);
  const enabledCount = report.modules.enabled.length;
  const availableCount = report.modules.available.length;
  return (
    <Card
      title="Modules"
      badge={
        <Badge tone="zinc">
          {enabledCount} / {availableCount} enabled
        </Badge>
      }
      testId="health-card-modules"
    >
      <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {report.modules.available.map((m) => {
          const on = enabledSet.has(m);
          return (
            <li
              key={m}
              className="flex items-center justify-between rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2 dark:border-zinc-800 dark:bg-zinc-900/50"
              data-testid={`health-module-${m}`}
            >
              <span className="font-mono text-xs text-zinc-700 dark:text-zinc-300">
                {m}
              </span>
              <Badge tone={on ? "emerald" : "zinc"}>{on ? "on" : "off"}</Badge>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
