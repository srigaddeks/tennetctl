import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ApiSuccess, PortalView, RoleViewAssignment } from "@/types/api";

const BASE = "/api/v1/iam";

// ─── Query keys ────────────────────────────────────────────────────────────────

export const portalViewsKeys = {
  all: ["iam", "portal-views"] as const,
  roleViews: (roleId: string) => ["iam", "portal-views", "role", roleId] as const,
  myViews: (orgId: string) => ["iam", "my-views", orgId] as const,
};

// ─── Queries ───────────────────────────────────────────────────────────────────

/** List all non-deprecated portal views from the global catalog. */
export function usePortalViews() {
  return useQuery<PortalView[]>({
    queryKey: portalViewsKeys.all,
    queryFn: async () => {
      const res = await fetch(`${BASE}/portal-views`);
      const data: ApiSuccess<PortalView[]> = await res.json();
      if (!data.ok) throw new Error((data as unknown as { error: { message: string } }).error?.message);
      return data.data;
    },
  });
}

/** List views granted to a specific role. */
export function useRoleViews(roleId: string | undefined) {
  return useQuery<RoleViewAssignment[]>({
    queryKey: roleId ? portalViewsKeys.roleViews(roleId) : [],
    enabled: !!roleId,
    queryFn: async () => {
      const res = await fetch(`${BASE}/roles/${roleId}/views`);
      const data: ApiSuccess<RoleViewAssignment[]> = await res.json();
      if (!data.ok) throw new Error((data as unknown as { error: { message: string } }).error?.message);
      return data.data;
    },
  });
}

/** Resolve the current user's granted portal views. */
export function useMyViews(orgId: string | undefined) {
  return useQuery<PortalView[]>({
    queryKey: orgId ? portalViewsKeys.myViews(orgId) : [],
    enabled: !!orgId,
    queryFn: async () => {
      const res = await fetch(`${BASE}/my-views`, {
        headers: orgId ? { "x-org-id": orgId } : {},
      });
      const data: ApiSuccess<PortalView[]> = await res.json();
      if (!data.ok) throw new Error((data as unknown as { error: { message: string } }).error?.message);
      return data.data;
    },
  });
}

// ─── Mutations ─────────────────────────────────────────────────────────────────

/** Attach a portal view to a role. */
export function useAttachView(roleId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (viewId: number) => {
      const res = await fetch(`${BASE}/roles/${roleId}/views`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ view_id: viewId }),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error?.message ?? "Failed to attach view");
      return data.data as RoleViewAssignment;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: portalViewsKeys.roleViews(roleId) });
    },
  });
}

/** Detach a portal view from a role. */
export function useDetachView(roleId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (viewId: number) => {
      const res = await fetch(`${BASE}/roles/${roleId}/views/${viewId}`, {
        method: "DELETE",
      });
      if (res.status !== 204) {
        const data = await res.json();
        throw new Error(data.error?.message ?? "Failed to detach view");
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: portalViewsKeys.roleViews(roleId) });
    },
  });
}
