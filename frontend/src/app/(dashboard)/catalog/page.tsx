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

  return (
    <>
      <PageHeader
        title="Catalog"
        description="Platform inventory: every feature + sub-feature currently registered. Boot-time snapshot from feature.manifest.yaml files."
        testId="heading-catalog"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="catalog-body">
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <Input
            type="search"
            placeholder="Search key or module…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-sm"
            data-testid="catalog-search"
          />
          <div className="flex items-center gap-2">
            <label className="text-xs text-zinc-500">Feature</label>
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
            className="ml-auto text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
          >
            → Browse nodes
          </Link>
        </div>

        <section className="mb-8">
          <h2 className="mb-3 text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            Features ({filteredFeatures.length})
          </h2>

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
                  >
                    <TD>
                      <span className="font-mono text-xs text-zinc-500">
                        {String(f.feature_number).padStart(2, "0")}
                      </span>
                    </TD>
                    <TD>
                      <span className="font-mono text-xs">{f.feature_key}</span>
                    </TD>
                    <TD>
                      <Badge tone="blue">{f.module}</Badge>
                    </TD>
                    <TD className="text-right text-xs">{f.sub_feature_count}</TD>
                    <TD className="text-right text-xs">{f.node_count}</TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
        </section>

        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
              Sub-features ({filteredSubs.length})
            </h2>
            {featureFilter && (
              <button
                type="button"
                onClick={() => setFeatureFilter("")}
                className="text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
              >
                Clear feature filter
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
                      <span className="font-mono text-xs text-zinc-500">
                        {sf.feature_key}
                      </span>
                    </TD>
                    <TD>
                      <span className="font-mono text-xs">{sf.sub_feature_key}</span>
                    </TD>
                    <TD>
                      <Badge tone="blue">{sf.module}</Badge>
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
