"use client";

/**
 * Role assignment panel for the user detail page.
 *
 * Lists the user's active role assignments (from /v1/users/{id}/roles)
 * and offers a Select + Grant button to assign a new role from the
 * existing roles catalog. Revoke is inline.
 */

import { useMemo, useState } from "react";

import { Badge, Button, ErrorState, Skeleton } from "@/components/ui";
import {
  useGrantUserRole,
  useRevokeUserRole,
  useUserRoles,
} from "@/features/iam-users/hooks/use-users";
import { useRoles } from "@/features/iam-roles/hooks/use-roles";

type Props = {
  userId: string;
  defaultOrgId: string | null;
};

export function RoleAssignmentPanel({ userId, defaultOrgId }: Props) {
  const assignmentsQ = useUserRoles(userId);
  const rolesQ = useRoles({ limit: 200 });
  const grant = useGrantUserRole(userId);
  const revoke = useRevokeUserRole(userId);

  const [selectedRoleId, setSelectedRoleId] = useState("");
  const [error, setError] = useState<string | null>(null);

  const assignedIds = useMemo(
    () => new Set((assignmentsQ.data ?? []).map((a) => a.role_id)),
    [assignmentsQ.data],
  );

  const allRoles = rolesQ.data?.items ?? [];
  const assignableRoles = useMemo(
    () => allRoles.filter((r) => !assignedIds.has(r.id)),
    [allRoles, assignedIds],
  );

  async function onGrant() {
    if (!selectedRoleId) return;
    setError(null);
    try {
      await grant.mutateAsync({
        role_id: selectedRoleId,
        org_id: defaultOrgId,
      });
      setSelectedRoleId("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function onRevoke(roleId: string, orgId: string) {
    setError(null);
    try {
      await revoke.mutateAsync({ role_id: roleId, org_id: orgId });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <section
      className="rounded border"
      style={{
        background: "var(--bg-surface)",
        borderColor: "var(--border)",
      }}
    >
      <header
        className="px-4 py-3 border-b flex items-center justify-between"
        style={{ borderColor: "var(--border)" }}
      >
        <span className="label-caps">Role assignments</span>
        <span
          className="text-xs"
          style={{ color: "var(--text-muted)" }}
        >
          {assignmentsQ.data?.length ?? 0} active
        </span>
      </header>

      <div className="p-4 space-y-4">
        {/* Grant new role */}
        <div className="flex flex-col sm:flex-row gap-3">
          <select
            className="rounded border px-3 py-2 text-sm flex-1 font-mono-data"
            style={{
              background: "var(--bg-elevated)",
              borderColor: "var(--border-bright)",
              color: "var(--text-primary)",
            }}
            value={selectedRoleId}
            onChange={(e) => setSelectedRoleId(e.target.value)}
          >
            <option value="">Select a role to grant…</option>
            {assignableRoles.map((r) => (
              <option key={r.id} value={r.id}>
                {r.code ?? r.id.slice(0, 8)}
                {r.label ? ` · ${r.label}` : ""}
              </option>
            ))}
          </select>
          <Button
            variant="primary"
            size="sm"
            onClick={onGrant}
            disabled={!selectedRoleId || grant.isPending}
          >
            {grant.isPending ? "Granting…" : "Grant role"}
          </Button>
        </div>

        {error && (
          <p className="text-xs" style={{ color: "var(--danger)" }}>
            {error}
          </p>
        )}

        {/* Active assignments */}
        {assignmentsQ.isLoading ? (
          <Skeleton className="h-12" />
        ) : assignmentsQ.isError ? (
          <ErrorState
            message={String(assignmentsQ.error)}
            retry={() => {
              void assignmentsQ.refetch();
            }}
          />
        ) : (assignmentsQ.data ?? []).length === 0 ? (
          <p
            className="text-sm"
            style={{ color: "var(--text-muted)" }}
          >
            No roles assigned. Grant one above.
          </p>
        ) : (
          <ul className="divide-y" style={{ borderColor: "var(--border)" }}>
            {(assignmentsQ.data ?? []).map((a) => (
              <li
                key={a.assignment_id}
                className="py-3 flex items-center justify-between gap-3"
              >
                <div className="flex flex-col gap-1">
                  <span
                    className="font-mono-data text-sm"
                    style={{ color: "var(--text-primary)" }}
                  >
                    {a.role_code ?? a.role_id.slice(0, 8)}
                  </span>
                  {a.role_label && (
                    <span
                      className="text-xs"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      {a.role_label}
                    </span>
                  )}
                  {a.role_description && (
                    <span
                      className="text-xs"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {a.role_description}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  {a.expires_at ? (
                    <Badge tone="amber">
                      expires {new Date(a.expires_at).toLocaleDateString()}
                    </Badge>
                  ) : (
                    <Badge tone="success">active</Badge>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onRevoke(a.role_id, a.org_id)}
                    disabled={revoke.isPending}
                  >
                    Revoke
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
