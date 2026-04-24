"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { getCustomer, listSubscriptions } from "@/lib/api";
import type { Customer, Subscription } from "@/types/api";

type CustomerState =
  | { status: "loading" }
  | { status: "ok"; data: Customer }
  | { status: "error"; message: string };

type SubsState =
  | { status: "loading" }
  | { status: "ok"; items: Subscription[] }
  | { status: "error"; message: string };

export default function CustomerDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [customer, setCustomer] = useState<CustomerState>({ status: "loading" });
  const [subs, setSubs] = useState<SubsState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    getCustomer(id)
      .then((data) => {
        if (!cancelled) setCustomer({ status: "ok", data });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setCustomer({
          status: "error",
          message: err instanceof Error ? err.message : "Unknown error",
        });
      });
    listSubscriptions({ customer_id: id })
      .then((items) => {
        if (!cancelled) setSubs({ status: "ok", items });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setSubs({
          status: "error",
          message: err instanceof Error ? err.message : "Unknown error",
        });
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        {customer.status === "ok" && (
          <h1 className="mt-2 text-3xl font-bold tracking-tight">
            {customer.data.name}
          </h1>
        )}
      </div>

      {customer.status === "loading" && (
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading customer…</p>
      )}
      {customer.status === "error" && (
        <p className="text-red-700">{customer.message}</p>
      )}

      {customer.status === "ok" && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
            <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide ">
              Info
            </h2>
            <dl className="grid grid-cols-2 gap-2 text-sm">
              <dt className="">Slug</dt>
              <dd className="font-mono">{customer.data.slug}</dd>
              <dt className="">Status</dt>
              <dd>{customer.data.status}</dd>
              <dt className="">Email</dt>
              <dd className="font-mono">{customer.data.email ?? "—"}</dd>
              <dt className="">Phone</dt>
              <dd className="font-mono">{customer.data.phone ?? "—"}</dd>
              <dt className="">Location</dt>
              <dd>{customer.data.location_name ?? "—"}</dd>
              <dt className="">Delivery notes</dt>
              <dd>{customer.data.delivery_notes ?? "—"}</dd>
              <dt className="">Acquired via</dt>
              <dd>{customer.data.acquisition_source ?? "—"}</dd>
              <dt className="">LTV</dt>
              <dd className="font-mono">{customer.data.lifetime_value}</dd>
            </dl>
            <div className="mt-4 rounded border border-slate-200 bg-slate-50 p-3 font-mono text-xs ">
              <div className="mb-1 font-semibold text-sm" style={{ color: "var(--text-muted)" }}>Address</div>
              <pre className="whitespace-pre-wrap">
                {JSON.stringify(customer.data.address_jsonb, null, 2)}
              </pre>
            </div>
          </div>

          <div className="rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-xs font-semibold uppercase tracking-wide ">
                Subscriptions
              </h2>
              <Link
                href={`/subscriptions/list/new?customer_id=${id}`}
                className="rounded-md bg-slate-900 px-3 py-1 text-xs font-medium text-white hover:bg-slate-800"
              >
                + New Subscription
              </Link>
            </div>
            {subs.status === "loading" && (
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading subscriptions…</p>
            )}
            {subs.status === "error" && (
              <p className="text-red-700">{subs.message}</p>
            )}
            {subs.status === "ok" && subs.items.length === 0 && (
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>No subscriptions yet.</p>
            )}
            {subs.status === "ok" && subs.items.length > 0 && (
              <ul >
                {subs.items.map((s) => (
                  <li key={s.id} className="py-3">
                    <Link
                      href={`/subscriptions/list/${s.id}`}
                      className="flex items-center justify-between hover:bg-slate-50"
                    >
                      <div>
                        <div className="font-medium">{s.plan_name}</div>
                        <div className="text-xs text-sm" style={{ color: "var(--text-muted)" }}>
                          {s.frequency_name} · since {s.start_date}
                        </div>
                      </div>
                      <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs font-medium ">
                        {s.status}
                      </span>
                    </Link>
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
