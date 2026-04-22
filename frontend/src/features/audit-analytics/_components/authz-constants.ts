import { Clock, Flag, KeyRound, Shield, ShieldCheck, Users } from "lucide-react";

export type CategoryCode =
  | "all"
  | "permissions"
  | "flags"
  | "roles"
  | "sso_mfa"
  | "sessions";

export type CategoryMeta = {
  label: string;
  icon: typeof Shield;
  prefixes: string[];
  borderCls: string;
  badgeCls: string;
  numCls: string;
  emptyMsg: string;
};

export const CATEGORY_META: Record<CategoryCode, CategoryMeta> = {
  all: {
    label: "All",
    icon: ShieldCheck,
    prefixes: [
      "authz.",
      "iam.users.",
      "flags.",
      "featureflags.",
      "iam.roles.",
      "iam.groups.",
      "iam.oidc.",
      "iam.saml.",
      "iam.mfa.",
      "iam.sessions.",
      "iam.auth.",
    ],
    borderCls: "border-l-zinc-900 dark:border-l-zinc-100",
    badgeCls:
      "bg-zinc-100 border-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-300",
    numCls: "text-zinc-900 dark:text-zinc-50",
    emptyMsg: "No AuthZ events in this time range — try widening the window.",
  },
  permissions: {
    label: "Permissions",
    icon: KeyRound,
    prefixes: ["authz.permission.", "iam.users."],
    borderCls: "border-l-violet-500",
    badgeCls:
      "bg-violet-50 border-violet-200 text-violet-700 dark:bg-violet-900/30 dark:border-violet-800 dark:text-violet-300",
    numCls: "text-violet-600 dark:text-violet-400",
    emptyMsg:
      "No permission checks in this time range — tighten the time range or widen the categories.",
  },
  flags: {
    label: "Flags",
    icon: Flag,
    prefixes: ["flags.", "featureflags."],
    borderCls: "border-l-amber-500",
    badgeCls:
      "bg-amber-50 border-amber-200 text-amber-700 dark:bg-amber-900/30 dark:border-amber-800 dark:text-amber-300",
    numCls: "text-amber-600 dark:text-amber-400",
    emptyMsg:
      "No flag evaluations in this time range — ensure feature flag activity is being recorded.",
  },
  roles: {
    label: "Roles",
    icon: Users,
    prefixes: ["iam.roles.", "iam.groups."],
    borderCls: "border-l-blue-500",
    badgeCls:
      "bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-900/30 dark:border-blue-800 dark:text-blue-300",
    numCls: "text-blue-600 dark:text-blue-400",
    emptyMsg:
      "No role mutations in this time range — role create/assign/revoke events will appear here.",
  },
  sso_mfa: {
    label: "SSO / MFA",
    icon: Shield,
    prefixes: ["iam.oidc.", "iam.saml.", "iam.mfa."],
    borderCls: "border-l-emerald-500",
    badgeCls:
      "bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-900/30 dark:border-emerald-800 dark:text-emerald-300",
    numCls: "text-emerald-600 dark:text-emerald-400",
    emptyMsg:
      "No SSO or MFA events in this time range — OIDC/SAML/MFA activity will appear here.",
  },
  sessions: {
    label: "Sessions",
    icon: Clock,
    prefixes: ["iam.sessions.", "iam.auth."],
    borderCls: "border-l-rose-500",
    badgeCls:
      "bg-rose-50 border-rose-200 text-rose-700 dark:bg-rose-900/30 dark:border-rose-800 dark:text-rose-300",
    numCls: "text-rose-600 dark:text-rose-400",
    emptyMsg:
      "No session or auth events in this time range — login and session activity appears here.",
  },
};

export const CATEGORIES = Object.keys(CATEGORY_META) as CategoryCode[];

// All authz prefixes combined (for the broad server-side q-filter fallback)
export const ALL_AUTHZ_PREFIXES = CATEGORY_META.all.prefixes;

export type TimeRange = "1h" | "24h" | "7d" | "30d";

export const TIME_RANGE_LABELS: Record<TimeRange, string> = {
  "1h": "1h",
  "24h": "24h",
  "7d": "7d",
  "30d": "30d",
};

export function sinceForRange(range: TimeRange): string {
  const now = new Date();
  const ms: Record<TimeRange, number> = {
    "1h": 60 * 60 * 1000,
    "24h": 24 * 60 * 60 * 1000,
    "7d": 7 * 24 * 60 * 60 * 1000,
    "30d": 30 * 24 * 60 * 60 * 1000,
  };
  return new Date(now.getTime() - ms[range]).toISOString();
}

export function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const secs = Math.floor(diff / 1000);
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export function dateGroupLabel(iso: string): string {
  const d = new Date(iso);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);

  if (d.toDateString() === today.toDateString()) return "Today";
  if (d.toDateString() === yesterday.toDateString()) return "Yesterday";
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function matchesPrefixes(eventKey: string, prefixes: string[]): boolean {
  return prefixes.some((p) => eventKey.startsWith(p));
}

export function deriveCategoryCode(eventKey: string): CategoryCode {
  for (const cat of CATEGORIES) {
    if (cat === "all") continue;
    if (matchesPrefixes(eventKey, CATEGORY_META[cat].prefixes)) return cat;
  }
  return "all";
}

export type StatCardDef = {
  kind: string;
  label: string;
  value: number;
  icon: typeof Shield;
  borderCls: string;
  numCls: string;
};
