"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listContacts, listDeals, listLeads, listActivities, getPipelineSummary } from "@/lib/api";
import type { Activity } from "@/types/api";

type CountState = number | null;

type ActivitiesState =
  | { status: "loading" }
  | { status: "ok"; items: Activity[] }
  | { status: "error"; message: string };

const STAT_COLORS = ["#1D4ED8", "#059669", "#D97706", "#7C3AED"];

const MODULES = [
  { href: "/contacts", title: "Contacts", description: "People you do business with" },
  { href: "/organizations", title: "Organizations", description: "Companies and teams" },
  { href: "/leads", title: "Leads", description: "Potential customers and opportunities" },
  { href: "/pipeline", title: "Pipeline", description: "Deals organized by stage" },
  { href: "/deals", title: "Deals", description: "Revenue opportunities and close rates" },
  { href: "/activities", title: "Activities", description: "Tasks, calls, emails, meetings" },
  { href: "/reports", title: "Reports", description: "Pipeline summary, lead conversion, growth" },
];

export default function DashboardPage() {
  const [contactCount, setContactCount] = useState<CountState>(null);
  const [dealCount, setDealCount] = useState<CountState>(null);
  const [openLeadCount, setOpenLeadCount] = useState<CountState>(null);
  const [pipelineValue, setPipelineValue] = useState<CountState>(null);
  const [recentActivities, setRecentActivities] = useState<ActivitiesState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    listContacts()
      .then((items) => { if (!cancelled) setContactCount(items.length); })
      .catch(() => { if (!cancelled) setContactCount(0); });

    listDeals()
      .then((items) => { if (!cancelled) setDealCount(items.length); })
      .catch(() => { if (!cancelled) setDealCount(0); });

    listLeads({ status: "new" })
      .then((items) => { if (!cancelled) setOpenLeadCount(items.length); })
      .catch(() => { if (!cancelled) setOpenLeadCount(0); });

    getPipelineSummary()
      .then((stages) => {
        if (!cancelled) {
          const total = stages.reduce((acc, s) => acc + s.total_value, 0);
          setPipelineValue(total);
        }
      })
      .catch(() => { if (!cancelled) setPipelineValue(0); });

    listActivities({ limit: 5 })
      .then((items) => { if (!cancelled) setRecentActivities({ status: "ok", items }); })
      .catch((err: unknown) => {
        if (!cancelled) setRecentActivities({
          status: "error",
          message: err instanceof Error ? err.message : "Unknown error",
        });
      });

    return () => { cancelled = true; };
  }, []);

  const stats = [
    { label: "Total Contacts", value: contactCount, color: STAT_COLORS[0] },
    { label: "Total Deals", value: dealCount, color: STAT_COLORS[1] },
    { label: "Open Leads", value: openLeadCount, color: STAT_COLORS[2] },
    { label: "Pipeline Value", value: pipelineValue !== null ? `$${pipelineValue.toLocaleString()}` : null, color: STAT_COLORS[3] },
  ];

  return (
    <div className="max-w-5xl">
      <div className="page-header">
        <div>
          <h1 className="page-title">somacrm — Dashboard</h1>
          <p className="page-subtitle">CRM built on tennetctl primitives. Contacts, pipeline, and activities in one place.</p>
        </div>
      </div>

      {/* Stat cards */}
      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="stat-card"
            style={{ borderTopColor: stat.color }}
          >
            <div className="stat-label">{stat.label}</div>
            <div className="stat-value" style={{ color: stat.value === null ? "var(--text-muted)" : "var(--text-primary)" }}>
              {stat.value === null ? "—" : stat.value}
            </div>
          </div>
        ))}
      </div>

      {/* Module navigation grid */}
      <div className="mb-6">
        <h2 style={{ marginBottom: 12, fontSize: 10.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)" }}>
          Modules
        </h2>
        <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {MODULES.map((mod) => (
            <li key={mod.href}>
              <Link href={mod.href} className="module-card">
                <div className="module-card-title">{mod.title}</div>
                <div className="module-card-desc">{mod.description}</div>
              </Link>
            </li>
          ))}
        </ul>
      </div>

      {/* Recent activities */}
      <div className="rounded border p-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <div className="flex items-center justify-between mb-3">
          <h2 style={{ fontSize: 10.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)" }}>
            Recent Activities
          </h2>
          <Link href="/activities" style={{ fontSize: 12, color: "var(--accent)", textDecoration: "none", fontWeight: 600 }}>
            View all →
          </Link>
        </div>

        {recentActivities.status === "loading" && (
          <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading activities…</p>
        )}

        {recentActivities.status === "error" && (
          <p style={{ fontSize: 13, color: "var(--status-error)" }}>Failed to load activities.</p>
        )}

        {recentActivities.status === "ok" && recentActivities.items.length === 0 && (
          <p style={{ fontSize: 13, color: "var(--text-muted)" }}>No activities yet. Create your first activity.</p>
        )}

        {recentActivities.status === "ok" && recentActivities.items.length > 0 && (
          <ul style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {recentActivities.items.map((activity) => (
              <li key={activity.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
                <span style={{
                  display: "inline-flex", alignItems: "center", justifyContent: "center",
                  width: 28, height: 28, borderRadius: 6,
                  backgroundColor: "var(--bg-surface)",
                  fontSize: 14,
                  flexShrink: 0,
                }}>
                  {activity.activity_type_icon}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {activity.title}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    {activity.activity_type_label} · {activity.due_at ? new Date(activity.due_at).toLocaleDateString() : "No due date"}
                  </div>
                </div>
                <ActivityStatusBadge status={activity.status} />
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function ActivityStatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800",
    in_progress: "bg-blue-100 text-blue-800",
    done: "bg-green-100 text-green-800",
    cancelled: "bg-red-100 text-red-800",
  };
  return (
    <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${styles[status] ?? "bg-slate-100 text-slate-700"}`}>
      {status}
    </span>
  );
}
