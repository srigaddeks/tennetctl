"use client";

import { useState } from "react";

import { useToast } from "@/components/toast";
import { Button, EmptyState, ErrorState, Skeleton, TD, TH, THead, TBody, TR, Table } from "@/components/ui";
import {
  useDeletePolicy,
  useOrgOverrides,
} from "@/features/iam/hooks/use-auth-policy";
import { useOrgs } from "@/features/iam-orgs/hooks/use-orgs";
import { PolicyForm } from "@/features/iam/_components/PolicyForm";
import { ApiClientError } from "@/lib/api";
import type { PolicyEntry } from "@/types/api";

function DeleteOverrideButton({ entry }: { entry: PolicyEntry }) {
  const { toast } = useToast();
  const del = useDeletePolicy();

  async function remove() {
    try {
      await del.mutateAsync(entry.id);
      toast("Override deleted — key will fall back to global default", "success");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : "Delete failed";
      toast(msg, "error");
    }
  }

  return (
    <Button
      variant="secondary"
      size="sm"
      onClick={remove}
      disabled={del.isPending}
      data-testid={`delete-override-${entry.id}`}
    >
      Remove
    </Button>
  );
}

export function OrgOverrideList() {
  const { data: orgsData, isLoading: orgsLoading } = useOrgs({ limit: 200 });
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const {
    data: overrides,
    isLoading: overridesLoading,
    isError,
    error,
  } = useOrgOverrides(selectedOrgId);

  if (orgsLoading) {
    return (
      <div className="flex flex-col gap-2">
        <Skeleton className="h-9 w-64" />
      </div>
    );
  }

  const orgs = orgsData?.items ?? [];

  return (
    <div className="flex flex-col gap-6" data-testid="org-override-list">
      <div className="flex items-center gap-4">
        <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Org
        </label>
        <select
          className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
          value={selectedOrgId ?? ""}
          onChange={(e) => setSelectedOrgId(e.target.value || null)}
          data-testid="org-override-select"
        >
          <option value="">— select org —</option>
          {orgs.map((org) => (
            <option key={org.id} value={org.id}>
              {org.display_name ?? org.slug}
            </option>
          ))}
        </select>
      </div>

      {selectedOrgId && (
        <>
          {overridesLoading && (
            <div className="flex flex-col gap-2">
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-9 w-full" />
            </div>
          )}
          {isError && (
            <ErrorState
              message={(error as Error)?.message ?? "Failed to load overrides"}
              retry={() => void 0}
            />
          )}
          {!overridesLoading && !isError && (overrides?.length ?? 0) > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-zinc-600 dark:text-zinc-400">
                Existing overrides
              </h4>
              <Table>
                <THead>
                  <TR>
                    <TH>Key</TH>
                    <TH>Value</TH>
                    <TH />
                  </TR>
                </THead>
                <TBody>
                  {(overrides ?? []).map((entry) => (
                    <TR key={entry.id} data-testid={`override-row-${entry.id}`}>
                      <TD>{entry.key.replace("iam.policy.", "")}</TD>
                      <TD>{String(entry.value)}</TD>
                      <TD>
                        <DeleteOverrideButton entry={entry} />
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            </div>
          )}
          {!overridesLoading && !isError && (overrides?.length ?? 0) === 0 && (
            <EmptyState
              title="No overrides"
              description="All policy keys will fall back to global defaults for this org."
            />
          )}
          <div>
            <h4 className="mb-2 text-sm font-medium text-zinc-600 dark:text-zinc-400">
              Add / edit overrides for this org
            </h4>
            <PolicyForm entries={overrides ?? []} orgId={selectedOrgId} />
          </div>
        </>
      )}
    </div>
  );
}
