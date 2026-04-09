"use client";

import * as React from "react";
import { Plus, Trash2, Star } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth-context";
import {
  listOrgMemberships, createOrg, addOrgMembership, removeOrgMembership,
} from "@/lib/api";
import type { OrgMembership } from "@/types/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";

function toSlug(s: string) {
  return s.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
}

export default function OrgsSettingsPage() {
  const { status, ...rest } = useAuth();
  const accessToken = status === "authenticated" ? (rest as { accessToken: string }).accessToken : null;
  const me = status === "authenticated"
    ? (rest as { me: { user_id: string; username: string | null; email: string | null; session_id: string } }).me
    : null;

  const [memberships, setMemberships] = React.useState<OrgMembership[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [showCreate, setShowCreate] = React.useState(false);
  const [defaultOrgId, setDefaultOrgId] = React.useState<string | null>(
    typeof window !== "undefined" ? localStorage.getItem("kf_default_org") : null
  );

  async function load() {
    if (!me || !accessToken) return;
    const res = await listOrgMemberships(me.user_id, accessToken);
    if (res.ok) setMemberships(res.data.items);
    setLoading(false);
  }

  React.useEffect(() => { load(); }, [me?.user_id, accessToken]);

  if (!accessToken || !me) return null;

  async function handleRemove(id: string) {
    const res = await removeOrgMembership(id, accessToken!);
    if (res.ok) { toast.success("Removed from org"); load(); }
    else toast.error(res.error.message);
  }

  function handleSetDefault(orgId: string) {
    localStorage.setItem("kf_default_org", orgId);
    setDefaultOrgId(orgId);
    toast.success("Default org updated");
  }

  return (
    <section>
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-base font-semibold">Organizations</h2>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus size={13} /> Create org
        </Button>
      </div>
      <p className="text-xs text-foreground-muted mb-5">Your org memberships. Set a default to auto-select on login.</p>

      <Card className="overflow-hidden">
        {loading ? (
          <div className="p-6 text-foreground-muted text-center text-sm">Loading…</div>
        ) : memberships.length === 0 ? (
          <div className="p-8 text-foreground-muted text-center text-sm">No org memberships.</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Organization</TableHead>
                <TableHead>Slug</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[120px]">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {memberships.map(m => (
                <TableRow key={m.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {m.org_name ?? m.org_slug}
                      {defaultOrgId === m.org_id && <Badge variant="info">default</Badge>}
                    </div>
                  </TableCell>
                  <TableCell><span className="font-mono text-xs">{m.org_slug}</span></TableCell>
                  <TableCell>
                    <Badge variant={m.org_is_active ? "success" : "danger"}>
                      {m.org_is_active ? "active" : "inactive"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1.5">
                      <Button
                        variant="ghost" size="icon"
                        title="Set as default"
                        onClick={() => handleSetDefault(m.org_id)}
                        className={defaultOrgId === m.org_id ? "text-[color:var(--warning)]" : ""}
                      >
                        <Star size={13} />
                      </Button>
                      <Button variant="danger" size="icon" title="Leave org" onClick={() => handleRemove(m.id)}>
                        <Trash2 size={13} />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      {showCreate && (
        <CreateOrgModal
          me={me} accessToken={accessToken}
          onClose={() => setShowCreate(false)}
          onCreated={() => { setShowCreate(false); load(); toast.success("Organization created"); }}
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

function CreateOrgModal({ me, accessToken, onClose, onCreated, onError }: {
  me: { user_id: string }; accessToken: string;
  onClose: () => void; onCreated: () => void; onError: (m: string) => void;
}) {
  const [name, setName] = React.useState("");
  const [slug, setSlug] = React.useState("");
  const [desc, setDesc] = React.useState("");
  const [saving, setSaving] = React.useState(false);

  function handleNameChange(v: string) { setName(v); setSlug(toSlug(v)); }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    const res = await createOrg({ name, slug, description: desc || undefined, owner_id: me.user_id }, accessToken);
    setSaving(false);
    if (res.ok) {
      await addOrgMembership(me.user_id, res.data.id, accessToken);
      onCreated();
    } else {
      onError(res.error.message);
    }
  }

  return (
    <Modal title="Create organization" onClose={onClose}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
        <div className="flex flex-col gap-1.5">
          <Label>Name</Label>
          <Input value={name} onChange={e => handleNameChange(e.target.value)} placeholder="Acme Corp" required />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Slug</Label>
          <Input value={slug} onChange={e => setSlug(e.target.value)} placeholder="acme-corp" required />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Description <span className="font-normal normal-case">(optional)</span></Label>
          <Input value={desc} onChange={e => setDesc(e.target.value)} placeholder="Short description…" />
        </div>
        <div className="flex gap-2.5 justify-end">
          <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
          <Button type="submit" disabled={saving}>{saving ? "Creating…" : "Create"}</Button>
        </div>
      </form>
    </Modal>
  );
}
