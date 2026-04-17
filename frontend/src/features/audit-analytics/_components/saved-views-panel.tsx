"use client";

import { useState } from "react";

import { Button, ErrorState, Skeleton } from "@/components/ui";
import {
  useAuditSavedViews,
  useCreateSavedView,
  useDeleteSavedView,
} from "@/features/audit-analytics/hooks/use-audit-events";
import type { AuditEventFilter, AuditBucket } from "@/types/api";

type Props = {
  currentFilter: AuditEventFilter;
  currentBucket: AuditBucket;
  onLoad: (filter: AuditEventFilter, bucket: AuditBucket) => void;
};

export function SavedViewsPanel({ currentFilter, currentBucket, onLoad }: Props) {
  const { data, isLoading, isError, error } = useAuditSavedViews();
  const create = useCreateSavedView();
  const del = useDeleteSavedView();
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);

  async function handleSave() {
    if (!name.trim()) return;
    await create.mutateAsync({
      name: name.trim(),
      filter_json: currentFilter as Record<string, unknown>,
      bucket: currentBucket,
    });
    setName("");
    setCreating(false);
  }

  return (
    <div
      className="flex flex-col gap-4 rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-950"
      data-testid="audit-saved-views-panel"
    >
      <div className="flex items-center justify-between">
        <div className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
          Saved Views
        </div>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => setCreating((v) => !v)}
          data-testid="audit-saved-views-new"
        >
          {creating ? "Cancel" : "Save current"}
        </Button>
      </div>

      {creating && (
        <div className="flex items-center gap-2">
          <input
            className="min-w-0 flex-1 rounded-md border border-zinc-200 bg-zinc-50 px-3 py-1.5 text-xs text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-400 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
            placeholder="View name…"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") void handleSave();
            }}
            data-testid="audit-saved-views-name-input"
            autoFocus
          />
          <Button
            size="sm"
            loading={create.isPending}
            onClick={() => void handleSave()}
            disabled={!name.trim()}
            data-testid="audit-saved-views-save"
          >
            Save
          </Button>
        </div>
      )}

      {isLoading && (
        <div className="flex flex-col gap-2">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
        </div>
      )}

      {isError && (
        <ErrorState
          message={error instanceof Error ? error.message : "Load failed"}
        />
      )}

      {data && data.items.length === 0 && !isLoading && (
        <div className="text-xs text-zinc-400">No saved views yet.</div>
      )}

      {data && data.items.length > 0 && (
        <ul className="flex flex-col gap-1" data-testid="audit-saved-views-list">
          {data.items.map((view) => (
            <li
              key={view.id}
              className="group flex items-center justify-between rounded-md px-2 py-1.5 hover:bg-zinc-50 dark:hover:bg-zinc-900"
            >
              <button
                className="min-w-0 flex-1 text-left text-xs font-medium text-zinc-800 dark:text-zinc-200"
                onClick={() =>
                  onLoad(view.filter_json as AuditEventFilter, view.bucket)
                }
                data-testid={`audit-saved-views-load-${view.id}`}
              >
                {view.name}
                <span className="ml-2 font-normal text-zinc-400">{view.bucket}</span>
              </button>
              <button
                className="ml-2 text-[10px] text-zinc-300 opacity-0 transition-opacity group-hover:opacity-100 hover:text-red-500 dark:text-zinc-600 dark:hover:text-red-400"
                onClick={() => void del.mutateAsync(view.id)}
                aria-label={`Delete ${view.name}`}
                data-testid={`audit-saved-views-delete-${view.id}`}
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
