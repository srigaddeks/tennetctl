"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import {
  Badge, Button, EmptyState, ErrorState, Field, Input, Select, Skeleton,
  Table, TBody, TD, TH, THead, TR, Textarea,
} from "@/components/ui";
import {
  useCohorts, useCreateCohort, useDeleteCohort, useRefreshCohort,
} from "@/features/product-ops/hooks/use-cohorts";
import type { CohortKind } from "@/types/api";

const KIND_TONE: Record<CohortKind, "blue" | "purple"> = {
  dynamic: "blue", static: "purple",
};

export default function CohortsPage() {
  const [workspaceId, setWorkspaceId] = useState<string | undefined>(undefined);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const ws = new URLSearchParams(window.location.search).get("workspace_id");
    if (ws) setWorkspaceId(ws);
  }, []);

  const list = useCohorts(workspaceId);
  const refresh = useRefreshCohort();
  const del = useDeleteCohort();

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Cohorts"
        description="Saved visitor filter sets with rolling membership. Dynamic cohorts re-compute from a rule (eligibility AST). Used by promos + campaigns + destinations as targeting primitive."
        actions={
          <Button variant="primary" onClick={() => setShowForm(v => !v)} data-testid="cohorts-new-toggle">
            {showForm ? "Cancel" : "New cohort"}
          </Button>
        }
      />

      {!workspaceId && (
        <EmptyState title="No workspace selected" description="Append ?workspace_id=… to view cohorts." />
      )}
      {workspaceId && showForm && <CreateForm workspaceId={workspaceId} onDone={() => setShowForm(false)} />}
      {workspaceId && list.isLoading && <Skeleton className="h-72 w-full" />}
      {workspaceId && list.isError && (
        <ErrorState
          message={list.error instanceof Error ? list.error.message : "Failed"}
          retry={() => { void list.refetch(); }}
        />
      )}
      {workspaceId && list.data && list.data.items.length === 0 && (
        <EmptyState title="No cohorts yet" description="Create one above to start segmenting visitors." />
      )}

      {workspaceId && list.data && list.data.items.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800">
          <Table>
            <THead>
              <TR>
                <TH>Cohort</TH>
                <TH>Kind</TH>
                <TH>Members</TH>
                <TH>Last refresh</TH>
                <TH>Actions</TH>
              </TR>
            </THead>
            <TBody>
              {list.data.items.map(c => (
                <TR key={c.id} data-testid={`cohort-row-${c.id}`}>
                  <TD>
                    <div className="flex flex-col">
                      <span className="font-medium">{c.name}</span>
                      <code className="text-[10px] text-zinc-500">{c.slug}</code>
                    </div>
                  </TD>
                  <TD><Badge tone={KIND_TONE[c.kind]}>{c.kind}</Badge></TD>
                  <TD>{c.member_count.toLocaleString()}</TD>
                  <TD className="text-xs">
                    {c.last_computed_at ?? <span className="text-zinc-400">—</span>}
                    {c.last_refresh_duration_ms != null && (
                      <span className="ml-1 text-zinc-500">({c.last_refresh_duration_ms}ms)</span>
                    )}
                  </TD>
                  <TD className="space-x-2">
                    {c.kind === "dynamic" && (
                      <Button
                        variant="secondary" size="sm"
                        onClick={() => refresh.mutate(c.id)}
                        disabled={refresh.isPending}
                        data-testid={`cohort-refresh-${c.slug}`}
                      >
                        Refresh
                      </Button>
                    )}
                    <Button
                      variant="secondary" size="sm"
                      onClick={() => { if (confirm(`Delete cohort ${c.slug}?`)) del.mutate(c.id); }}
                      data-testid={`cohort-delete-${c.slug}`}
                    >
                      Delete
                    </Button>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </div>
      )}
    </div>
  );
}

function CreateForm({ workspaceId, onDone }: { workspaceId: string; onDone: () => void }) {
  const create = useCreateCohort();
  const [slug, setSlug] = useState("");
  const [name, setName] = useState("");
  const [kind, setKind] = useState<CohortKind>("dynamic");
  const [definitionJson, setDefinitionJson] = useState(
    '{"op":"eq","field":"visitor.plan","value":"pro"}'
  );

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    let definition: Record<string, unknown> = {};
    if (kind === "dynamic") {
      try { definition = JSON.parse(definitionJson) as Record<string, unknown>; }
      catch { alert("definition must be valid JSON"); return; }
    }
    await create.mutateAsync({ slug, name, workspace_id: workspaceId, kind, definition });
    setSlug(""); setName(""); setDefinitionJson('{"op":"eq","field":"visitor.plan","value":"pro"}');
    onDone();
  };

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
      <div className="grid grid-cols-3 gap-4">
        <Field label="Slug" required htmlFor="cohort-slug">
          <Input id="cohort-slug" value={slug} onChange={e => setSlug(e.target.value)} required placeholder="pro_users" />
        </Field>
        <Field label="Name" required htmlFor="cohort-name">
          <Input id="cohort-name" value={name} onChange={e => setName(e.target.value)} required placeholder="Pro Users" />
        </Field>
        <Field label="Kind" htmlFor="cohort-kind">
          <Select id="cohort-kind" value={kind} onChange={e => setKind(e.target.value as CohortKind)}>
            <option value="dynamic">Dynamic (rule)</option>
            <option value="static">Static (manual list)</option>
          </Select>
        </Field>
      </div>
      {kind === "dynamic" && (
        <Field label="Definition (eligibility rule JSON)" hint='e.g. {"op":"eq","field":"visitor.plan","value":"pro"} — supports eq/ne/gt/lt/in/nin/exists + all/any/not' htmlFor="cohort-def">
          <Textarea id="cohort-def" value={definitionJson} onChange={e => setDefinitionJson(e.target.value)} rows={4} className="font-mono text-xs" />
        </Field>
      )}
      {create.isError && <p className="text-sm text-red-600">{create.error instanceof Error ? create.error.message : "Failed"}</p>}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="secondary" onClick={onDone}>Cancel</Button>
        <Button type="submit" variant="primary" disabled={create.isPending}>
          {create.isPending ? "Creating…" : "Create"}
        </Button>
      </div>
    </form>
  );
}
