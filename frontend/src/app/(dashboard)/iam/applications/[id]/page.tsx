"use client";

import Link from "next/link";
import { use, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  ArrowLeft,
  ChevronRight,
  Copy,
  ExternalLink,
  Flag,
  Key,
  Layers,
  Shield,
  Terminal,
} from "lucide-react";

import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Skeleton,
  StatCard,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import { useApplication } from "@/features/iam-applications/hooks/use-applications";
import { apiFetch, apiList, buildQuery } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { AuditEventRow, Flag as FlagType, Role } from "@/types/api";

// ─── Types ────────────────────────────────────────────────────────────────────

type ApiKey = {
  id: string;
  key_id: string;
  name: string;
  prefix: string;
  created_at: string;
  last_used_at: string | null;
  expires_at: string | null;
  is_active: boolean;
};

type Tab = "overview" | "flags" | "roles" | "api-keys" | "audit";

// ─── Helpers ──────────────────────────────────────────────────────────────────

const APP_COLORS = [
  "#1f6feb", "#6e40c9", "#e36209", "#2da44e",
  "#f78166", "#79c0ff", "#56d364", "#d29922",
];

function appColor(code: string) {
  return APP_COLORS[(code?.charCodeAt(0) ?? 0) % APP_COLORS.length];
}

function timeAgo(ts: string) {
  const diff = Date.now() - new Date(ts).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function formatDate(ts: string) {
  return new Date(ts).toLocaleDateString("en-GB", {
    day: "2-digit", month: "short", year: "numeric",
  });
}

// ─── Tab button ───────────────────────────────────────────────────────────────

function TabBtn({
  label, icon: Icon, active, onClick,
}: {
  label: string; icon: React.ElementType; active: boolean; onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-1.5 px-4 py-2.5 text-xs font-semibold uppercase tracking-wider border-b-2 transition-colors whitespace-nowrap",
        active
          ? "border-[#388bfd] text-[#58a6ff]"
          : "border-transparent text-[#8b949e] hover:text-[#e6edf3] hover:border-[#30363d]"
      )}
    >
      <Icon size={13} />
      {label}
    </button>
  );
}

// ─── Detail row ───────────────────────────────────────────────────────────────

function DetailRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start py-2.5 border-b border-[#21262d] last:border-0">
      <span className="w-36 flex-shrink-0 text-xs font-semibold uppercase tracking-wider text-[#8b949e]">
        {label}
      </span>
      <span className="text-sm text-[#e6edf3] font-mono break-all">{children}</span>
    </div>
  );
}

// ─── Outcome badge ────────────────────────────────────────────────────────────

