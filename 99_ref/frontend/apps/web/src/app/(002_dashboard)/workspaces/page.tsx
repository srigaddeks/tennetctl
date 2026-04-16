"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Button,
  Input,
  Label,
  Badge,
} from "@kcontrol/ui";
import {
  Building2,
  Layers,
  Plus,
  AlertCircle,
  ChevronDown,
  ArrowRight,
  X,
} from "lucide-react";
import Link from "next/link";
import { listWorkspaces, createWorkspace } from "@/lib/api/workspaces";
import type { WorkspaceResponse } from "@/lib/types/orgs";
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext";

function slugify(val: string) {
  return val.toLowerCase().replace(/[^a-z0-9-]/g, "-").replace(/--+/g, "-");
}

export default function WorkspacesPage() {
  const { orgs, selectedOrgId, setSelectedOrgId, ready } = useOrgWorkspace();

  const [workspaces, setWorkspaces] = useState<WorkspaceResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [orgPickerOpen, setOrgPickerOpen] = useState(false);

  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newSlug, setNewSlug] = useState("");
  const [newType, setNewType] = useState<"project" | "sandbox">("project");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const selectedOrg = orgs.find((o) => o.id === selectedOrgId) ?? null;

  const loadWorkspaces = useCallback(async (orgId: string) => {
    if (!orgId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await listWorkspaces(orgId);
      setWorkspaces(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load workspaces");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (ready && selectedOrgId) {
      loadWorkspaces(selectedOrgId);
    }
  }, [ready, selectedOrgId, loadWorkspaces]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedOrgId) return;
    setCreating(true);
    setCreateError(null);
    try {
      await createWorkspace(selectedOrgId, {
        name: newName.trim(),
        slug: newSlug.trim() || slugify(newName.trim()),
        workspace_type_code: newType,
      });
      setNewName("");
      setNewSlug("");
      setNewType("project");
      setShowCreate(false);
      await loadWorkspaces(selectedOrgId);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Failed to create workspace");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-semibold text-foreground">Workspaces</h2>
          <p className="text-sm text-muted-foreground">
            Manage workspaces for your organization.
          </p>
        </div>
        <Button size="sm" onClick={() => setShowCreate((v) => !v)} className="gap-1.5 shrink-0">
          <Plus className="h-3.5 w-3.5" />
          New Workspace
        </Button>
      </div>

      {/* Org selector */}
      <div className="rounded-2xl border border-border bg-card p-4">
        <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-3">
          Current Organization
        </p>
        {!ready ? (
          <div className="h-10 bg-muted rounded-xl animate-pulse" />
        ) : orgs.length === 0 ? (
          <p className="text-sm text-muted-foreground">No organizations found.</p>
        ) : (
          <div className="relative">
            <button
              onClick={() => setOrgPickerOpen((v) => !v)}
              className="flex w-full items-center gap-3 rounded-xl border border-border bg-background px-4 py-2.5 hover:bg-muted/30 transition-colors text-left"
            >
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                <Building2 className="h-4 w-4 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-foreground truncate">
                  {selectedOrg?.name ?? "Select organization"}
                </p>
                {selectedOrg && (
                  <p className="text-xs text-muted-foreground font-mono">{selectedOrg.slug}</p>
                )}
              </div>
              {orgs.length > 1 && (
                <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
              )}
            </button>

            {orgPickerOpen && orgs.length > 1 && (
              <div className="absolute z-50 top-full mt-1 left-0 right-0 rounded-xl border border-border bg-background shadow-lg overflow-hidden">
                {orgs.map((org) => (
                  <button
                    key={org.id}
                    onClick={() => {
                      setSelectedOrgId(org.id);
                      setOrgPickerOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 px-4 py-2.5 hover:bg-muted/50 transition-colors text-left ${
                      org.id === selectedOrgId ? "bg-primary/5" : ""
                    }`}
                  >
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                      <Building2 className="h-3.5 w-3.5 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">{org.name}</p>
                      <p className="text-xs text-muted-foreground font-mono">{org.slug}</p>
                    </div>
                    {org.id === selectedOrgId && (
                      <Badge variant="outline" className="text-xs text-primary border-primary/30 shrink-0">
                        selected
                      </Badge>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create workspace form */}
      {showCreate && selectedOrgId && (
        <form onSubmit={handleCreate} className="rounded-2xl border border-primary/30 bg-primary/5 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">New workspace</p>
            <button
              type="button"
              onClick={() => { setShowCreate(false); setCreateError(null); }}
              className="rounded-lg p-1 text-muted-foreground hover:bg-muted transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="space-y-1">
              <Label htmlFor="ws-name">Name</Label>
              <Input
                id="ws-name"
                value={newName}
                onChange={(e) => {
                  setNewName(e.target.value);
                  setNewSlug(slugify(e.target.value));
                }}
                placeholder="e.g. Production"
                required
                autoFocus
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="ws-product">Product</Label>
              <select
                id="ws-product"
                value={newType}
                onChange={(e) => setNewType(e.target.value as "project" | "sandbox")}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              >
                <option value="project">K-Control</option>
                <option value="sandbox">K-Control Sandbox</option>
              </select>
            </div>
          </div>
          {createError && (
            <div className="flex items-center gap-2 text-xs text-red-500">
              <AlertCircle className="h-3.5 w-3.5 shrink-0" />
              {createError}
            </div>
          )}
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={creating || !newName.trim()}>
              {creating ? "Creating…" : "Create workspace"}
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => { setShowCreate(false); setCreateError(null); }}
            >
              Cancel
            </Button>
          </div>
        </form>
      )}

      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3">
          <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
          <p className="text-sm text-red-500">{error}</p>
        </div>
      )}

      {/* Workspace list */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            {selectedOrg ? `Workspaces in ${selectedOrg.name}` : "Workspaces"}
          </p>
          {!loading && (
            <span className="text-xs text-muted-foreground">
              {workspaces.length} {workspaces.length === 1 ? "workspace" : "workspaces"}
            </span>
          )}
        </div>
        {loading ? (
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-14 bg-muted rounded-xl animate-pulse" />
            ))}
          </div>
        ) : workspaces.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-muted/10 py-14 gap-4 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
              <Layers className="h-6 w-6 text-muted-foreground" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-semibold text-foreground">No workspaces yet</p>
              <p className="text-xs text-muted-foreground">Create your first workspace to get started.</p>
            </div>
            <Button size="sm" onClick={() => setShowCreate(true)} className="gap-1.5">
              <Plus className="h-3.5 w-3.5" /> New Workspace
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            {workspaces.map((ws) => {
              const isSandbox = ws.workspace_type_code === "sandbox"
              const borderCls = isSandbox ? "border-l-purple-500" : "border-l-primary"
              const iconCls = isSandbox ? "text-purple-500" : "text-primary"
              return (
                <div key={ws.id}
                  className={`flex items-center gap-3 rounded-xl border border-l-[3px] ${borderCls} bg-card px-4 py-3 hover:bg-muted/20 transition-colors group`}>
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                    <Layers className={`h-4 w-4 ${iconCls}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-semibold text-foreground">{ws.name}</span>
                      <code className="font-mono text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">{ws.slug}</code>
                      <Badge variant="outline" className="text-xs text-muted-foreground capitalize">
                        {ws.workspace_type_code.replace(/_/g, " ")}
                      </Badge>
                      {!ws.is_active && (
                        <Badge variant="outline" className="text-xs text-red-500 border-red-500/30">Inactive</Badge>
                      )}
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" asChild
                    className="gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                    <Link href={`/workspaces/${selectedOrgId}`}>
                      Manage <ArrowRight className="h-3 w-3" />
                    </Link>
                  </Button>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  );
}
