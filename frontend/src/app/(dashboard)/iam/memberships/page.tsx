"use client";

import { useState } from "react";

import { Modal } from "@/components/modal";
import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
  Button,
  EmptyState,
  Field,
  Select,
  Skeleton,
  StatCard,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import {
  useCreateOrgMembership,
  useCreateWorkspaceMembership,
  useDeleteOrgMembership,
  useDeleteWorkspaceMembership,
  useOrgMemberships,
  useWorkspaceMemberships,
} from "@/features/iam-memberships/hooks/use-memberships";
import { useOrgs } from "@/features/iam-orgs/hooks/use-orgs";
import { useUsers } from "@/features/iam-users/hooks/use-users";
import { useWorkspaces } from "@/features/iam-workspaces/hooks/use-workspaces";
import { ApiClientError } from "@/lib/api";
import { cn } from "@/lib/cn";

type Tab = "org" | "workspace";

export default function MembershipsPage() {
  const [tab, setTab] = useState<Tab>("org");
  const [openAssign, setOpenAssign] = useState(false);

  const { data: orgRows } = useOrgMemberships();
  const { data: wsRows } = useWorkspaceMemberships();

  const totalOrg = orgRows?.items.length ?? 0;
  const totalWs = wsRows?.items.length ?? 0;
  const totalMemberships = totalOrg + totalWs;

  return (
    <>
      <PageHeader
        title="Memberships"
        description="User assignments to orgs and workspaces. lnk rows are immutable — revoke = delete."
        testId="heading-memberships"
        actions={
          <Button
            variant="primary"
            onClick={() => setOpenAssign(true)}
            data-testid="open-assign-membership"
          >
            + Assign
          </Button>
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6 animate-fade-in">

        {/* Stat cards */}
        <div className="mb-6 grid grid-cols-3 gap-4">
          <StatCard
            label="Total Memberships"
            value={totalMemberships}
            sub="org + workspace"
            accent="blue"
          />
          <StatCard
            label="Org Memberships"
            value={totalOrg}
            sub="users in orgs"
            accent="green"
          />
          <StatCard
            label="Workspace Memberships"
            value={totalWs}
            sub="users in workspaces"
            accent="blue"
          />
        </div>

        {/* Tab switcher */}
        <div
          className="mb-5 inline-flex gap-1 rounded-lg p-1"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
          }}
        >
          {(["org", "workspace"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              data-testid={`tab-${t}`}
              className={cn(
                "rounded-md px-4 py-1.5 text-xs font-medium transition",
              )}
              style={
                tab === t
                  ? {
                      background: "var(--accent)",
                      color: "#fff",
                    }
                  : {
                      background: "transparent",
                      color: "var(--text-secondary)",
                    }
              }
            >
              {t === "org" ? "Org memberships" : "Workspace memberships"}
              <span
                className="ml-2 rounded px-1.5 py-0.5 font-mono-data"
                style={{
                  background: tab === t ? "rgba(255,255,255,0.15)" : "var(--bg-elevated)",
                  fontSize: "10px",
                }}
              >
                {t === "org" ? totalOrg : totalWs}
              </span>
            </button>
          ))}
        </div>

        {tab === "org" ? <OrgMembersTable /> : <WorkspaceMembersTable />}
      </div>

      {openAssign && (
        <AssignDialog
          defaultTab={tab}
          open={openAssign}
          onClose={() => setOpenAssign(false)}
        />
      )}
    </>
  );
}

