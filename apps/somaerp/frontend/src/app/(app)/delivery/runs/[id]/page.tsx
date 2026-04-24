"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  generateRunStops,
  getDeliveryRun,
  patchRunStop,
  updateDeliveryRun,
} from "@/lib/api";
import type {
  DeliveryRun,
  DeliveryRunDetail,
  DeliveryRunStatus,
  DeliveryStop,
  DeliveryStopStatus,
} from "@/types/api";

type State =
  | { status: "loading" }
  | { status: "ok"; detail: DeliveryRunDetail }
  | { status: "error"; message: string };

const RUN_STATUS_STYLES: Record<DeliveryRunStatus, string> = {
  planned: "bg-slate-200 text-slate-800",
  in_transit: "bg-amber-200 text-amber-900 animate-pulse",
  completed: "bg-emerald-200 text-emerald-900",
  cancelled: "bg-rose-200 text-rose-900",
};

const STOP_STATUS_STYLES: Record<DeliveryStopStatus, string> = {
  pending: "bg-slate-100 ",
  delivered: "bg-emerald-100 text-emerald-800",
  missed: "bg-rose-100 text-rose-800",
  customer_unavailable: "bg-amber-100 text-amber-800",
  cancelled: "bg-slate-300 text-slate-800",
  rescheduled: "bg-sky-100 text-sky-800",
};

