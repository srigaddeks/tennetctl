"use client";

import { useState } from "react";
import Link from "next/link";

import { Modal } from "@/components/modal";
import { PageHeader } from "@/components/page-header";
import {
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Skeleton,
  Textarea,
} from "@/components/ui";
import {
  useCreateDashboard,
  useDashboards,
  useDeleteDashboard,
} from "@/features/monitoring/hooks/use-dashboards";

export default function DashboardsPage() {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const { data, isLoading, isError, error, refetch } = useDashboards();
  const create = useCreateDashboard();
  const del = useDeleteDashboard();

  const submit = async () => {
    if (!name) return;
    await create.mutateAsync({ name, description: description || null });
    setOpen(false);
    setName("");
    setDescription("");
  };

  return (
    <>
      <PageHeader
        title="Dashboards"
        description="Grid-layout dashboards of panels. Each panel runs a DSL query."
        testId="heading-monitoring-dashboards"
        actions={
          <Button
            onClick={() => setOpen(true)}
            data-testid="monitoring-dashboard-new"
          >
            New dashboard
          </Button>
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        {isLoading && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        )}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}
        {data && data.items.length === 0 && (
          <EmptyState
            title="No dashboards"
            description="Create a dashboard to start adding panels."
            action={
              <Button onClick={() => setOpen(true)}>New dashboard</Button>
            }
          />
        )}
        {data && data.items.length > 0 && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((d) => (
              <div
                key={d.id}
                className="group relative flex flex-col gap-2 rounded-xl border border-zinc-200 bg-white p-5 transition hover:border-zinc-900 dark:border-zinc-800 dark:bg-zinc-950 dark:hover:border-zinc-100"
                data-testid={`monitoring-dashboard-card-${d.id}`}
              >
                <Link href={`/monitoring/dashboards/${d.id}`}>
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-base font-semibold text-zinc-900 dark:text-zinc-50">
                      {d.name}
                    </span>
                    {d.shared && (
                      <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-medium text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
                        Shared
                      </span>
                    )}
                  </div>
                  {d.description && (
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">
                      {d.description}
                    </p>
                  )}
                  <div className="mt-1 flex gap-2 text-[11px] text-zinc-500">
                    <span>{d.panel_count} panels</span>
                    <span>·</span>
                    <span>
                      Updated {new Date(d.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </Link>
                <button
                  type="button"
                  onClick={() => {
                    if (confirm(`Delete dashboard "${d.name}"?`)) {
                      void del.mutateAsync(d.id);
                    }
                  }}
                  data-testid={`monitoring-dashboard-delete-${d.id}`}
                  className="absolute right-3 top-3 rounded-md bg-white p-1 text-xs text-zinc-500 opacity-0 transition hover:bg-red-50 hover:text-red-700 group-hover:opacity-100 dark:bg-zinc-900 dark:text-zinc-400 dark:hover:bg-red-950 dark:hover:text-red-300"
                  aria-label="Delete dashboard"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="New dashboard"
        size="md"
      >
        <div className="flex flex-col gap-4">
          <Field label="Name" htmlFor="dash-name" required>
            <Input
              id="dash-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              data-testid="monitoring-dashboard-name"
            />
          </Field>
          <Field label="Description" htmlFor="dash-desc">
            <Textarea
              id="dash-desc"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </Field>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button onClick={submit} loading={create.isPending} disabled={!name}>
              Create
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
