"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { getTodaysBoard } from "@/lib/api";
import type { ProductionBoard, ProductionBatchStatus } from "@/types/api";

type LoadState =
  | { status: "loading" }
  | { status: "ok"; board: ProductionBoard }
  | { status: "error"; message: string };

const STATUS_STYLES: Record<ProductionBatchStatus, string> = {
  planned: "bg-slate-100 ",
  in_progress: "bg-amber-100 text-amber-800",
  completed: "bg-emerald-100 text-emerald-800",
  cancelled: "bg-rose-100 text-rose-800",
};

export default function BoardPage() {
  const [date, setDate] = useState<string>(() =>
    new Date().toISOString().slice(0, 10)
  );
  const [state, setState] = useState<LoadState>({ status: "loading" });

  const load = useCallback(async () => {
    setState({ status: "loading" });
    try {
      const board = await getTodaysBoard(date);
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
          href="/production"
          className="text-sm" style={{ color: "var(--text-secondary)" }}
        >
          ← Production
        </Link>
        <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-3xl font-bold tracking-tight">
            Production Board
          </h1>
          <div className="flex items-center gap-2">
            <label className="text-sm">
              <span className="mr-2 ">Date</span>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="rounded border border-slate-300 bg-white px-2 py-1.5"
              />
            </label>
            <button
              type="button"
              onClick={() => void load()}
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold  hover:bg-slate-50"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {state.status === "loading" && (
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading board…</p>
      )}
      {state.status === "error" && (
        <div className="rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
          <p className="font-semibold">Error</p>
          <p className="mt-1 text-sm opacity-80">{state.message}</p>
        </div>
      )}
      {state.status === "ok" && state.board.kitchens.length === 0 && (
        <div className="rounded border border-slate-200 bg-white p-6 text-center shadow-sm">
          <p className="">
            No batches scheduled for {state.board.date}.
          </p>
          <Link
            href="/production/batches/new"
            className="mt-3 inline-block rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
          >
            Plan a batch
          </Link>
        </div>
      )}
      {state.status === "ok" && state.board.kitchens.length > 0 && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {state.board.kitchens.map((k) => (
            <div
              key={k.kitchen_id}
              className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
            >
              <div className="px-4 py-3" style={{ borderBottom: "1px solid var(--border)" }}>
                <div className="text-sm font-semibold text-slate-800">
                  {k.kitchen_name ?? k.kitchen_id}
                </div>
                <div className="mt-0.5 text-xs text-sm" style={{ color: "var(--text-muted)" }}>
                  {k.batches.length} batch
                  {k.batches.length === 1 ? "" : "es"}
                </div>
              </div>
              <ul >
                {k.batches.map(({ batch, summary }) => (
                  <li key={batch.id} className="px-4 py-3">
                    <Link
                      href={`/production/batches/${batch.id}`}
                      className="block hover:bg-slate-50"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="text-sm font-medium">
                            {batch.product_name ?? batch.product_id}
                          </div>
                          <div className="mt-0.5 text-xs text-sm" style={{ color: "var(--text-muted)" }}>
                            v{batch.recipe_version ?? "?"} · planned{" "}
                            {batch.planned_qty}
                            {batch.actual_qty ? ` · actual ${batch.actual_qty}` : ""}
                          </div>
                        </div>
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[batch.status]}`}
                        >
                          {batch.status}
                        </span>
                      </div>
                      {summary && (
                        <div className="mt-2 grid grid-cols-3 gap-1 text-xs ">
                          <div>
                            <div className="text-[10px] text-slate-400">Yield</div>
                            <div className="font-mono">
                              {summary.yield_pct
                                ? `${Number.parseFloat(summary.yield_pct).toFixed(0)}%`
                                : "—"}
                            </div>
                          </div>
                          <div>
                            <div className="text-[10px] text-slate-400">
                              COGS/bottle
                            </div>
                            <div className="font-mono">
                              {summary.cogs_per_unit
                                ? `${summary.currency_code} ${Number.parseFloat(summary.cogs_per_unit).toFixed(1)}`
                                : "—"}
                            </div>
                          </div>
                          <div>
                            <div className="text-[10px] text-slate-400">
                              Margin
                            </div>
                            <div className="font-mono">
                              {summary.gross_margin_pct
                                ? `${Number.parseFloat(summary.gross_margin_pct).toFixed(0)}%`
                                : "—"}
                            </div>
                          </div>
                        </div>
                      )}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