export default function RunDetailPage() {
  const params = useParams<{ id: string }>();
  const runId = params.id;
  const [state, setState] = useState<State>({ status: "loading" });
  const [err, setErr] = useState<string | null>(null);
  const [mutating, setMutating] = useState(false);

  const load = useCallback(async () => {
    try {
      const detail = await getDeliveryRun(runId);
      setState({ status: "ok", detail });
    } catch (e: unknown) {
      setState({
        status: "error",
        message: e instanceof Error ? e.message : "Unknown error",
      });
    }
  }, [runId]);

  useEffect(() => {
    void load();
  }, [load]);

  const transitionRun = async (
    status: DeliveryRunStatus,
    opts?: { allow_incomplete_completion?: boolean },
  ) => {
    setErr(null);
    setMutating(true);
    try {
      await updateDeliveryRun(runId, { status, ...(opts ?? {}) });
      await load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setMutating(false);
    }
  };

  const onGenerateStops = async () => {
    setErr(null);
    setMutating(true);
    try {
      await generateRunStops(runId);
      await load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setMutating(false);
    }
  };

  const patchStop = async (
    stop: DeliveryStop,
    patch: Parameters<typeof patchRunStop>[2],
  ) => {
    setErr(null);
    try {
      await patchRunStop(runId, stop.id, patch);
      await load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Unknown error");
    }
  };

  if (state.status === "loading") {
    return <div className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading run…</div>;
  }
  if (state.status === "error") {
    return (
      <div className="p-6">
        <Link
          href="/delivery/runs"
          className="text-sm" style={{ color: "var(--text-secondary)" }}
        >
          ← Runs
        </Link>
        <div className="mt-4 rounded border border-red-300 bg-red-50 p-4">
          <p className="font-semibold">Error</p>
          <p className="mt-1 text-sm opacity-80">{state.message}</p>
        </div>
      </div>
    );
  }

  const { run, stops } = state.detail;
  const pct =
    run.completion_pct !== null ? Math.round(run.completion_pct) : null;
  const showGenerate = run.total_stops === 0 && run.status === "planned";

  return (
    <div className="max-w-5xl">
      {/* Sticky top */}
      <div className="sticky top-0 z-20 border-b border-slate-200 bg-white px-4 py-3 shadow-sm sm:px-6">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <Link
              href="/delivery/runs"
              className="text-xs text-sm" style={{ color: "var(--text-secondary)" }}
            >
              ← Runs
            </Link>
            <div className="mt-0.5 flex items-center gap-2">
              <span
                className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${RUN_STATUS_STYLES[run.status]}`}
              >
                {run.status.replace("_", " ")}
              </span>
              <span className="truncate text-sm font-medium text-slate-800">
                {run.route_name ?? "—"}
              </span>
            </div>
          </div>
          <PrimaryAction
            run={run}
            mutating={mutating}
            onStart={() => void transitionRun("in_transit")}
            onComplete={() => void transitionRun("completed")}
            onForceComplete={() =>
              void transitionRun("completed", {
                allow_incomplete_completion: true,
              })
            }
            onCancel={() => void transitionRun("cancelled")}
          />
        </div>
        <div className="mt-2">
          <ProgressBar
            completed={run.completed_stops}
            missed={run.missed_stops}
            total={run.total_stops}
          />
          <p className="mt-1 text-xs ">
            {run.completed_stops} delivered · {run.missed_stops} missed ·{" "}
            {run.total_stops} total
            {pct !== null ? ` · ${pct}%` : ""}
          </p>
        </div>
        {err && (
          <div className="mt-2 rounded bg-red-50 px-3 py-1.5 text-xs text-red-700">
            {err}
          </div>
        )}
      </div>

      <div className="mx-auto max-w-2xl space-y-4 p-4 sm:p-6">
        {/* Run info */}
        <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm shadow-sm">
          <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
            <dt className="text-sm" style={{ color: "var(--text-muted)" }}>Rider</dt>
            <dd className="font-medium">{run.rider_name ?? "—"}</dd>
            <dt className="text-sm" style={{ color: "var(--text-muted)" }}>Kitchen</dt>
            <dd>{run.kitchen_name ?? "—"}</dd>
            <dt className="text-sm" style={{ color: "var(--text-muted)" }}>Date</dt>
            <dd className="font-mono">{run.run_date}</dd>
            <dt className="text-sm" style={{ color: "var(--text-muted)" }}>Started</dt>
            <dd className="font-mono">
              {run.started_at
                ? new Date(run.started_at).toLocaleString()
                : "—"}
            </dd>
            <dt className="text-sm" style={{ color: "var(--text-muted)" }}>Completed</dt>
            <dd className="font-mono">
              {run.completed_at
                ? new Date(run.completed_at).toLocaleString()
                : "—"}
            </dd>
          </dl>
        </div>

        {showGenerate && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 shadow-sm">
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-amber-900">
              No stops yet
            </h2>
            <p className="mb-3 text-sm text-amber-900">
              Generate stops from the route&apos;s customer sequence. This
              snapshots current customers as pending stops.
            </p>
            <button
              type="button"
              onClick={onGenerateStops}
              disabled={mutating}
              className="rounded-md bg-amber-500 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-600 disabled:bg-slate-300"
            >
              {mutating ? "Generating…" : "Generate Stops"}
            </button>
          </div>
        )}

        {/* Stops list */}
        <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <div className="px-4 py-3" style={{ borderBottom: "1px solid var(--border)" }}>
            <h2 className="text-sm font-semibold uppercase tracking-wide ">
              Stops ({stops.length})
            </h2>
          </div>
          {stops.length === 0 ? (
            <div className="p-6 text-sm text-sm" style={{ color: "var(--text-muted)" }}>No stops yet.</div>
          ) : (
            <ul >
              {stops.map((stop) => (
                <StopCard
                  key={stop.id}
                  stop={stop}
                  locked={
                    run.status === "completed" || run.status === "cancelled"
                  }
                  onPatch={(patch) => void patchStop(stop, patch)}
                />
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

function ProgressBar({
  completed,
  missed,
  total,
}: {
  completed: number;
  missed: number;
  total: number;
}) {
  if (total <= 0) {
    return (
      <div className="h-2 w-full rounded-full bg-slate-200">
        <div className="h-full w-0 rounded-full bg-slate-400" />
      </div>
    );
  }
  const cpct = Math.min(100, (completed / total) * 100);
  const mpct = Math.min(100 - cpct, (missed / total) * 100);
  return (
    <div className="flex h-2 w-full overflow-hidden rounded-full bg-slate-200">
      <div
        className="h-full bg-emerald-500"
        style={{ width: `${cpct}%` }}
      />
      <div className="h-full bg-rose-500" style={{ width: `${mpct}%` }} />
    </div>
  );
}

function PrimaryAction({
  run,
  mutating,
  onStart,
  onComplete,
  onForceComplete,
  onCancel,
}: {
  run: DeliveryRun;
  mutating: boolean;
  onStart: () => void;
  onComplete: () => void;
  onForceComplete: () => void;
  onCancel: () => void;
}) {
  if (run.status === "planned") {
    return (
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onStart}
          disabled={mutating || run.total_stops === 0}
          title={run.total_stops === 0 ? "Generate stops first" : "Start run"}
          className="rounded-md bg-amber-500 px-3 py-2 text-sm font-semibold text-white hover:bg-amber-600 disabled:bg-slate-300"
        >
          Start
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={mutating}
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold  hover:bg-slate-50"
        >
          Cancel
        </button>
      </div>
    );
  }
  if (run.status === "in_transit") {
    const allResolved =
      run.total_stops > 0 &&
      run.completed_stops + run.missed_stops >= run.total_stops;
    return (
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={allResolved ? onComplete : onForceComplete}
          disabled={mutating}
          className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:bg-slate-300"
        >
          {allResolved ? "Complete" : "Force complete"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={mutating}
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold  hover:bg-slate-50"
        >
          Cancel
        </button>
      </div>
    );
  }
  return (
    <div className="text-xs text-sm" style={{ color: "var(--text-muted)" }}>
      {run.status === "completed" ? "Run completed" : "Run cancelled"}
    </div>
  );
}

function StopCard({
  stop,
  locked,
  onPatch,
}: {
  stop: DeliveryStop;
  locked: boolean;
  onPatch: (patch: Parameters<typeof patchRunStop>[2]) => void;
}) {
  const [notes, setNotes] = useState<string>(stop.notes ?? "");
  const [photoKey, setPhotoKey] = useState<string>(stop.photo_vault_key ?? "");

  useEffect(() => {
    setNotes(stop.notes ?? "");
    setPhotoKey(stop.photo_vault_key ?? "");
  }, [stop.notes, stop.photo_vault_key]);

  const isPending = stop.status === "pending";
  const addressStr = formatAddress(stop.customer_address);

  return (
    <li className="px-4 py-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-xs text-sm" style={{ color: "var(--text-muted)" }}>
              #{stop.sequence_position}
            </span>
            <span className="truncate text-base font-semibold ">
              {stop.customer_name ?? "—"}
            </span>
          </div>
          <div className="mt-0.5 text-xs ">
            {stop.customer_phone ?? "—"}
          </div>
          {addressStr && (
            <div className="mt-0.5 text-xs text-sm" style={{ color: "var(--text-muted)" }}>{addressStr}</div>
          )}
          <div className="mt-1 text-[11px] text-slate-400">
            Scheduled{" "}
            {stop.scheduled_at
              ? new Date(stop.scheduled_at).toLocaleTimeString()
              : "—"}
            {stop.actual_at
              ? ` · Delivered ${new Date(stop.actual_at).toLocaleTimeString()}`
              : ""}
          </div>
        </div>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${STOP_STATUS_STYLES[stop.status]}`}
        >
          {stop.status.replace(/_/g, " ")}
        </span>
      </div>

      {!locked && (
        <div className="mt-3 grid grid-cols-3 gap-2">
          <button
            type="button"
            disabled={!isPending}
            onClick={() =>
              onPatch({
                status: "delivered",
                notes: notes || null,
                photo_vault_key: photoKey || null,
              })
            }
            className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:bg-slate-300"
          >
            Delivered
          </button>
          <button
            type="button"
            disabled={!isPending}
            onClick={() =>
              onPatch({ status: "missed", notes: notes || null })
            }
            className="rounded-md bg-rose-600 px-3 py-2 text-sm font-semibold text-white hover:bg-rose-700 disabled:bg-slate-300"
          >
            Missed
          </button>
          <button
            type="button"
            disabled={!isPending}
            onClick={() =>
              onPatch({
                status: "customer_unavailable",
                notes: notes || null,
              })
            }
            className="rounded-md bg-amber-500 px-3 py-2 text-sm font-semibold text-white hover:bg-amber-600 disabled:bg-slate-300"
          >
            N/A
          </button>
        </div>
      )}

      {!locked && (
        <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
          <input
            type="text"
            value={photoKey}
            onChange={(e) => setPhotoKey(e.target.value)}
            onBlur={() => {
              if (photoKey !== (stop.photo_vault_key ?? "")) {
                onPatch({ photo_vault_key: photoKey || null });
              }
            }}
            placeholder="Photo vault key (placeholder)"
            className="rounded border border-slate-300 px-2 py-1.5 text-xs font-mono"
          />
          <input
            type="text"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            onBlur={() => {
              if (notes !== (stop.notes ?? "")) {
                onPatch({ notes: notes || null });
              }
            }}
            placeholder="Notes"
            className="rounded border border-slate-300 px-2 py-1.5 text-xs"
          />
        </div>
      )}
    </li>
  );
}

function formatAddress(addr: Record<string, unknown> | null): string {
  if (!addr) return "";
  const parts: string[] = [];
  const addAny = (k: string) => {
    const v = (addr as Record<string, unknown>)[k];
    if (typeof v === "string" && v.length > 0) parts.push(v);
  };
  addAny("line1");
  addAny("line2");
  addAny("landmark");
  addAny("pincode");
  return parts.join(", ");
}
