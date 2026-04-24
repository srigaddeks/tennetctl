"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "@/components/page-header";
import { EmptyState, ErrorState, Skeleton, StatCard } from "@/components/ui";
import { apiList } from "@/lib/api";
import type { CatalogNode } from "@/types/api";

function useCatalogNodes() {
  return useQuery({
    queryKey: ["catalog", "nodes"],
    queryFn: async () => {
      const res = await apiList<CatalogNode>("/v1/catalog/nodes");
      return res.items;
    },
  });
}

const KIND_CONFIG: Record<string, { label: string; accent: string; bg: string; border: string }> = {
  request: {
    label: "REQUEST",
    accent: "var(--accent)",
    bg: "var(--accent-muted)",
    border: "var(--accent)",
  },
  effect: {
    label: "EFFECT",
    accent: "#a855f7",
    bg: "#1a0933",
    border: "#a855f7",
  },
  control: {
    label: "CONTROL",
    accent: "var(--warning)",
    bg: "var(--warning-muted)",
    border: "var(--warning)",
  },
};

function KindBadge({ kind }: { kind: string }) {
  const cfg = KIND_CONFIG[kind] ?? KIND_CONFIG.control;
  return (
    <span
      className="label-caps"
      style={{
        background: cfg.bg,
        color: cfg.accent,
        border: `1px solid ${cfg.border}`,
        borderRadius: 4,
        padding: "2px 7px",
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: "0.07em",
      }}
    >
      {cfg.label}
    </span>
  );
}

