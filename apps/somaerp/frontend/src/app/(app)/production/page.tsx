"use client";

import Link from "next/link";

export default function ProductionLandingPage() {
  return (
    <div className="max-w-5xl">
      <div className="mb-8">
        <Link
          href="/"
          className="text-sm" style={{ color: "var(--text-secondary)" }}
        >
          ← somaerp
        </Link>
        <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
          Production
        </h1>
        <p className="mt-2 ">
          The 4 AM tracker. State machine planned → in_progress → completed.
          Auto-emits inventory consumption on complete. Live yield, COGS,
          gross margin.
        </p>
      </div>

      <ul className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <li>
          <Link
            href="/production/board"
            className="block rounded-lg border border-amber-300 bg-amber-50 p-5 shadow-sm transition hover:border-amber-500 hover:shadow"
          >
            <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Today’s Board</div>
            <div className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
              Live per-kitchen view of today’s batches.
            </div>
          </Link>
        </li>
        <li>
          <Link
            href="/production/batches/new"
            className="block rounded-lg border border-emerald-300 bg-emerald-50 p-5 shadow-sm transition hover:border-emerald-500 hover:shadow"
          >
            <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>New Batch</div>
            <div className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
              Plan a batch — kitchen, product, recipe, planned yield.
            </div>
          </Link>
        </li>
        <li>
          <Link
            href="/production/batches"
            className="block rounded border p-5 transition-colors" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
          >
            <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Batches</div>
            <div className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
              Browse all batches — filter by kitchen, status, date.
            </div>
          </Link>
        </li>
      </ul>
    </div>
  );
}
