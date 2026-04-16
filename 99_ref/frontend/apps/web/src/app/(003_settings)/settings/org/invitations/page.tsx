"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Input,
  Badge,
} from "@kcontrol/ui";
import {
  Mail,
  AlertCircle,
  XCircle,
  Search,
  Clock,
  CheckCircle2,
  Ban,
  Filter,
} from "lucide-react";
import { fetchAccessContext } from "@/lib/api/access";
import { listInvitations, revokeInvitation } from "@/lib/api/invitations";
import type { InvitationResponse } from "@/lib/api/invitations";
import { fetchUserProperties } from "@/lib/api/auth";

const ALL_STATUSES = ["pending", "accepted", "expired", "revoked"] as const;
type InviteStatus = (typeof ALL_STATUSES)[number];

function statusBadgeClass(status: string) {
  switch (status) {
    case "pending":  return "bg-amber-500/10 text-amber-600 border-amber-500/20";
    case "accepted": return "bg-green-500/10 text-green-600 border-green-500/20";
    case "expired":  return "bg-gray-500/10 text-gray-600 border-gray-500/20";
    case "revoked":  return "bg-red-500/10 text-red-500 border-red-500/20";
    default:         return "bg-muted text-muted-foreground border-border";
  }
}

function roleBadgeClass(role: string) {
  switch (role) {
    case "owner":   return "bg-purple-500/10 text-purple-600 border-purple-500/20";
    case "admin":   return "bg-blue-500/10 text-blue-600 border-blue-500/20";
    case "member":  return "bg-green-500/10 text-green-600 border-green-500/20";
    case "viewer":  return "bg-gray-500/10 text-gray-600 border-gray-500/20";
    case "billing": return "bg-amber-500/10 text-amber-600 border-amber-500/20";
    default:        return "bg-muted text-muted-foreground border-border";
  }
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case "pending":  return <Clock className="h-3.5 w-3.5 text-amber-500" />;
    case "accepted": return <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />;
    case "expired":  return <Ban className="h-3.5 w-3.5 text-gray-400" />;
    case "revoked":  return <XCircle className="h-3.5 w-3.5 text-red-500" />;
    default:         return <Mail className="h-3.5 w-3.5 text-muted-foreground" />;
  }
}

function fmt(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { dateStyle: "medium" });
}

function SkeletonRow() {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border px-4 py-3 animate-pulse">
      <div className="flex items-center gap-3 min-w-0">
        <div className="h-4 w-4 rounded bg-muted shrink-0" />
        <div className="space-y-1 min-w-0">
          <div className="h-3.5 w-40 rounded bg-muted" />
          <div className="h-3 w-28 rounded bg-muted" />
        </div>
      </div>
      <div className="flex items-center gap-2">
        <div className="h-5 w-14 rounded bg-muted" />
        <div className="h-5 w-14 rounded bg-muted" />
      </div>
    </div>
  );
}