function OrgMembersTable() {
  const { toast } = useToast();
  const { data: rows, isLoading } = useOrgMemberships();
  const { data: orgs } = useOrgs({ limit: 500 });
  const { data: users } = useUsers({ limit: 500 });
  const del = useDeleteOrgMembership();

  if (isLoading)
    return (
      <div className="flex flex-col gap-2">
        {[1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} className="h-11 w-full" />
        ))}
      </div>
    );

  if (!rows || rows.items.length === 0)
    return (
      <EmptyState
        title="No org memberships"
        description="Assign users to orgs to grant access."
      />
    );

  return (
    <Table>
      <THead>
        <tr>
          <TH>User</TH>
          <TH>Org</TH>
          <TH>Membership ID</TH>
          <TH>Assigned</TH>
          <TH />
        </tr>
      </THead>
      <TBody>
        {rows.items.map((m) => {
          const user = users?.items.find((u) => u.id === m.user_id);
          const org = orgs?.items.find((o) => o.id === m.org_id);
          const initial = (user?.display_name || user?.email || m.user_id)
            .slice(0, 1)
            .toUpperCase();
          return (
            <TR key={m.id}>
              <TD>
                <div className="flex items-center gap-2.5">
                  <div
                    className="flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold"
                    style={{
                      background: "var(--accent-muted)",
                      color: "var(--accent)",
                      border: "1px solid var(--accent-dim)",
                    }}
                  >
                    {initial}
                  </div>
                  <span style={{ color: "var(--text-primary)" }}>
                    {user?.display_name ?? user?.email ?? (
                      <span className="font-mono-data text-xs" style={{ color: "var(--text-muted)" }}>
                        {m.user_id.slice(0, 8)}…
                      </span>
                    )}
                  </span>
                </div>
              </TD>
              <TD>
                <span
                  className="font-mono-data text-xs"
                  style={{ color: "var(--accent)" }}
                >
                  {org?.slug ?? m.org_id.slice(0, 8)}
                </span>
              </TD>
              <TD>
                <span
                  className="font-mono-data text-xs"
                  style={{ color: "var(--text-muted)" }}
                >
                  {m.id.slice(0, 8)}…
                </span>
              </TD>
              <TD>
                <span
                  className="font-mono-data text-xs"
                  style={{ color: "var(--text-secondary)" }}
                >
                  {m.created_at.slice(0, 10)}
                </span>
              </TD>
              <TD className="text-right">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    if (!confirm("Revoke membership?")) return;
                    try {
                      await del.mutateAsync(m.id);
                      toast("Revoked", "success");
                    } catch (err) {
                      const msg =
                        err instanceof ApiClientError
                          ? err.message
                          : String(err);
                      toast(msg, "error");
                    }
                  }}
                >
                  Revoke
                </Button>
              </TD>
            </TR>
          );
        })}
      </TBody>
    </Table>
  );
}

function WorkspaceMembersTable() {
  const { toast } = useToast();
  const { data: rows, isLoading } = useWorkspaceMemberships();
  const { data: wss } = useWorkspaces({ limit: 500 });
  const { data: users } = useUsers({ limit: 500 });
  const { data: orgs } = useOrgs({ limit: 500 });
  const del = useDeleteWorkspaceMembership();

  if (isLoading)
    return (
      <div className="flex flex-col gap-2">
        {[1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} className="h-11 w-full" />
        ))}
      </div>
    );

  if (!rows || rows.items.length === 0)
    return (
      <EmptyState
        title="No workspace memberships"
        description="Assign users to workspaces to grant scoped access."
      />
    );

  return (
    <Table>
      <THead>
        <tr>
          <TH>User</TH>
          <TH>Workspace</TH>
          <TH>Org</TH>
          <TH>Assigned</TH>
          <TH />
        </tr>
      </THead>
      <TBody>
        {rows.items.map((m) => {
          const user = users?.items.find((u) => u.id === m.user_id);
          const ws = wss?.items.find((w) => w.id === m.workspace_id);
          const org = orgs?.items.find((o) => o.id === m.org_id);
          const initial = (user?.display_name || user?.email || m.user_id)
            .slice(0, 1)
            .toUpperCase();
          return (
            <TR key={m.id}>
              <TD>
                <div className="flex items-center gap-2.5">
                  <div
                    className="flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold"
                    style={{
                      background: "var(--accent-muted)",
                      color: "var(--accent)",
                      border: "1px solid var(--accent-dim)",
                    }}
                  >
                    {initial}
                  </div>
                  <span style={{ color: "var(--text-primary)" }}>
                    {user?.display_name ?? user?.email ?? (
                      <span className="font-mono-data text-xs" style={{ color: "var(--text-muted)" }}>
                        {m.user_id.slice(0, 8)}…
                      </span>
                    )}
                  </span>
                </div>
              </TD>
              <TD>
                <span
                  className="font-mono-data text-xs"
                  style={{ color: "var(--accent)" }}
                >
                  {ws?.slug ?? m.workspace_id.slice(0, 8)}
                </span>
              </TD>
              <TD>
                <span
                  className="font-mono-data text-xs"
                  style={{ color: "var(--text-secondary)" }}
                >
                  {org?.slug ?? m.org_id.slice(0, 8)}…
                </span>
              </TD>
              <TD>
                <span
                  className="font-mono-data text-xs"
                  style={{ color: "var(--text-secondary)" }}
                >
                  {m.created_at.slice(0, 10)}
                </span>
              </TD>
              <TD className="text-right">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    if (!confirm("Revoke?")) return;
                    try {
                      await del.mutateAsync(m.id);
                      toast("Revoked", "success");
                    } catch (err) {
                      const msg =
                        err instanceof ApiClientError
                          ? err.message
                          : String(err);
                      toast(msg, "error");
                    }
                  }}
                >
                  Revoke
                </Button>
              </TD>
            </TR>
          );
        })}
      </TBody>
    </Table>
  );
}

