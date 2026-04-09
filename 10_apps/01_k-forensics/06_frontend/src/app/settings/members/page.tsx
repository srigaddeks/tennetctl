"use client";

import * as React from "react";
import { Building2, Layers, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth-context";
import {
  listOrgs, listWorkspaces, listUsers,
  listOrgMemberships, addOrgMembership, removeOrgMembership,
  listWorkspaceMemberships, addWorkspaceMembership, removeWorkspaceMembership,
} from "@/lib/api";
import type { OrgData, OrgMembership, WorkspaceData, WorkspaceMembership, UserData } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";

export default function MembersSettingsPage() {
  const { status, ...rest } = useAuth();
  const accessToken = status === "authenticated" ? (rest as { accessToken: string }).accessToken : null;

  const [orgs, setOrgs] = React.useState<OrgData[]>([]);
  const [users, setUsers] = React.useState<UserData[]>([]);
  const [selectedOrg, setSelectedOrg] = React.useState("");
  const [workspaces, setWorkspaces] = React.useState<WorkspaceData[]>([]);
  const [orgMembers, setOrgMembers] = React.useState<OrgMembership[]>([]);
  const [wsMembers, setWsMembers] = React.useState<WorkspaceMembership[]>([]);
  const [selectedWs, setSelectedWs] = React.useState("");
  const [loading, setLoading] = React.useState(true);

  const [addOrgUser, setAddOrgUser] = React.useState("");
  const [addWsUser, setAddWsUser] = React.useState("");
  const [addingOrg, setAddingOrg] = React.useState(false);
  const [addingWs, setAddingWs] = React.useState(false);

  async function loadInitial() {
    if (!accessToken) return;
    const [orgsRes, usersRes] = await Promise.all([listOrgs(accessToken), listUsers(accessToken)]);
    if (orgsRes.ok) {
      setOrgs(orgsRes.data.items);
      if (orgsRes.data.items.length > 0) setSelectedOrg(orgsRes.data.items[0].id);
    }
    if (usersRes.ok) setUsers(usersRes.data.items);
    setLoading(false);
  }

  async function loadOrgDetails(orgId: string) {
    if (!accessToken) return;
    const wssRes = await listWorkspaces(accessToken, orgId);
    if (wssRes.ok) {
      setWorkspaces(wssRes.data.items);
      if (wssRes.data.items.length > 0) setSelectedWs(wssRes.data.items[0].id);
    }
    const allMembers: OrgMembership[] = [];
    for (const u of users) {
      const r = await listOrgMemberships(u.id, accessToken, { limit: 200 });
      if (r.ok) allMembers.push(...r.data.items.filter(m => m.org_id === orgId));
    }
    setOrgMembers(allMembers);
  }

  async function loadWsMembers(wsId: string) {
    if (!accessToken) return;
    const allMembers: WorkspaceMembership[] = [];
    for (const u of users) {
      const r = await listWorkspaceMemberships(u.id, accessToken, { limit: 200 });
      if (r.ok) allMembers.push(...r.data.items.filter(m => m.workspace_id === wsId));
    }
    setWsMembers(allMembers);
  }

  React.useEffect(() => { loadInitial(); }, [accessToken]);
  React.useEffect(() => { if (selectedOrg && users.length > 0) loadOrgDetails(selectedOrg); }, [selectedOrg, users]);
  React.useEffect(() => { if (selectedWs && users.length > 0) loadWsMembers(selectedWs); }, [selectedWs, users]);

  if (!accessToken) return null;

  async function handleAddOrgMember(e: React.FormEvent) {
    e.preventDefault();
    if (!addOrgUser) return;
    setAddingOrg(true);
    const res = await addOrgMembership(addOrgUser, selectedOrg, accessToken!);
    setAddingOrg(false);
    if (res.ok) { toast.success("User added to org"); setAddOrgUser(""); loadOrgDetails(selectedOrg); }
    else toast.error(res.error.message);
  }

  async function handleAddWsMember(e: React.FormEvent) {
    e.preventDefault();
    if (!addWsUser || !selectedWs) return;
    setAddingWs(true);
    const res = await addWorkspaceMembership({ user_id: addWsUser, workspace_id: selectedWs, org_id: selectedOrg }, accessToken!);
    setAddingWs(false);
    if (res.ok) { toast.success("User added to workspace"); setAddWsUser(""); loadWsMembers(selectedWs); }
    else toast.error(res.error.message);
  }

  async function handleRemoveOrgMember(id: string) {
    const res = await removeOrgMembership(id, accessToken!);
    if (res.ok) { toast.success("Removed"); loadOrgDetails(selectedOrg); }
    else toast.error(res.error.message);
  }

  async function handleRemoveWsMember(id: string) {
    const res = await removeWorkspaceMembership(id, accessToken!);
    if (res.ok) { toast.success("Removed"); loadWsMembers(selectedWs); }
    else toast.error(res.error.message);
  }

  function userName(userId: string) {
    const u = users.find(x => x.id === userId);
    return u?.username ?? userId.slice(0, 8);
  }

  if (loading) return <div className="text-foreground-muted text-sm">Loading…</div>;

  return (
    <section>
      <h2 className="text-base font-semibold mb-1">Members</h2>
      <p className="text-xs text-foreground-muted mb-5">Manage who has access to your orgs and workspaces.</p>

      <div className="mb-6 max-w-[320px]">
        <div className="flex flex-col gap-1.5">
          <Label>Organization</Label>
          <select
            value={selectedOrg} onChange={e => setSelectedOrg(e.target.value)}
            className="flex h-9 w-full rounded-md border border-border bg-surface px-3 py-1 text-sm text-foreground cursor-pointer focus-visible:outline-none focus-visible:border-border-strong focus-visible:ring-1 focus-visible:ring-ring"
          >
            {orgs.map(o => <option key={o.id} value={o.id}>{o.name ?? o.slug}</option>)}
          </select>
        </div>
      </div>

      <Card className="mb-6 overflow-hidden">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 size={14} className="text-foreground-muted" /> Org members
          </CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow><TableHead>User</TableHead><TableHead>User ID</TableHead><TableHead>Joined</TableHead><TableHead className="w-[60px]" /></TableRow>
          </TableHeader>
          <TableBody>
            {orgMembers.map(m => (
              <TableRow key={m.id}>
                <TableCell className="font-medium">{userName(m.user_id)}</TableCell>
                <TableCell><span className="font-mono text-xs">{m.user_id.slice(0, 18)}…</span></TableCell>
                <TableCell className="text-foreground-muted text-xs">{new Date(m.created_at).toLocaleDateString()}</TableCell>
                <TableCell>
                  <Button variant="danger" size="icon" onClick={() => handleRemoveOrgMember(m.id)}>
                    <Trash2 size={12} />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <form onSubmit={handleAddOrgMember} className="flex gap-2.5 px-5 py-3 border-t border-border">
          <select
            value={addOrgUser} onChange={e => setAddOrgUser(e.target.value)}
            className="flex-1 h-9 rounded-md border border-border bg-surface px-3 text-sm text-foreground cursor-pointer"
          >
            <option value="">Select user to add…</option>
            {users.filter(u => !orgMembers.find(m => m.user_id === u.id)).map(u => (
              <option key={u.id} value={u.id}>{u.username ?? u.id}</option>
            ))}
          </select>
          <Button size="sm" type="submit" disabled={!addOrgUser || addingOrg}>
            <Plus size={13} /> {addingOrg ? "Adding…" : "Add"}
          </Button>
        </form>
      </Card>

      {workspaces.length > 0 && (
        <Card className="overflow-hidden">
          <CardHeader className="flex-wrap">
            <CardTitle className="flex items-center gap-2">
              <Layers size={14} className="text-foreground-muted" /> Workspace members
            </CardTitle>
            <select
              value={selectedWs} onChange={e => setSelectedWs(e.target.value)}
              className="h-8 rounded-md border border-border bg-surface px-2.5 text-xs text-foreground cursor-pointer"
            >
              {workspaces.map(w => <option key={w.id} value={w.id}>{w.name ?? w.slug}</option>)}
            </select>
          </CardHeader>
          <Table>
            <TableHeader>
              <TableRow><TableHead>User</TableHead><TableHead>User ID</TableHead><TableHead>Joined</TableHead><TableHead className="w-[60px]" /></TableRow>
            </TableHeader>
            <TableBody>
              {wsMembers.map(m => (
                <TableRow key={m.id}>
                  <TableCell className="font-medium">{userName(m.user_id)}</TableCell>
                  <TableCell><span className="font-mono text-xs">{m.user_id.slice(0, 18)}…</span></TableCell>
                  <TableCell className="text-foreground-muted text-xs">{new Date(m.created_at).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <Button variant="danger" size="icon" onClick={() => handleRemoveWsMember(m.id)}>
                      <Trash2 size={12} />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <form onSubmit={handleAddWsMember} className="flex gap-2.5 px-5 py-3 border-t border-border">
            <select
              value={addWsUser} onChange={e => setAddWsUser(e.target.value)}
              className="flex-1 h-9 rounded-md border border-border bg-surface px-3 text-sm text-foreground cursor-pointer"
            >
              <option value="">Select user to add…</option>
              {users.filter(u => !wsMembers.find(m => m.user_id === u.id)).map(u => (
                <option key={u.id} value={u.id}>{u.username ?? u.id}</option>
              ))}
            </select>
            <Button size="sm" type="submit" disabled={!addWsUser || addingWs}>
              <Plus size={13} /> {addingWs ? "Adding…" : "Add"}
            </Button>
          </form>
        </Card>
      )}
    </section>
  );
}