export default function OrgInvitationsPage() {
  const [orgId, setOrgId] = useState<string | null>(null);
  const [invitations, setInvitations] = useState<InvitationResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<InviteStatus | "all">("all");
  const [search, setSearch] = useState("");

  // Revoke
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [revokeError, setRevokeError] = useState<string | null>(null);

  const load = useCallback(async (id: string, status?: string) => {
    setError(null);
    try {
      const data = await listInvitations({
        scope: "organization",
        org_id: id,
        ...(status && status !== "all" ? { status } : {}),
      });
      setInvitations(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load invitations");
    }
  }, []);

  useEffect(() => {
    async function init() {
      try {
        let defaultOrgId: string | undefined
        try {
          const props = await fetchUserProperties()
          defaultOrgId = props["default_org_id"] || undefined
        } catch {}
        const access = await fetchAccessContext(defaultOrgId)
        const id = access.current_org?.org_id;
        if (!id) { setError("No organization found. Complete onboarding first."); return; }
        setOrgId(id);
        await load(id);
      } catch {
        setError("Failed to load organization.");
      } finally {
        setIsLoading(false);
      }
    }
    init();
  }, [load]);

  async function handleStatusFilter(status: InviteStatus | "all") {
    setStatusFilter(status);
    if (!orgId) return;
    setIsLoading(true);
    await load(orgId, status === "all" ? undefined : status);
    setIsLoading(false);
  }

  async function handleRevoke(invId: string) {
    setRevokingId(invId); setRevokeError(null);
    try {
      await revokeInvitation(invId);
      setInvitations(prev => prev.map(i => i.id === invId ? { ...i, status: "revoked" } : i));
    } catch (err) {
      setRevokeError(err instanceof Error ? err.message : "Failed to revoke invitation");
    } finally {
      setRevokingId(null);
    }
  }

  // Stats from loaded invitations (unfiltered would be ideal, but compute from what we have)
  const statuses = invitations.reduce<Record<string, number>>((acc, i) => {
    acc[i.status] = (acc[i.status] ?? 0) + 1;
    return acc;
  }, {});

  const filtered = invitations.filter(inv => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return inv.email.toLowerCase().includes(q) || (inv.role?.toLowerCase() || "").includes(q) || inv.status.toLowerCase().includes(q);
  });

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-semibold text-foreground">Invitations</h2>
          <p className="text-sm text-muted-foreground">
            View and manage all invitations sent to your organization.
          </p>
        </div>
      </div>

      {/* Stats */}
      {!isLoading && !error && (
        <div className="flex items-center gap-3 flex-wrap text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <Mail className="h-3.5 w-3.5" />
            {invitations.length} total
          </span>
          {ALL_STATUSES.map(s => (
            statuses[s] != null ? (
              <Badge key={s} variant="outline" className={`text-[10px] capitalize ${statusBadgeClass(s)}`}>
                {statuses[s]} {s}
              </Badge>
            ) : null
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex items-center gap-1 p-0.5 bg-muted rounded-lg">
          {(["all", ...ALL_STATUSES] as const).map(s => (
            <button
              key={s}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors capitalize ${
                statusFilter === s
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
              onClick={() => handleStatusFilter(s as InviteStatus | "all")}
            >
              {s === "all" ? "All" : s}
            </button>
          ))}
        </div>
        <div className="relative w-full sm:w-72 min-w-[180px]">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            className="pl-8 h-8 text-sm"
            placeholder="Search by email or role…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
      </div>

      {revokeError && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2">
          <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
          <p className="text-sm text-red-500">{revokeError}</p>
        </div>
      )}

      {/* List */}
      <Card>
        <CardHeader className="py-3 px-4">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-sm">
              {isLoading
                ? "Loading…"
                : search.trim()
                  ? `${filtered.length} of ${invitations.length} invitations`
                  : `${invitations.length} invitation${invitations.length !== 1 ? "s" : ""}`}
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="px-4 pb-4">
          {isLoading ? (
            <div className="space-y-2">
              {[...Array(4)].map((_, i) => <SkeletonRow key={i} />)}
            </div>
          ) : error ? (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2">
              <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
              <p className="text-sm text-red-500">{error}</p>
            </div>
          ) : filtered.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-6">
              {search.trim() ? `No invitations match "${search}"` : "No invitations found."}
            </p>
          ) : (
            <div className="space-y-1.5">
              {filtered.map(inv => (
                <div
                  key={inv.id}
                  className="flex items-center justify-between rounded-lg border border-border px-4 py-2.5 hover:bg-accent/20 transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <StatusIcon status={inv.status} />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">{inv.email}</p>
                      <p className="text-xs text-muted-foreground">
                        Sent {fmt(inv.created_at)}
                        {inv.expires_at && ` · Expires ${fmt(inv.expires_at)}`}
                        {inv.accepted_at && ` · Accepted ${fmt(inv.accepted_at)}`}
                        {inv.revoked_at && ` · Revoked ${fmt(inv.revoked_at)}`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-2">
                    <Badge variant="outline" className={`text-[10px] capitalize ${statusBadgeClass(inv.status)}`}>
                      {inv.status}
                    </Badge>
                    <Badge variant="outline" className={`text-[10px] capitalize ${roleBadgeClass(inv.role || "")}`}>
                      {inv.role || "None"}
                    </Badge>
                    {inv.status === "pending" && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0 text-muted-foreground hover:text-destructive"
                        onClick={() => handleRevoke(inv.id)}
                        disabled={revokingId === inv.id}
                        title="Revoke invitation"
                      >
                        <XCircle className="h-3.5 w-3.5" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
