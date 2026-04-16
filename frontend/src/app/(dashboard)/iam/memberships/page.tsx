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

  return (
    <>
      <PageHeader
        title="Memberships"
        description="User assignments to orgs and workspaces. lnk rows are immutable — revoke = delete."
        testId="heading-memberships"
        actions={
          <Button
            onClick={() => setOpenAssign(true)}
            data-testid="open-assign-membership"
          >
            + Assign
          </Button>
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="mb-4 inline-flex gap-1 rounded-lg border border-zinc-200 bg-white p-1 dark:border-zinc-800 dark:bg-zinc-950">
          {(["org", "workspace"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              data-testid={`tab-${t}`}
              className={cn(
                "rounded-md px-3 py-1.5 text-xs font-medium transition",
                tab === t
                  ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                  : "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50"
              )}
            >
              {t === "org" ? "Org memberships" : "Workspace memberships"}
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

  if (isLoading) return <Skeleton className="h-12 w-full" />;
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
          <TH>Assigned</TH>
          <TH />
        </tr>
      </THead>
      <TBody>
        {rows.items.map((m) => {
          const user = users?.items.find((u) => u.id === m.user_id);
          const org = orgs?.items.find((o) => o.id === m.org_id);
          return (
            <TR key={m.id}>
              <TD>{user?.display_name ?? user?.email ?? m.user_id.slice(0, 8)}</TD>
              <TD>
                <span className="font-mono text-xs">
                  {org?.slug ?? m.org_id.slice(0, 8)}
                </span>
              </TD>
              <TD>
                <span className="text-xs text-zinc-500">
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
  const del = useDeleteWorkspaceMembership();

  if (isLoading) return <Skeleton className="h-12 w-full" />;
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
          return (
            <TR key={m.id}>
              <TD>{user?.display_name ?? user?.email ?? m.user_id.slice(0, 8)}</TD>
              <TD>
                <span className="font-mono text-xs">
                  {ws?.slug ?? m.workspace_id.slice(0, 8)}
                </span>
              </TD>
              <TD>
                <span className="text-xs text-zinc-500">
                  {m.org_id.slice(0, 8)}…
                </span>
              </TD>
              <TD>
                <span className="text-xs text-zinc-500">
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
        <div className="inline-flex gap-1 rounded-lg border border-zinc-200 bg-zinc-50 p-1 dark:border-zinc-800 dark:bg-zinc-900">
          {(["org", "workspace"] as Tab[]).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setMode(t)}
              className={cn(
                "rounded-md px-3 py-1.5 text-xs font-medium transition",
                mode === t
                  ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                  : "text-zinc-600 dark:text-zinc-400"
              )}
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
