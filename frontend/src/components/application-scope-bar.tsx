"use client";

/**
 * ApplicationScopeBar — shared filter bar that makes Application a first-class
 * navigation lens across every IAM page.
 *
 * Pattern: drop this at the top of any page that manages application-scoped
 * resources. It shows a compact app picker with colored avatars, org context,
 * and a "View hub" shortcut. Pages read `appId` from their URL query string or
 * local state and pass it back via `onChange`.
 */

import Link from "next/link";
import { ExternalLink, Filter, Layers } from "lucide-react";

import { useApplications } from "@/features/iam-applications/hooks/use-applications";
import { cn } from "@/lib/cn";

// ── Deterministic per-app colour ───────────────────────────────────────────

const APP_COLORS = [
  "#1f6feb", "#6e40c9", "#e36209", "#2da44e",
  "#f78166", "#79c0ff", "#56d364", "#d29922",
];

export function appColor(code: string): string {
  return APP_COLORS[(code?.charCodeAt(0) ?? 0) % APP_COLORS.length];
}

// ── Mini avatar ────────────────────────────────────────────────────────────

export function AppAvatar({
  code,
  size = 24,
}: {
  code: string | null;
  size?: number;
}) {
  const ch = (code ?? "A")[0]?.toUpperCase() ?? "A";
  const color = appColor(code ?? "a");
  const fs = Math.round(size * 0.46);
  return (
    <div
      className="rounded-md flex items-center justify-center text-white font-bold flex-shrink-0"
      style={{ width: size, height: size, backgroundColor: color, fontSize: fs }}
    >
      {ch}
    </div>
  );
}

// ── Scope bar ──────────────────────────────────────────────────────────────

type Props = {
  appId: string | null;
  onChange: (appId: string | null) => void;
  orgId?: string | null;
  label?: string;
};

export function ApplicationScopeBar({ appId, onChange, orgId, label }: Props) {
  const { data } = useApplications({ limit: 200, org_id: orgId ?? undefined });
  const apps = data?.items ?? [];
  const selected = apps.find((a) => a.id === appId) ?? null;

  return (
    <div className="flex items-center gap-3 px-4 py-2.5 border border-[#21262d] rounded-lg bg-[#0d1117]/60">
      <Filter size={13} className="text-[#8b949e] flex-shrink-0" />
      <span className="text-[10px] font-semibold uppercase tracking-wider text-[#8b949e] whitespace-nowrap">
        {label ?? "Application scope"}
      </span>

      {/* Picker */}
      <div className="relative flex-1">
        <select
          value={appId ?? ""}
          onChange={(e) => onChange(e.target.value || null)}
          className={cn(
            "w-full appearance-none bg-[#161b22] border border-[#30363d] rounded-md",
            "pl-9 pr-8 py-1.5 text-xs text-[#e6edf3] font-mono",
            "hover:border-[#58a6ff] focus:border-[#58a6ff] focus:outline-none transition-colors",
            "cursor-pointer"
          )}
        >
          <option value="">All applications ({apps.length})</option>
          {apps.map((a) => (
            <option key={a.id} value={a.id}>
              {a.label ?? a.code} · {a.code}
            </option>
          ))}
        </select>
        {/* Avatar overlay */}
        <div className="absolute left-2 top-1/2 -translate-y-1/2 pointer-events-none">
          {selected ? (
            <AppAvatar code={selected.code} size={18} />
          ) : (
            <Layers size={14} className="text-[#8b949e]" />
          )}
        </div>
        {/* Chevron */}
        <span className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-[#8b949e] text-[9px]">
          ▼
        </span>
      </div>

      {/* Hub shortcut */}
      {selected && (
        <Link
          href={`/iam/applications/${selected.id}`}
          className={cn(
            "flex items-center gap-1 px-2.5 py-1.5 rounded-md",
            "text-xs font-semibold text-[#58a6ff] hover:text-white",
            "border border-[#30363d] hover:bg-[#1f6feb] hover:border-[#1f6feb]",
            "transition-colors whitespace-nowrap"
          )}
          title="Open this application's hub"
        >
          Hub
          <ExternalLink size={10} />
        </Link>
      )}
    </div>
  );
}
