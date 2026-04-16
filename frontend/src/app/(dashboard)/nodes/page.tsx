"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "@/components/page-header";
import { apiList } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { CatalogNode } from "@/types/api";

const KIND_TONE: Record<string, string> = {
  request: "bg-blue-100 text-blue-900 dark:bg-blue-900/40 dark:text-blue-100",
  effect: "bg-emerald-100 text-emerald-900 dark:bg-emerald-900/40 dark:text-emerald-100",
  control: "bg-zinc-200 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-100",
};

function useCatalogNodes() {
  return useQuery({
    queryKey: ["catalog", "nodes"],
    queryFn: async () => {
      const res = await apiList<CatalogNode>("/v1/catalog/nodes");
      return res.items;
    },
  });
}

export default function NodesPage() {
  const { data: nodes = [], isLoading, error } = useCatalogNodes();
  const [featureFilter, setFeatureFilter] = useState<string>("");
  const [kindFilter, setKindFilter] = useState<string>("");

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
          (!kindFilter || n.kind === kindFilter)
      ),
    [nodes, featureFilter, kindFilter]
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

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader
        title="Node Catalog"
        description="Live registry of features, sub-features, and nodes. Populated on boot from every feature.manifest.yaml."
        testId="heading"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-xs text-zinc-500">
            Feature
            <select
              value={featureFilter}
              onChange={(e) => setFeatureFilter(e.target.value)}
              className="rounded-md border border-zinc-300 bg-white px-2 py-1 text-sm dark:border-zinc-700 dark:bg-zinc-900"
              data-testid="nodes-feature-filter"
            >
              <option value="">All features</option>
              {features.map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2 text-xs text-zinc-500">
            Kind
            <select
              value={kindFilter}
              onChange={(e) => setKindFilter(e.target.value)}
              className="rounded-md border border-zinc-300 bg-white px-2 py-1 text-sm dark:border-zinc-700 dark:bg-zinc-900"
              data-testid="nodes-kind-filter"
            >
              <option value="">All kinds</option>
              <option value="request">request</option>
              <option value="effect">effect</option>
              <option value="control">control</option>
            </select>
          </label>
          <div className="ml-auto text-xs text-zinc-500">
            {visible.length} of {nodes.length} nodes
          </div>
        </div>
        {isLoading && <div className="text-sm text-zinc-500">Loading…</div>}
        {error && (
          <div className="text-sm text-red-600">
            {error instanceof Error ? error.message : "Failed to load nodes"}
          </div>
        )}
        {!isLoading && !error && grouped.length === 0 && (
          <div className="rounded-xl border border-zinc-200 bg-white p-8 text-center text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-950">
            No nodes match the current filters.
          </div>
        )}
        {grouped.map(([subFeature, items]) => (
          <section key={subFeature} className="mb-6">
            <div className="mb-2 flex items-baseline justify-between">
              <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
                {subFeature}
              </h2>
              <span className="text-xs text-zinc-400">{items.length} nodes</span>
            </div>
            <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
              <table className="w-full text-sm">
                <thead className="bg-zinc-50 text-[10px] uppercase tracking-wider text-zinc-500 dark:bg-zinc-900 dark:text-zinc-400">
                  <tr>
                    <th className="px-3 py-2 text-left">Key</th>
                    <th className="px-3 py-2 text-left">Kind</th>
                    <th className="px-3 py-2 text-left">Handler</th>
                    <th className="px-3 py-2 text-left">Audit</th>
                    <th className="px-3 py-2 text-left">Tx</th>
                    <th className="px-3 py-2 text-right">Timeout</th>
                    <th className="px-3 py-2 text-right">Retries</th>
                    <th className="px-3 py-2 text-right">v</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((n) => (
                    <tr
                      key={n.node_key}
                      className="border-t border-zinc-100 dark:border-zinc-900"
                      data-testid={`node-row-${n.node_key}`}
                    >
                      <td className="px-3 py-2 font-mono text-xs">{n.node_key}</td>
                      <td className="px-3 py-2">
                        <span
                          className={cn(
                            "rounded px-2 py-0.5 text-[10px] font-semibold uppercase",
                            KIND_TONE[n.kind] ?? "bg-zinc-100"
                          )}
                        >
                          {n.kind}
                        </span>
                      </td>
                      <td className="px-3 py-2 font-mono text-[11px] text-zinc-500">
                        {n.handler}
                      </td>
                      <td className="px-3 py-2 text-xs">
                        {n.emits_audit ? "yes" : "—"}
                      </td>
                      <td className="px-3 py-2 text-xs">{n.tx_mode}</td>
                      <td className="px-3 py-2 text-right text-xs">
                        {n.timeout_ms}ms
                      </td>
                      <td className="px-3 py-2 text-right text-xs">{n.retries}</td>
                      <td className="px-3 py-2 text-right text-xs">{n.version}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
