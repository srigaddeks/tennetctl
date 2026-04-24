"use client";

import Link from "next/link";

export default function SubscriptionsLandingPage() {
  return (
    <div className="max-w-5xl">
      <div className="mb-8">
        <h1 className="mt-2 text-3xl font-bold tracking-tight">
          Subscriptions
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Plan templates and customer subscriptions.
        </p>
      </div>

      <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <li>
          <Link
            href="/subscriptions/plans"
            className="block rounded border p-5 transition-colors" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
          >
            <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Plans</div>
            <div className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
              Plan templates with cadence + product mix
            </div>
          </Link>
        </li>
        <li>
          <Link
            href="/subscriptions/list"
            className="block rounded border p-5 transition-colors" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
          >
            <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Customer Subscriptions</div>
            <div className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
              Active + paused + cancelled subscriptions per customer
            </div>
          </Link>
        </li>
      </ul>
    </div>
  );
}
