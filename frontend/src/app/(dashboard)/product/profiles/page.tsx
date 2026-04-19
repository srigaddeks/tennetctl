"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import {
  Badge,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Skeleton,
  Table,
  TBody,
  TD,
  TH,
  THead,
  TR,
} from "@/components/ui";
import { useProfiles } from "@/features/product-ops/hooks/use-profiles";

export default function ProfilesPage() {
  const [workspaceId, setWorkspaceId] = useState<string | undefined>(undefined);
  const [q, setQ] = useState<string>("");
  const [plan, setPlan] = useState<string>("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const ws = params.get("workspace_id");
    if (ws) setWorkspaceId(ws);
  }, []);

  const list = useProfiles({
    workspace_id: workspaceId,
    q: q || undefined,
    plan: plan || undefined,
  });

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Profiles"
        description="Per-visitor accumulated traits (Mixpanel-style people layer). Filter by email/name/company, plan, country."
      />

      {!workspaceId && (
        <EmptyState
          title="No workspace selected"
          description="Append ?workspace_id=… to view profiles."
        />
      )}

      {workspaceId && (
        <section className="grid grid-cols-3 gap-4 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
          <Field label="Search (email / name / company)" htmlFor="profile-q">
            <Input id="profile-q" value={q} onChange={(e) => setQ(e.target.value)} placeholder="alice@" />
          </Field>
          <Field label="Plan filter" htmlFor="profile-plan">
            <Input id="profile-plan" value={plan} onChange={(e) => setPlan(e.target.value)} placeholder="pro" />
          </Field>
          <div className="flex items-end text-xs text-zinc-500">
            {list.data && (
              <span>
                {list.data.total.toLocaleString()} total · showing {list.data.items.length}
              </span>
            )}
          </div>
        </section>
      )}

      {workspaceId && list.isLoading && <Skeleton className="h-72 w-full" />}

      {workspaceId && list.isError && (
        <ErrorState
          message={list.error instanceof Error ? list.error.message : "Failed to load profiles"}
          retry={() => {
            void list.refetch();
          }}
        />
      )}

      {workspaceId && list.data && list.data.items.length === 0 && (
        <EmptyState
          title="No profiles match"
          description="Try clearing filters, or send identify() events from the SDK to populate profiles."
        />
      )}

      {workspaceId && list.data && list.data.items.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800">
          <Table>
            <THead>
              <TR>
                <TH>Email</TH>
                <TH>Name</TH>
                <TH>Plan</TH>
                <TH>Company</TH>
                <TH>Country</TH>
                <TH>First touch</TH>
                <TH>Last seen</TH>
              </TR>
            </THead>
            <TBody>
              {list.data.items.map((p) => (
                <TR key={p.id} data-testid={`profile-row-${p.id}`}>
                  <TD>
                    <a
                      href={`/product/visitors/${p.id}`}
                      className="text-blue-600 hover:underline dark:text-blue-400"
                    >
                      {p.email ?? <span className="text-zinc-400">—</span>}
                    </a>
                  </TD>
                  <TD>{p.name ?? "—"}</TD>
                  <TD>{p.plan ? <Badge tone="emerald">{p.plan}</Badge> : "—"}</TD>
                  <TD>{p.company ?? "—"}</TD>
                  <TD>{p.country ?? "—"}</TD>
                  <TD className="text-xs">{p.first_utm_campaign ?? "—"}</TD>
                  <TD className="text-xs">{p.last_seen}</TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </div>
      )}
    </div>
  );
}
