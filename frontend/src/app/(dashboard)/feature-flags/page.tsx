"use client";

import Link from "next/link";
import { useState } from "react";

import { PageHeader } from "@/components/page-header";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Select,
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import { CreateFlagDialog } from "@/features/featureflags/create-flag-dialog";
import { useFlags } from "@/features/featureflags/hooks/use-flags";
import { useOrgs } from "@/features/iam-orgs/hooks/use-orgs";

export default function FlagsListPage() {
  const [scope, setScope] = useState<string>("");
  const [openCreate, setOpenCreate] = useState(false);
  const { data: orgs } = useOrgs({ limit: 500 });
  const { data, isLoading, isError, error, refetch } = useFlags({
    limit: 200,
    scope: scope || undefined,
  });

  return (
    <>
      <PageHeader
        title="Feature Flags"
        description="Define flags at global, org, or application scope. Per-environment toggles, targeting rules, per-entity overrides, role-based permissions, and deterministic rollout."
        testId="heading-flags"
        actions={
          <>
            <Link
              href="/feature-flags/evaluate"
              className="inline-flex h-10 items-center rounded-lg border border-zinc-200 bg-white px-4 text-sm font-medium text-zinc-900 transition hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-50 dark:hover:bg-zinc-800"
              data-testid="link-evaluate"
            >
              Try evaluator →
            </Link>
            <Button
              onClick={() => setOpenCreate(true)}
              data-testid="open-create-flag"
            >
              + New flag
            </Button>
          </>
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="mb-4 flex items-center gap-2">
          <label className="text-xs text-zinc-500">Filter by scope</label>
          <Select
            value={scope}
            onChange={(e) => setScope(e.target.value)}
            className="w-64"
            data-testid="filter-flag-scope"
          >
            <option value="">All scopes</option>
            <option value="global">Global</option>
            <option value="org">Org-scoped</option>
            <option value="application">Application-scoped</option>
          </Select>
        </div>
        {isLoading && <Skeleton className="h-12 w-full" />}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}
        {data && data.items.length === 0 && (
          <EmptyState
            title="No flags yet"
            description="Create your first flag. Pick a scope, value type, and a default. Per-environment toggles come next."
            action={
              <Button onClick={() => setOpenCreate(true)}>
                + Create first flag
              </Button>
            }
          />
        )}
        {data && data.items.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>Key</TH>
                <TH>Scope</TH>
                <TH>Type</TH>
                <TH>Default</TH>
                <TH>Status</TH>
                <TH />
              </tr>
            </THead>
            <TBody>
              {data.items.map((f) => {
                const scopeTone =
                  f.scope === "global"
                    ? "amber"
                    : f.scope === "org"
                      ? "blue"
                      : "purple";
                const org = orgs?.items.find((o) => o.id === f.org_id);
                return (
                  <TR key={f.id}>
                    <TD>
                      <Link
                        href={`/feature-flags/${f.id}`}
                        className="font-mono text-xs text-zinc-900 underline-offset-2 hover:underline dark:text-zinc-50"
                        data-testid={`flag-key-${f.flag_key}`}
                      >
                        {f.flag_key}
                      </Link>
                      {f.description && (
                        <div className="mt-0.5 max-w-sm truncate text-xs text-zinc-500">
                          {f.description}
                        </div>
                      )}
                    </TD>
                    <TD>
                      <Badge tone={scopeTone}>{f.scope}</Badge>
                      {f.scope !== "global" && org && (
                        <span className="ml-1.5 text-xs text-zinc-500">
                          {org.slug}
                        </span>
                      )}
                    </TD>
                    <TD>
                      <Badge tone="zinc">{f.value_type}</Badge>
                    </TD>
                    <TD>
                      <code className="rounded bg-zinc-100 px-1.5 py-0.5 text-[11px] text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200">
                        {JSON.stringify(f.default_value)}
                      </code>
                    </TD>
                    <TD>
                      <Badge tone={f.is_active ? "emerald" : "zinc"}>
                        {f.is_active ? "active" : "inactive"}
                      </Badge>
                    </TD>
                    <TD className="text-right">
                      <Link
                        href={`/feature-flags/${f.id}`}
                        className="text-xs font-medium text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50"
                      >
                        Manage →
                      </Link>
                    </TD>
                  </TR>
                );
              })}
            </TBody>
          </Table>
        )}
      </div>

      {openCreate && (
        <CreateFlagDialog
          open={openCreate}
          onClose={() => setOpenCreate(false)}
        />
      )}
    </>
  );
}
