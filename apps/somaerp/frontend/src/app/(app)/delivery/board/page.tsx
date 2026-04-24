"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { getDeliveryBoard } from "@/lib/api";
import type { DeliveryBoard, DeliveryRunStatus } from "@/types/api";

type State =
  | { status: "loading" }
  | { status: "ok"; board: DeliveryBoard }
  | { status: "error"; message: string };

const STATUS_STYLES: Record<DeliveryRunStatus, string> = {
  planned: "bg-slate-100 ",
  in_transit: "bg-amber-100 text-amber-800",
  completed: "bg-emerald-100 text-emerald-800",
  cancelled: "bg-rose-100 text-rose-800",
};

export default function DeliveryBoardPage() {
  const [date, setDate] = useState<string>(() =>
    new Date().toISOString().slice(0, 10),
  );
  const [state, setState] = useState<State>({ status: "loading" });

  const load = useCallback(async () => {
    setState({ status: "loading" });
    try {
      const board = await getDeliveryBoard(date);
      setState({ status: "ok", board });
    } catch (err: unknown) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : "Unknown error",
      });
    }
  }, [date]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <Link
          href="/delivery"
          className="text-sm" style={{ color: "var(--text-secondary)" }}
        >
          ← Delivery
        </Link>
        <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Delivery Board</h1>
          <label className="text-sm">
            <span className="mr-2 ">Date</span>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
            />
          </label>
        </div>
      </div>

      {state.status === "loading" && (
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading board…</p>
      )}
      {state.status === "error" && (
        <div className="rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
          <p className="font-semibold">Failed</p>
          <p className="mt-1 text-sm opacity-80">{state.message}</p>
        </div>
      )}
      {state.status === "ok" && state.board.kitchens.length === 0 && (
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>No runs for this date.</p>
      )}
      {state.status === "ok" && state.board.kitchens.length > 0 && (
        <div className="space-y-6">
          {state.board.kitchens.map((k) => (
            <div
              key={k.kitchen_id}
              className="rounded border p-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
            >
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                  {k.kitchen_name ?? "—"}
                </h2>
                <span className="text-xs text-sm" style={{ color: "var(--text-muted)" }}>
                  {k.runs.length} run{k.runs.length === 1 ? "" : "s"}
                </span>
              </div>
              <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {k.runs.map((r) => {
                  const pct =
                    r.completion_pct !== null
                      ? Math.round(r.completion_pct)
                      : null;
                  return (
                    <li
                      key={r.id}
                      className="rounded border border-slate-200 bg-slate-50 p-3"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <Link
                            href={`/delivery/runs/${r.id}`}
                            className="font-medium  hover:underline"
                          >
                            {r.route_name ?? "—"}
                          </Link>
                          <div className="text-xs text-sm" style={{ color: "var(--text-muted)" }}>
                            {r.rider_name ?? "—"}
                          </div>
                        </div>
                        <span
                          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${STATUS_STYLES[r.status]}`}
                        >
                          {r.status.replace("_", " ")}
                        </span>
                      </div>
                      <div className="mt-2">
                        <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
                          <div
                            className="h-full bg-emerald-500"
                            style={{ width: `${pct ?? 0}%` }}
                          />
                        </div>
                        <p className="mt-1 text-[11px] font-mono ">
                          {r.completed_stops}/{r.total_stops}
                          {r.missed_stops > 0
                            ? ` · ${r.missed_stops} missed`
                            : ""}
                          {pct !== null ? ` · ${pct}%` : ""}
                        </p>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