function AssignDialog({
  defaultTab,
  open,
  onClose,
}: {
  defaultTab: Tab;
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const [mode, setMode] = useState<Tab>(defaultTab);
  const [userId, setUserId] = useState("");
  const [orgId, setOrgId] = useState("");
  const [workspaceId, setWorkspaceId] = useState("");

  const { data: users } = useUsers({ limit: 500 });
  const { data: orgs } = useOrgs({ limit: 500 });
  const { data: wss } = useWorkspaces({
    limit: 500,
    org_id: orgId || undefined,
  });
  const createOrg = useCreateOrgMembership();
  const createWs = useCreateWorkspaceMembership();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      if (mode === "org") {
        if (!userId || !orgId) return toast("User and org required", "error");
        await createOrg.mutateAsync({ user_id: userId, org_id: orgId });
        toast("Assigned to org", "success");
      } else {
        if (!userId || !workspaceId)
          return toast("User and workspace required", "error");
        await createWs.mutateAsync({
          user_id: userId,
          workspace_id: workspaceId,
        });
        toast("Assigned to workspace", "success");
      }
      onClose();
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  const submitting = createOrg.isPending || createWs.isPending;

  return (
    <Modal open={open} onClose={onClose} title="Assign membership">
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <div
          className="inline-flex gap-1 rounded-lg p-1"
          style={{
            background: "var(--bg-elevated)",
            border: "1px solid var(--border)",
          }}
        >
          {(["org", "workspace"] as Tab[]).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setMode(t)}
              className="rounded-md px-3 py-1.5 text-xs font-medium transition"
              style={
                mode === t
                  ? { background: "var(--accent)", color: "#fff" }
                  : { color: "var(--text-secondary)" }
              }
            >
              {t === "org" ? "To org" : "To workspace"}
            </button>
          ))}
        </div>

        <Field label="User" required htmlFor="assign-user">
          <Select
            id="assign-user"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            data-testid="assign-user"
          >
            <option value="">Select user…</option>
            {users?.items.map((u) => (
              <option key={u.id} value={u.id}>
                {u.display_name ?? u.email ?? u.id.slice(0, 8)} — {u.email}
              </option>
            ))}
          </Select>
        </Field>

        {mode === "org" ? (
          <Field label="Org" required htmlFor="assign-org">
            <Select
              id="assign-org"
              value={orgId}
              onChange={(e) => setOrgId(e.target.value)}
              data-testid="assign-org"
            >
              <option value="">Select org…</option>
              {orgs?.items.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.display_name ?? o.slug} ({o.slug})
                </option>
              ))}
            </Select>
          </Field>
        ) : (
          <>
            <Field label="Scope to org" hint="filters workspaces" htmlFor="assign-scope-org">
              <Select
                id="assign-scope-org"
                value={orgId}
                onChange={(e) => {
                  setOrgId(e.target.value);
                  setWorkspaceId("");
                }}
              >
                <option value="">All orgs</option>
                {orgs?.items.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.display_name ?? o.slug}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Workspace" required htmlFor="assign-ws">
              <Select
                id="assign-ws"
                value={workspaceId}
                onChange={(e) => setWorkspaceId(e.target.value)}
                data-testid="assign-workspace"
              >
                <option value="">Select workspace…</option>
                {wss?.items.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.display_name ?? w.slug} ({w.slug})
                  </option>
                ))}
              </Select>
            </Field>
          </>
        )}

        <div className="mt-2 flex justify-end gap-2">
          <Button variant="secondary" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            loading={submitting}
            data-testid="assign-submit"
          >
            Assign
          </Button>
        </div>
      </form>
    </Modal>
  );
}
