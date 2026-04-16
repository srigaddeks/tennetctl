"use client";

import { useEffect, useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Input,
  Label,
  Badge,
} from "@kcontrol/ui";
import {
  Building2,
  CheckCircle2,
  AlertCircle,
  Pencil,
  X,
  Users,
  Layers,
  Crown,
  Shield,
} from "lucide-react";
import { fetchAccessContext } from "@/lib/api/access";
import { listOrgs, updateOrg, listOrgMembers } from "@/lib/api/orgs";
import { listWorkspaces } from "@/lib/api/workspaces";
import { getEntitySettings } from "@/lib/api/admin";
import type { OrgResponse } from "@/lib/types/orgs";

function LoadingSkeleton() {
  return (
    <div className="space-y-3">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="h-10 rounded-lg bg-muted animate-pulse" />
      ))}
    </div>
  );
}

function tierBadgeClass(tier: string) {
  switch (tier) {
    case "free":
      return "bg-gray-500/10 text-gray-600 border-gray-500/20";
    case "pro":
    case "pro_trial":
      return "bg-blue-500/10 text-blue-600 border-blue-500/20";
    case "enterprise":
      return "bg-purple-500/10 text-purple-600 border-purple-500/20";
    case "partner":
      return "bg-teal-500/10 text-teal-600 border-teal-500/20";
    case "internal":
      return "bg-amber-500/10 text-amber-600 border-amber-500/20";
    default:
      return "bg-muted text-muted-foreground border-border";
  }
}

