"use client";

import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { FEATURES } from "@/config/features";

const FEATURE_META: Record<
  string,
  { accent: string; glyph: string; desc: string }
> = {
  iam: {
    accent: "#00c47a",
    glyph: "IAM",
    desc: "Identity & access management — orgs, workspaces, users, roles, sessions",
  },
  "feature-flags": {
    accent: "#2d7ef7",
    glyph: "FF",
    desc: "Feature flag targeting — environments, rules, overrides, evaluation",
  },
  vault: {
    accent: "#f5a623",
    glyph: "VLT",
    desc: "Encrypted secrets & runtime config — rotations, expiry, access logs",
  },
  audit: {
    accent: "#ff6b35",
    glyph: "AUD",
    desc: "Immutable audit trail — events, authz decisions, analytics, funnels",
  },
  monitoring: {
    accent: "#9d6ef8",
    glyph: "MON",
    desc: "Logs, metrics, traces, alerts, dashboards, SLO tracking",
  },
  notify: {
    accent: "#00c8f0",
    glyph: "NTF",
    desc: "Notification delivery — templates, campaigns, deliveries, preferences",
  },
  nodes: {
    accent: "#ff4d7d",
    glyph: "NOD",
    desc: "Node registry — platform building blocks, flow composition, execution",
  },
  flows: {
    accent: "#7ef7c8",
    glyph: "FLW",
    desc: "Workflow DAGs — draft, publish, version, execute, trace",
  },
};

function FeatureCard({
  f,
}: {
  f: (typeof FEATURES)[number];
}) {
  const landing = f.subFeatures[0]?.href ?? f.basePath;
  const meta = FEATURE_META[f.key];
  const accent = meta?.accent ?? "var(--accent)";

  return (
    <Link
      href={landing}
      className="group flex flex-col gap-3 rounded border p-4 transition-all duration-150"
      style={{
        background: "var(--bg-surface)",
        borderColor: "var(--border)",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = accent;
        (e.currentTarget as HTMLElement).style.boxShadow = `0 0 20px ${accent}18`;
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = "var(--border)";
        (e.currentTarget as HTMLElement).style.boxShadow = "none";
      }}
      data-testid={`overview-feature-${f.key}`}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <div
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded text-[9px] font-bold tracking-wider"
          style={{
            background: `${accent}18`,
            color: accent,
            border: `1px solid ${accent}30`,
            fontFamily: "var(--font-mono)",
          }}
        >
          {meta?.glyph ?? f.label.slice(0, 3).toUpperCase()}
        </div>
        <span
          className="text-[10px] font-semibold tracking-wider opacity-0 transition-opacity group-hover:opacity-100"
          style={{ color: accent, fontFamily: "var(--font-mono)" }}
        >
          ENTER →
        </span>
      </div>

      {/* Feature name */}
      <div>
        <div
          className="text-[13px] font-semibold tracking-wide"
          style={{ color: "var(--text-primary)" }}
        >
          {f.label}
        </div>
        <p
          className="mt-0.5 text-[11px] leading-relaxed"
          style={{ color: "var(--text-muted)" }}
        >
          {meta?.desc ?? f.description}
        </p>
      </div>

      {/* Sub-feature pills */}
      {f.subFeatures.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {f.subFeatures.slice(0, 5).map((s) => (
            <span
              key={s.href}
              className="rounded px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide"
              style={{
                border: `1px solid var(--border)`,
                color: "var(--text-muted)",
                background: "var(--bg-elevated)",
                fontFamily: "var(--font-mono)",
              }}
            >
              {s.label}
            </span>
          ))}
          {f.subFeatures.length > 5 && (
            <span
              className="rounded px-1.5 py-0.5 text-[9px]"
              style={{ color: "var(--text-muted)" }}
            >
              +{f.subFeatures.length - 5}
            </span>
          )}
        </div>
      )}

      {/* Accent bottom bar */}
      <div
        className="mt-auto h-0.5 w-0 rounded-full transition-all duration-300 group-hover:w-full"
        style={{
          background: `linear-gradient(90deg, ${accent}, transparent)`,
        }}
        aria-hidden
      />
    </Link>
  );
}

export default function Overview() {
  const features = FEATURES.filter((f) => f.key !== "overview");
  return (
    <div className="flex flex-1 flex-col">
      <PageHeader
        title="Platform Overview"
        description="Every module installed on this TennetCTL instance."
        testId="heading"
      />
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {features.map((f) => (
            <FeatureCard key={f.key} f={f} />
          ))}
        </div>
      </div>
    </div>
  );
}