function NodeCard({ node }: { node: CatalogNode }) {
  return (
    <div
      className="flex flex-col gap-2 rounded border p-4 transition-colors"
      style={{
        background: "var(--bg-surface)",
        borderColor: "var(--border)",
      }}
      data-testid={`node-row-${node.node_key}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <code
          className="font-mono-data text-xs leading-snug"
          style={{ color: "#ff4d7d", wordBreak: "break-all" }}
        >
          {node.node_key}
        </code>
        <KindBadge kind={node.kind} />
      </div>

      {/* Handler */}
      <div
        className="font-mono-data truncate text-[11px]"
        style={{ color: "var(--text-muted)" }}
        title={node.handler}
      >
        {node.handler}
      </div>

      {/* Meta row */}
      <div className="flex flex-wrap items-center gap-3 pt-1">
        {node.emits_audit && (
          <span
            className="label-caps"
            style={{ color: "var(--success)", fontSize: 10 }}
          >
            audit
          </span>
        )}
        {node.tx_mode && node.tx_mode !== "none" && (
          <span
            className="label-caps"
            style={{ color: "var(--info)", fontSize: 10 }}
          >
            {node.tx_mode}
          </span>
        )}
        <span
          className="font-mono-data ml-auto text-[11px]"
          style={{ color: "var(--text-muted)" }}
        >
          {node.timeout_ms}ms · {node.retries}r · v{node.version}
        </span>
      </div>
    </div>
  );
}

function FilterSelect({
  value,
  onChange,
  testId,
  children,
}: {
  value: string;
  onChange: (v: string) => void;
  testId: string;
  children: React.ReactNode;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      data-testid={testId}
      className="rounded border px-2.5 py-1.5 text-xs"
      style={{
        background: "var(--bg-elevated)",
        borderColor: "var(--border-bright)",
        color: "var(--text-primary)",
        outline: "none",
      }}
    >
      {children}
    </select>
  );
}

export default function NodesPage() {
  const { data: nodes = [], isLoading, error } = useCatalogNodes();
  const [featureFilter, setFeatureFilter] = useState<string>("");
  const [kindFilter, setKindFilter] = useState<string>("");
  const [search, setSearch] = useState<string>("");

  const features = useMemo(() => {
    const seen = new Map<string, number>();
    for (const n of nodes) seen.set(n.feature_key, n.feature_number);
    return [...seen.entries()]
      .sort((a, b) => a[1] - b[1])
      .map(([key]) => key);
  }, [nodes]);

  const visible = useMemo(
    () =>
      nodes.filter(
        (n) =>
          (!featureFilter || n.feature_key === featureFilter) &&
          (!kindFilter || n.kind === kindFilter) &&
          (!search || n.node_key.includes(search.toLowerCase()) || n.handler.includes(search.toLowerCase()))
      ),
    [nodes, featureFilter, kindFilter, search]
  );

  const grouped = useMemo(() => {
    const m = new Map<string, CatalogNode[]>();
    for (const n of visible) {
      const arr = m.get(n.sub_feature_key) ?? [];
      arr.push(n);
      m.set(n.sub_feature_key, arr);
    }
    return [...m.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [visible]);

  const requestCount = nodes.filter((n) => n.kind === "request").length;
  const effectCount = nodes.filter((n) => n.kind === "effect").length;
  const controlCount = nodes.filter((n) => n.kind === "control").length;

  const perFeatureCounts = useMemo(() => {
    const m = new Map<string, number>();
    for (const n of nodes) m.set(n.feature_key, (m.get(n.feature_key) ?? 0) + 1);
    return [...m.entries()].sort((a, b) => b[1] - a[1]);
  }, [nodes]);

  return (
    <div className="flex flex-1 flex-col animate-fade-in">
      <PageHeader
        title="Node Registry"
        description="Live catalog of platform building blocks. Populated on boot from every feature.manifest.yaml."
        testId="heading"
      />

      <div className="flex-1 overflow-y-auto px-6 py-5">
        {/* Stat cards */}
        <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard
            label="Total Nodes"
            value={nodes.length}
            accent="blue"
          />
          <StatCard
            label="Request"
            value={requestCount}
            accent="blue"
          />
          <StatCard
            label="Effect"
            value={effectCount}
            accent="amber"
          />
          <StatCard
            label="Control"
            value={controlCount}
            accent="amber"
          />
        </div>

        {/* Filters */}
        <div
          className="mb-5 flex flex-wrap items-center gap-3 rounded border px-4 py-3"
          style={{
            background: "var(--bg-surface)",
            borderColor: "var(--border)",
          }}
        >
          <input
            type="search"
            placeholder="Search by key or handler…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="min-w-[200px] flex-1 rounded border px-3 py-1.5 text-xs"
            style={{
              background: "var(--bg-base)",
              borderColor: "var(--border-bright)",
              color: "var(--text-primary)",
              outline: "none",
            }}
          />
          <FilterSelect
            value={featureFilter}
            onChange={setFeatureFilter}
            testId="nodes-feature-filter"
          >
            <option value="">All features</option>
            {features.map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </FilterSelect>
          <FilterSelect
            value={kindFilter}
            onChange={setKindFilter}
            testId="nodes-kind-filter"
          >
            <option value="">All kinds</option>
            <option value="request">request</option>
            <option value="effect">effect</option>
            <option value="control">control</option>
          </FilterSelect>
          <span
            className="ml-auto font-mono-data text-xs"
            style={{ color: "var(--text-muted)" }}
          >
            {visible.length} / {nodes.length}
          </span>
        </div>

        {/* Per-feature counter strip */}
        {perFeatureCounts.length > 0 && (
          <div
            className="mb-5 flex flex-wrap items-center gap-2"
            data-testid="nodes-per-feature-counters"
          >
            {perFeatureCounts.map(([fk, count]) => (
              <button
                type="button"
                key={fk}
                onClick={() => setFeatureFilter(featureFilter === fk ? "" : fk)}
                className="rounded border px-2 py-1 font-mono-data text-[11px] transition-colors"
                style={{
                  background: featureFilter === fk ? "var(--accent-muted)" : "var(--bg-surface)",
                  borderColor: featureFilter === fk ? "var(--accent)" : "var(--border)",
                  color: featureFilter === fk ? "var(--accent)" : "var(--text-secondary)",
                }}
              >
                {fk} <span style={{ color: "var(--text-muted)" }}>({count})</span>
              </button>
            ))}
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-28 w-full rounded" />
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <ErrorState
            message={error instanceof Error ? error.message : "Failed to load nodes"}
          />
        )}

        {/* Empty */}
        {!isLoading && !error && visible.length === 0 && (
          <EmptyState
            title="No nodes match"
            description="Try clearing filters or broadening your search."
          />
        )}

        {/* Node groups */}
        {grouped.map(([subFeature, items]) => (
          <section key={subFeature} className="mb-8">
            <div
              className="mb-3 flex items-center gap-3 border-b pb-2"
              style={{ borderColor: "var(--border)" }}
            >
              <div
                className="h-3 w-3 rounded-full"
                style={{ background: "#ff4d7d" }}
              />
              <h2
                className="label-caps text-xs"
                style={{ color: "var(--text-secondary)" }}
              >
                {subFeature}
              </h2>
              <span
                className="font-mono-data ml-auto text-[11px]"
                style={{ color: "var(--text-muted)" }}
              >
                {items.length} {items.length === 1 ? "node" : "nodes"}
              </span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {items.map((n) => (
                <NodeCard key={n.node_key} node={n} />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