export default function OrgProfilePage() {
  const [org, setOrg] = useState<OrgResponse | null>(null);
  const [orgId, setOrgId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Stats
  const [memberCount, setMemberCount] = useState<number | null>(null);
  const [workspaceCount, setWorkspaceCount] = useState<number | null>(null);
  const [licenseTier, setLicenseTier] = useState<string | null>(null);

  // Edit
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    fetchAccessContext()
      .then(async (access) => {
        const id = access.current_org?.org_id;
        if (!id) {
          setError("No organization found. Complete onboarding first.");
          return;
        }
        setOrgId(id);

        const orgs = await listOrgs();
        const found = orgs.find((o) => o.id === id) ?? null;
        setOrg(found);
        if (found) {
          setName(found.name);
          setDescription(found.description ?? "");
        }

        // Load stats in parallel
        const [membersResult, workspacesResult, settingsResult] =
          await Promise.allSettled([
            listOrgMembers(id),
            listWorkspaces(id),
            getEntitySettings("org", id),
          ]);
        if (membersResult.status === "fulfilled") {
          setMemberCount(membersResult.value.length);
        }
        if (workspacesResult.status === "fulfilled") {
          setWorkspaceCount(workspacesResult.value.length);
        }
        if (settingsResult.status === "fulfilled") {
          const tier = settingsResult.value.find(
            (s) => s.key === "license_tier"
          )?.value;
          if (tier) setLicenseTier(tier);
        }
      })
      .catch(() => setError("Failed to load organization."))
      .finally(() => setIsLoading(false));
  }, []);

  function startEdit() {
    if (!org) return;
    setName(org.name);
    setDescription(org.description ?? "");
    setSaveError(null);
    setSaveSuccess(false);
    setEditing(true);
  }

  function cancelEdit() {
    setEditing(false);
    setSaveError(null);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!orgId) return;
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);
    try {
      const updated = await updateOrg(orgId, {
        name: name.trim(),
        description: description.trim() || undefined,
      });
      setOrg(updated);
      setSaveSuccess(true);
      setEditing(false);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err) {
      setSaveError(
        err instanceof Error ? err.message : "Failed to save organization"
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="w-full space-y-8 pb-10">
      {/* Hero Header */}
      <div className="flex items-start gap-4">
        <div className="rounded-xl bg-primary/10 p-3.5 shrink-0 shadow-[0_0_15px_rgba(var(--primary),0.1)] border border-primary/20 relative group overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <Building2 className="h-6 w-6 text-primary relative z-10" />
        </div>
        <div className="pt-0.5">
          <h2 className="text-2xl font-semibold text-foreground tracking-tight">
            Organization Overview
          </h2>
          <p className="text-muted-foreground mt-1 text-sm max-w-2xl leading-relaxed">
            Manage your organization&apos;s master profile, view key health metrics, and control architectural governance.
          </p>
        </div>
      </div>

      {/* Metrics Row */}
      {!isLoading && org && (
        <div className="flex flex-wrap gap-3">
          {[
            { label: "Members", value: memberCount ?? "—", icon: Users, color: "text-blue-500 bg-blue-500/10" },
            { label: "Workspaces", value: workspaceCount ?? "—", icon: Layers, color: "text-indigo-500 bg-indigo-500/10" },
            { label: "License Plan", value: licenseTier ?? "free", icon: Crown, color: "text-amber-500 bg-amber-500/10", uppercase: true },
            { 
              label: "Org Status", 
              value: org.is_active ? "Active" : "Inactive", 
              icon: Shield, 
              color: org.is_active ? "text-emerald-500 bg-emerald-500/10" : "text-rose-500 bg-rose-500/10",
              dot: true
            },
          ].map((stat) => (
            <div key={stat.label} className="flex-1 min-w-[180px] max-w-[260px] rounded-xl border border-border/40 bg-card/40 px-4 py-3 flex items-center gap-3 transition-all hover:border-border hover:shadow-sm">
              <div className={`rounded-lg p-2 ${stat.color.split(" ")[1]} shrink-0`}>
                <stat.icon className={`h-4 w-4 ${stat.color.split(" ")[0]}`} />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  {stat.dot && (
                    <span className={`h-1.5 w-1.5 rounded-full ${org.is_active ? "bg-emerald-500" : "bg-rose-500"}`} />
                  )}
                  <div className={`text-lg font-semibold text-foreground tabular-nums leading-tight truncate ${stat.uppercase ? "capitalize" : ""}`}>
                    {stat.value}
                  </div>
                </div>
                <div className="text-[10px] text-muted-foreground/50 font-medium uppercase tracking-wider mt-0.5">{stat.label}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Organization Details */}
        <Card className="rounded-xl border-border/40 shadow-sm overflow-hidden flex flex-col">
          <CardHeader className="border-b border-border/40 bg-muted/5 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 bg-muted rounded-lg">
                  <Pencil className="h-3.5 w-3.5 text-muted-foreground" />
                </div>
                <div>
                  <CardTitle className="text-base font-semibold">Organization Details</CardTitle>
                  <CardDescription className="text-xs">Professional profile information</CardDescription>
                </div>
              </div>
              {!editing && !isLoading && org && (
                <Button variant="outline" size="sm" onClick={startEdit} className="h-7 text-xs gap-1.5">
                  <Pencil className="h-3 w-3" />
                  Edit Details
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-6 flex-1">
            {isLoading ? (
              <LoadingSkeleton />
            ) : error ? (
              <div className="flex items-center gap-3 rounded-lg border border-rose-500/30 bg-rose-500/5 px-4 py-3">
                <AlertCircle className="h-4 w-4 text-rose-500 shrink-0" />
                <p className="text-sm text-rose-500">{error}</p>
              </div>
            ) : !org ? (
              <p className="text-sm text-muted-foreground">Organization not found.</p>
            ) : (
              <div className="space-y-6">
                {saveSuccess && (
                  <div className="flex items-center gap-3 rounded-lg border border-emerald-500/30 bg-emerald-500/5 px-4 py-3 animate-in fade-in slide-in-from-top-1">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                    <p className="text-sm text-emerald-600 dark:text-emerald-400 font-medium">Changes saved successfully</p>
                  </div>
                )}

                {editing ? (
                  <form onSubmit={handleSave} className="space-y-5">
                    <div className="space-y-1.5">
                      <Label htmlFor="org-name" className="text-xs font-medium uppercase tracking-wider text-muted-foreground/70 ml-1">Official Name</Label>
                      <Input
                        id="org-name"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Organization name"
                        className="rounded-lg h-10 text-sm"
                        required
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="org-description" className="text-xs font-medium uppercase tracking-wider text-muted-foreground/70 ml-1">Business Description</Label>
                      <textarea
                        id="org-description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="What does your organization do?"
                        rows={4}
                        className="flex w-full rounded-lg border border-input bg-transparent px-3 py-2 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                      />
                    </div>

                    {saveError && <div className="text-xs text-rose-500 px-1">{saveError}</div>}

                    <div className="flex items-center gap-2 pt-2">
                      <Button type="submit" size="sm" disabled={saving || !name.trim()} className="rounded-lg">
                        {saving ? "Saving…" : "Save Changes"}
                      </Button>
                      <Button type="button" variant="ghost" size="sm" onClick={cancelEdit} disabled={saving} className="rounded-lg">
                        Cancel
                      </Button>
                    </div>
                  </form>
                ) : (
                  <div className="grid grid-cols-1 gap-y-6">
                    {[
                      { label: "Formal Name", value: org.name },
                      { label: "Slug Identifier", value: org.slug, mono: true },
                      { label: "Organization Type", value: org.org_type_code.replace(/_/g, " "), capitalize: true },
                      { label: "About", value: org.description ?? "No description provided." },
                    ].map(({ label, value, mono, capitalize }) => (
                      <div key={label} className="group">
                        <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
                          {label}
                        </span>
                        <div className={`mt-1 text-sm text-foreground leading-relaxed ${mono ? "font-mono bg-muted/20 px-2 py-0.5 rounded w-fit text-[13px]" : "font-medium"} ${capitalize ? "capitalize" : ""}`}>
                          {value}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right Column: Status & Metadata */}
        {!isLoading && org && (
          <Card className="rounded-xl border-border/40 shadow-sm overflow-hidden flex flex-col">
            <CardHeader className="border-b border-border/40 bg-muted/5 py-3">
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 bg-muted rounded-lg">
                  <Shield className="h-3.5 w-3.5 text-muted-foreground" />
                </div>
                <div>
                  <CardTitle className="text-base font-semibold">System Governance</CardTitle>
                  <CardDescription className="text-xs">Identities & Compliance state</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-6 flex-1">
              <div className="grid grid-cols-1 gap-y-6">
                <div className="group">
                  <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">Lifecycle State</span>
                  <div className="mt-2 flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className={`h-2 w-2 rounded-full ${org.is_active ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.3)]" : "bg-rose-500"}`} />
                      <span className="text-sm font-semibold text-foreground">{org.is_active ? "Operational" : "Suspended"}</span>
                    </div>
                    {orgId && (
                      <Button
                        variant="secondary"
                        size="sm"
                        className={`h-6 px-3 text-[10px] font-semibold rounded-md transition-all ${
                          org.is_active 
                            ? "hover:bg-rose-500 hover:text-white" 
                            : "bg-emerald-500 text-white hover:bg-emerald-600"
                        }`}
                        onClick={async () => {
                          try {
                            const updated = await updateOrg(orgId, { is_disabled: org.is_active });
                            setOrg(updated);
                          } catch (err) {
                            setSaveError(err instanceof Error ? err.message : "Failed to update status");
                          }
                        }}
                      >
                        {org.is_active ? "Suspend Account" : "Activate Account"}
                      </Button>
                    )}
                  </div>
                </div>

                <div className="group">
                  <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">License Commitment</span>
                  <div className="mt-2 text-sm font-medium">
                    <Badge variant="outline" className={`py-0.5 px-2 rounded-md border text-xs font-semibold ${tierBadgeClass(licenseTier ?? "free")}`}>
                      <Crown className="h-3 w-3 mr-1.5" />
                      {licenseTier ?? "free"} Plan
                    </Badge>
                  </div>
                </div>

                <div className="pt-4 grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-6 border-t border-border/40 mt-2">
                  {[
                    { label: "Creation Date", value: new Date(org.created_at).toLocaleDateString(undefined, { dateStyle: "long" }) },
                    { label: "Last Sync", value: new Date(org.updated_at).toLocaleDateString(undefined, { dateStyle: "long" }) },
                  ].map(({ label, value }) => (
                    <div key={label}>
                      <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">{label}</span>
                      <p className="mt-1 text-sm font-medium text-foreground">{value}</p>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
