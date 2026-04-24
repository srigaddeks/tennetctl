"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import {
  getSubscription,
  listSubscriptionEvents,
  updateSubscription,
} from "@/lib/api";
import type { Subscription, SubscriptionEvent } from "@/types/api";

type SubState =
  | { status: "loading" }
  | { status: "ok"; sub: Subscription; events: SubscriptionEvent[] }
  | { status: "error"; message: string };

export default function SubscriptionDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [state, setState] = useState<SubState>({ status: "loading" });
  const [acting, setActing] = useState(false);
  const [reason, setReason] = useState("");

  const reload = async () => {
    setState({ status: "loading" });
    try {
      const sub = await getSubscription(id);
      const events = await listSubscriptionEvents(id);
      setState({ status: "ok", sub, events });
    } catch (err: unknown) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : "Unknown error",
      });
    }
  };

  useEffect(() => {
    reload();
  }, [id]);

  const onAction = async (
    action: "pause" | "resume" | "cancel" | "end",
  ) => {
    const labels: Record<typeof action, string> = {
      pause: "Pause this subscription?",
      resume: "Resume this subscription?",
      cancel: "Cancel this subscription? This cannot be undone.",
      end: "Mark this subscription as ended (term completed)?",
    };
    if (!confirm(labels[action])) return;
    setActing(true);
    try {
      const targetStatus =
        action === "pause"
          ? "paused"
          : action === "resume"
          ? "active"
          : action === "cancel"
          ? "cancelled"
          : "ended";
      await updateSubscription(id, {
        status: targetStatus,
        reason: reason || undefined,
      });
      setReason("");
      await reload();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setActing(false);
    }
  };

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        {state.status === "ok" && (
          <h1 className="mt-2 text-3xl font-bold tracking-tight">
            {state.sub.customer_name} — {state.sub.plan_name}
          </h1>
        )}
      </div>

      {state.status === "loading" && (
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading subscription…</p>
      )}
      {state.status === "error" && (
        <p className="text-red-700">{state.message}</p>
      )}

      {state.status === "ok" && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:col-span-1">
            <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide ">
              Info
            </h2>
            <dl className="grid grid-cols-2 gap-2 text-sm">
              <dt className="">Status</dt>
              <dd>{state.sub.status}</dd>
              <dt className="">Customer</dt>
              <dd>
                <Link
                  href={`/customers/${state.sub.customer_id}`}
                  className="hover:underline"
                >
                  {state.sub.customer_name}
                </Link>
              </dd>
              <dt className="">Plan</dt>
              <dd>
                <Link
                  href={`/subscriptions/plans/${state.sub.plan_id}`}
                  className="hover:underline"
                >
                  {state.sub.plan_name}
                </Link>
              </dd>
              <dt className="">Frequency</dt>
              <dd>{state.sub.frequency_name ?? "—"}</dd>
              <dt className="">Service Zone</dt>
              <dd>{state.sub.service_zone_name ?? "—"}</dd>
              <dt className="">Start</dt>
              <dd className="font-mono">{state.sub.start_date}</dd>
              <dt className="">End</dt>
              <dd className="font-mono">{state.sub.end_date ?? "—"}</dd>
              <dt className="">Paused</dt>
              <dd className="font-mono">
                {state.sub.paused_from
                  ? `${state.sub.paused_from} → ${state.sub.paused_to ?? "indef"}`
                  : "—"}
              </dd>
              <dt className="">Billing</dt>
              <dd>{state.sub.billing_cycle ?? "—"}</dd>
              <dt className="">Price</dt>
              <dd className="font-mono">
                {state.sub.price_per_delivery !== null
                  ? `${state.sub.currency_code} ${state.sub.price_per_delivery}`
                  : "—"}
              </dd>
            </dl>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:col-span-1">
            <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide ">
              Actions
            </h2>
            <p className="mb-3 text-xs text-sm" style={{ color: "var(--text-muted)" }}>
              Status transitions emit an evt_subscription_events row.
            </p>
            <input
              className="mb-3 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Reason (optional)"
            />
            <div className="flex flex-col gap-2">
              {state.sub.status === "active" && (
                <button
                  onClick={() => onAction("pause")}
                  disabled={acting}
                  className="rounded-md bg-yellow-500 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-yellow-600 disabled:opacity-50"
                >
                  Pause
                </button>
              )}
              {state.sub.status === "paused" && (
                <button
                  onClick={() => onAction("resume")}
                  disabled={acting}
                  className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-green-700 disabled:opacity-50"
                >
                  Resume
                </button>
              )}
              {(state.sub.status === "active" ||
                state.sub.status === "paused") && (
                <>
                  <button
                    onClick={() => onAction("end")}
                    disabled={acting}
                    className="rounded-md bg-slate-700 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-slate-800 disabled:opacity-50"
                  >
                    End (term completed)
                  </button>
                  <button
                    onClick={() => onAction("cancel")}
                    disabled={acting}
                    className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-red-700 disabled:opacity-50"
                  >
                    Cancel
                  </button>
                </>
              )}
              {(state.sub.status === "cancelled" ||
                state.sub.status === "ended") && (
                <p className="rounded-md border border-slate-300 bg-slate-50 px-4 py-2 text-sm ">
                  Terminal state — no actions available.
                </p>
              )}
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:col-span-1">
            <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide ">
              Event Log ({state.events.length})
            </h2>
            {state.events.length === 0 && (
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>No events yet.</p>
            )}
            {state.events.length > 0 && (
              <ul className="divide-y divide-slate-100 text-sm">
                {state.events.map((ev) => (
                  <li key={ev.id} className="py-2">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{ev.event_type}</span>
                      <span className="font-mono text-xs text-sm" style={{ color: "var(--text-muted)" }}>
                        {new Date(ev.ts).toLocaleString()}
                      </span>
                    </div>
                    {ev.from_date && (
                      <div className="text-xs text-sm" style={{ color: "var(--text-muted)" }}>
                        {ev.from_date}
                        {ev.to_date && ` → ${ev.to_date}`}
                      </div>
                    )}
                    {ev.reason && (
                      <div className="text-xs italic text-sm" style={{ color: "var(--text-muted)" }}>
                        “{ev.reason}”
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
