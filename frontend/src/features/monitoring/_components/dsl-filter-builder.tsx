"use client";

import { useMemo } from "react";

import { Input, Select } from "@/components/ui";
import type { Filter } from "@/types/api";

type Op = "eq" | "ne" | "contains" | "in";
type Row = { field: string; op: Op; value: string };

type Props = {
  target: "logs" | "metrics" | "traces";
  rows: Row[];
  onChange: (rows: Row[]) => void;
};

const FIELD_OPTIONS: Record<Props["target"], string[]> = {
  logs: ["severity_text", "body", "trace_id", "service_name", "span_id"],
  metrics: ["metric_key", "service_name"],
  traces: ["service_name", "name", "status_code", "trace_id"],
};

export function rowsToFilter(rows: Row[]): Filter | undefined {
  const valid = rows.filter((r) => r.field && r.value);
  if (valid.length === 0) return undefined;
  const parts: Filter[] = valid.map((r) => {
    if (r.op === "in") {
      return {
        in: {
          field: r.field,
          values: r.value.split(",").map((s) => s.trim()).filter(Boolean),
        },
      };
    }
    if (r.op === "ne") return { ne: { field: r.field, value: r.value } };
    if (r.op === "contains")
      return { contains: { field: r.field, value: r.value } };
    return { eq: { field: r.field, value: r.value } };
  });
  if (parts.length === 1) return parts[0];
  return { and: parts };
}

export function DslFilterBuilder({ target, rows, onChange }: Props) {
  const fields = useMemo(() => FIELD_OPTIONS[target], [target]);

  const update = (i: number, patch: Partial<Row>) => {
    onChange(rows.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
  };

  const addRow = () => {
    onChange([...rows, { field: fields[0] ?? "", op: "eq", value: "" }]);
  };

  const removeRow = (i: number) => {
    onChange(rows.filter((_, idx) => idx !== i));
  };

  return (
    <div
      className="flex flex-col gap-2 rounded-lg border border-zinc-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-950"
      data-testid="monitoring-dsl-filter-builder"
    >
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">
          Filters
        </span>
        <button
          type="button"
          onClick={addRow}
          data-testid="monitoring-filter-add"
          className="rounded-md border border-zinc-200 px-2 py-0.5 text-[11px] text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900"
        >
          + Add filter
        </button>
      </div>
      {rows.length === 0 && (
        <p className="text-xs text-zinc-500">No filters.</p>
      )}
      {rows.map((r, i) => (
        <div key={i} className="flex flex-wrap items-center gap-2">
          <Select
            className="h-8 w-auto text-xs"
            value={r.field}
            onChange={(e) => update(i, { field: e.target.value })}
            data-testid={`monitoring-filter-field-${i}`}
          >
            {fields.map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </Select>
          <Select
            className="h-8 w-auto text-xs"
            value={r.op}
            onChange={(e) => update(i, { op: e.target.value as Op })}
            data-testid={`monitoring-filter-op-${i}`}
          >
            <option value="eq">=</option>
            <option value="ne">≠</option>
            <option value="contains">contains</option>
            <option value="in">in (comma)</option>
          </Select>
          <Input
            className="h-8 flex-1 text-xs"
            placeholder="value"
            value={r.value}
            onChange={(e) => update(i, { value: e.target.value })}
            data-testid={`monitoring-filter-value-${i}`}
          />
          <button
            type="button"
            onClick={() => removeRow(i)}
            aria-label="Remove filter"
            data-testid={`monitoring-filter-remove-${i}`}
            className="rounded-md px-2 py-0.5 text-xs text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}
