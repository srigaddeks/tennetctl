"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, listLocations, listProducts, listRawMaterials, listCustomers } from "@/lib/api";
import type { HealthData } from "@/types/api";

type HealthState =
  | { status: "loading" }
  | { status: "ok"; data: HealthData }
  | { status: "error"; message: string };

type Module = {
  href: string;
  title: string;
  description: string;
};

const MODULES: Module[] = [
  { href: "/geography", title: "Geography", description: "Locations, kitchens, service zones" },
  { href: "/catalog", title: "Catalog", description: "Product lines, products, variants" },
  { href: "/supply", title: "Supply", description: "Raw materials, suppliers, supply matrix" },
  { href: "/recipes", title: "Recipes", description: "Versioned recipes, BOM cost rollup" },
  { href: "/equipment", title: "Equipment", description: "Kitchen equipment + attach to kitchens" },
  { href: "/quality", title: "Quality", description: "QC checkpoints + append-only check events" },
  { href: "/procurement", title: "Procurement", description: "Procurement runs + MRP-lite BOM planner" },
  { href: "/inventory", title: "Inventory", description: "Current stock per kitchen + movement feed" },
  { href: "/production", title: "Production", description: "The 4 AM tracker — batches, step log, yield" },
  { href: "/customers", title: "Customers", description: "Customer directory + status + subscriptions" },
  { href: "/subscriptions", title: "Subscriptions", description: "Plan templates + pause/resume/cancel" },
  { href: "/delivery", title: "Delivery", description: "Routes, riders, runs, stop-by-stop delivery" },
  { href: "/reports", title: "Reports", description: "KPI snapshot, yield/COGS trends, alerts" },
];

// Greyscale-only — top borders use a single charcoal stroke, no decorative colour.
const STAT_COLOR = "var(--grey-900)";

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthState>({ status: "loading" });
  const [locationCount, setLocationCount] = useState<number | null>(null);
  const [productCount, setProductCount] = useState<number | null>(null);
  const [rawMatCount, setRawMatCount] = useState<number | null>(null);
  const [customerCount, setCustomerCount] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiFetch<HealthData>("/v1/somaerp/health")
      .then((data) => { if (!cancelled) setHealth({ status: "ok", data }); })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setHealth({ status: "error", message });
      });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    listLocations()
      .then((items) => { if (!cancelled) setLocationCount(items.length); })
      .catch(() => { if (!cancelled) setLocationCount(0); });
    listProducts()
      .then((items) => { if (!cancelled) setProductCount(items.length); })
      .catch(() => { if (!cancelled) setProductCount(0); });
    listRawMaterials()
      .then((items) => { if (!cancelled) setRawMatCount(items.length); })
      .catch(() => { if (!cancelled) setRawMatCount(0); });
    listCustomers()
      .then((items) => { if (!cancelled) setCustomerCount(items.length); })
      .catch(() => { if (!cancelled) setCustomerCount(0); });
    return () => { cancelled = true; };
  }, []);

  const stats = [
    { label: "Locations", value: locationCount, color: STAT_COLOR },
    { label: "Products", value: productCount, color: STAT_COLOR },
    { label: "Raw Materials", value: rawMatCount, color: STAT_COLOR },
    { label: "Customers", value: customerCount, color: STAT_COLOR },
  ];

  return (
    <div className="max-w-5xl">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Good morning — somaerp</h1>
          <p className="page-subtitle">Generic multi-kitchen, multi-region ERP built on tennetctl primitives.</p>
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
        <h2
          style={{ marginBottom: 12, fontSize: 10.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)" }}
        >
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

      {/* Health widget */}
      <div
        className="rounded border p-4"
        style={{
          backgroundColor: "var(--bg-card)",
          borderColor: "var(--border)",
        }}
      >
        <h2
          style={{ marginBottom: 12, fontSize: 10.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)" }}
        >
          System Health
        </h2>

        {health.status === "loading" && (
          <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
            Checking backend…
          </p>
        )}

        {health.status === "error" && (
          <div
            className="rounded border p-3"
            style={{
              borderColor: "var(--status-error)",
              backgroundColor: "var(--status-error-bg)",
              color: "var(--status-error-text)",
              fontSize: 13,
            }}
          >
            <span style={{ fontWeight: 600 }}>Backend unreachable</span>
            <span style={{ marginLeft: 8, opacity: 0.8 }}>{health.message}</span>
            <span style={{ marginLeft: 8, fontSize: 11, opacity: 0.6 }}>
              Start somaerp backend on port 51736.
            </span>
          </div>
        )}

        {health.status === "ok" && (
          <div className="flex flex-wrap gap-6">
            <div>
              <div style={{ fontSize: 10.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)" }}>Version</div>
              <div className="mt-0.5 mono" style={{ fontSize: 12, color: "var(--text-primary)" }}>
                {health.data.somaerp_version}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 10.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)" }}>Uptime</div>
              <div className="mt-0.5 mono" style={{ fontSize: 12, color: "var(--text-primary)" }}>
                {health.data.somaerp_uptime_s.toFixed(1)} s
              </div>
            </div>
            <div>
              <div style={{ fontSize: 10.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)" }}>Proxy</div>
              <div className="mt-0.5 mono" style={{ fontSize: 12, color: health.data.tennetctl_proxy.ok ? "var(--status-active)" : "var(--status-error)" }}>
                {health.data.tennetctl_proxy.ok ? "OK" : "FAIL"} — {health.data.tennetctl_proxy.latency_ms.toFixed(0)} ms
              </div>
            </div>
            <div>
              <div style={{ fontSize: 10.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)" }}>Base URL</div>
              <div className="mt-0.5 mono" style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                {health.data.tennetctl_proxy.base_url}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