function OutcomeBadge({ outcome }: { outcome: string }) {
  return (
    <Badge tone={outcome === "success" ? "success" : "danger"}>
      {outcome}
    </Badge>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ApplicationHubPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { toast } = useToast();
  const [tab, setTab] = useState<Tab>("overview");

  // ─── Data ────────────────────────────────────────────────────────────
  const { data: app, isLoading: appLoading, isError: appError } =
    useApplication(id);

  const { data: flagsData, isLoading: flagsLoading } = useQuery({
    queryKey: ["app-hub", id, "flags"],
    queryFn: () => apiList<FlagType>(`/v1/flags${buildQuery({ application_id: id, limit: 100 })}`),
    enabled: !!id,
  });

  const { data: auditData, isLoading: auditLoading } = useQuery({
    queryKey: ["app-hub", id, "audit"],
    queryFn: () =>
      apiFetch<{ items: AuditEventRow[]; total: number }>(
        `/v1/audit-events${buildQuery({ application_id: id, limit: 20 })}`
      ),
    enabled: !!id,
  });

  const { data: rolesData, isLoading: rolesLoading } = useQuery({
    queryKey: ["app-hub", id, "roles"],
    queryFn: () => apiList<Role>(`/v1/roles${buildQuery({ limit: 100 })}`),
    enabled: !!id,
  });

  const { data: keysData, isLoading: keysLoading } = useQuery({
    queryKey: ["app-hub", id, "keys"],
    queryFn: () =>
      apiFetch<{ items: ApiKey[]; total: number }>(
        `/v1/api-keys${buildQuery({ limit: 100 })}`
      ),
    enabled: !!id,
  });

  // ─── Derived counts ──────────────────────────────────────────────────
  const flagCount = flagsData?.items?.length ?? 0;
  const auditCount = auditData?.total ?? 0;
  const keyCount = keysData?.items?.length ?? 0;
  const orgRoles = (rolesData?.items ?? []).filter(
    (r) => r.org_id === app?.org_id
  );

  // ─── Loading / error ─────────────────────────────────────────────────
  if (appLoading) {
    return (
      <div className="p-8 space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-6 w-48" />
        <div className="grid grid-cols-5 gap-4 mt-6">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      </div>
    );
  }

  if (appError || !app) {
    return (
      <div className="p-8">
        <ErrorState message="Application not found — it may have been deleted or you don't have access to it." />
      </div>
    );
  }

  const color = appColor(app.code ?? "a");

  return (
    <div className="flex flex-col min-h-full">
      {/* ── Breadcrumb ── */}
      <div className="px-8 pt-6 pb-0">
        <Link
          href="/iam/applications"
          className="inline-flex items-center gap-1 text-xs text-[#8b949e] hover:text-[#e6edf3] transition-colors mb-4"
        >
          <ArrowLeft size={12} />
          Applications
        </Link>
      </div>

      {/* ── App header ── */}
      <div className="px-8 pb-6 border-b border-[#21262d]">
        <div className="flex items-start gap-5">
          {/* Avatar */}
          <div
            className="w-14 h-14 rounded-lg flex items-center justify-center text-white font-bold text-xl flex-shrink-0 shadow-lg"
            style={{ backgroundColor: color }}
          >
            {(app.code ?? app.label ?? "A")[0].toUpperCase()}
          </div>

          {/* Name + meta */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-2xl font-bold text-[#e6edf3]">
                {app.label ?? app.code ?? "Untitled App"}
              </h1>
              <Badge tone="default">
                <Terminal size={10} className="mr-1" />
                {app.code}
              </Badge>
              <Badge tone={app.is_active ? "success" : "danger"}>
                {app.is_active ? "● Active" : "● Inactive"}
              </Badge>
            </div>
            {app.description && (
              <p className="text-sm text-[#8b949e] mt-1">{app.description}</p>
            )}
            <div className="flex items-center gap-4 mt-2">
              <span className="text-xs text-[#8b949e]">
                Org: <span className="text-[#e6edf3] font-mono">{app.org_id.slice(0, 8)}…</span>
              </span>
              <span className="text-xs text-[#8b949e]">
                Created {formatDate(app.created_at)}
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => {
                navigator.clipboard.writeText(app.id);
                toast("Application ID copied to clipboard.", "success");
              }}
            >
              <Copy size={12} className="mr-1" />
              Copy ID
            </Button>
            <Link href={`/iam/applications`}>
              <Button size="sm" variant="secondary">
                <Layers size={12} className="mr-1" />
                All apps
              </Button>
            </Link>
          </div>
        </div>

        {/* ── Stat bar ── */}
        <div className="grid grid-cols-5 gap-3 mt-6">
          <StatCard
            label="Feature Flags"
            value={flagsLoading ? "…" : String(flagCount)}
          />
          <StatCard
            label="API Keys"
            value={keysLoading ? "…" : String(keyCount)}
          />
          <StatCard
            label="Org Roles"
            value={rolesLoading ? "…" : String(orgRoles.length)}
          />
          <StatCard
            label="Audit Events"
            value={auditLoading ? "…" : String(auditCount)}
          />
          <StatCard
            label="Created"
            value={formatDate(app.created_at)}
          />
        </div>
      </div>

      {/* ── Tab bar ── */}
      <div className="flex items-center border-b border-[#21262d] px-8 overflow-x-auto">
        <TabBtn label="Overview" icon={Layers} active={tab === "overview"} onClick={() => setTab("overview")} />
        <TabBtn label={`Flags (${flagCount})`} icon={Flag} active={tab === "flags"} onClick={() => setTab("flags")} />
        <TabBtn label={`Roles (${orgRoles.length})`} icon={Shield} active={tab === "roles"} onClick={() => setTab("roles")} />
        <TabBtn label={`API Keys (${keyCount})`} icon={Key} active={tab === "api-keys"} onClick={() => setTab("api-keys")} />
        <TabBtn label={`Audit (${auditCount})`} icon={Activity} active={tab === "audit"} onClick={() => setTab("audit")} />
      </div>

      {/* ── Tab content ── */}
      <div className="flex-1 p-8">
        {/* OVERVIEW */}
        {tab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Details */}
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[#8b949e] mb-3">
                Application Details
              </h3>
              <div className="border border-[#21262d] rounded-lg px-4 bg-[#161b22]">
                <DetailRow label="ID">{app.id}</DetailRow>
                <DetailRow label="Code">{app.code ?? "—"}</DetailRow>
                <DetailRow label="Label">{app.label ?? "—"}</DetailRow>
                <DetailRow label="Description">
                  {app.description ?? <span className="text-[#8b949e]">—</span>}
                </DetailRow>
                <DetailRow label="Org ID">{app.org_id}</DetailRow>
                <DetailRow label="Status">
                  <Badge tone={app.is_active ? "success" : "danger"}>
                    {app.is_active ? "Active" : "Inactive"}
                  </Badge>
                </DetailRow>
                <DetailRow label="Created">{formatDate(app.created_at)}</DetailRow>
                <DetailRow label="Updated">{formatDate(app.updated_at)}</DetailRow>
              </div>
            </div>

            {/* Recent audit */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[#8b949e]">
                  Recent Audit Events
                </h3>
                <Link
                  href={`/audit?application_id=${id}`}
                  className="text-xs text-[#58a6ff] hover:text-[#79c0ff] flex items-center gap-1"
                >
                  View all <ExternalLink size={10} />
                </Link>
              </div>
              {auditLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => <Skeleton key={i} className="h-12" />)}
                </div>
              ) : (auditData?.items ?? []).length === 0 ? (
                <EmptyState
                  title="No audit events yet"
                  description="Events will appear here when this application makes API calls."
                />
              ) : (
                <div className="border border-[#21262d] rounded-lg overflow-hidden bg-[#161b22]">
                  {(auditData?.items ?? []).slice(0, 8).map((evt) => (
                    <div
                      key={evt.id}
                      className="flex items-center gap-3 px-4 py-2.5 border-b border-[#21262d] last:border-0"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-mono text-[#e6edf3] truncate">
                          {evt.event_key}
                        </p>
                        <p className="text-xs text-[#8b949e]">
                          {evt.category_code}
                        </p>
                      </div>
                      <OutcomeBadge outcome={evt.outcome} />
                      <span className="text-xs text-[#8b949e] whitespace-nowrap">
                        {timeAgo(evt.created_at)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* FEATURE FLAGS */}
        {tab === "flags" && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-[#e6edf3]">
                Feature Flags scoped to this application
              </h3>
              <Link href={`/feature-flags`}>
                <Button size="sm" variant="primary">
                  <Flag size={12} className="mr-1" />
                  Manage flags
                </Button>
              </Link>
            </div>
            {flagsLoading ? (
              <Skeleton className="h-48" />
            ) : (flagsData?.items ?? []).length === 0 ? (
              <EmptyState
                title="No feature flags for this application"
                description="Create flags in Feature Flags and set scope to Application to see them here."
                action={
                  <Link href="/feature-flags">
                    <Button size="sm" variant="primary">
                      <Flag size={12} className="mr-1" />
                      Go to Feature Flags
                    </Button>
                  </Link>
                }
              />
            ) : (
              <Table>
                <THead>
                  <TR>
                    <TH>Flag key</TH>
                    <TH>Type</TH>
                    <TH>Default</TH>
                    <TH>Status</TH>
                    <TH>Manage</TH>
                  </TR>
                </THead>
                <TBody>
                  {(flagsData?.items ?? []).map((flag) => (
                    <TR key={flag.id}>
                      <TD>
                        <span className="font-mono text-xs text-[#58a6ff]">
                          {flag.flag_key}
                        </span>
                      </TD>
                      <TD>
                        <Badge tone="default">{flag.value_type}</Badge>
                      </TD>
                      <TD>
                        <span className="font-mono text-xs">
                          {String(flag.default_value)}
                        </span>
                      </TD>
                      <TD>
                        <Badge tone="success">enabled</Badge>
                      </TD>
                      <TD>
                        <Link
                          href={`/feature-flags/${flag.id}`}
                          className="text-xs text-[#58a6ff] hover:text-[#79c0ff] flex items-center gap-1"
                        >
                          Manage <ChevronRight size={10} />
                        </Link>
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            )}
          </div>
        )}

        {/* ROLES */}
        {tab === "roles" && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-[#e6edf3]">
                  Roles in this application's org
                </h3>
                <p className="text-xs text-[#8b949e] mt-0.5">
                  Showing all roles scoped to org <span className="font-mono">{app.org_id.slice(0, 8)}…</span>. Assign these to users from the Memberships page.
                </p>
              </div>
              <Link href="/iam/roles">
                <Button size="sm" variant="primary">
                  <Shield size={12} className="mr-1" />
                  Manage roles
                </Button>
              </Link>
            </div>
            {rolesLoading ? (
              <Skeleton className="h-48" />
            ) : orgRoles.length === 0 ? (
              <EmptyState
                title="No org-scoped roles yet"
                description="Create roles in Identity → Roles and assign them to users."
              />
            ) : (
              <Table>
                <THead>
                  <TR>
                    <TH>Code</TH>
                    <TH>Label</TH>
                    <TH>Type</TH>
                    <TH>Created</TH>
                  </TR>
                </THead>
                <TBody>
                  {orgRoles.map((role) => (
                    <TR key={role.id}>
                      <TD>
                        <span className="font-mono text-xs text-[#e6edf3]">
                          {role.code ?? "—"}
                        </span>
                      </TD>
                      <TD>{role.label ?? "—"}</TD>
                      <TD>
                        <Badge tone={role.role_type === "system" ? "purple" : "default"}>
                          {role.role_type}
                        </Badge>
                      </TD>
                      <TD className="text-[#8b949e] text-xs">
                        {formatDate(role.created_at)}
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            )}
          </div>
        )}

        {/* API KEYS */}
        {tab === "api-keys" && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-[#e6edf3]">API Keys</h3>
                <p className="text-xs text-[#8b949e] mt-0.5">
                  Scoped bearer tokens for backend-to-backend calls.
                </p>
              </div>
              <Link href="/account/api-keys">
                <Button size="sm" variant="primary">
                  <Key size={12} className="mr-1" />
                  Manage API keys
                </Button>
              </Link>
            </div>
            {keysLoading ? (
              <Skeleton className="h-48" />
            ) : (keysData?.items ?? []).length === 0 ? (
              <EmptyState
                title="No API keys"
                description="Create an API key so this application can authenticate to TennetCTL without a user session."
                action={
                  <Link href="/account/api-keys">
                    <Button size="sm" variant="primary">
                      <Key size={12} className="mr-1" />
                      Create API key
                    </Button>
                  </Link>
                }
              />
            ) : (
              <Table>
                <THead>
                  <TR>
                    <TH>Name</TH>
                    <TH>Prefix</TH>
                    <TH>Created</TH>
                    <TH>Last used</TH>
                    <TH>Expires</TH>
                    <TH>Status</TH>
                  </TR>
                </THead>
                <TBody>
                  {(keysData?.items ?? []).map((key) => (
                    <TR key={key.id}>
                      <TD className="font-semibold">{key.name}</TD>
                      <TD>
                        <span className="font-mono text-xs text-[#8b949e]">
                          {key.prefix}…
                        </span>
                      </TD>
                      <TD className="text-xs text-[#8b949e]">
                        {formatDate(key.created_at)}
                      </TD>
                      <TD className="text-xs text-[#8b949e]">
                        {key.last_used_at ? timeAgo(key.last_used_at) : "Never"}
                      </TD>
                      <TD className="text-xs text-[#8b949e]">
                        {key.expires_at ? formatDate(key.expires_at) : "Never"}
                      </TD>
                      <TD>
                        <Badge tone={key.is_active ? "success" : "danger"}>
                          {key.is_active ? "Active" : "Revoked"}
                        </Badge>
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            )}
          </div>
        )}

        {/* AUDIT */}
        {tab === "audit" && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-[#e6edf3]">
                Audit Events for this application
              </h3>
              <Link href="/audit" className="text-xs text-[#58a6ff] hover:text-[#79c0ff] flex items-center gap-1">
                Open Audit Explorer <ExternalLink size={10} />
              </Link>
            </div>
            {auditLoading ? (
              <Skeleton className="h-64" />
            ) : (auditData?.items ?? []).length === 0 ? (
              <EmptyState
                title="No audit events"
                description="Audit events will appear here when this application's resources are accessed."
              />
            ) : (
              <Table>
                <THead>
                  <TR>
                    <TH>Event</TH>
                    <TH>Category</TH>
                    <TH>Outcome</TH>
                    <TH>Metadata</TH>
                    <TH>When</TH>
                  </TR>
                </THead>
                <TBody>
                  {(auditData?.items ?? []).map((evt) => (
                    <TR key={evt.id}>
                      <TD>
                        <span className="font-mono text-xs text-[#58a6ff]">
                          {evt.event_key}
                        </span>
                      </TD>
                      <TD>
                        <Badge tone="default">{evt.category_code}</Badge>
                      </TD>
                      <TD>
                        <OutcomeBadge outcome={evt.outcome} />
                      </TD>
                      <TD className="max-w-xs">
                        <span className="font-mono text-xs text-[#8b949e] truncate block">
                          {JSON.stringify(evt.metadata ?? {}).slice(0, 60)}…
                        </span>
                      </TD>
                      <TD className="text-xs text-[#8b949e] whitespace-nowrap">
                        {timeAgo(evt.created_at)}
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
