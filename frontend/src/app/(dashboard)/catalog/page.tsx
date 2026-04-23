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
import {
  useCatalogFeatures,
  useCatalogSubFeatures,
} from "@/features/catalog/hooks/use-catalog";

export default function CatalogPage() {
  const features = useCatalogFeatures();
  const subFeatures = useCatalogSubFeatures();

  const [search, setSearch] = useState("");
  const [featureFilter, setFeatureFilter] = useState<string>("");

  const filteredFeatures = useMemo(() => {
    const list = features.data ?? [];
    if (!search) return list;
    const q = search.toLowerCase();
    return list.filter(
      (f) =>
        f.feature_key.toLowerCase().includes(q) ||
        f.module.toLowerCase().includes(q),
    );
  }, [features.data, search]);

  const filteredSubs = useMemo(() => {
    const list = subFeatures.data ?? [];
    return list.filter((sf) => {
      if (featureFilter && sf.feature_key !== featureFilter) return false;
      if (!search) return true;
      const q = search.toLowerCase();
      return (
        sf.feature_key.toLowerCase().includes(q) ||
        sf.sub_feature_key.toLowerCase().includes(q) ||
        sf.module.toLowerCase().includes(q)
      );
    });
  }, [subFeatures.data, featureFilter, search]);

  const featureKeys = (features.data ?? []).map((f) => f.feature_key);
  const totalNodes = (features.data ?? []).reduce((acc, f) => acc + f.node_count, 0);
  const totalSubs = (features.data ?? []).reduce((acc, f) => acc + f.sub_feature_count, 0);

  return (
    <>
      <PageHeader
        title="Catalog"
        description="Platform inventory: every feature + sub-feature registered at boot from feature.manifest.yaml files."
        testId="heading-catalog"
      />
      <div
        className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in"
        data-testid="catalog-body"
      >
        {/* Stat row */}
        <div className="mb-6 grid grid-cols-3 gap-3">
          <StatCard
            label="Features"
            value={(features.data ?? []).length}
            accent="blue"
          />
          <StatCard
            label="Sub-features"
            value={totalSubs}
            accent="blue"
          />
          <StatCard
            label="Nodes"
            value={totalNodes}
            accent="green"
          />
        </div>

        {/* Toolbar */}
        <div
          className="mb-5 flex flex-wrap items-center gap-3 rounded border px-4 py-3"
          style={{ background: "var(--bg-surface)", borderColor: "var(--border)" }}
        >
          <Input
            type="search"
            placeholder="Search key or module…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-sm"
            data-testid="catalog-search"
          />
          <div className="flex items-center gap-2">
            <span
              className="label-caps text-[11px]"
              style={{ color: "var(--text-muted)" }}
            >
              Feature
            </span>
            <Select
              value={featureFilter}
              onChange={(e) => setFeatureFilter(e.target.value)}
              className="w-44"
              data-testid="catalog-feature-filter"
            >
              <option value="">All features</option>
              {featureKeys.map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </Select>
          </div>
          <Link
            href="/nodes"
            className="ml-auto text-xs transition-colors"
            style={{ color: "var(--text-secondary)" }}
          >
            Browse nodes →
          </Link>
        </div>

        {/* Features section */}
        <section className="mb-8">
          <div
            className="mb-3 flex items-center gap-2 border-b pb-2"
            style={{ borderColor: "var(--border)" }}
          >
            <div
              className="h-3 w-3 rounded-full"
              style={{ background: "#7ef7c8" }}
            />
            <h2
              className="label-caps text-xs"
              style={{ color: "var(--text-secondary)" }}
            >
              Features
            </h2>
            <span
              className="font-mono-data ml-auto text-[11px]"
              style={{ color: "var(--text-muted)" }}
            >
              {filteredFeatures.length}
            </span>
          </div>

          {features.isLoading && <Skeleton className="h-40 w-full" />}
          {features.isError && (
            <ErrorState
              message={
                features.error instanceof Error
                  ? features.error.message
                  : "Failed to load features"
              }
              retry={() => features.refetch()}
            />
          )}
          {features.data && filteredFeatures.length === 0 && (
            <EmptyState
              title="No features match"
              description="Try a different search term."
            />
          )}
          {features.data && filteredFeatures.length > 0 && (
            <Table>
              <THead>
                <tr>
                  <TH>#</TH>
                  <TH>Key</TH>
                  <TH>Module</TH>
                  <TH className="text-right">Sub-features</TH>
                  <TH className="text-right">Nodes</TH>
                </tr>
              </THead>
              <TBody>
                {filteredFeatures.map((f) => (
                  <TR
                    key={f.feature_key}
                    data-testid={`catalog-feature-${f.feature_key}`}
                    onClick={() => setFeatureFilter(f.feature_key)}
                    style={{ cursor: "pointer" }}
                  >
                    <TD>
                      <span
                        className="font-mono-data text-xs"
                        style={{ color: "var(--text-muted)" }}
                      >
                        {String(f.feature_number).padStart(2, "0")}
                      </span>
                    </TD>
                    <TD>
                      <span
                        className="font-mono-data text-xs"
                        style={{ color: "#7ef7c8" }}
                      >
                        {f.feature_key}
                      </span>
                    </TD>
                    <TD>
                      <Badge tone="cyan">{f.module}</Badge>
                    </TD>
                    <TD className="text-right text-xs">{f.sub_feature_count}</TD>
                    <TD className="text-right text-xs">{f.node_count}</TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
        </section>

        {/* Sub-features section */}
        <section>
          <div
            className="mb-3 flex items-center gap-2 border-b pb-2"
            style={{ borderColor: "var(--border)" }}
          >
            <div
              className="h-3 w-3 rounded-full"
              style={{ background: "#7ef7c8", opacity: 0.5 }}
            />
            <h2
              className="label-caps text-xs"
              style={{ color: "var(--text-secondary)" }}
            >
              Sub-features
            </h2>
            <span
              className="font-mono-data ml-auto text-[11px]"
              style={{ color: "var(--text-muted)" }}
            >
              {filteredSubs.length}
            </span>
            {featureFilter && (
              <button
                type="button"
                onClick={() => setFeatureFilter("")}
                className="text-xs transition-colors"
                style={{ color: "var(--text-secondary)" }}
              >
                Clear filter ×
              </button>
            )}
          </div>

          {subFeatures.isLoading && <Skeleton className="h-60 w-full" />}
          {subFeatures.isError && (
            <ErrorState
              message={
                subFeatures.error instanceof Error
                  ? subFeatures.error.message
                  : "Failed to load sub-features"
              }
              retry={() => subFeatures.refetch()}
            />
          )}
          {subFeatures.data && filteredSubs.length === 0 && (
            <EmptyState
              title="No sub-features match"
              description="Try a different search or clear the feature filter."
            />
          )}
          {subFeatures.data && filteredSubs.length > 0 && (
            <Table>
              <THead>
                <tr>
                  <TH>Feature</TH>
                  <TH>Sub-feature</TH>
                  <TH>Module</TH>
                  <TH className="text-right">Nodes</TH>
                </tr>
              </THead>
              <TBody>
                {filteredSubs.map((sf) => (
                  <TR
                    key={`${sf.feature_key}/${sf.sub_feature_key}`}
                    data-testid={`catalog-sub-${sf.feature_key}-${sf.sub_feature_key}`}
                  >
                    <TD>
                      <span
                        className="font-mono-data text-xs"
                        style={{ color: "var(--text-muted)" }}
                      >
                        {sf.feature_key}
                      </span>
                    </TD>
                    <TD>
                      <span
                        className="font-mono-data text-xs"
                        style={{ color: "#7ef7c8" }}
                      >
                        {sf.sub_feature_key}
                      </span>
                    </TD>
                    <TD>
                      <Badge tone="cyan">{sf.module}</Badge>
                    </TD>
                    <TD className="text-right text-xs">{sf.node_count}</TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
        </section>
      </div>
    </>
  );
}
