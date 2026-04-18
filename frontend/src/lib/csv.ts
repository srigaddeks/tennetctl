/**
 * Minimal CSV export for browser-side tables. Escapes per RFC 4180:
 * quote cells containing commas, quotes, or newlines; double up inner quotes.
 * Cell-to-string: null/undefined → "", boolean/number → String(), object → JSON.
 */

export type CsvColumn<T> = {
  key: string;
  label?: string;
  accessor: (row: T) => unknown;
};

function cellToString(v: unknown): string {
  if (v === null || v === undefined) return "";
  if (typeof v === "string") return v;
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  if (v instanceof Date) return v.toISOString();
  try {
    return JSON.stringify(v);
  } catch {
    return String(v);
  }
}

function escapeCell(v: unknown): string {
  const s = cellToString(v);
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

export function rowsToCsv<T>(rows: T[], columns: CsvColumn<T>[]): string {
  const header = columns.map((c) => escapeCell(c.label ?? c.key)).join(",");
  const lines = rows.map((row) =>
    columns.map((c) => escapeCell(c.accessor(row))).join(","),
  );
  return [header, ...lines].join("\r\n");
}

export function downloadCsv<T>(
  filename: string,
  rows: T[],
  columns: CsvColumn<T>[],
): void {
  if (typeof window === "undefined") return;
  const csv = rowsToCsv(rows, columns);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename.endsWith(".csv") ? filename : `${filename}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
