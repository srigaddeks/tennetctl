"use client";

import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import {
  Badge,
  ErrorState,
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

  return (
    <>
      <PageHeader
        title="Catalog"
        description="Platform inventory: every feature + sub-feature currently registered. Boot-time snapshot from feature.manifest.yaml files."
        testId="heading-catalog"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="catalog-body">
        <section className="mb-8">
          <div className="mb-3 flex items-baseline justify-between">
            <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
              Features
            </h2>
            <Link
              href="/nodes"
              className="text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
            >
              → Browse nodes
            </Link>
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
          {features.data && (
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
                {features.data.map((f) => (
                  <TR key={f.feature_key} data-testid={`catalog-feature-${f.feature_key}`}>
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
          <h2 className="mb-3 text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            Sub-features
          </h2>

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
          {subFeatures.data && (
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
                {subFeatures.data.map((sf) => (
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
