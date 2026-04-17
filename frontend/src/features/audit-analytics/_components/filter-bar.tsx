"use client";

import { Input, Select } from "@/components/ui";
import type { AuditBucket, AuditEventFilter } from "@/types/api";

type Props = {
  value: AuditEventFilter;
  bucket: AuditBucket;
  onChange: (next: AuditEventFilter) => void;
  onBucketChange: (b: AuditBucket) => void;
  onReset: () => void;
};

export function FilterBar({ value, bucket, onChange, onBucketChange, onReset }: Props) {
  const update = <K extends keyof AuditEventFilter>(k: K, v: AuditEventFilter[K]) => {
    onChange({ ...value, [k]: v });
  };

  return (
    <div
      className="flex flex-wrap gap-3 rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950"
      data-testid="audit-filter-bar"
    >
      <div className="flex min-w-[220px] flex-col gap-1">
        <label className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">Event key (glob)</label>
        <Input
          data-testid="audit-filter-event-key"
          placeholder="e.g. iam.orgs.*"
          value={value.event_key ?? ""}
          onChange={(e) => update("event_key", e.target.value || null)}
        />
      </div>
      <div className="flex min-w-[140px] flex-col gap-1">
        <label className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">Category</label>
        <Select
          data-testid="audit-filter-category"
          value={value.category_code ?? ""}
          onChange={(e) => update("category_code", (e.target.value || null) as AuditEventFilter["category_code"])}
        >
          <option value="">Any</option>
          <option value="system">System</option>
          <option value="user">User</option>
          <option value="integration">Integration</option>
          <option value="setup">Setup</option>
        </Select>
      </div>
      <div className="flex min-w-[140px] flex-col gap-1">
        <label className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">Outcome</label>
        <Select
          data-testid="audit-filter-outcome"
          value={value.outcome ?? ""}
          onChange={(e) => update("outcome", (e.target.value || null) as AuditEventFilter["outcome"])}
        >
          <option value="">Any</option>
          <option value="success">Success</option>
          <option value="failure">Failure</option>
        </Select>
      </div>
      <div className="flex min-w-[180px] flex-col gap-1">
        <label className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">Actor user</label>
        <Input
          data-testid="audit-filter-actor"
          placeholder="user uuid"
          value={value.actor_user_id ?? ""}
          onChange={(e) => update("actor_user_id", e.target.value || null)}
        />
      </div>
      <div className="flex min-w-[220px] flex-col gap-1">
        <label className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">Metadata contains</label>
        <Input
          data-testid="audit-filter-q"
          placeholder="substring of metadata JSON"
          value={value.q ?? ""}
          onChange={(e) => update("q", e.target.value || null)}
        />
      </div>
      <div className="flex min-w-[120px] flex-col gap-1">
        <label className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">Stats bucket</label>
        <Select
          data-testid="audit-filter-bucket"
          value={bucket}
          onChange={(e) => onBucketChange(e.target.value as AuditBucket)}
        >
          <option value="hour">Hour</option>
          <option value="day">Day</option>
        </Select>
      </div>
      <div className="flex items-end">
        <button
          type="button"
          data-testid="audit-filter-reset"
          className="h-10 rounded-lg border border-zinc-200 bg-white px-3 text-sm text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800"
          onClick={onReset}
        >
          Reset
        </button>
      </div>
    </div>
  );
}
