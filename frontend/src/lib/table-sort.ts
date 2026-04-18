"use client";

import { useMemo, useState } from "react";

import type { SortDir } from "@/components/ui";

export type SortState<K extends string> = {
  key: K | null;
  dir: SortDir;
};

export function useTableSort<T, K extends string>(
  rows: T[],
  accessors: Record<K, (row: T) => unknown>,
  initial: SortState<K> = { key: null, dir: "asc" as SortDir },
) {
  const [sort, setSort] = useState<SortState<K>>(initial);

  function toggle(key: K) {
    setSort((s) => {
      if (s.key !== key) return { key, dir: "asc" };
      if (s.dir === "asc") return { key, dir: "desc" };
      return { key: null, dir: "asc" };
    });
  }

  function dirFor(key: K): SortDir | null {
    return sort.key === key ? sort.dir : null;
  }

  const sorted = useMemo(() => {
    if (sort.key == null) return rows;
    const accessor = accessors[sort.key];
    const copy = [...rows];
    copy.sort((a, b) => {
      const av = accessor(a);
      const bv = accessor(b);
      const cmp = compare(av, bv);
      return sort.dir === "asc" ? cmp : -cmp;
    });
    return copy;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows, sort.key, sort.dir]);

  return { sorted, sort, toggle, dirFor };
}

function compare(a: unknown, b: unknown): number {
  if (a === b) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  if (typeof a === "boolean" && typeof b === "boolean") {
    return (a ? 1 : 0) - (b ? 1 : 0);
  }
  const as = String(a);
  const bs = String(b);
  return as.localeCompare(bs, undefined, { numeric: true, sensitivity: "base" });
}
