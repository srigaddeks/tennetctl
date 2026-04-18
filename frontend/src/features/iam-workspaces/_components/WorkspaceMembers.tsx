"use client";

import { useMemo, useState } from "react";

import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
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
  useCreateWorkspaceMembership,
  useDeleteWorkspaceMembership,
  useWorkspaceMemberships,
} from "@/features/iam-memberships/hooks/use-memberships";
import { useUsers } from "@/features/iam-users/hooks/use-users";
import { ApiClientError } from "@/lib/api";

export function WorkspaceMembers({
  workspaceId,
  orgId,
}: {
  workspaceId: string;
  orgId: string;
}) {
  const { toast } = useToast();
  const [pendingUserId, setPendingUserId] = useState<string>("");

  const memberships = useWorkspaceMemberships({ workspace_id: workspaceId });
  const users = useUsers({ limit: 500 });
  const addMember = useCreateWorkspaceMembership();
  const removeMember = useDeleteWorkspaceMembership();

  const usersList = users.data?.items ?? [];
  const userById = useMemo(() => {
    const m = new Map<string, (typeof usersList)[number]>();
    for (const u of usersList) m.set(u.id, u);
    return m;
  }, [usersList]);

  const memberIds = useMemo(
    () => new Set((memberships.data?.items ?? []).map((m) => m.user_id)),
    [memberships.data],
  );

  const candidates = useMemo(
    () =>
      (users.data?.items ?? []).filter(
        (u) => u.is_active && !memberIds.has(u.id),
      ),
    [users.data, memberIds],
  );

  async function handleAdd() {
    if (!pendingUserId) return;
    try {
      await addMember.mutateAsync({ user_id: pendingUserId, workspace_id: workspaceId });
      toast("Member added", "success");
      setPendingUserId("");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  async function handleRemove(membershipId: string, userLabel: string) {
    if (!confirm(`Remove ${userLabel} from this workspace?`)) return;
    try {
      await removeMember.mutateAsync(membershipId);
      toast("Member removed", "success");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  return (
    <section
      className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950"
      data-testid="ws-members-section"
    >
      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
          Members
        </h2>
        <span className="text-xs text-zinc-500">
          org: <span className="font-mono">{orgId.slice(0, 8)}…</span>
        </span>
      </div>

      <div className="mb-4 flex items-end gap-2">
        <div className="flex-1">
          <Field label="Add member" htmlFor="ws-members-add-user">
            <Select
              id="ws-members-add-user"
              value={pendingUserId}
              onChange={(e) => setPendingUserId(e.target.value)}
              data-testid="ws-members-add-user"
            >
              <option value="">Select a user…</option>
              {candidates.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.display_name ?? u.email ?? u.id.slice(0, 8)}
                  {u.email ? ` <${u.email}>` : ""}
                </option>
              ))}
            </Select>
          </Field>
        </div>
        <Button
          onClick={handleAdd}
          disabled={!pendingUserId}
          loading={addMember.isPending}
          data-testid="ws-members-add-submit"
        >
          Add
        </Button>
      </div>

      {memberships.isLoading && (
        <div className="flex flex-col gap-2" data-testid="ws-members-loading">
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-full" />
        </div>
      )}

      {memberships.isError && (
        <ErrorState
          message={
            memberships.error instanceof Error
              ? memberships.error.message
              : "Failed to load members"
          }
          retry={() => memberships.refetch()}
        />
      )}

      {memberships.data && memberships.data.items.length === 0 && (
        <EmptyState
          title="No members yet"
          description="Add a user to this workspace using the selector above."
        />
      )}

      {memberships.data && memberships.data.items.length > 0 && (
        <div data-testid="ws-members-table">
        <Table>
          <THead>
            <tr>
              <TH>User</TH>
              <TH>Email</TH>
              <TH>Joined</TH>
              <TH></TH>
            </tr>
          </THead>
          <TBody>
            {memberships.data.items.map((m) => {
              const user = userById.get(m.user_id);
              const label = user?.display_name ?? user?.email ?? m.user_id.slice(0, 8);
              return (
                <TR key={m.id}>
                  <TD>
                    <span className="text-sm">{label}</span>
                    {!user && (
                      <Badge tone="zinc" className="ml-2">
                        unknown
                      </Badge>
                    )}
                  </TD>
                  <TD>
                    <span className="text-xs text-zinc-500">
                      {user?.email ?? "—"}
                    </span>
                  </TD>
                  <TD>
                    <span className="text-xs text-zinc-500">
                      {m.created_at.slice(0, 10)}
                    </span>
                  </TD>
                  <TD>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleRemove(m.id, label)}
                      data-testid={`ws-member-remove-${m.id}`}
                    >
                      Remove
                    </Button>
                  </TD>
                </TR>
              );
            })}
          </TBody>
        </Table>
        </div>
      )}
    </section>
  );
}
