"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  attachRouteCustomer,
  detachRouteCustomer,
  getDeliveryRoute,
  listCustomers,
  listRouteCustomers,
  reorderRouteCustomers,
} from "@/lib/api";
import type {
  Customer,
  DeliveryRoute,
  RouteCustomerLink,
} from "@/types/api";

type State =
  | { status: "loading" }
  | { status: "ok"; route: DeliveryRoute; links: RouteCustomerLink[] }
  | { status: "error"; message: string };

export default function RouteDetailPage() {
  const params = useParams<{ id: string }>();
  const routeId = params.id;
  const [state, setState] = useState<State>({ status: "loading" });
  const [allCustomers, setAllCustomers] = useState<Customer[]>([]);
  const [addCustomerId, setAddCustomerId] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [mutating, setMutating] = useState(false);
  const [orderEdits, setOrderEdits] = useState<Record<string, number>>({});

  const load = useCallback(async () => {
    try {
      const [route, links] = await Promise.all([
        getDeliveryRoute(routeId),
        listRouteCustomers(routeId),
      ]);
      setState({ status: "ok", route, links });
      setOrderEdits(
        Object.fromEntries(links.map((l) => [l.customer_id, l.sequence_position])),
      );
    } catch (e: unknown) {
      setState({
        status: "error",
        message: e instanceof Error ? e.message : "Unknown error",
      });
    }
  }, [routeId]);

  useEffect(() => {
    void load();
    listCustomers({ status: "active", limit: 200 })
      .then(setAllCustomers)
      .catch(() => setAllCustomers([]));
  }, [load]);

  const onAttach = async () => {
    if (!addCustomerId) return;
    setErr(null);
    setMutating(true);
    try {
      await attachRouteCustomer(routeId, { customer_id: addCustomerId });
      setAddCustomerId("");
      await load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setMutating(false);
    }
  };

  const onDetach = async (customerId: string) => {
    setErr(null);
    setMutating(true);
    try {
      await detachRouteCustomer(routeId, customerId);
      await load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setMutating(false);
    }
  };

  const onSaveOrder = async () => {
    if (state.status !== "ok") return;
    setErr(null);
    setMutating(true);
    try {
      const sorted = [...state.links].sort(
        (a, b) =>
          (orderEdits[a.customer_id] ?? a.sequence_position) -
          (orderEdits[b.customer_id] ?? b.sequence_position),
      );
      const newOrder = sorted.map((l) => l.customer_id);
      await reorderRouteCustomers(routeId, newOrder);
      await load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setMutating(false);
    }
  };

  if (state.status === "loading") {
    return <div className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading route…</div>;
  }
  if (state.status === "error") {
    return (
      <div className="p-6">
        <Link
          href="/delivery/routes"
          className="text-sm" style={{ color: "var(--text-secondary)" }}
        >
          ← Routes
        </Link>
        <div className="mt-4 rounded border border-red-300 bg-red-50 p-4">
          <p className="font-semibold">Error</p>
          <p className="mt-1 text-sm opacity-80">{state.message}</p>
        </div>
      </div>
    );
  }

  const { route, links } = state;
  const linkedIds = new Set(links.map((l) => l.customer_id));
  const available = allCustomers.filter((c) => !linkedIds.has(c.id));

  const orderDirty = links.some(
    (l) => (orderEdits[l.customer_id] ?? l.sequence_position) !== l.sequence_position,
  );

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>{route.name}</h1>
        <p className="text-sm ">
          {route.kitchen_name ?? "—"} · {route.area ?? "—"} ·{" "}
          {route.target_window_start ?? "—"} → {route.target_window_end ?? "—"} ·{" "}
          <span className="font-semibold">{route.status}</span>
        </p>
      </div>

      {err && (
        <div className="mb-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {err}
        </div>
      )}

      <div className="mb-6 rounded border p-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide ">
          Attach customer
        </h2>
        <div className="flex flex-col gap-2 sm:flex-row">
          <select
            value={addCustomerId}
            onChange={(e) => setAddCustomerId(e.target.value)}
            className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="">Select customer…</option>
            {available.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} {c.phone ? `(${c.phone})` : ""}
              </option>
            ))}
          </select>
          <button
            type="button"
            disabled={!addCustomerId || mutating}
            onClick={onAttach}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:bg-slate-400"
          >
            Attach
          </button>
        </div>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <div className="flex items-center justify-between gap-2 border-b border-slate-200 px-4 py-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide ">
            Customers on route ({links.length})
          </h2>
          <button
            type="button"
            disabled={!orderDirty || mutating}
            onClick={onSaveOrder}
            className="rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700 disabled:bg-slate-300"
          >
            {mutating ? "Saving…" : "Save Order"}
          </button>
        </div>
        {links.length === 0 && (
          <div className="p-6 text-sm text-sm" style={{ color: "var(--text-muted)" }}>
            No customers on this route yet.
          </div>
        )}
        {links.length > 0 && (
          <ul >
            {links.map((l) => (
              <li
                key={l.id}
                className="flex items-center gap-3 px-4 py-3 text-sm"
              >
                <input
                  type="number"
                  min={1}
                  value={orderEdits[l.customer_id] ?? l.sequence_position}
                  onChange={(e) =>
                    setOrderEdits((o) => ({
                      ...o,
                      [l.customer_id]: Number.parseInt(e.target.value, 10),
                    }))
                  }
                  className="w-16 rounded border border-slate-300 px-2 py-1 text-right font-mono"
                />
                <div className="flex-1">
                  <div className="font-medium ">
                    {l.customer_name ?? "—"}
                  </div>
                  <div className="text-xs text-sm" style={{ color: "var(--text-muted)" }}>
                    {l.customer_phone ?? "—"}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => onDetach(l.customer_id)}
                  disabled={mutating}
                  className="rounded border border-rose-200 bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-700 hover:bg-rose-100"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
