"use client";

import type { StatCard } from "./types";

export function StatCards({ cards }: { cards: StatCard[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {cards.map(({ label, value, icon: Icon, testId }) => (
        <div
          key={label}
          className="flex items-center gap-3 rounded-lg px-4 py-3"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
            borderTop: "2px solid var(--accent)",
          }}
          data-testid={testId}
        >
          <div
            className="shrink-0 rounded-lg p-2"
            style={{ background: "var(--accent-muted)" }}
          >
            <Icon className="h-4 w-4" style={{ color: "var(--accent)" }} />
          </div>
          <div className="min-w-0">
            <span
              className="block text-2xl font-bold tabular-nums leading-none"
              style={{ color: "var(--text-primary)" }}
            >
              {value}
            </span>
            <span
              className="mt-0.5 block truncate"
              style={{ fontSize: "10px", color: "var(--text-muted)", letterSpacing: "0.06em", textTransform: "uppercase" }}
            >
              {label}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
