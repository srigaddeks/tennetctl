"use client";

import * as React from "react";
import {
  Building2, ChevronDown, ChevronRight, Plus, Trash2, Star,
} from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth-context";
import {
  listWorkspaceMemberships, listOrgMemberships, getOrg,
  createWorkspace, addWorkspaceMembership, removeWorkspaceMembership,
} from "@/lib/api";
import type { OrgMembership, WorkspaceMembership } from "@/types/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
function toSlug(s: string) {
  return s.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
}

export default function WorkspacesSettingsPage() {
  const { status, ...rest } = useAuth();
  const accessToken = status === "authenticated" ? (rest as { accessToken: string }).accessToken : null;
  const me = status === "authenticated"
    ? (rest as { me: { user_id: string; username: string | null; email: string | null; session_id: string } }).me
    : null;

  const [memberships, setMemberships] = React.useState<WorkspaceMembership[]>([]);
  const [orgNames, setOrgNames] = React.useState<Record<string, string>>({});
  const [orgMemberships, setOrgMemberships] = React.useState<OrgMembership[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [showCreate, setShowCreate] = React.useState(false);
  const [expandedOrg, setExpandedOrg] = React.useState<string | null>(null);
  const [defaults, setDefaults] = React.useState<Record<string, string>>(() => {
    if (typeof window === "undefined") return {};
    try { return JSON.parse(localStorage.getItem("kf_default_ws") ?? "{}"); } catch { return {}; }
  });

  async function load() {
    if (!me || !accessToken) return;
    const [msRes, orgMsRes] = await Promise.all([
      listWorkspaceMemberships(me.user_id, accessToken),
      listOrgMemberships(me.user_id, accessToken),
    ]);

    const orgMsList = orgMsRes.ok ? orgMsRes.data.items : [];
    setOrgMemberships(orgMsList);

    const knownOrgIds = new Set(orgMsList.map(m => m.org_id));
    const nameMap: Record<string, string> = {};
    for (const m of orgMsList) nameMap[m.org_id] = m.org_name ?? m.org_slug ?? m.org_id.slice(0, 8);

    if (msRes.ok) {
      setMemberships(msRes.data.items);
      const missingIds = [...new Set(msRes.data.items.map(m => m.org_id).filter(id => !knownOrgIds.has(id)))];
      if (missingIds.length > 0) {
        const fetched = await Promise.all(missingIds.map(id => getOrg(id, accessToken)));
        for (let i = 0; i < missingIds.length; i++) {
          const r = fetched[i];
          nameMap[missingIds[i]] = r.ok ? (r.data.name ?? r.data.slug ?? missingIds[i].slice(0, 8)) : missingIds[i].slice(0, 8);
        }
      }
    }

    setOrgNames(nameMap);
    setLoading(false);
  }

  React.useEffect(() => { load(); }, [me?.user_id, accessToken]);

  if (!accessToken || !me) return null;

  const byOrg = (() => {
    const map: Record<string, WorkspaceMembership[]> = {};
    for (const m of memberships) {
      if (!map[m.org_id]) map[m.org_id] = [];
      map[m.org_id].push(m);
    }
    return map;
  })();

  const orgIds = Object.keys(byOrg);

  function handleSetDefault(orgId: string, wsId: string) {
    const next = { ...defaults, [orgId]: wsId };
    setDefaults(next);
    localStorage.setItem("kf_default_ws", JSON.stringify(next));
    toast.success("Default workspace updated");
  }

  async function handleRemove(id: string) {
    const res = await removeWorkspaceMembership(id, accessToken!);
    if (res.ok) { toast.success("Removed from workspace"); load(); }
    else toast.error(res.error.message);
  }

  function orgName(orgId: string) {
    return orgNames[orgId] ?? orgId.slice(0, 8);
  }

  return (
    <section>
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-base font-semibold">Workspaces</h2>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus size={13} /> Create workspace
        </Button>
      </div>
      <p className="text-xs text-foreground-muted mb-5">Your workspaces grouped by org. Star to set the default per org.</p>

      {loading ? (
        <Card className="text-center text-foreground-muted p-6 text-sm">Loading…</Card>
      ) : orgIds.length === 0 ? (
        <Card className="text-center text-foreground-muted p-8 text-sm">No workspace memberships.</Card>
      ) : (
        <div className="flex flex-col gap-2.5">
          {orgIds.map(orgId => {
            const wsList = byOrg[orgId];
            const open = expandedOrg === orgId;
            return (
              <Card key={orgId} className="overflow-hidden">
                <button
                  onClick={() => setExpandedOrg(open ? null : orgId)}
                  className="flex items-center gap-2.5 w-full px-4 py-3 bg-transparent border-none cursor-pointer text-foreground font-semibold text-sm"
                >
                  {open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
                  <Building2 size={15} className="text-foreground-muted" />
                  {orgName(orgId)}
                  <span className="ml-auto text-xs text-foreground-muted font-normal">
                    {wsList.length} workspace{wsList.length !== 1 ? "s" : ""}
                  </span>
                </button>
                {open && (
                  <div className="border-t border-border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Workspace</TableHead>
                          <TableHead>Slug</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead className="w-[80px]">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {wsList.map(ws => (
                          <TableRow key={ws.id}>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                {ws.workspace_name ?? ws.workspace_slug}
                                {defaults[orgId] === ws.workspace_id && <Badge variant="info">default</Badge>}
                              </div>
                            </TableCell>
                            <TableCell><span className="font-mono text-xs">{ws.workspace_slug}</span></TableCell>
                            <TableCell>
                              <Badge variant={ws.workspace_is_active ? "success" : "danger"}>
                                {ws.workspace_is_active ? "active" : "inactive"}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="flex gap-1.5">
                                <Button
                                  variant="ghost" size="icon"
                                  title="Set as default"
                                  onClick={() => handleSetDefault(orgId, ws.workspace_id)}
                                  className={defaults[orgId] === ws.workspace_id ? "text-[color:var(--warning)]" : ""}
                                >
                                  <Star size={13} />
                                </Button>
                                <Button variant="danger" size="icon" title="Leave workspace" onClick={() => handleRemove(ws.id)}>
                                  <Trash2 size={13} />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {showCreate && (
        <CreateWorkspaceModal
          me={me} accessToken={accessToken} orgMemberships={orgMemberships}
          onClose={() => setShowCreate(false)}
          onCreated={() => { setShowCreate(false); load(); toast.success("Workspace created"); }}
          onError={(msg) => toast.error(msg)}
        />
      )}
    </section>
  );
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-[100] bg-black/60 flex items-center justify-center p-6" onClick={onClose}>
      <div className="bg-surface border border-border rounded-lg p-7 w-full max-w-[440px] flex flex-col gap-5" onClick={(e) => e.stopPropagation()}>
        <div className="text-base font-semibold">{title}</div>
        {children}
      </div>
    </div>
  );
}

function CreateWorkspaceModal({ me, accessToken, orgMemberships, onClose, onCreated, onError }: {
  me: { user_id: string }; accessToken: string; orgMemberships: OrgMembership[];
  onClose: () => void; onCreated: () => void; onError: (m: string) => void;
}) {
  const [orgId, setOrgId] = React.useState(orgMemberships[0]?.org_id ?? "");
  const [name, setName] = React.useState("");
  const [slug, setSlug] = React.useState("");
  const [saving, setSaving] = React.useState(false);

  function handleNameChange(v: string) { setName(v); setSlug(toSlug(v)); }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    const res = await createWorkspace({ org_id: orgId, name, slug }, accessToken);
    setSaving(false);
    if (res.ok) {
      await addWorkspaceMembership({ user_id: me.user_id, workspace_id: res.data.id, org_id: orgId }, accessToken);
      onCreated();
    } else {
      onError(res.error.message);
    }
  }

  return (
    <Modal title="Create workspace" onClose={onClose}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
        <div className="flex flex-col gap-1.5">
          <Label>Organization</Label>
          <select
            value={orgId} onChange={e => setOrgId(e.target.value)} required
            className="flex h-9 w-full rounded-md border border-border bg-surface px-3 py-1 text-sm text-foreground cursor-pointer focus-visible:outline-none focus-visible:border-border-strong focus-visible:ring-1 focus-visible:ring-ring"
          >
            {orgMemberships.map(o => <option key={o.id} value={o.org_id}>{o.org_name ?? o.org_slug}</option>)}
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Name</Label>
          <Input value={name} onChange={e => handleNameChange(e.target.value)} placeholder="Production" required />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Slug</Label>
          <Input value={slug} onChange={e => setSlug(e.target.value)} placeholder="production" required />
        </div>
        <div className="flex gap-2.5 justify-end">
          <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
          <Button type="submit" disabled={saving || !orgId}>{saving ? "Creating…" : "Create"}</Button>
        </div>
      </form>
    </Modal>
  );
}
